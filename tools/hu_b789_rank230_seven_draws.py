"""Solve two new SB3_BTN originals after checking their physical J7-suited trainer routes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import hu_b782_rank230_mid_pairs as base
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_trainer_route_gate import compatible

native=base.native
WORKER='tools/hu_b789_rank230_seven_draws.py'
PRIOR='data/solver_evidence/partial/b784_rank230.json'
PRIOR_SHA='73a8d38bb2f4cac3906f3418a30c3ddd17f6646bf0c251b99d51de2ecec9e78f'
SOURCE_BLOB='d93bef8fa8aca87dbf1838808128653a3ba24c79'
CASES={'9h8h7c':('7hJh',['5d','6c','4s','2d','3s']),'Ts7h6s':('7sJs',['4c','5d','8c','3h','2d'])}
OLD=('9h8c5h','JhTh8c','Kc9d4h','Kd7s2h','KdQc5h','KhJc4s','Qh9c4s','Qs8h3d','Td9d5c','Th9h7c','Ts8s7h','Ts9s6h',
     *native.CASES,*native.OLD_FLOPS,*native.OTHER_FLOPS)


def git_head(path):
    return subprocess.check_output(['git','-C',path,'rev-parse','HEAD'],text=True).strip()


def preflight(flop,route,ranges,pipeline):
    hand,turns=CASES[flop];villain='3c3d';suited=hand[1]
    assert hand[1]==hand[3] and hand[0]=='7' and hand[2]=='J'
    assert sum(flop[i]==suited for i in (1,3,5))==2 and any(flop[i]=='7' and flop[i+1]!=suited for i in (0,2,4))
    assert not ({suit_isomorphism_class(f) for f in CASES}&{suit_isomorphism_class(f) for f in OLD})
    assert len({suit_isomorphism_class(f) for f in CASES})==2
    assert sha(Path(PRIOR).read_bytes())==PRIOR_SHA
    group=json.loads(Path(PRIOR).read_bytes())
    assert [(p['flop'],p['rendered_decision_hands'][0]['hand']) for p in group['pins']]==[('Th9h7c','7hJh'),('Ts8s7h','7sJs')]
    oop,ip=ranges.ranges('SB3_BTN','gto')
    assert oop[ranges.NAMES.index('J7s')]==.41 and ip[ranges.NAMES.index('33')]==.41
    job=pipeline.make_job('SB3_BTN','gto',flop,'result.json',iters=2200,target=.4,compress=True)
    job.update(flop_oop='33%',flop_ip='33%',extract=[dict(prefix=[],street=True)]+[
        dict(prefix=['x','x',turn],street=False,raw=True) for turn in turns])
    assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(2100,9000,.05,1000)
    assert (job['oop'],job['ip'])==(ranges.to_str(oop),ranges.to_str(ip)) and not job.get('locks')
    examples={}
    for turn in turns:
        legal=[]
        for river in native.DECK:
            pub=flop+turn+river
            if len(native.public_cards(pub+hand+villain))!=9:continue
            if all(route[s].get(native.hand_cell(hand,pub[:n])[0])=='過' for s,n in (('flop',6),('turn',8),('river',10))):
                legal.append(river)
        assert legal,(flop,turn)
        examples[turn]=dict(physical_sb=hand,physical_btn=villain,example_river=legal[0],legal_example_rivers=len(legal))
    return job,examples


def turn_job(root,turn,boundary,rivers,pipeline):
    job=pipeline.make_job('SB3_BTN','gto',root['flop'],'result.json',iters=2400,target=.4,compress=False)
    job.update(pipeline.SUB);job.update(oop='',ip='',line0=['x','x','/'],turn=turn,pot=2100,stack=9000,root_no_bet=False,
        turn_oop=base.MENU,turn_ip=base.MENU,river_oop='33%,50%,75%,100%,a',river_ip='33%,50%,75%,100%,a',
        extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
    for i,k in enumerate(('oop_w','ip_w')):
        job[k]=[[h,w] for h,w in zip(root['hands'][i],boundary['wr'][i],strict=True) if w>1e-4]
    assert job['oop_w'] and job['ip_w'] and (job['rake_rate'],job['rake_cap'])==(.05,1000)
    return job


def run(a):
    flop=a.flop;hand,scheduled=CASES[flop];solver=a.solver.resolve();py=solver/'postflop/py'
    assert sys.version_info[:2]==(3,11) and git_head(solver)==native.SOLVER and base.blob(base.WORKER)==SOURCE_BLOB
    assert base.blob(base.ROUTE)=='522ea33d7326c38a7493507cbde96b5df4a6f3f7'
    assert sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    if a.driver:assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and git_head(solver/'postflop/postflop-solver')==native.RUST
    sys.path.insert(0,str(py));import pipeline,ranges
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==native.POOL;pool=json.loads(pool_raw)['NL2']
    route_bytes=subprocess.check_output(['node',base.ROUTE]);route=json.loads(route_bytes)['230']
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][base.MODEL]
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][base.MODEL]
    assert (reg['frequency_rank'],reg['solver_profile'],contract['seat'],contract['streets'])==(230,'SB3_BTN',0,['x x','x x',''])
    assert abs(90/21/reg['assumed_model_node_spr']-1)<.05
    assert route['model']==base.MODEL and route['flop']==route['turn']==route['river']=={'low:2':'過','mid_high:2':'過'}
    job,examples=preflight(flop,route,ranges,pipeline)
    if a.preflight:print(json.dumps(dict(flop=flop,static_examples=examples)));return
    out=a.output.resolve();dest=out/'flop';checkpoint=out/'root-checkpoint.json'
    if a.root_only:
        assert a.driver and not dest.exists() and not checkpoint.exists()
    else:
        assert (dest/'result.json').is_file() and checkpoint.is_file()
    out.mkdir(parents=True,exist_ok=True)
    root=native.solve(dest,job,a.driver if a.root_only else None)
    assert (dest/'job.json').read_bytes()==compact(job)
    assert (root['flop'],root['pot'],root['stack'])==(flop,2100,9000) and not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    bounds={t:native.parent(root,t) for t in scheduled}
    assert len(root['nodes'])==len({(n['board'],n['line'],n['player']) for n in root['nodes']})
    for t,b in bounds.items():
        assert b['board'][6:]==t and native.public_cards(b['board'][:6])==native.public_cards(flop) and len(b['wr'])==2
    origin=dict(schema='NL2_B789_ORIGINAL_R230_ROOT_V1',new_native_flop=True,flop=flop,spot='SB3_BTN',solver=native.SOLVER,rust=native.RUST,
        source_worker_blob=base.blob(WORKER),root_job_sha256=sha((dest/'job.json').read_bytes()),root_result_sha256=sha((dest/'result.json').read_bytes()),
        original_nodes=len(root['nodes']),root_pot=2100,root_stack=9000,root_solve_invocations=1,flop_reexports=0,
        new_raw_boundaries={t:sha(compact(b)) for t,b in bounds.items()})
    if a.root_only:checkpoint.write_bytes(json_bytes(origin));return
    assert checkpoint.read_bytes()==json_bytes(origin)
    (out/'rendered-routes.json').write_bytes(route_bytes)
    proof=dict(schema='NL2_B789_R230_NEW_SEVEN_PAIR_DRAW_ROOT_V1',rank=230,model_id=base.MODEL,actor=0,spot='SB3_BTN',flop=flop,line=native.LINE,
        source_worker_blob=base.blob(WORKER),parent_worker_blob=SOURCE_BLOB,origin=origin,solver=native.SOLVER,rust=native.RUST,pool_sha256=native.POOL,
        root_job_sha256=origin['root_job_sha256'],root_sha256=origin['root_result_sha256'],new_raw_boundaries=origin['new_raw_boundaries'],
        original_flop_reexports=0,restricted_flop_sizes='33% both seats',root_price=[2100,9000],no_observed_per_private_hand_frequency=True,
        lock_scope='FROZEN_GTO_FLOP_AND_MEASURED_PARTIAL_TURN_RIVER_NL2_MARGINALS',static_examples=examples,
        preregistered_turns=scheduled,turns=[],selected=None)
    for turn in scheduled:
        heroes,btn=base.root_hands(root,turn,route,bounds[turn])
        gate=native.available_rivers(root,turn,route,None);assert gate['compatible_hero_hands']==sorted(''.join(h) for h in heroes)
        rivers=gate['river_extracts'];item=dict(turn=turn,root_gate=gate,preregistered_rivers=rivers,policies={},common={},
            physical_J7s_at_checked_boundary=hand in gate['compatible_hero_hands']);proof['turns'].append(item)
        if not rivers:continue
        gj=turn_job(root,turn,bounds[turn],rivers,pipeline);before=None
        for ver in ('gto','exp_oop'):
            tar=gj;applied=None
            if ver=='exp_oop':
                tar,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='SB3_BTN')),job=gj),ver,pool,pipeline)
                tar['out']='result.json';assert tar['hero']==0 and tar['locks']
            leaf=out/(turn+'-'+ver)
            if a.driver:assert not leaf.exists()
            game=native.solve(leaf,tar,a.driver);assert (leaf/'job.json').read_bytes()==compact(tar)
            assert (game['flop'],game['pot'],game['stack'])==(flop,2100,9000) and 0<=game['info']['gto_expl_pct']<=.5
            if ver=='gto':
                gto_hands=game['hands'];assert not game['info'].get('lock_stats')
            else:
                assert game['hands']==gto_hands and 0<=game['info']['hero_gap_pct']<=.5
                applied=native.audit_patterns(game,tar,dict(spot='SB3_BTN',locks=rules),pool,0)
                assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
            rows,witnesses=base.decisions(root,game,turn,rivers,route,heroes,btn,before)
            item['policies'][ver]=dict(source_sha256=sha((leaf/'result.json').read_bytes()),job_sha256=sha(compact(tar)),measured_lock_application=applied,boards=rows)
            if ver=='gto':
                before=witnesses
                if not any(witnesses.values()):break
            else:item['common']={k:sorted({h for h,v in pairs}) for k,pairs in sorted(witnesses.items()) if pairs}
        if item['common']:
            public=next(iter(item['common']));assert compatible(contract,dict(public_board=public,actual_exact_action_line=native.LINE,acting_seat=0))
            proof['selected']=dict(turn=turn,public_board=public);break
    locked=[b['reach'] for t in proof['turns'] for b in t['policies'].get('exp_oop',{}).get('boards',{}).values()]
    assert len({r['public_board'] for r in locked})==len(locked)
    joint=[r for r in locked if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None]
    proof.update(positive_distinct_flops=int(bool(proof['selected'])),locked_named_boards=len(locked),joint_halfpot_assessed=len(joint),
        nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    proof['native_file_sha256']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(proof))
    print(json.dumps({k:proof[k] for k in ('flop','selected','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True);p.add_argument('--driver',type=Path)
    p.add_argument('--preflight',action='store_true');p.add_argument('--root-only',action='store_true')
    run(p.parse_args())
