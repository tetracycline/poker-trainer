"""B816: two genuinely distinct rank75 monotone flops; QJo observed B807
in both policies motivates, but does not certify, these new originals."""
import argparse,base64,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
import hu_b758_rank75_monotone as prior
import hu_b814_rank75_other_roots as paired
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_sequential_cfr_reach import accepted,cardkey

native=prior.native
checked=prior.checked
CASES={'9d8d5d':['6d','4d','7d'],'9d8d7d':['5d','4d','6d']}
HERO='JcQh'
FOE='AcQc'
B807=Path('data/solver_evidence/NL2_B807_R75_9D8D6D.zip')
OLD=set(prior.HISTORICAL)|set(prior.CASES)
WORKER='tools/hu_b816_rank75_new_monotone.py'

def preflight(a):
    solver=a.solver.resolve(); p=solver/'postflop/py'
    assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    assert checked.blob(prior.WORKER)=='44528fa0da5661425f7b259281eba4062c034747'
    assert checked.blob(paired.__file__)=='3cf88fba3e00548d2266a2e455da51ecf922edc0'
    assert checked.blob('data/solver_evidence/partial/b809_rank75_original_observations.json')=='03ca86e30e24b0fb9f14aedd11f071871f5f3ea8'
    assert all(checked.blob(path)==v for path,v in checked.PINS.items())
    assert tuple(checked.blob(path) for path in checked.APP_FILES)==prior.APP
    assert (sha((p/'pipeline.py').read_bytes()),sha((p/'ranges.py').read_bytes()),sha((solver/'inputs/pool_stats.json').read_bytes()))==(native.PIPELINE,native.RANGES,native.POOL)
    assert sha(B807.read_bytes())=='9086fd74f8a54cb3a27d4cb192057367e51d5fa8deb849d7cba1be2fc0db5648'
    with ZipFile(B807) as z:
        proof=json.loads(z.read('proof.json'))
        old,=[x for x in proof['turns'] if x['turn']=='5d']
        assert HERO in old['shared_hands'] and old['exp_ip']['reach']['compatible_hole_card_pairs']>0
        for mode in ('gto','exp_ip'):
            assert sha(z.read('5d-'+mode+'/result.json'))==old[mode]['result_sha256']
    assert len({suit_isomorphism_class(f) for f in CASES})==len(CASES)==2
    assert not ({suit_isomorphism_class(f) for f in CASES}&{suit_isomorphism_class(f) for f in OLD})
    sys.path.insert(0,str(p));import pipeline,ranges
    ranges.SPOTS.update(native.EXTRA_SPOTS)
    route=json.loads(subprocess.check_output(['node','tools/hu_b674_threebet_call_routes.cjs']))['75']
    assert (route['id'],route['line'],route['seat'],route['turn_pot'],route['turn_stack'])==(native.MODEL,native.LINE,1,2740,8705)
    assert route['routes']['mono']==dict(parents=['DRAW','WDRAW'],decisions={'DRAW':'下注 ½','WDRAW':'過'})
    w=ranges.ranges('CO3_BTN','gto')
    assert w[1][ranges.NAMES.index('QJo')]==w[0][ranges.NAMES.index('AQs')]==1
    template,_=prior.source(prior.OLD)
    assert (template['oop'],template['ip'])==tuple(ranges.to_str(row) for row in w)
    assert template['flop_oop']==template['flop_ip']=='33%,50%,75%,100%'
    f=a.flop;turns=CASES[f];eligible=[]
    for t in turns:
        pub=f+t
        assert len(checked.cards(pub+HERO+FOE))==8 and native.tx(f)==native.tx(pub)=='mono'
        if native.hcls(HERO,f) in route['routes']['mono']['parents'] and native.hcls(HERO,pub)=='WDRAW':
            eligible.append(t)
    assert eligible, 'No exact physical QJo route; do not solve'
    job=dict(template,flop=f,out='result.json',iters=2100,target_pct=.45,
             extract=[dict(prefix=[],street=True)]+[dict(prefix=['b33','c',t],street=False,raw=True) for t in eligible])
    assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(1650,9250,.05,1000)
    return pipeline,route,job,eligible

