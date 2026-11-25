"""B861: rank128 original SB/BB GTO boundary and exported river screen.
No solver invocation; B735 exact previously tested boundary is excluded.
GTO-only positives are leads, not CERT or new hero locks.
"""
import json,sys,subprocess
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
from collections import Counter
from hu_b467_river_source_gate import sha,json_bytes,compact
from hu_b483_locked_medium import PIPELINE,RANGES,POOL
from hu_b463_rank45_gate import SOLVER,RUST
from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted,cardkey
from hu_b859_limp_boundaries import api

MODEL='ln-ipc-r_model-va4mgd'
BRANCH='fix/nl2-hu-lines-audit-20261118'
RUNS={44666285424:('92c10f1d3ed037e04ca9b99feb702f2174ebd9af','B1','success'),
      44736420272:('e4bc0095a7cbfd75820c6d211bf0dacb255c5e3d','B5_SBGAPS','cancelled')}
# Artifact ID, completed individual job, ZIP digest, source run.
PINS={
 '8s8h3d':(14598504895,136056270785,'17f1f9d0c1e6e5bb1301873e4eb76e44e619dd23b5fe4d32d911fdd258020722',44666285424),
 'As9h2d':(14598935222,136056270201,'b1a8e88fd871a2e0e9f8f43f068ed5187df9fc51511a09de93bd663bac2fca8d',44666285424),
 'Js9h4d':(14599361276,136056270468,'50f129112a18235d20dbc3938a7a2160c560b143216fb7e92270fa1d404fb6d7',44666285424),
 'As7h3d':(14628913050,136288829126,'b22c76c1e20f29d34096a197d1e50e3a5e03843bfe43554f6bcb02a9890a1aff',44736420272),
 'Jh9d6s':(14628394918,136288829238,'2e95b5b63a796934ed2d4e20c73a785d0d14b48b180c9baca47252127171b7b5',44736420272),
 'KsQh4d':(14630030655,136288829082,'5ad798c2d3516b289acc7b23edb634293b632c150ddbbc2997912198dc498bac',44736420272),
}
DECK=[r+s for r in '23456789TJQKA' for s in 'cdhs']
def read(p):return json.loads(api(p))
def cards(b):return {b[i:i+2] for i in range(0,len(b),2)}
def live(g,n,s,key):
    return {cardkey(h) for h,w in zip(g['hands'][s],n[key][s],strict=True) if w>1e-4 and cards(n['board']).isdisjoint(cardkey(h))}
def pick(g,line,b,actor):
    ns=[n for n in g['nodes'] if (n['line'],n['board'],n['player'])==(line,b,actor)]
    assert len(ns)<=1
    return ns[0] if ns else None
def witness(hero,villain):
    for h in sorted(hero):
        for v in sorted(villain):
            if set(h).isdisjoint(v):
                return [''.join(v),''.join(h)]
    return None
def pairs(hero,villain):
    return sum(set(h).isdisjoint(v) for h in hero for v in villain)
def source(z,path,expected):
    path='solver/postflop/'+path
    raw=z.read(path);jraw=z.read(path[:-5]+'.job.json')
    assert sha(raw)==expected
    return json.loads(raw),json.loads(jraw),sha(jraw)
def validate(g,j,flop,pot,stack):
    assert all((x['flop'],x['pot'],x['stack'])==(flop,pot,stack) for x in (g,j))
    assert (j['rake_rate'],j['rake_cap'])==(.05,1000)
    assert j.get('hero') is None and not j.get('locks')
    assert 0<=g['info']['gto_expl_pct']<=.5 and not g['info'].get('lock_stats')
