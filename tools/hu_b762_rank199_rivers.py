"""Append missing river nodes to the paired B755 turn strategies for rank 199."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b755_rank151 as native
import hu_b759_rank46_barrel_gates as gate
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b637_rank57 import solve
from hu_sequential_cfr_reach import accepted,cardkey,game_reach
from hu_trainer_route_gate import compatible

FLOP='7h6d4s'
MODEL='ln-iso-lmp_r_model-10l8t7i'
LINE='x b50 c/x b33 c/x'
RIVERS={'2c':['3c','3d','3h','3s'],'8d':['2c','2h','2s','3c','3h','3s']}
ROUTE='tools/hu_b759_rank46_barrel_routes.cjs'


def original(path,turn,route):
    aid,digest=gate.PINS[FLOP]
    assert sha(path.read_bytes())==digest
    with ZipFile(path) as z:
        take=lambda name:json.loads(z.read(name))
        claim=take('proof.json');root=take('flop/result.json')
        assert sha(z.read('flop/result.json'))==claim['root_sha256']
        frozen,template,manifest,pin,root_job=native.source(FLOP)
        assert take('flop/job.json')==root_job and claim['source']==pin
        bounds=native.compare_extraction(frozen,root,native.CASES[FLOP])
        parent=bounds[turn]
        entry,=[t for t in claim['turns'] if t['turn']==turn]
        assert sha(compact(parent))==entry['boundary_sha256']
        games=gate.load_pair(z,entry)
        jobs={m:take(turn+'-'+m+'/job.json') for m in games}
    fs={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    live=[{cardkey(h) for h,w in zip(root['hands'][i],parent['wr'][i],strict=True) if w>1e-4} for i in (0,1)]
    bb=live[0]&accepted(fs[''],root['hands'],'x')&accepted(fs['x b50'],root['hands'],'c')
    co=live[1]&accepted(fs['x'],root['hands'],'b50')
    gates={m:gate.check(parent,bb,co,game,m,199,route) for m,game in games.items()}
    shared_bb=gates['gto'][1]&gates['exp_ip'][1]
    shared_co=gates['gto'][0]&gates['exp_ip'][0]
    public=parent['board'];per_river={}
    for r in native.DECK:
        if r in native.cards(public):
            continue
        hands={}
        for h in sorted(shared_co):
            hand=''.join(h)
            if r in h or route['river'].get(native.hand_cell(hand,public+r)[0])!='過':
                continue
            villains={v for v in shared_bb if r not in v and set(h).isdisjoint(v)}
            if villains:
                hands[hand]=villains
        if hands:per_river[r]=hands
    assert list(per_river)==RIVERS[turn]
    for mode,game in games.items():
        job=jobs[mode]
        assert len(game['nodes'])==210 and len(job['extract'])==13
        assert all(not n['line'].startswith('x b50 c/x b33 c/') for n in game['nodes'])
        assert all(e['prefix'][:3]!=['x','b33','c'] for e in job['extract'])
        assert not gates[mode][2]['sampled_river_nodes']
    return root,manifest,jobs,games,per_river,dict(source_run=gate.RUN,source_head=gate.HEAD,archive_id=aid,
        archive_sha256=digest,root_sha256=claim['root_sha256'],root_original=pin,verified_frozen_flop_nodes=len(frozen['nodes']),
        parent_raw_wr_sha256=entry['boundary_sha256'],source_policies=entry['policies'])


def compare(old,new,count):
    assert all(new[k]==old[k] for k in ('flop','pot','stack','hands'))
    key=lambda n:(n['board'],n['line'],n['player'])
    nodes={key(n):n for n in new['nodes']}
    assert len(nodes)==len(new['nodes'])==len(old['nodes'])+2*count
    for n in old['nodes']:
        assert nodes.pop(key(n))==n, key(n)
    assert {(n['line'],n['player']) for n in nodes.values()}=={(LINE[:-1],0),(LINE,1)}
    return nodes


def observed(root,game,turn,route,per_river,contract):
    game.update(line0='x b50 c',turn=turn,rivers=RIVERS[turn])
    masks=game_reach(root,game)[0]
    index={(n['board'],n['line']):n for n in game['nodes']}
    out={};deals={}
    for river,prior in per_river.items():
        target,=[n for n in game['nodes'] if (n['line'],n['player'],n['board'][-2:])==(LINE,1,river)]
        public=target['board'];check=index[public,LINE[:-1]]
        assert public[6:8]==turn and native.cards(public[:6])==native.cards(FLOP)
        assert (check['player'],check['pot'],check['bets'],target['pot'],target['bets'])==(0,830,[165,165],830,[165,165])
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
        row=native.proof(root,game,target,masks)
        bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        hh={''.join(cardkey(h)) for h,b in zip(game['hands'][1],bits,strict=True) if b&(1<<target['acts'].index('x'))}
        bb=accepted(check,game['hands'],'x')
        bb &= {cardkey(h) for h,w in zip(game['hands'][0],target['w'][0],strict=True) if w>1e-4 and native.cards(public).isdisjoint(cardkey(h))}
        joint={h:prior[h]&bb for h in sorted(hh&prior.keys()) if prior[h]&bb}
        for h in joint:
            cells=[native.hand_cell(h,public[:i])[0] for i in (6,8,10)]
            assert cells[0] in route['flop'] and cells[1] in route['turn'] and route['river'][cells[2]]=='過'
        if not row['strict_legal_combos']:
            assert row['b50'] is None and not joint
        deals[public]=joint
        out[public]=dict(reach=row,displayed_hands=sorted(joint))
    return out,deals


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve()
    head=lambda p:subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip()
    assert head(solver)==native.SOLVER
    py=solver/'postflop/py'
    assert (sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(native.PIPELINE,native.RANGES)
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and head(solver/'postflop/postflop-solver')==native.RUST
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes();assert sha(raw_pool)==native.POOL
    pool=json.loads(raw_pool)['NL2']
    sys.path.insert(0,str(py));import pipeline
    raw=a.routes.read_bytes();route=json.loads(raw)['199']
    assert (route['model_id'],route['model_spr'])==(MODEL,11.53) and set(route['river'].values())=={'過'}
    record=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (record['frequency_rank'],record['solver_profile'],record['assumed_model_node_spr'])==(199,'LMP_CO_BB',11.53)
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(1,['x b50 c','x b33 c','x']) and abs(9610/830/11.53-1)<.005
    root,manifest,jobs,old,eligible,source=original(a.archive,a.turn,route)
    locked,rules=native.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=jobs['gto']),'exp_ip',pool,pipeline)
    locked['out']='result.json'
    assert locked==jobs['exp_ip'] and locked['hero']==1 and locked['locks']
    cases={r:{h:''.join(min(v)) for h,v in hands.items()} for r,hands in eligible.items()}
    if a.preflight:
        print(json.dumps(dict(turn=a.turn,original_native_nodes_per_mode=210,preflight_same_private_hands=cases)))
        return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True);(out/'rendered-routes.json').write_bytes(raw)
    policies={};pairs={}
    for mode in ('gto','exp_ip'):
        job=jobs[mode]
        extracts=[dict(prefix=['x','b33','c',r]+branch,street=False,raw=True) for r in eligible for branch in ([],['x'])]
        target=dict(job,extract=job['extract']+extracts)
        folder=out/mode
        game=solve(folder,target,a.driver)
        compare(old[mode],game,len(eligible))
        assert 0<=game['info']['gto_expl_pct']<=.5
        applied=None
        if mode=='exp_ip':
            assert 0<=game['info']['hero_gap_pct']<=.5
            applied=native.audit_patterns(game,target,dict(locks=rules),pool,hero_seat=1)
            assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
        else:assert not game['info'].get('lock_stats') and not target.get('locks')
        rows,pairs[mode]=observed(root,game,a.turn,route,eligible,contract)
        policies[mode]=dict(original_node_count=len(old[mode]['nodes']),original_nodes_sha256=sha(compact(old[mode]['nodes'])),
            original_job_sha256=source['source_policies'][mode]['job_sha256'],original_source_sha256=source['source_policies'][mode]['source_sha256'],
            job_sha256=sha((folder/'job.json').read_bytes()),source_sha256=sha((folder/'result.json').read_bytes()),
            measured_lock_application=applied,boards=rows)
    common={}
    for board,g in pairs['gto'].items():
        e=pairs['exp_ip'][board]
        same={h:''.join(min(g[h]&e[h])) for h in sorted(g.keys()&e.keys()) if g[h]&e[h]}
        if same:common[board]=same
    del source['source_policies']
    locked_rows=[v['reach'] for v in policies['exp_ip']['boards'].values()]
    halfpot=[v for v in locked_rows if v['strict_legal_combos'] and v['compatible_hole_card_pairs'] and v['b50'] is not None and 'b50' in v['source_actions']]
    report=dict(schema='NL2_B762_R199_ORIGINAL_PAIRED_TURN_NEW_RIVERS_V1',rank=199,model_id=MODEL,line=LINE,
        flop=FLOP,turn=a.turn,actor=1,original_source=source,preregistered_rivers=RIVERS[a.turn],preflight_deals=cases,
        native_river_pot=830,native_river_stack=9610,native_river_spr=9610/830,model_spr=11.53,route_sha256=sha(raw),
        solver=native.SOLVER,rust=native.RUST,pool_sha256=native.POOL,raw_flop_recomputed=False,
        flop_bet_menu='50% only for both players',assumed_169class_limp_ranges=True,observed_private_frequencies=False,
        policies=policies,common_physical_co_bb=common,positive_distinct_flops=int(bool(common)),
        locked_public_boards=len(locked_rows),joint_halfpot_assessed=len(halfpot),halfpot_candidates=sum(bool(v['b50']['candidate']) for v in halfpot))
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','turn','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','routes','output','archive'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--turn',choices=RIVERS,required=True);p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
