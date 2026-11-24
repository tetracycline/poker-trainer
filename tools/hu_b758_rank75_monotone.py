"""Study BTN's decision after CO leads one third on three monotone three-bet flops."""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b690_rank75_connected as native
import hu_b707_rank75_highcards as checked
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_sequential_cfr_reach import accepted

WORKER='tools/hu_b758_rank75_monotone.py'
EVIDENCE=Path('data/solver_evidence')
OLD='9h7h5h'
CASES={OLD:['2d','3c','Qc','Ks'],'9d8d6d':['2c','3h','Ts','Kh'],'8c7c5c':['2d','3h','9s','Qh']}
ORIGINALS={
    OLD:('NL2_B581_R261_9H7H5H.zip','e303c7ef0566109a9e45e464006df828c353677c62ff0e1283708f44a58fa1a3',
        'root.job.json','0282a68081ed4bf915143fb0290b256ea95891785997c0742723391e2fe5bfa3','root.json',
        'ac852ea78726d6d1fdac741ceb8df4a5224b701f2a26490fa39f0c610c51a56e'),
    '9d8d6d':('NL2_B690_R75_9D8D6H.zip','aada3cd6caa2f70b3265eea43b2892f64a77ad1e3efd246fbd88a6aaff2c74df',
        'flop/job.json','7ebd310c2afc9ef1147f898795bdd1ef946d75acb07e8922186c916e4bff4acb','flop/result.json',
        'e73f2f8ed93e7545ce91039a8ff9de08762d9c5d6f39b2c3602c6b0e357b9ab6'),
    '8c7c5c':('NL2_B690_R75_8C7C5H.zip','984812d4dc7a34501cb585b2ea6730db7c830bbfd44638682a59159838a1e773',
        'flop/job.json','242a10157d6419eed5647e6f650248a898297e9a1ed5f40763e0650bc348a9dc','flop/result.json',
        'd4bed3a0f9b9c2095ec5993bfd5e06c4db8b56c451441efb53473648b1bcaed3'),
}
HISTORICAL=set('7c5d3h 7c5d4h 7d7c3h 7s6s4d 8c6h3d 8c7c5h 8h6d3c 8h6s4c 8s7h4d 9d8d6h 9h7h5h As9s4d JcTs6c JdTc5d Jh9c4d JhTd7h Kc9h3d KdTh5h QhJc4d Td9c6d Th9s4h'.split())
APP=('b3dea42d0478e178aefda628e539ec7d95fbe6bd','15aee97e53a156fe073c96a120638a8a3679958f','88f702e6d0a645e23b1f9359febfab658ec92f80')
NATIVE_SOLVE=native.solve
NATIVE_DECISION=native.decision


@lru_cache
def source(flop):
    name,digest,job_name,job_sha,result_name,result_sha=ORIGINALS[flop]
    archive=EVIDENCE/name
    assert sha(archive.read_bytes())==digest
    with ZipFile(archive) as z:
        j=z.read(job_name);r=z.read(result_name)
        assert sha(j)==job_sha and sha(r)==result_sha
    job=json.loads(j);root=json.loads(r)
    assert (job['pot'],job['stack'],root['pot'],root['stack'])==(1650,9250,1650,9250)
    assert job['flop']==root['flop'] and job['flop'][::2]==flop[::2]
    assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    return job,root


def root_job(flop,pipeline):
    original,old=source(OLD)
    assert original['flop_oop']==original['flop_ip']=='33%,50%,75%,100%'
    extra=[dict(prefix=['b33','c',turn],street=False,raw=True) for turn in CASES[flop]]
    if flop==OLD:
        assert len(old['nodes'])==37 and not any(n['line']=='b33 c/' for n in old['nodes'])
        assert not any(i['prefix']==j['prefix'] for i in extra for j in original['extract'])
        return dict(original,out='result.json',extract=original['extract']+extra)
    return dict(original,flop=flop,out='result.json',iters=2100,target_pct=.45,
        extract=[dict(prefix=[],street=True)]+extra)


