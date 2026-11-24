"""B814: held-out fourth-suit-card turns on the two OTHER archived B758 roots.
No original flop solve; four original binary64 leave-one-out ranges and exact
conditional job bytes must agree before any new conditional native job.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
import hu_b766_rank75_chance_turns as prev
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_sequential_cfr_reach import accepted,cardkey

native=prev.native
checked=prev.checked
CASES={
 '8c7c5c':(['2d','3h','9s','Qh'],['2c','3c','4c','6c'],138258993487,
  14894742842,'49b031533518bf904b2de2111d41d00bb6c0bbe00807a5d7794c26e3173baa93',
  14895047629,'abfcd2923842264af690892648cd814aec311120fbd036b97baa99a7801dbf10'),
 '9h7h5h':(['2d','3c','Qc','Ks'],['2h','3h','4h','6h'],138258993993,
  14894499446,'238ef9aed23527137a61ed74ac4210061a2de04a77c5c084fa4efec8de1df442',
  14894509332,'950fa177257a430830a4b3c03371db8b40f5664c45256dcbeac438c4172c13be')
}
def head(p):
    return subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip()

def preflight(a):
    solver=a.solver.resolve()
    rust=solver/'postflop/postflop-solver'
    assert sys.version_info[:2]==(3,11) and head(solver)==native.SOLVER and head(rust)==native.RUST
    assert checked.blob(prev.__file__)=='2624730b49abd405db6aa82b2f87c5e8bf728c64'
    assert all(checked.blob(rust/p)==v for p,v in prev.RUST_FILES.items())
    assert checked.blob(solver/'postflop/pfdriver/src/main.rs')==prev.DRIVER_SOURCE
    assert all(checked.blob(p)==v for p,v in checked.PINS.items())
    assert tuple(checked.blob(p) for p in checked.APP_FILES)==prev.old.APP
    for p,v in [('postflop/py/pipeline.py',native.PIPELINE),('postflop/py/ranges.py',native.RANGES),('inputs/pool_stats.json',native.POOL)]:
        assert sha((solver/p).read_bytes())==v
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline,ranges
    ranges.SPOTS.update(native.EXTRA_SPOTS)
    old,new,jid,aid,digest,cid,cpdigest=CASES[a.flop]
    e=Path('data/solver_evidence')
    manifest=e.parent/'nl2_hu_b761_source_manifest.json'
    assert checked.blob(manifest)==prev.MANIFEST
    receipt=json.loads(manifest.read_bytes())
    assert (receipt['run']['id'],receipt['run']['head_sha'],receipt['run']['conclusion'])==(45339357100,prev.OLD_HEAD,'success')
    j,=[j for j in receipt['jobs'] if j['id']==jid]
    assert (j['name'],j['status'],j['conclusion'],j['head_sha'])==('solve ('+a.flop+')','completed','success',prev.OLD_HEAD)
    files=[e/('NL2_B758_R75_'+a.flop.upper()+'.zip'),e/('NL2_B758_ROOT_R75_'+a.flop.upper()+'.zip')]
    for p,i,d in zip(files,[aid,cid],[digest,cpdigest],strict=True):
        r,=[r for r in receipt['artifacts'] if r['id']==i]
        assert r['digest']=='sha256:'+d and r['workflow_run']['head_sha']==prev.OLD_HEAD
        assert sha(p.read_bytes())==d
    with ZipFile(files[0]) as z,ZipFile(files[1]) as cp:
        raw=z.read('flop/result.json');job=z.read('flop/job.json')
        assert cp.read('flop/result.json')==raw and cp.read('flop/job.json')==job
        pin=json.loads(cp.read('checkpoint.json'))
        assert pin['root_sha256']==sha(raw) and pin['job_sha256']==sha(job)
        assert pin['worker_blob']==checked.blob('tools/hu_b758_rank75_monotone.py')=='44528fa0da5661425f7b259281eba4062c034747'
        original=json.loads(z.read('proof.json'))
        assert original['root_sha256']==sha(raw) and original['root_job_sha256']==sha(job)
        assert original['positive_distinct_flops']==0
        assert all(sha(z.read(n))==v for n,v in original['native_files_sha256'].items())
        prior_jobs={t:z.read(t+'-gto/job.json') for t in old if t+'-gto/job.json' in z.namelist()}
    root=json.loads(raw);fj=json.loads(job)
    assert (root['flop'],root['pot'],root['stack'])==(a.flop,1650,9250)
    assert not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    assert (fj['oop'],fj['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('CO3_BTN','gto'))
    assert fj['flop_oop']==fj['flop_ip']=='33%,50%,75%,100%'
    observed={n['board'][6:]:n for n in root['nodes'] if n['line']=='b33 c/'}
    assert set(observed)==set(old) and all(sha(compact(n))==pin['new_raw_boundary_sha256'][t] for t,n in observed.items())
    orbit=lambda t:(t[0],t[1]==a.flop[1])
    assert len({orbit(t) for t in old+new})==len(old+new)
    masks={t:prev.blocked(root['hands'],t) for t in old+new}
    held={}
    for t in old:
        weights=prev.reconstruct(root,observed,masks,[u for u in old if u!=t],t)
        assert all(prev.weight_bytes(x)==prev.weight_bytes(y) for x,y in zip(weights,observed[t]['wr'],strict=True))
        rebuilt=compact(native.turn_job(prev.range_input(root,t,weights),t,pipeline))
        if t in prior_jobs:assert rebuilt==prior_jobs[t]
        held[t]=dict(full_job_sha256=sha(rebuilt),original_job_compared=t in prior_jobs,raw_seat_sha256=[sha(prev.weight_bytes(x)) for x in weights])
    assert len(prior_jobs)>=3
    route=json.loads(subprocess.check_output(['node','tools/hu_b674_threebet_call_routes.cjs']))['75']
    assert (route['id'],route['line'],route['seat'],route['turn_pot'],route['turn_stack'])==(native.MODEL,native.LINE,1,2740,8705)
    assert route['routes']['mono']==dict(parents=['DRAW','WDRAW'],decisions={'DRAW':'下注 ½','WDRAW':'過'})
    gates={};jobs={}
    for t in new:
        weights=prev.reconstruct(root,observed,masks,old,t)
        source=prev.range_input(root,t,weights)
        g=checked.checked_gate(source,t,route)
        assert native.tx(a.flop+t)=='mono'
        g['weak_draw_hands']=[h for h in g['rendered_hands'] if native.hcls(h,a.flop+t)=='WDRAW']
        g['raw_seat_sha256']=[sha(prev.weight_bytes(x)) for x in weights]
        gates[t]=g
        if g['weak_draw_hands']:jobs[t]=native.turn_job(source,t,pipeline)
    return root,route,pipeline,jobs,dict(source_run=45339357100,source_head=prev.OLD_HEAD,source_job=jid,archives=[dict(id=aid,sha256=digest),dict(id=cid,sha256=cpdigest)],root=pin,heldout=held,root_gates=gates)

def common_pairs(root,games,hands,turn):
    root_bet,=[n for n in root['nodes'] if n['line']=='' and len(n['board'])==6]
    villains=accepted(root_bet,root['hands'],'b33')
    for game in games:
        parent,=[n for n in game['nodes'] if n['line']=='b33 c/' and n['player']==0 and len(n['board'])==8]
        target,=[n for n in game['nodes'] if n['line']==native.LINE and n['player']==1 and len(n['board'])==8]
        villains &= accepted(parent,game['hands'],'x')
        villains &= {cardkey(h) for h,w in zip(game['hands'][0],target['w'][0],strict=True) if w>1e-4}
    dead=checked.cards(root['flop']+turn)
    return [[h,''.join(v)] for h in sorted(hands) for v in sorted(villains) if dead.isdisjoint(v) and checked.cards(h).isdisjoint(v)]

def run(a):
    root,route,pipeline,jobs,evidence=preflight(a)
    if a.preflight:print(json.dumps(evidence));return
    out=a.output
    if a.driver:
        assert a.driver.resolve()==a.solver.resolve()/'postflop/pfdriver/target/release/pfdriver'
        assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True)
    pool=json.loads((a.solver/'inputs/pool_stats.json').read_bytes())['NL2']
    rows=[]
    for t,gate in evidence['root_gates'].items():
        item=dict(turn=t,gate=gate,policies={},shared_displayed_pairs=[],joint_pairs=[])
        rows.append(item)
        if t not in jobs:continue
        gj=jobs[t];games=[];common=None;reachable=None
        for mode in ('gto','exp_ip'):
            job=gj
            if mode=='exp_ip':
                job,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='CO3_BTN')),job=gj),mode,pool,pipeline)
                job['out']='result.json'
            leaf=out/(t+'-'+mode)
            game=native.solve(leaf,job,a.driver)
            assert (leaf/'job.json').read_bytes()==compact(job)
            assert (game['flop'],game['pot'],game['stack'])==(a.flop,2740,8705)
            assert 0<=game['info']['gto_expl_pct']<=.5
            row,hands=native.decision(root,game,t,route)
            import base64
            mask=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
            allhands={''.join(cardkey(h)) for h,m in zip(game['hands'][1],mask,strict=True) if m}
            assert set(hands)<=set(gate['rendered_hands'])
            record=dict(reach=row,displayed=hands,source_sha256=sha((leaf/'result.json').read_bytes()),job_sha256=sha(compact(job)))
            item['policies'][mode]=record
            games.append(game)
            common=set(hands) if common is None else common & set(hands)
            reachable=allhands if reachable is None else reachable & allhands
            if mode=='gto':
                assert not game['info'].get('lock_stats')
                if not hands:break
            else:
                assert game['hands']==games[0]['hands'] and 0<=game['info']['hero_gap_pct']<=.5
                record['measured_lock_application']=native.audit_patterns(game,job,dict(locks=rules),pool,1)
                r=record['measured_lock_application']
                assert any(n>0 for k,n in r['driver_tree_nodes'].items() if k in r['marginal_targets'])
                item['shared_displayed_pairs']=common_pairs(root,games,common,t)
                item['joint_pairs']=common_pairs(root,games,reachable,t)
        if item['shared_displayed_pairs']:break
    locked=[r for r in rows if 'exp_ip' in r['policies']]
    half=[r for r in locked if r['joint_pairs'] and all(p['reach']['b50'] is not None and 'b50' in p['reach']['source_actions'] for p in r['policies'].values())]
    report=dict(schema='NL2_B814_R75_HELDOUT_OTHER_ROOTS_V1',rank=75,flop=a.flop,source_worker_blob=checked.blob(__file__),origin=evidence,turns=rows,new_flop_solve_invocations=0,
        locked_public_boards=len(locked),joint_halfpot_assessed=len(half),halfpot_candidates=sum(all(p['reach']['b50']['candidate'] for p in r['policies'].values()) for r in half),
        positive_distinct_flops=int(any(r['shared_displayed_pairs'] for r in rows)),not_a_certification=True)
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','locked_public_boards','joint_halfpot_assessed','halfpot_candidates','positive_distinct_flops')}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--driver',type=Path)
    p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
