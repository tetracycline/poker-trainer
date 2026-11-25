"""B851: rank106 new b75 turn continuation ONLY from original B505 b33 roots.
B505 tested b50, never b75. No new flop solve. Both original policies retain
their own exact parent weights; only shared physical pairs are eligible.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
from hu_b505_rank107_originals import BOARDS,original
from hu_b463_rank45_gate import SOLVER,RUST
from hu_b483_locked_medium import POOL,PIPELINE,RANGES,proof
from hu_b467_river_source_gate import sha,json_bytes
from hu_b470_rank73_new_rivers import audit_patterns
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted,cardkey,game_reach
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from verify_hu_multiboard_100bb import lock_scope
DECK=[r+s for r in '23456789TJQKA' for s in 'cdhs']
JOBIDS={14752561398:137191779554,14752473776:137191779861,14755175780:137210203349,14754959467:137216250866}
ACT={'過':'x','下注 ½':'b50','下注 ¾':'b75'}
def cards(b):return {b[i:i+2] for i in range(0,len(b),2)}
def node(game,line,board,seat):
    n,=[n for n in game['nodes'] if (n['line'],n['board'],n['player'])==(line,board,seat)]
    return n
def live(game,n,seat):
    return {cardkey(h) for h,w in zip(game['hands'][seat],n['w'][seat],strict=True) if w>1e-4 and cards(n['board']).isdisjoint(cardkey(h))}
def load(folder,aid,flop,turn,version,ranges):
    pin=json.loads(Path('data/nl2_hu_b505_rank107_artifacts.json').read_bytes())[str(aid)]
    meta=json.loads((folder/f'{aid}.json').read_bytes());jmeta=json.loads((folder/f'{aid}-job.json').read_bytes())
    assert (meta['id'],meta['name'],meta['digest'],meta['workflow_run']['id'],meta['workflow_run']['head_sha'],meta['workflow_run']['repository_id'])==(aid,pin['name'],'sha256:'+pin['sha256'],pin['run'],pin['head'],1438346845)
    assert (jmeta['id'],jmeta['run_id'],jmeta['head_sha'],jmeta['status'],jmeta['conclusion'])==(JOBIDS[aid],pin['run'],pin['head'],'completed','success')
    archive=folder/f'{aid}.zip';assert sha(archive.read_bytes())==pin['sha256']
    with ZipFile(archive) as z:
        assert z.read('evidence/poker-solver-pin.txt').decode().strip()==SOLVER
        assert z.read('evidence/rust-pin.txt').decode().strip()==RUST
        m=json.loads(z.read(f'evidence/BTN_BB-{flop}-{version}.json'))
        assert (m['spot'],m['pot_family'],m['version'],m['failures'],m['pool_source_sha256'])==('BTN_BB','SRP',version,[],POOL)
        case,=[c for c in m['cases'] if (c['line'],c['turn'])==('b33 c',turn)]
        root,rj=original(z,m['file_flop'],m['file_flop_sha256'])
        sub,j=original(z,case['source_path'],case['source_sha256'])
    hero=1 if version=='exp_ip' else None
    for g,k,p,s in ((root,rj,550,9750),(sub,j,914,9568)):
        assert (g['flop'],g['pot'],g['stack'],k['flop'],k['pot'],k['stack'])==(flop,p,s,flop,p,s)
        assert (k.get('hero'),k['rake_rate'],k['rake_cap'])==(hero,.05,1000)
        assert 0<=g['info']['gto_expl_pct']<=.5
        if hero is not None:assert 0<=g['info']['hero_gap_pct']<=.5 and g['info']['lock_stats']
    assert rj['flop_oop']==rj['flop_ip']=='33%,50%,75%,100%'
    assert (rj['oop'],rj['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('BTN_BB',version))
    assert j['turn_ip']==j['turn_oop']=='50%,100%' # b75 is genuinely absent
    assert (j['line0'],j['turn'],sub['line0'])==(['b33','c','/'],turn,'b33 c')
    f,=[n['board'] for n in root['nodes'] if n['line']==''];b=f+turn
    assert cards(f)==cards(flop)
    par=node(root,'b33 c/',b,0);assert (par['pot'],par['bets'])==(914,[182,182])
    for s,k in enumerate(('oop_w','ip_w')):
        assert j[k]==[[h,w] for h,w in zip(root['hands'][s],par['wr'][s],strict=True) if w>1e-4]
    if hero is not None:assert lock_scope(sub,m['locks'],version)['observed_marginal_source_nodes']>0
    a=node(root,'',f,0);c=node(root,'b33',f,1)
    assert (a['pot'],a['bets'],c['pot'],c['bets'])==(550,[0,0],732,[182,0])
    alive=[accepted(a,root['hands'],'b33'),accepted(c,root['hands'],'c')]
    for s in (0,1):
        alive[s]&={cardkey(h) for h,w in zip(root['hands'][s],par['wr'][s],strict=True) if w>1e-4 and cards(b).isdisjoint(cardkey(h))}
    return dict(root=root,job=j,alive=alive,board=b,identity=dict(artifact=aid,run=pin['run'],job=JOBIDS[aid],head=pin['head'],archive_sha256=pin['sha256'],root_sha256=m['file_flop_sha256'],old_subgame_sha256=case['source_sha256']))
def pairs(seats):
    return sum(set(h).isdisjoint(v) for h in seats[1] for v in seats[0])
def decision(root,g,b,route):
    n=node(g,route['line'],b,1)
    assert (n['pot'],n['bets'],g['stack']-max(n['bets']))==(2286,[686,686],8882)
    assert {'x','b50','b75'}<=set(n['acts'])
    seq=[(root,'',b[:6],0,'b33'),(root,'b33',b[:6],1,'c'),
         (g,'b33 c/',b[:8],0,'x'),(g,'b33 c/x',b[:8],1,'b75'),
         (g,'b33 c/x b75',b[:8],0,'c'),(g,'b33 c/x b75 c/',b,0,'x')]
    seats=[live(g,n,s) for s in (0,1)]
    for gg,line,board,s,act in seq:seats[s]&=accepted(node(gg,line,board,s),gg['hands'],act)
    shown=set()
    for h in seats[1]:
        cls=[hand_cell(''.join(h),b[:k])[0] for k in (6,8,10)]
        if all(k in route['routes'][st] for k,st in zip(cls,('flop','turn','river'))):
            act=ACT[route['routes']['river'][cls[-1]]]
            if act in n['acts'] and h in accepted(n,g['hands'],act):shown.add(h)
    return seats,shown,proof(root,g,n,game_reach(root,g)[0])
def main(a):
    solver=a.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    for p,d in [('postflop/py/pipeline.py',PIPELINE),('postflop/py/ranges.py',RANGES),('inputs/pool_stats.json',POOL)]:assert sha((solver/p).read_bytes())==d
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    route=json.loads(a.routes.read_bytes());assert (route['id'],route['actor'],route['line'])==('ln-ipfr-r_model-5ce65m',1,'b33 c/x b75 c/x')
    pri=json.loads(Path('data/nl2_hu_b838_234_approx_frequency_priority.json').read_bytes())
    row,=[r for r in pri['rows'] if r['rank']==106];assert row['passes_min_0_2_pct_frequency'] and pri['current_certified_opportunity_share_pct']<90
    flop,public,gid,eid=next(x for x in BOARDS if x[0]==a.flop);turn=public[6:8]
    gs,es=[load(a.receipts,i,flop,turn,v,ranges) for i,v in ((gid,'gto'),(eid,'exp_ip'))]
    b=gs['board'];assert b==es['board']
    both=[gs['alive'][s]&es['alive'][s] for s in (0,1)]
    both[1]={h for h in both[1] if hand_cell(''.join(h),b[:6])[0] in route['routes']['flop'] and hand_cell(''.join(h),b)[0] in route['routes']['turn']}
    viable=[]
    for river in DECK:
        if river in cards(b):continue
        ss=[{h for h in both[s] if river not in h} for s in (0,1)]
        ss[1]={h for h in ss[1] if hand_cell(''.join(h),b+river)[0] in route['routes']['river']}
        if pairs(ss):viable.append(river)
    keep=viable if len(viable)<=16 else [viable[round(i*(len(viable)-1)/15)] for i in range(16)]
    a.output.mkdir(parents=True,exist_ok=True)
    report=dict(schema='NL2_B851_R106_FROZEN_B33_ROOT_NEW_B75_V1',flop=flop,turn=turn,origins=[gs['identity'],es['identity']],route_sha256=sha(a.routes.read_bytes()),prior_pair_count=pairs(both),preselected_rivers=keep,original_flop_solves=0,cert_promotions=0,locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,positive_distinct_flops=0,observations={})
    if a.preflight:
        (a.output/'preflight.json').write_bytes(json_bytes(report));print(json.dumps(report));return
    if keep:
        if a.driver:
            assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
        games=[]
        for version,origin in [('gto',gs),('exp_ip',es)]:
            job=dict(origin['job'],out='result.json',iters=2450,target_pct=.4,rank_pct=.4,compress=False,root_no_bet=False,
                     turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',
                     river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',river_donk='50%,75%,100%',
                     extract=[dict(prefix=[],street=True)])
            for river in keep:
                job['extract'] += [dict(prefix=['x','b75','c',river],street=False),dict(prefix=['x','b75','c',river,'x'],street=False)]
            manifest=None
            if version=='exp_ip':
                # Fresh measured marginal lock, but retain original exp root's own boundary weights.
                from hu_checked_gto_boundary import lock_metadata
                from solve_hu_multiboard_100bb import make_fallbacks
                rules,meta=make_fallbacks('BTN_BB',version,pool,pipeline.lock_list,flop,by_street=True)
                job['locks']=rules;manifest=dict(locks=lock_metadata(meta));assert job['hero']==1
            folder=a.output/version;g=solve(folder,job,None if (folder/'result.json').exists() else a.driver)
            assert 0<=g['info']['gto_expl_pct']<=.5 and (g['flop'],g['pot'],g['stack'])==(flop,914,9568)
            g.update(line0='b33 c',turn=turn,rivers=keep)
            lock=None
            if manifest:
                assert 0<=g['info']['hero_gap_pct']<=.5
                lock=audit_patterns(g,job,manifest,pool,1)
                assert any(v>0 for k,v in lock['driver_tree_nodes'].items() if k in lock['marginal_targets'])
            else:assert not g['info'].get('lock_stats')
            games.append((origin['root'],g,lock))
        for river in keep:
            board=b+river;d=[decision(root,g,board,route) for root,g,l in games]
            common=[d[0][0][s]&d[1][0][s] for s in (0,1)]
            hero=d[0][1]&d[1][1];eligible=[common[0],hero&common[1]]
            pc=pairs(eligible);joint=pairs(common)
            report['observations'][board]=dict(gto=d[0][2],nl2=d[1][2],common_pair_count=joint,displayed_pair_count=pc,displayed_witness=next(([''.join(h),''.join(v)] for h in sorted(eligible[1]) for v in sorted(eligible[0]) if set(h).isdisjoint(v)),None))
            report['locked_public_boards']+=1
            if joint:
                assert d[0][2]['b50'] is not None and d[1][2]['b50'] is not None
                report['joint_halfpot_assessed']+=1
                report['halfpot_candidates']+=int(d[0][2]['b50']['candidate'] and d[1][2]['b50']['candidate'])
            if pc:report['positive_distinct_flops']=1
        report['measured_lock']=games[1][2]
    report['native_files']={str(p.relative_to(a.output)):sha(p.read_bytes()) for p in sorted(a.output.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (a.output/'proof.json').write_bytes(json_bytes(report));print(json.dumps({k:v for k,v in report.items() if k not in ('observations','measured_lock')}))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('solver','receipts','routes','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=[x[0] for x in BOARDS],required=True);p.add_argument('--driver',type=Path);p.add_argument('--preflight',action='store_true')
    main(p.parse_args())