def before_native(flop,solver):
    assert sys.version_info[:2]==(3,11)
    assert all(checked.blob(p)==v for p,v in checked.PINS.items())
    assert checked.blob('tools/hu_b707_rank75_highcards.py')=='9b845a82f46de9d058117204dba58ae234bb23e6'
    assert tuple(checked.blob(p) for p in checked.APP_FILES)==APP
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    py=solver/'postflop/py'
    assert sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    assert sha((solver/'inputs/pool_stats.json').read_bytes())==native.POOL
    sys.path.insert(0,str(py))
    import pipeline,ranges
    ranges.SPOTS.update(native.EXTRA_SPOTS)
    weights=[dict(zip(ranges.NAMES,w,strict=True)) for w in ranges.ranges('CO3_BTN','gto')]
    donor_job,root=source(flop)
    root_template,_=source(OLD)
    assert all(j['oop']==ranges.to_str(ranges.ranges('CO3_BTN','gto')[0]) and j['ip']==ranges.to_str(ranges.ranges('CO3_BTN','gto')[1]) for j in (root_template,donor_job))
    new_flops={suit_isomorphism_class(f) for f in CASES if f!=OLD}
    assert len(new_flops)==2 and new_flops.isdisjoint({suit_isomorphism_class(f) for f in HISTORICAL})
    assert native.tx(flop)=='mono' and len(set(flop[::2]))==3
    routes=json.loads(subprocess.check_output(['node','tools/hu_b674_threebet_call_routes.cjs']))['75']
    assert (routes['id'],routes['line'],routes['seat'],routes['turn_pot'],routes['turn_stack'])==(native.MODEL,'b33 c/x',1,2740,8705)
    assert routes['routes']['mono']==dict(parents=['DRAW','WDRAW'],decisions={'DRAW':'下注 ½','WDRAW':'過'})
    nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    co=accepted(nodes[''],root['hands'],'b33');btn=accepted(nodes['b33'],root['hands'],'c')
    examples={}
    for turn in CASES[flop]:
        public=flop+turn
        assert len(checked.cards(public))==4 and native.tx(public)=='mono'
        rows={}
        for h in sorted(btn):
            hero=''.join(h)
            if checked.cards(public).intersection(h) or weights[1][checked.range_class(hero)]<=0:continue
            old_class=native.hcls(hero,root['flop'])
            if old_class not in ('DRAW','WDRAW') or native.hcls(hero,flop) not in routes['routes']['mono']['parents']:continue
            action=routes['routes']['mono']['decisions'].get(native.hcls(hero,public))
            if not action:continue
            villain=next((''.join(v) for v in sorted(co) if checked.cards(public+hero).isdisjoint(v)
                and weights[0][checked.range_class(''.join(v))]>0),None)
            if villain and action not in rows:
                rows[action]=dict(btn=hero,co=villain,old_flop_class=old_class,new_flop_class=native.hcls(hero,flop),
                    new_turn_class=native.hcls(hero,public),prior_actions=['b33','c'],
                    co_range_weight=weights[0][checked.range_class(villain)],btn_range_weight=weights[1][checked.range_class(hero)])
        assert rows
        examples[turn]=rows
    return dict(archive=ORIGINALS[flop][0],archive_sha256=ORIGINALS[flop][1],original_root_sha256=ORIGINALS[flop][-1],
        source_flop=root['flop'],real_original_co_b33=len(co),real_original_btn_call=len(btn),examples=examples,
        relationship='SAME_FLOP_MISSING_CHANCE_BOUNDARIES' if flop==OLD else 'DISTINCT_NEW_FLOP_STATIC_ONLY'),pipeline


def verify_root(flop,root):
    assert (root['flop'],root['pot'],root['stack'])==(flop,1650,9250)
    assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    compared=0
    if flop==OLD:
        _,old=source(OLD)
        assert all(root[k]==old[k] for k in ('flop','pot','stack','hands'))
        def ident(n):return (n['board'],n['line'],n['player'])
        nodes={ident(n):n for n in root['nodes']}
        assert len(nodes)==len(root['nodes'])==len(old['nodes'])+len(CASES[flop])
        for n in old['nodes']:
            assert nodes.pop(ident(n))==n,ident(n)
        assert all(n['line']=='b33 c/' for n in nodes.values())
        compared=len(old['nodes'])
    parents=[n for n in root['nodes'] if n['line']=='b33 c/']
    assert len(parents)==len(CASES[flop]) and {n['board'][-2:] for n in parents}==set(CASES[flop])
    for n in parents:
        assert checked.cards(n['board'][:6])==checked.cards(flop) and (n['player'],n['pot'],n['bets'])==(0,2740,[545,545])
        assert len(n['wr'])==2 and all(len(w)==len(h) for w,h in zip(n['wr'],root['hands'],strict=True))
    return dict(previous_nodes_identical=compared,new_raw_boundary_sha256={n['board'][-2:]:sha(compact(n)) for n in parents})


