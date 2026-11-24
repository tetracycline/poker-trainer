"""Extract four missing ranges from the original 7h6c4h flop and stop once the two policies share a physical deal."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b767_rank199_new_turns as source
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b637_rank57 import solve
from hu_b723_rank115_limp_rivers import load_root,EVIDENCE

FLOP='7h6c4h'
TURNS=['Qc','8d','Qd','8c']
EXPECTED={'Qc':(21,14),'8d':(2,6),'Qd':(21,21),'8c':(2,4)}
ROUTE=source.ROUTE
MODEL=source.MODEL
LINE=source.LINE


def original(route):
    root,template,pin=load_root(FLOP)
    archive=EVIDENCE/pin['archive']
    assert pin['archive']=='NL2_B580_R27_LMP.zip' and sha(archive.read_bytes())==pin['archive_sha256']
    with ZipFile(archive) as z:
        raw=z.read(FLOP+'/root.job.json')
        manifest=json.loads(z.read('original-manifest.json'))
    assert sha(raw)==pin['root_job_sha256'];job=json.loads(raw)
    assert job['flop_oop']==job['flop_ip']=='50%' and (job['pot'],job['stack'])==(250,9900)
    assert len(root['nodes'])==15 and not any(n['line']=='x b50 c/' for n in root['nodes'])
    extra=[dict(prefix=['x','b50','c',t],street=False,raw=True) for t in TURNS]
    assert all(a['prefix']!=b['prefix'] for a in job['extract'] for b in extra)
    def canonical_turn(turn):
        # Original rank cards distinguish the present heart and club suits. Interchanging
        # the two absent flop suits leaves a river subtree equivalent.
        return (turn[0],turn[1] if turn[1] in {'h','c'} else 'unused')
    assert len({canonical_turn(t) for t in TURNS})==len(TURNS)
    assert len({source.base.suit_isomorphism_class(f) for f in [FLOP,'7h6d4s','7h6h4c']})==3
    static={}
    for turn in TURNS:
        allowed,_,gate=source.base.routes(root,turn,route)
        assert (gate['two_street_displayed_co'],len(allowed))==EXPECTED[turn]
        static[turn]=dict(gate,all_prequalified_rivers=list(allowed))
    return root,template,manifest,pin,dict(job,out='result.json',extract=job['extract']+extra),static


def evaluate(out,driver,root,parent,template,manifest,route,contract,pool,pipeline,turn):
    allowed,_,gate=source.base.routes(root,turn,route,parent)
    item=dict(turn=turn,original_parent_sha256=sha(compact(parent)),gate=gate,all_rivers=list(allowed),
              policies={},common_physical_co_bb={},locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0)
    if not allowed:
        item['stop_reason']='ZERO_FULL_PARENT_TWO_SEAT_UI_REACH'
        return item
    job=source.turn_job(root,parent,template,turn,allowed)
    deals={}
    for mode in ('gto','exp_ip'):
        target=job;applied=None
        if mode=='exp_ip':
            target,rules=source.base.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=job),mode,pool,pipeline)
            target['out']='result.json'
            assert target['hero']==1 and target['locks']
        folder=out/(turn+'-'+mode)
        sub=solve(folder,target,driver)
        assert (sub['flop'],sub['pot'],sub['stack'])==(FLOP,500,9775) and 0<=sub['info']['gto_expl_pct']<=.5
        if mode=='exp_ip':
            assert 0<=sub['info']['hero_gap_pct']<=.5
            applied=source.base.audit_patterns(sub,target,dict(locks=rules),pool,hero_seat=1)
            assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
        else:assert not sub['info'].get('lock_stats') and not target.get('locks')
        rows,deals[mode]=source.decisions(root,sub,parent,turn,route,allowed,contract)
        item['policies'][mode]=dict(job_sha256=sha((folder/'job.json').read_bytes()),source_sha256=sha((folder/'result.json').read_bytes()),applied_lock=applied,boards=rows)
        if mode=='gto' and not any(deals[mode].values()):
            item['stop_reason']='ZERO_DISPLAYED_GTO_RIVER'
            return item
    for public,g in deals['gto'].items():
        e=deals['exp_ip'][public]
        same={h:''.join(min(g[h]&e[h])) for h in sorted(g.keys()&e.keys()) if g[h]&e[h]}
        if same:item['common_physical_co_bb'][public]=same
    locked=[v['reach'] for v in item['policies']['exp_ip']['boards'].values()]
    half=[r for r in locked if r['strict_legal_combos'] and r['compatible_hole_card_pairs'] and 'b50' in r['source_actions'] and r['b50'] is not None]
    item.update(locked_public_boards=len(locked),joint_halfpot_assessed=len(half),halfpot_candidates=sum(bool(r['b50']['candidate']) for r in half))
    return item


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve();py=solver/'postflop/py'
    head=lambda p:subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip()
    assert head(solver)==source.base.SOLVER
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert head(solver/'postflop/postflop-solver')==source.base.RUST
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert (sha(poolraw),sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(source.base.POOL,source.base.PIPELINE,source.base.RANGES)
    sys.path.insert(0,str(py));import pipeline
    pool=json.loads(poolraw)['NL2']
    raw=a.routes.read_bytes();route=json.loads(raw)['199']
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (route['model_id'],route['model_spr'],model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(MODEL,11.53,199,'LMP_CO_BB',11.53)
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(1,['x b50 c','x b33 c','x']) and abs(9610/830/11.53-1)<.005
    old,template,m,pin,job,static=original(route)
    if a.preflight:
        print(json.dumps(dict(flop=FLOP,original_15_nodes_sha256=sha(compact(old['nodes'])),static=static)))
        return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True);(out/'rendered-routes.json').write_bytes(raw)
    root=solve(out/'flop',job,a.driver)
    boundaries=source.base.compare_extraction(old,root,TURNS)
    result=dict(schema='NL2_B771_R199_VERIFY_15_ORIGINAL_FLOP_NODES_V1',rank=199,model_id=MODEL,line=LINE,actor=1,
        flop=FLOP,turn_order=TURNS,original=pin,original_nodes_unchanged=len(old['nodes']),original_nodes_sha256=sha(compact(old['nodes'])),
        root_sha256=sha((out/'flop/result.json').read_bytes()),root_job_sha256=sha((out/'flop/job.json').read_bytes()),
        added_turn_boundary_sha256={t:sha(compact(n)) for t,n in boundaries.items()},source_solver=source.base.SOLVER,rust=source.base.RUST,
        pool_sha256=source.base.POOL,route_sha256=sha(raw),assumed_preflop_ranges=True,observed_private_combo_rates=False,
        original_flop_menu='50% only for both players',actual_river_pot=830,actual_river_stack=9610,actual_river_spr=9610/830,model_spr=11.53,
        turns=[],positive_distinct_flops=0,selected_turn=None)
    for t in TURNS:
        item=evaluate(out,a.driver,root,boundaries[t],template,m,route,contract,pool,pipeline,t)
        result['turns'].append(item)
        if item['common_physical_co_bb']:
            result.update(positive_distinct_flops=1,selected_turn=t)
            break
    for key in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates'):
        result[key]=sum(t[key] for t in result['turns'])
    (out/'proof.json').write_bytes(json_bytes(result))
    print(json.dumps({k:result[k] for k in ('flop','selected_turn','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output','routes'):c.add_argument('--'+k,type=Path,required=True)
    c.add_argument('--driver',type=Path);c.add_argument('--preflight',action='store_true')
    run(c.parse_args())