def screen(flop,route,ranges,out):
    aid,jid,digest,rid=PINS[flop];head,batch,conclusion=RUNS[rid]
    run=read(f'actions/runs/{rid}');job=read(f'actions/jobs/{jid}');meta=read(f'actions/artifacts/{aid}')
    assert (run['id'],run['head_sha'],run['head_branch'],run['status'],run['conclusion'])==(rid,head,BRANCH,'completed',conclusion)
    assert (job['run_id'],job['head_sha'],job['status'],job['conclusion'],job['name'])==(rid,head,'completed','success',f'solve (SB_BB, {flop}, gto)')
    assert (meta['id'],meta['digest'],meta['expired'])==(aid,'sha256:'+digest,False)
    assert (meta['workflow_run']['id'],meta['workflow_run']['head_sha'],meta['workflow_run']['repository_id'])==(rid,head,1438346845)
    assert meta['name'] in (f'nl2-multiboard-{batch}-SB_BB-gto-{flop}',)
    raw=api(f'actions/artifacts/{aid}/zip')
    assert sha(raw)==digest and len(raw)==meta['size_in_bytes']
    (out/f'{aid}-receipts.json').write_bytes(json_bytes(dict(run=run,job=job,artifact=meta)))
    rows=[]
    with ZipFile(BytesIO(raw)) as z:
        assert z.testzip() is None
        pins={z.read(n).decode().strip() for n in z.namelist() if n.startswith('evidence/') and n.endswith('.txt')}
        assert {SOLVER,RUST}<=pins
        ms=[json.loads(z.read(n)) for n in z.namelist() if n.startswith('evidence/') and n.endswith('.json')]
        m,=[x for x in ms if isinstance(x,dict) and x.get('schema')=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1']
        assert (m['spot'],m['flop'],m['version'],m['pot_family'],m['failures'],m['locks'])==('SB_BB',flop,'gto','SRP',[],[])
        assert (m['pool_source_sha256'],m['solver_pin'],m['solver_ranges_sha256'])==(POOL,PIPELINE,RANGES)
        assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
        root,rj,rjs=source(z,m['file_flop'],m['file_flop_sha256'])
        validate(root,rj,flop,600,9700)
        assert rj['flop_oop']==rj['flop_ip']=='33%,50%,75%,100%'
        assert (rj['oop'],rj['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('SB_BB','gto'))
        f,=[n['board'] for n in root['nodes'] if n['line']=='']
        assert cards(f)==cards(flop)
        a=pick(root,'',f,0);c=pick(root,'b33',f,1)
        assert (a['pot'],a['bets'],c['pot'],c['bets'])==(600,[0,0],798,[198,0])
        rootseats=[accepted(a,root['hands'],'b33'),accepted(c,root['hands'],'c')]
        boundaries=sorted([n for n in root['nodes'] if n['line']=='b33 c/' and len(n['board'])==8],key=lambda n:n['board'])
        for n in boundaries:
            b=n['board'];t=b[-2:]
            assert b[:6]==f and (n['player'],n['pot'],n['bets'])==(0,996,[198,198])
            if (flop,t)==('KsQh4d','Tc'):
                rows.append(dict(turn=t,status='EXCLUDED_PREVIOUS_B735_BOUNDARY'));continue
            alive=[rootseats[s]&live(root,n,s,'wr') for s in (0,1)]
            hero={h for h in alive[1] if hand_cell(''.join(h),f)[0] in route['flop'] and hand_cell(''.join(h),b)[0] in route['turn']}
            possible={}
            for river in DECK:
                if river in cards(b):continue
                hh={h for h in hero if river not in h and route['river'].get(hand_cell(''.join(h),b+river)[0])=='過'}
                vv={v for v in alive[0] if river not in v}
                w=witness(hh,vv)
                if w:possible[river]=w
            row=dict(turn=t,boundary_sha256=sha(compact(n)),root_actor_counts=[len(x) for x in alive],displayed_turn_hands=len(hero),root_boundary_river_witnesses=possible,
                     status='ROOT_BOUNDARY_ONLY' if possible else 'NO_DISPLAYED_BOUNDARY_WITNESS',exact_gto_river_nodes=[])
            cases=[x for x in m['cases'] if (x['line'],x['turn'])==('b33 c',t)]
            assert len(cases)<=1
            if cases and possible:
                case=cases[0];sub,sj,sjs=source(z,case['source_path'],case['source_sha256'])
                validate(sub,sj,flop,996,9502)
                assert (sub['turn'],sub['line0'],sj['turn'],sj['line0'])==(t,'b33 c',t,['b33','c','/'])
                for s,k in enumerate(('oop_w','ip_w')):
                    assert sj[k]==[[h,w] for h,w in zip(root['hands'][s],n['wr'][s],strict=True) if w>1e-4]
                row.update(original_turn_source_sha256=case['source_sha256'],original_turn_job_sha256=sjs)
                for target in sub['nodes']:
                    if (target['line'],target['player'])!=('b33 c/x b100 c/x',1):continue
                    board=target['board'];river=board[-2:]
                    assert board[:8]==b and (target['pot'],target['bets'],sub['stack']-996)==(2988,[996,996],8506)
                    assert abs((8506/2988)/2.833-1)<.05
                    seq=[('b33 c/',b,0,'x'),('b33 c/x',b,1,'b100'),('b33 c/x b100',b,0,'c'),('b33 c/x b100 c/',board,0,'x')]
                    ancestors=[(pick(sub,line,bb,s),s,act) for line,bb,s,act in seq]
                    if any(q is None for q,_,_ in ancestors):
                        row['exact_gto_river_nodes'].append(dict(board=board,status='MISSING_EXPORTED_ANCESTOR_NOT_NEGATIVE'));continue
                    ss=[alive[s]&live(sub,target,s,'w') for s in (0,1)]
                    for q,s,act in ancestors:
                        assert act in q['acts']
                        ss[s]&=accepted(q,sub['hands'],act)
                    hh=ss[1]&hero&accepted(target,sub['hands'],'x')
                    hh={h for h in hh if route['river'].get(hand_cell(''.join(h),board)[0])=='過'}
                    w=witness(hh,ss[0]);count=pairs(hh,ss[0])
                    assert bool(w)==bool(count)
                    row['exact_gto_river_nodes'].append(dict(board=board,status='GTO_ONLY_WITNESS' if count else 'GTO_EXACT_ZERO_DISPLAYED_PAIRS',
                          gto_displayed_pairs=count,witness=w,pot=2988,stack=8506,actor=1))
            rows.append(row)
        return dict(flop=flop,run=rid,job=jid,artifact=aid,head=head,zip_sha256=digest,root_sha256=m['file_flop_sha256'],
                    root_job_sha256=rjs,boundary_count=len(boundaries),rows=rows)
def main(out,solver):
    out.mkdir(parents=True,exist_ok=False)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    native=solver/'postflop/py'
    for p,d in ((native/'pipeline.py',PIPELINE),(native/'ranges.py',RANGES),(solver/'inputs/pool_stats.json',POOL)):
        assert sha(p.read_bytes())==d
    sys.path.insert(0,str(native));import ranges
    route_raw=subprocess.check_output(['node','tools/hu_b734_rank128_routes.cjs'])
    route=json.loads(route_raw)
    assert (route['model'],route['turn'],route['river'])==(MODEL,['KQ_high:1'],{'KQ_high:1':'過'})
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    rec=reg['records'][MODEL]
    assert (rec['frequency_rank'],rec['label'],rec['solver_profile'],rec['assumed_model_node_spr'])==(128,'APPROX','SB_BB',2.833)
    pri=json.loads(Path('data/nl2_hu_b838_234_approx_frequency_priority.json').read_bytes())
    r,=[r for r in pri['rows'] if r['rank']==128]
    assert r['model_id']==MODEL and r['passes_min_0_2_pct_frequency'] and pri['current_certified_opportunity_share_pct']<90
    old=json.loads(Path('data/solver_evidence/partial/b735/summary.json').read_bytes())
    assert old['rank']==128 and old['positive_distinct_flops']==0
    rows=[screen(f,route,ranges,out) for f in PINS]
    result=dict(schema='NL2_B861_R128_ORIGINAL_SB_BB_SOURCE_PREFLIGHT_V1',rank=128,model=MODEL,route_sha256=sha(route_raw),
                source_flops=rows,cert_promotions=0,native_solves=0,locked_public_boards=0,joint_halfpot_assessed=0,nonpolarized_candidates=0,
                scope='GTO original boundaries and exported GTO-only river nodes; no NL2 common-reach evidence; missing exports are not zero reach.',
                actual_model_opportunity_coverage_pct=pri['current_certified_opportunity_share_pct'])
    (out/'report.json').write_bytes(json_bytes(result));(out/'rendered-routes.json').write_bytes(route_raw)
    print(json.dumps(dict(flops=len(rows),boundary_status=Counter(x['status'] for f in rows for x in f['rows']),
         exact_river_status=Counter(y['status'] for f in rows for x in f['rows'] for y in x.get('exact_gto_river_nodes',[])),native_solves=0,cert_promotions=0)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