def run(a):
    solver=a.solver.resolve();prior,pipeline=before_native(a.flop,solver)
    if a.preflight:
        print(json.dumps(prior));return
    native.CASES=CASES;native.root_gate=checked.checked_gate;native.root_job=root_job
    if a.checkpoint_only:
        assert a.driver and (not a.output.exists() or not any(a.output.iterdir()))
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==native.RUST
        job=root_job(a.flop,pipeline)
        root=NATIVE_SOLVE(a.output/'flop',job,a.driver)
        pin=verify_root(a.flop,root)
        pin.update(flop=a.flop,worker_blob=checked.blob(WORKER),root_sha256=sha((a.output/'flop/result.json').read_bytes()),
            job_sha256=sha((a.output/'flop/job.json').read_bytes()))
        (a.output/'checkpoint.json').write_bytes(json_bytes(pin));return
    if a.driver:assert a.checkpoint and (not a.output.exists() or not any(a.output.iterdir()))
    details={}
    def solve(folder,job,driver):
        if folder.name=='flop' and driver:
            record=json.loads((a.checkpoint/'checkpoint.json').read_bytes())
            raw=(a.checkpoint/'flop/result.json').read_bytes()
            assert record['worker_blob']==checked.blob(WORKER) and record['flop']==a.flop and record['root_sha256']==sha(raw)
            assert (a.checkpoint/'flop/job.json').read_bytes()==compact(job) and record['job_sha256']==sha(compact(job))
            folder.mkdir(parents=True);(folder/'job.json').write_bytes(compact(job));(folder/'result.json').write_bytes(raw)
            driver=None
        game=NATIVE_SOLVE(folder,job,driver)
        assert (folder/'job.json').read_bytes()==compact(job)
        if folder.name=='flop':verify_root(a.flop,game)
        return game
    def decision(root,game,turn,route):
        row,hands=NATIVE_DECISION(root,game,turn,route)
        mode='exp_ip' if game['info'].get('lock_stats') else 'gto'
        details.setdefault(turn,{})[mode]=dict(reach=row,rendered_hands=hands)
        return row,hands
    native.solve=solve;native.decision=decision
    saved=sys.argv
    sys.argv=[saved[0],'--solver',str(a.solver),'--flop',a.flop,'--output',str(a.output)]
    if a.driver:sys.argv+=['--driver',str(a.driver)]
    try:native.main()
    finally:sys.argv=saved
    path=a.output/'proof.json';report=json.loads(path.read_bytes())
    report.update(schema='NL2_B758_R75_MONOTONE_ORIGINAL_V1',source_worker_blob=checked.blob(WORKER),
        original_donor=prior,root_verification=verify_root(a.flop,json.loads((a.output/'flop/result.json').read_bytes())),
        full_root_bet_sizes_pct=[33,50,75,100],full_root_raise_sizes_from_original=True,actual_decisions=details,
        native_files_sha256={str(p.relative_to(a.output)):sha(p.read_bytes()) for p in sorted(a.output.rglob('*')) if p.is_file() and p.name!='proof.json'})
    del report['restricted_flop_oop_sizes_pct'],report['restricted_flop_ip_sizes_pct']
    for item in report['turns']:
        if item['paired']:
            measured=item['measured_lock_application']
            assert any(n>0 for k,n in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
            observed=details[item['turn']]['exp_ip']['reach']
            assert 'b50' in observed['source_actions']
    path.write_bytes(json_bytes(report))
    joint=[s['exp_ip']['reach'] for s in details.values() if 'exp_ip' in s and s['exp_ip']['reach']['strict_legal_combos']>0 and s['exp_ip']['reach']['compatible_hole_card_pairs']>0]
    half=[r for r in joint if r['b50'] is not None and 'b50' in r['source_actions']]
    print(json.dumps(dict(flop=a.flop,positive=report['positive_distinct_flops'],actor_locked_joint_boards=len(joint),
        half_pot_assessed=len(half),nonpolarized_candidates=sum(r['b50']['candidate'] for r in half))))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):cli.add_argument('--'+k,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--driver',type=Path);cli.add_argument('--checkpoint',type=Path)
    cli.add_argument('--checkpoint-only',action='store_true');cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
