"""Extract rank233 check-through rivers from the authenticated B695/B699 native turn jobs."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b689_rank84 as original
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_b714_rank255_rivers import DECK, cards
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible

MODEL='ln-3bp-3b_r_model-4k40h1'
LINE='x b33 c/x x/'
CASES={
    'Ts9s6h':('2c','B695_R84_TS9S6H','edf549f1ea8f2acd1c3b839b29a3334efdf89476e9a87a11a8f7658e23063299'),
    'Th9h7c':('2s','B699_R84_TH9H7C','8712803dce0228c02fd854dd1efd39b4c7b4ffa38f1d08f07c5039209979f381'),
    'Ts8s7h':('2c','B699_R84_TS8S7H','a121527bc646b49df6d9989def4e0e29fbab196b61c88f834fc874afefa895a8'),
}
PARENT='ln-3bp-3b_t_model-ciziut'


def source(flop,pipeline,ranges,pool):
    turn,code,digest=CASES[flop]
    path=Path('data/solver_evidence')/('NL2_'+code+'.zip')
    assert sha(path.read_bytes())==digest
    group=json.loads(Path('data/solver_evidence/reverified/rank84.json').read_bytes())
    pin,=[p for p in group['pins'] if p['flop']==flop]
    assert (group['rank'],group['model_id'],pin['archive_code'],pin['archive_sha256'],pin['turn'])==(84,PARENT,code,digest,turn)
    with ZipFile(path) as z:
        load=lambda n:json.loads(z.read(n))
        root=load('flop/result.json'); root_job=load('flop/job.json'); report=load('proof.json')
        assert (root['flop'],root['pot'],root['stack'],sha(z.read('flop/result.json')))==(flop,2100,9000,report['root_sha256'])
        assert sha(z.read('flop/job.json'))==report['root_job_sha256'] and (root_job['flop_oop'],root_job['flop_ip'])==('33%','33%')
        assert not root_job.get('locks') and not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
        assert (root_job['oop'],root_job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('SB3_BTN','gto'))
        jobs={v:load(turn+'-'+v+'/job.json') for v in ('gto','exp_oop')}
        games={v:load(turn+'-'+v+'/result.json') for v in jobs}
        assert sha(z.read(turn+'-gto/result.json'))==pin['original_GTO_SHA256']
        assert sha(z.read(turn+'-exp_oop/result.json'))==pin['actual_NL2_SHA256']
    gto=original.turn_job(root,turn,pipeline)
    locked,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='SB3_BTN')),job=gto),'exp_oop',pool,pipeline)
    locked['out']='result.json'
    assert jobs==dict(gto=gto,exp_oop=locked)
    for v,g in games.items():
        assert (g['pot'],g['stack'],g['flop'])==(3486,8307,flop) and jobs[v]['extract']==[dict(prefix=[],street=True)]
        assert len(g['nodes'])==18 and all(len(n['board'])==8 and n['board'].endswith(turn) for n in g['nodes'])
        assert 0<=g['info']['gto_expl_pct']<=.5
    assert not games['gto']['info'].get('lock_stats') and 0<=games['exp_oop']['info']['hero_gap_pct']<=.5
    assert games['gto']['hands']==games['exp_oop']['hands']
    return root,jobs,games,rules,pin,report['root_sha256']


def eligible_pairs(root,game,turn,route):
    """Require one physical SB/BTN deal through both flop and turn choices."""
    root_nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    limit,=[n for n in root['nodes'] if n['line']==original.LINE and n['board'].endswith(turn)]
    start,bet,call=[root_nodes[k] for k in ('','x','x b33')]
    assert (start['player'],bet['player'],call['player'],start['pot'],bet['pot'],call['pot'])==(0,1,0,2100,2100,2793)
    weights=[{cardkey(h) for h,w in zip(root['hands'][i],limit['wr'][i],strict=True) if w>1e-4} for i in (0,1)]
    actors=weights[0]&accepted(start,root['hands'],'x')&accepted(call,root['hands'],'c')
    foes=weights[1]&accepted(bet,root['hands'],'b33')
    turn_nodes={n['line']:n for n in game['nodes'] if len(n['board'])==8}
    sb,btn=turn_nodes[original.LINE],turn_nodes[original.LINE+'x']
    assert (sb['player'],btn['player'],sb['pot'],btn['pot'],sb['bets'],btn['bets'])==(0,1,3486,3486,[0,0],[0,0])
    public=sb['board'];assert public==btn['board']==limit['board']
    actors &= accepted(sb,game['hands'],'x')
    foes &= accepted(btn,game['hands'],'x')
    def previous(hand):
        f,t=[hand_cell(''.join(hand),public[:n]) for n in (6,8)]
        path=route['flop_turn']
        return f[1] in path.get(f[0].split(':')[0],{}).get('parents',[]) and path.get(t[0].split(':')[0],{}).get('decisions',{}).get(t[1])=='過'
    pairs={(h,v) for h in actors if previous(h) and cards(public).isdisjoint(h) for v in foes if set(h).isdisjoint(v) and cards(public).isdisjoint(v)}
    return pairs,public


def preregister(root,games,turn,route):
    pg,public=eligible_pairs(root,games['gto'],turn,route)
    pe,other=eligible_pairs(root,games['exp_oop'],turn,route)
    assert public==other
    common=pg&pe
    allowed={}
    for river in DECK:
        if river in cards(public):continue
        rows={(h,v) for h,v in common if river not in h and river not in v and route['river'].get(hand_cell(''.join(h),public+river)[0])=='過'}
        if rows:allowed[river]=rows
    options=list(allowed)
    rivers=options if len(options)<=12 else [options[round(i*(len(options)-1)/11)] for i in range(12)]
    return allowed,rivers,dict(common_sb_btn_private_pairs=len(common),common_sb_hands=len({h for h,v in common}),
        eligible_rivers=len(allowed),preregistered_rivers=rivers,example_per_river={r:[''.join(v) for v in min(allowed[r])] for r in rivers})


def observed(root,game,turn,rivers,allowed,route,contract):
    game.update(line0='x b33 c',turn=turn,rivers=rivers)
    masks=game_reach(root,game)[0];rows={}
    nodes=[n for n in game['nodes'] if n['line']==LINE]
    assert len(nodes)==len(rivers) and {n['board'][-2:] for n in nodes}==set(rivers)
    for n in nodes:
        public=n['board'];rv=public[-2:]
        assert (n['player'],n['pot'],n['bets'])==(0,3486,[0,0]) and len(cards(public))==5
        assert public[6:8]==turn and cards(public[:6])==cards(root['flop'])
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=0))
        row=proof(root,game,n,masks)
        hh={h for h,v in allowed[rv]}
        accepted_check={cardkey(h) for h,b in zip(game['hands'][0],base64.b64decode(row['compatible_action_mask_b64'],validate=True),strict=True)
            if b&(1<<n['acts'].index('x'))}
        actual=sorted(''.join(h) for h in hh&accepted_check)
        assert all(route['river'][hand_cell(h,public)[0]]=='過' for h in actual)
        rows[public]=dict(reach=row,displayed_check_hands=actual)
    return rows


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve();py=solver/'postflop/py'
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==original.SOLVER
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==original.RUST
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==POOL
    assert sha((py/'pipeline.py').read_bytes())==PIPELINE and sha((py/'ranges.py').read_bytes())==RANGES
    sys.path.insert(0,str(py));import pipeline,ranges
    pool=json.loads(poolraw)['NL2']
    raw=a.routes.read_bytes();route=json.loads(raw)
    assert (route['model'],route['parent'],route['actor'],route['line'],route['spot'])==(MODEL,PARENT,0,LINE,'SB3_BTN')
    status=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    record=status['records'][MODEL]
    assert (record['frequency_rank'],record['source_model_id'],record['solver_profile'])==(233,PARENT,'SB3_BTN')
    assert abs(8307/3486/record['assumed_model_node_spr']-1)<.001
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    root,jobs,games,rules,pin,rootsha=source(a.flop,pipeline,ranges,pool)
    turn=CASES[a.flop][0]
    allowed,rivers,gate=preregister(root,games,turn,route)
    assert rivers
    if a.preflight:
        print(json.dumps(dict(flop=a.flop,turn=turn,gate=gate)));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True)
    (out/'rendered-routes.json').write_bytes(raw)
    policies={};common={}
    for v in ('gto','exp_oop'):
        sourcegame,job=games[v],dict(jobs[v],extract=jobs[v]['extract']+[dict(prefix=['x','x',r],street=False,raw=True) for r in rivers])
        target=out/(turn+'-'+v)
        game=solve(target,job,a.driver)
        for key in ('flop','pot','stack','hands'):assert game[key]==sourcegame[key],(v,key)
        original_nodes=[n for n in game['nodes'] if len(n['board'])==8]
        assert original_nodes==sourcegame['nodes'] and len(original_nodes)==18,(v,'original turn nodes')
        assert 0<=game['info']['gto_expl_pct']<=.5
        measured=None
        if v=='exp_oop':
            assert job['hero']==0 and 0<=game['info']['hero_gap_pct']<=.5
            measured=audit_patterns(game,job,dict(locks=rules),pool,hero_seat=0)
            assert any(n>0 for k,n in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
        else:assert not job.get('locks') and not game['info'].get('lock_stats')
        rows=observed(root,game,turn,rivers,allowed,route,contract)
        policies[v]=dict(original_turn_nodes_replayed=len(original_nodes),source_sha256=sha((target/'result.json').read_bytes()),job_sha256=sha((target/'job.json').read_bytes()),
            original_18_node_sha256=sha(compact(original_nodes)),measured_lock_application=measured,boards=rows)
        if v=='gto' and not any(row['displayed_check_hands'] for row in rows.values()):break
    if 'exp_oop' in policies:
        for board,g in policies['gto']['boards'].items():
            kept=sorted(set(g['displayed_check_hands'])&set(policies['exp_oop']['boards'][board]['displayed_check_hands']))
            if kept:common[board]=kept
    obj=dict(schema='NL2_B737_R233_FROZEN_TURN_NEW_EXTRACTS_V1',rank=233,model_id=MODEL,line=LINE,actor=0,flop=a.flop,turn=turn,
        source_parent=pin,source_root_sha256=rootsha,route_sha256=sha(raw),solver=original.SOLVER,rust=original.RUST,
        pool_sha256=POOL,ranges_sha256=RANGES,pipeline_sha256=PIPELINE,preregistered_flops=list(CASES),parent_gate=gate,
        root_recomputed=False,lock_scope='Observed aggregate partial NL2 lock on BTN with SB hero, frozen original GTO flop.',
        no_observed_per_private_hand_frequency=True,policies=policies,common=common,positive_distinct_flops=int(bool(common)),
        selected_public_board=next(iter(sorted(common)),None))
    (out/'proof.json').write_bytes(json_bytes(obj))
    print(json.dumps(dict(flop=a.flop,checked_rivers=len(rivers),common=len(common),locked='exp_oop' in policies)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','routes','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--driver',type=Path)
    p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--preflight',action='store_true')
    run(p.parse_args())