def run(a):
    pipeline,route,job,turns=preflight(a)
    if a.preflight:
        print(json.dumps(dict(flop=a.flop,eligible_static_turns=turns,hero=HERO,opponent=FOE,original_gto_nl2_shared_hands_source='B807 9d8d6d/5d',not_native_evidence=True)));return
    if a.driver:
        assert a.driver.resolve()==a.solver.resolve()/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',str(a.solver/'postflop/postflop-solver'),'rev-parse','HEAD'],text=True).strip()==native.RUST
    if a.checkpoint_only:
        assert a.driver and not a.output.exists()
        root=native.solve(a.output/'flop',job,a.driver)
    else:
        if a.driver:
            assert a.checkpoint and not a.output.exists()
            a.output.mkdir(parents=True);(a.output/'flop').mkdir()
            for name in ('job.json','result.json'):
                (a.output/'flop'/name).write_bytes((a.checkpoint/'flop'/name).read_bytes())
        else:assert (a.output/'proof.json').exists()
        root=native.solve(a.output/'flop',job,None)
    assert (a.output/'flop/job.json').read_bytes()==compact(job)
    assert (root['flop'],root['pot'],root['stack'])==(a.flop,1650,9250)
    assert not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    original={n['board'][-2:]:n for n in root['nodes'] if n['line']=='b33 c/'}
    assert set(original)==set(turns)
    for t,n in original.items():
        assert (n['player'],n['pot'],n['bets'])==(0,2740,[545,545])
        assert checked.cards(n['board'])==checked.cards(a.flop+t)
    origin=dict(flop=a.flop,worker_blob=checked.blob(WORKER),root_job_sha256=sha(compact(job)),root_sha256=sha((a.output/'flop/result.json').read_bytes()),
                raw_boundaries={t:sha(compact(n)) for t,n in original.items()})
    if a.checkpoint_only:
        (a.output/'checkpoint.json').write_bytes(json_bytes(origin));return
    if a.driver:assert (a.checkpoint/'checkpoint.json').read_bytes()==json_bytes(origin)
    pool=json.loads((a.solver/'inputs/pool_stats.json').read_bytes())['NL2']
    rows=[]
    for t in turns:
        gate=checked.checked_gate(root,t,route)
        row=dict(turn=t,root_gate=gate,policies={},shared_displayed_pairs=[],joint_pairs=[]);rows.append(row)
        if not gate['rendered_hero_combos']:continue
        gj=native.turn_job(root,t,pipeline);games=[];common=None;reach=None
        for mode in ('gto','exp_ip'):
            target=gj;rules=None
            if mode=='exp_ip':
                target,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='CO3_BTN')),job=gj),mode,pool,pipeline)
                target['out']='result.json'
            leaf=a.output/(t+'-'+mode);g=native.solve(leaf,target,a.driver)
            assert (leaf/'job.json').read_bytes()==compact(target) and (g['flop'],g['pot'],g['stack'])==(a.flop,2740,8705)
            assert 0<=g['info']['gto_expl_pct']<=.5
            r,hands=native.decision(root,g,t,route)
            assert set(hands)<=set(gate['rendered_hands'])
            bits=base64.b64decode(r['compatible_action_mask_b64'],validate=True)
            legal={''.join(cardkey(h)) for h,m in zip(g['hands'][1],bits,strict=True) if m}
            e=dict(reach=r,displayed=hands,result_sha256=sha((leaf/'result.json').read_bytes()),job_sha256=sha(compact(target)))
            row['policies'][mode]=e;games.append(g)
            common=set(hands) if common is None else common&set(hands)
            reach=legal if reach is None else reach&legal
            if mode=='gto':
                assert not g['info'].get('lock_stats')
                if not hands:break
            else:
                assert g['hands']==games[0]['hands'] and 0<=g['info']['hero_gap_pct']<=.5
                e['measured_lock_application']=native.audit_patterns(g,target,dict(locks=rules),pool,1)
                m=e['measured_lock_application'];assert any(v>0 for k,v in m['driver_tree_nodes'].items() if k in m['marginal_targets'])
                row['shared_displayed_pairs']=paired.common_pairs(root,games,common,t)
                row['joint_pairs']=paired.common_pairs(root,games,reach,t)
        if row['shared_displayed_pairs']:break
    locked=[r for r in rows if 'exp_ip' in r['policies']]
    half=[r for r in locked if r['joint_pairs'] and all(p['reach']['b50'] is not None and 'b50' in p['reach']['source_actions'] for p in r['policies'].values())]
    report=dict(schema='NL2_B816_R75_TWO_NEW_MONOTONE_V1',rank=75,flop=a.flop,origin=origin,preregistered_turns=turns,turns=rows,
        new_flop_solve_invocations=1,locked_public_boards=len(locked),joint_halfpot_assessed=len(half),
        halfpot_candidates=sum(all(p['reach']['b50']['candidate'] for p in r['policies'].values()) for r in half),
        positive_distinct_flops=int(any(r['shared_displayed_pairs'] for r in rows)),not_a_certification=True)
    (a.output/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','locked_public_boards','joint_halfpot_assessed','halfpot_candidates','positive_distinct_flops')}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--checkpoint',type=Path)
    p.add_argument('--checkpoint-only',action='store_true');p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
