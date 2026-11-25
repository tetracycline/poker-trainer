"""B837: two untested same-suit turns from authenticated B833 Td8d6d root.
No root rerun. Fail closed unless the original binary64 chance weights and
all existing conditional job bytes can be reproduced. Also verify B809's
same-physical-two-seat witness rather than counting shared hero hands alone."""
import argparse,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
import hu_b766_rank75_chance_turns as prev
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_sequential_cfr_reach import accepted,cardkey
native=prev.native
checked=prev.checked
CASES={'Td8d6d':(['2d','3d','5d'],138884347079)}
NEW=['4d','7d']
def head(p):
    return subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip()

def preflight(a):
    solver=a.solver.resolve()
    rust=solver/'postflop/postflop-solver'
    assert sys.version_info[:2]==(3,11) and head(solver)==native.SOLVER and head(rust)==native.RUST
    assert all(checked.blob(rust/p)==v for p,v in prev.RUST_FILES.items())
    assert checked.blob(solver/'postflop/pfdriver/src/main.rs')==prev.DRIVER_SOURCE
    assert all(checked.blob(p)==v for p,v in checked.PINS.items())
    assert tuple(checked.blob(p) for p in checked.APP_FILES)==prev.old.APP
    for p,v in [('postflop/py/pipeline.py',native.PIPELINE),('postflop/py/ranges.py',native.RANGES),('inputs/pool_stats.json',native.POOL)]:
        assert sha((solver/p).read_bytes())==v
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline,ranges
    ranges.SPOTS.update(native.EXTRA_SPOTS)
    e=Path('data/solver_evidence')
    # Independent positive witness check on archived B807 original.
    source=e/'NL2_B807_R75_9D8D6D.zip'
    assert sha(source.read_bytes())=='9086fd74f8a54cb3a27d4cb192057367e51d5fa8deb849d7cba1be2fc0db5648'
    root_src=e/'NL2_B758_ROOT_R75_9D8D6D.zip'
    assert sha(root_src.read_bytes())=='09b502857f7858c7680d09312c20dd60999486e5b7b310eb98fd586018746827'
    with ZipFile(source) as z,ZipFile(root_src) as cp:
        prior_proof=json.loads(z.read('proof.json'))
        row,=[r for r in prior_proof['turns'] if r['turn']=='5d']
        old_root=json.loads(cp.read('flop/result.json'))
        assert sha(cp.read('flop/result.json'))==json.loads(cp.read('checkpoint.json'))['root_sha256']
        games=[]
        for mode in ('gto','exp_ip'):
            rb=z.read('5d-'+mode+'/result.json');jb=z.read('5d-'+mode+'/job.json')
            assert sha(rb)==row[mode]['result_sha256'] and sha(jb)==row[mode]['job_sha256']
            games.append(json.loads(rb))
        prior_pairs=common_pairs(old_root,games,set(row['shared_hands']),'5d')
    old,jid=CASES[a.flop]
    receipt=json.loads(Path('data/nl2_hu_b835_source_receipts.json').read_bytes())
    assert (receipt['run']['id'],receipt['run']['head_sha'],receipt['run']['conclusion'])==(45518585298,'e6f29a285a5ed45dbfc6971e3c861b2c17712be2','success')
    j,=[j for j in receipt['jobs'] if j['id']==jid]
    assert (j['name'],j['status'],j['conclusion'],j['head_sha'])==('solve ('+a.flop+')','completed','success',receipt['run']['head_sha'])
    assert checked.blob('tools/hu_b833_rank75_new_monotone.py')==receipt['blobs']['tools/hu_b833_rank75_new_monotone.py']=='d0b92980c4aaf6e2003dc1237383563b4294517e'
    files=[e/('NL2_B833_R75_'+a.flop.upper()+'.zip'),e/('NL2_B833_R75_'+a.flop.upper()+'_ROOT.zip')]
    art=[]
    for p,n in zip(files,['B833-R75-','B833-root-R75-'],strict=True):
        r,=[r for r in receipt['artifacts'] if r['name']==n+a.flop]
        assert sha(p.read_bytes())==r['digest'].removeprefix('sha256:')
        art.append(dict(id=r['id'],sha256=r['digest'].removeprefix('sha256:')))
    with ZipFile(files[0]) as z,ZipFile(files[1]) as cp:
        raw=z.read('flop/result.json');job=z.read('flop/job.json')
        assert cp.read('flop/result.json')==raw and cp.read('flop/job.json')==job
        pin=json.loads(cp.read('checkpoint.json'));original=json.loads(z.read('proof.json'))
        assert original['origin']==pin and pin['root_sha256']==sha(raw) and pin['root_job_sha256']==sha(job)
        assert original['positive_distinct_flops']==0 and original['preregistered_turns']==old
        prior_jobs={}
        for row in original['turns']:
            for mode,policy in row['policies'].items():
                t=row['turn'];jb=z.read(t+'-'+mode+'/job.json');rb=z.read(t+'-'+mode+'/result.json')
                assert sha(jb)==policy['job_sha256'] and sha(rb)==policy['result_sha256']
                if mode=='gto':prior_jobs[t]=jb
    root=json.loads(raw);fj=json.loads(job)
    assert (root['flop'],root['pot'],root['stack'])==(a.flop,1650,9250)
    assert not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    assert (fj['oop'],fj['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('CO3_BTN','gto'))
    assert fj['flop_oop']==fj['flop_ip']=='33%,50%,75%,100%'
    observed={n['board'][6:]:n for n in root['nodes'] if n['line']=='b33 c/'}
    assert set(observed)==set(old) and all(sha(compact(n))==pin['raw_boundaries'][t] for t,n in observed.items())
    orbit=lambda t:(t[0],t[1]==a.flop[1])
    assert len({orbit(t) for t in old+NEW})==len(old+NEW)
    masks={t:prev.blocked(root['hands'],t) for t in old+NEW}
    held={}
    for t in old:
        weights=prev.reconstruct(root,observed,masks,[u for u in old if u!=t],t)
        assert all(prev.weight_bytes(x)==prev.weight_bytes(y) for x,y in zip(weights,observed[t]['wr'],strict=True))
        rebuilt=compact(native.turn_job(prev.range_input(root,t,weights),t,pipeline))
        if t in prior_jobs:assert rebuilt==prior_jobs[t]
        held[t]=dict(full_job_sha256=sha(rebuilt),original_job_compared=t in prior_jobs,raw_seat_sha256=[sha(prev.weight_bytes(x)) for x in weights])
    assert len(prior_jobs)>=2
    route=json.loads(subprocess.check_output(['node','tools/hu_b674_threebet_call_routes.cjs']))['75']
    assert (route['id'],route['line'],route['seat'],route['turn_pot'],route['turn_stack'])==(native.MODEL,native.LINE,1,2740,8705)
    assert route['routes']['mono']==dict(parents=['DRAW','WDRAW'],decisions={'DRAW':'下注 ½','WDRAW':'過'})
    gates={};jobs={}
    for t in NEW:
        weights=prev.reconstruct(root,observed,masks,old,t)
        source=prev.range_input(root,t,weights)
        g=checked.checked_gate(source,t,route)
        assert native.tx(a.flop+t)=='mono'
        g['weak_draw_hands']=[h for h in g['rendered_hands'] if native.hcls(h,a.flop+t)=='WDRAW']
        g['raw_seat_sha256']=[sha(prev.weight_bytes(x)) for x in weights]
        gates[t]=g
        if g['weak_draw_hands']:jobs[t]=native.turn_job(source,t,pipeline)
    return root,route,pipeline,jobs,dict(source_run=45518585298,source_head=receipt['run']['head_sha'],source_job=jid,archives=art,root=pin,heldout=held,root_gates=gates,prior_B809_shared_physical_pairs=prior_pairs)

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
    report=dict(schema='NL2_B837_R75_HELDOUT_B833_ROOT_V1',rank=75,flop=a.flop,source_worker_blob=checked.blob(__file__),origin=evidence,turns=rows,new_flop_solve_invocations=0,
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
