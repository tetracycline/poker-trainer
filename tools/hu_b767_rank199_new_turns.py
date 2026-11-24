"""Solve three unplayed rank199 turn branches using B755's already exported native ranges."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b755_rank151 as base
import hu_b759_rank46_barrel_gates as gates
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b637_rank57 import solve
from hu_sequential_cfr_reach import accepted,cardkey,game_reach
from hu_trainer_route_gate import compatible

MODEL='ln-iso-lmp_r_model-10l8t7i'
LINE='x b50 c/x b33 c/x'
CASES={('7s5h3d','9c'):(9,12),('7s5h3d','Qd'):(29,21),('7h6h4c','Qc'):(19,14)}
ROUTE='tools/hu_b759_rank46_barrel_routes.cjs'


def original(flop,turn,route):
    count=CASES[flop,turn]
    frozen,template,m,pin,original_job=base.source(flop)
    artifact,digest=gates.PINS[flop]
    path=Path('data/solver_evidence')/('NL2_B755_R151_'+flop.upper()+'.zip')
    assert sha(path.read_bytes())==digest
    with ZipFile(path) as z:
        claim=json.loads(z.read('proof.json'));root=json.loads(z.read('flop/result.json'))
        assert claim['root_sha256']==sha(z.read('flop/result.json')) and pin==claim['source']
        assert json.loads(z.read('flop/job.json'))==original_job
        assert turn not in {t['turn'] for t in claim['turns']}
        assert all(not p.startswith((turn+'-gto/',turn+'-exp_ip/')) for p in z.namelist())
    parent=base.compare_extraction(frozen,root,base.CASES[flop])[turn]
    assert len(parent['wr'])==2 and all(len(w)==len(h) for w,h in zip(parent['wr'],root['hands'],strict=True))
    allowed,_,diagnostic=base.routes(root,turn,route,parent)
    assert (diagnostic['two_street_displayed_co'],len(allowed))==count
    assert set(allowed)=={r for r in base.DECK if r in allowed} and len(allowed)<=21
    return root,parent,template,m,allowed,dict(root_archive_id=artifact,root_archive_sha256=digest,root_run=gates.RUN,
        root_head=gates.HEAD,root_raw_sha256=claim['root_sha256'],original_replayed_nodes=len(frozen['nodes']),
        original_root=pin,boundary_sha256=sha(compact(parent)),static_route=diagnostic,preregistered_rivers=list(allowed))


def turn_job(root,parent,template,turn,rivers):
    job=dict(template,flop=root['flop'],turn=turn,line0=['x','b50','c','/'],root_no_bet=False,oop='',ip='',pot=500,stack=9775,
             turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',
             river_donk='50%,75%,100%',iters=2200,target_pct=.45,rank_pct=.45,compress=False,out='result.json',
             extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','b33','c',r]+suffix,street=False,raw=True)
                  for r in rivers for suffix in ([],['x'])])
    for i,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][i],parent['wr'][i],strict=True) if w>1e-4]
    assert job['oop_w'] and job['ip_w'] and not job.get('locks') and (job['rake_rate'],job['rake_cap'])==(.05,1000)
    return job


def decisions(root,sub,parent,turn,route,eligible,contract):
    sub.update(line0='x b50 c',turn=turn,rivers=list(eligible))
    masks=game_reach(root,sub)[0]
    flop_nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    turn_nodes={n['line']:n for n in sub['nodes'] if len(n['board'])==8}
    line='x b50 c/'
    opening,bet,call=[turn_nodes[k] for k in (line,line+'x',line+'x b33')]
    assert (opening['player'],bet['player'],call['player'],call['pot'],call['bets'])==(0,1,0,665,[0,165])
    assert opening['board']==bet['board']==call['board']==parent['board']
    live=[{cardkey(h) for h,w in zip(root['hands'][s],parent['wr'][s],strict=True) if w>1e-4} for s in (0,1)]
    bb=live[0]&accepted(flop_nodes[''],root['hands'],'x')&accepted(flop_nodes['x b50'],root['hands'],'c')
    bb&=accepted(opening,sub['hands'],'x')&accepted(call,sub['hands'],'c')
    co=live[1]&accepted(flop_nodes['x'],root['hands'],'b50')&accepted(bet,sub['hands'],'b33')
    targets={n['board'][-2:]:n for n in sub['nodes'] if n['line']==LINE}
    bb_nodes={n['board']:n for n in sub['nodes'] if n['line']==LINE[:-1]}
    assert set(targets)==set(eligible) and len(bb_nodes)==len(eligible)
    rows={};deals={}
    for r,node in targets.items():
        public=node['board'];first=bb_nodes[public]
        assert (public[6:8],base.cards(public[:6]),node['player'],first['player'])==(turn,base.cards(root['flop']),1,0)
        assert (node['pot'],node['bets'],first['pot'],first['bets'])==(830,[165,165],830,[165,165])
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
        row=base.proof(root,sub,node,masks)
        active=[{cardkey(h) for h,w in zip(sub['hands'][s],node['w'][s],strict=True) if w>1e-4 and base.cards(public).isdisjoint(cardkey(h))} for s in (0,1)]
        villains=bb&active[0]&accepted(first,sub['hands'],'x')
        heroes=co&active[1]&accepted(node,sub['hands'],'x')
        valid={}
        for h in sorted(heroes):
            key=''.join(h)
            if key not in eligible[r]:continue
            cells=[base.hand_cell(key,public[:i])[0] for i in (6,8,10)]
            assert cells[0] in route['flop'] and cells[1] in route['turn'] and route['river'][cells[2]]=='過'
            foes={v for v in villains if set(h).isdisjoint(v)}
            if foes:valid[key]=foes
        bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        from_proof={''.join(cardkey(h)) for h,b in zip(sub['hands'][1],bits,strict=True) if b & (1<<node['acts'].index('x'))}
        assert set(valid)==from_proof.intersection(eligible[r])
        if not row['strict_legal_combos']:assert row['b50'] is None and not valid
        deals[public]=valid
        rows[public]=dict(reach=row,displayed_hands=sorted(valid))
    return rows,deals


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve();py=solver/'postflop/py'
    head=lambda p:subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip()
    assert head(solver)==base.SOLVER
    if a.driver:assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and head(solver/'postflop/postflop-solver')==base.RUST
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==base.POOL and (sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(base.PIPELINE,base.RANGES)
    pool=json.loads(poolraw)['NL2'];sys.path.insert(0,str(py));import pipeline
    raw=a.routes.read_bytes();route=json.loads(raw)['199']
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (route['model_id'],route['model_spr'],model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(MODEL,11.53,199,'LMP_CO_BB',11.53)
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(1,['x b50 c','x b33 c','x']) and abs(9610/830/11.53-1)<.005
    assert len({base.suit_isomorphism_class(f) for f in ('7h6d4s','7s5h3d','7h6h4c')})==3
    root,parent,template,m,allowed,origin=original(a.flop,a.turn,route)
    job=turn_job(root,parent,template,a.turn,allowed)
    if a.preflight:
        print(json.dumps(dict(flop=a.flop,turn=a.turn,root_raw_sha256=origin['root_raw_sha256'],wr=origin['boundary_sha256'],
            co=origin['static_route']['two_street_displayed_co'],rivers=len(allowed),example=next(iter(origin['static_route']['examples'].values())))))
        return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True);(out/'rendered-routes.json').write_bytes(raw)
    policies={};deals={}
    for mode in ('gto','exp_ip'):
        target=job;applied=None
        if mode=='exp_ip':
            target,rules=base.prepare_job(dict(source=dict(root=root,version='gto',manifest=m),job=job),mode,pool,pipeline)
            target['out']='result.json';assert target['hero']==1 and target['locks']
        folder=out/mode;game=solve(folder,target,a.driver)
        assert (game['flop'],game['pot'],game['stack'])==(a.flop,500,9775) and 0<=game['info']['gto_expl_pct']<=.5
        if mode=='exp_ip':
            assert 0<=game['info']['hero_gap_pct']<=.5
            applied=base.audit_patterns(game,target,dict(locks=rules),pool,hero_seat=1)
            assert any(v>0 for k,v in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
        else:assert not game['info'].get('lock_stats') and not target.get('locks')
        rows,deals[mode]=decisions(root,game,parent,a.turn,route,allowed,contract)
        policies[mode]=dict(job_sha256=sha((folder/'job.json').read_bytes()),source_sha256=sha((folder/'result.json').read_bytes()),
                          applied_lock=applied,boards=rows)
        if mode=='gto' and not any(deals[mode].values()):break
    common={}
    if 'exp_ip' in policies:
        for public,g in deals['gto'].items():
            e=deals['exp_ip'][public]
            same={h:''.join(min(g[h]&e[h])) for h in sorted(g.keys()&e.keys()) if g[h]&e[h]}
            if same:common[public]=same
    locked=[v['reach'] for v in policies.get('exp_ip',{}).get('boards',{}).values()]
    medium=[r for r in locked if r['strict_legal_combos'] and r['compatible_hole_card_pairs'] and r['b50'] is not None and 'b50' in r['source_actions']]
    report=dict(schema='NL2_B767_R199_TWO_ORIGINAL_FLOPS_NEW_TURNS_V1',rank=199,model_id=MODEL,line=LINE,actor=1,flop=a.flop,turn=a.turn,
        original=origin,source_solver=base.SOLVER,rust=base.RUST,pool_sha256=base.POOL,route_sha256=sha(raw),flop_recomputed=False,
        original_flop_menu='50% only for both players',assumed_preflop_ranges=True,observed_private_combo_rates=False,
        model_spr=11.53,actual_river_pot=830,actual_river_stack=9610,actual_river_spr=9610/830,
        policies=policies,common_physical_co_bb=common,positive_distinct_flops=int(bool(common)),
        locked_public_boards=len(locked),joint_halfpot_assessed=len(medium),halfpot_candidates=sum(bool(r['b50']['candidate']) for r in medium))
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','turn','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','routes','output'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('flop','turn'):p.add_argument('--'+k,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
