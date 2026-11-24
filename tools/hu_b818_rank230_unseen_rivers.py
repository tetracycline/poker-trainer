"""B818: only unexported rivers with same physical two-seat check ancestry.
Reuses archived B799/B804/B810 roots and fixed conditional jobs; no flop solve."""
import argparse,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
import hu_b782_rank230_mid_pairs as base
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_sequential_cfr_reach import accepted,cardkey
native=base.native
MODES=('gto','exp_oop')
BATCHES=(801,805,811)
def read(b):return json.loads(b)
def git(*a):return subprocess.check_output(['git',*map(str,a)],text=True).strip()
def sources(route,raw_route):
    for b in BATCHES:
        ledger=read(Path(f'data/solver_evidence/partial/b{b}_rank230_original_observations.json').read_bytes())
        for ob in ledger['observations']:
            pin=ob if 'archive' in ob else ob['archives'][0]
            f=ob['flop'];path=Path('data/solver_evidence')/pin['archive']
            raw=path.read_bytes();assert sha(raw)==pin['sha256']
            with ZipFile(path) as z:
                for name,digest in ob['native_file_sha256'].items():
                    assert sha(z.read(name))==digest
                claim=read(z.read('proof.json'));assert claim==ob['proof'] and claim['flop']==f and claim['selected'] is None
                assert z.read('rendered-routes.json')==raw_route
                root=read(z.read('flop/result.json'));assert sha(z.read('flop/result.json'))==claim['root_sha256']
                assert (root['pot'],root['stack'],root['flop'])==(2100,9000,f)
                for turn in claim['turns']:
                    if set(turn['policies'])!=set(MODES) or turn['root_gate']['legal_river_count']<=len(turn['preregistered_rivers']):continue
                    t=turn['turn'];bound=native.parent(root,t);pub=bound['board']
                    jobs={};games={}
                    hero,foe=base.root_hands(root,t,route,bound)
                    live=[set(hero),set(foe)]
                    for mode in MODES:
                        prev=turn['policies'][mode];prefix=t+'-'+mode+'/'
                        jb=z.read(prefix+'job.json');rb=z.read(prefix+'result.json')
                        assert (sha(jb),sha(rb))==(prev['job_sha256'],prev['source_sha256'])
                        jobs[mode]=read(jb);g=games[mode]=read(rb)
                        assert (g['pot'],g['stack'],g['flop'])==(2100,9000,f)
                        nodes={n['line']:n for n in g['nodes'] if len(n['board'])==8}
                        for seat,(line,field) in enumerate((('x x/','oop_w'),('x x/x','ip_w'))):
                            assert nodes[line]['player']==seat and nodes[line]['board']==pub
                            live[seat]&={cardkey(h) for h,w in jobs[mode][field] if w>1e-4}&accepted(nodes[line],g['hands'],'x')
                    gate={}
                    for r in native.DECK:
                        if r in native.public_cards(pub) or r in turn['preregistered_rivers']:continue
                        pairs=[(''.join(h),''.join(v)) for h in sorted(live[0]) if r not in h and route['river'].get(native.hand_cell(''.join(h),pub+r)[0])=='過'
                               for v in sorted(live[1]) if r not in v and set(h).isdisjoint(v)]
                        if pairs:gate[r]=pairs
                    report=dict(batch=b,flop=f,turn=t,archive=path.name,archive_sha256=pin['sha256'],source_jobs={m:turn['policies'][m]['job_sha256'] for m in MODES},
                                old_rivers=turn['preregistered_rivers'],common_turn_hands=[len(x) for x in live],
                                missing_river_pair_counts={r:len(v) for r,v in gate.items()},example_pairs={r:v[0] for r,v in gate.items()})
                    yield report,root,jobs,games,gate,hero,foe
def run(a):
    assert sys.version_info[:2]==(3,11)
    raw_route=subprocess.check_output(['node',base.ROUTE]);route=read(raw_route)['230']
    assert route['model']==base.MODEL and route['flop']==route['turn']==route['river']=={'low:2':'過','mid_high:2':'過'}
    entries=list(sources(route,raw_route))
    assert len(entries)==7 and len({(x[0]['flop'],x[0]['turn']) for x in entries})==7
    a.output.mkdir(parents=True,exist_ok=True)
    plans=[x[0] for x in entries]
    plan=dict(rank=230,original_flop_solves=0,checked_turns=plans,eligible_turns=sum(bool(x[4]) for x in entries))
    (a.output/'preflight.json').write_bytes(json_bytes(plan));print(json.dumps(plan))
    if not a.driver:return
    solver=a.solver.resolve();py=solver/'postflop/py'
    assert git('-C',solver,'rev-parse','HEAD')==native.SOLVER and git('-C',solver/'postflop/postflop-solver','rev-parse','HEAD')==native.RUST
    assert (sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(native.PIPELINE,native.RANGES)
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==native.POOL
    pool=read(pool_raw)['NL2'];sys.path.insert(0,str(py));import pipeline
    for report,root,jobs,games,gate,hero,foe in entries:
        if not gate:continue
        f,t=report['flop'],report['turn'];folder=a.output/(f+'-'+t);folder.mkdir()
        lock,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='SB3_BTN')),job=jobs['gto']),'exp_oop',pool,pipeline)
        lock['out']='result.json';assert compact(lock)==compact(jobs['exp_oop'])
        prior=None;results={};live_pairs={}
        for mode in MODES:
            old=games[mode];job=jobs[mode]
            extra=[dict(prefix=['x','x',r],street=True) for r in gate]
            assert not any(x['prefix']==y['prefix'] for x in extra for y in job['extract'])
            target=dict(job,extract=job['extract']+extra)
            loc=folder/mode;new=native.solve(loc,target,a.driver)
            assert (loc/'job.json').read_bytes()==compact(target)
            assert set(old)==set(new)
            for k in old:
                if k not in ('nodes','info'):assert old[k]==new[k],k
            assert {k:v for k,v in old['info'].items() if k!='secs'}=={k:v for k,v in new['info'].items() if k!='secs'}
            length=len(old['nodes']);assert compact(new['nodes'][:length])==compact(old['nodes'])
            added=new['nodes'][length:];assert added and {n['board'][8:] for n in added}==set(gate)
            assert all(len(n['board'])==10 for n in added)
            filtered=dict(new,nodes=[n for n in old['nodes'] if len(n['board'])==8]+added)
            rows,pairs=base.decisions(root,filtered,t,list(gate),route,hero,foe,prior)
            if mode=='gto':prior=pairs
            scope=None
            if mode=='exp_oop':
                scope=native.audit_patterns(new,target,dict(spot='SB3_BTN',locks=rules),pool,0)
                assert any(v>0 for k,v in scope['driver_tree_nodes'].items() if k in scope['marginal_targets'])
            for node in added:
                if node['line']!=native.LINE or node['player']!=0:continue
                board=node['board'];r=board[8:]
                seats=[{''.join(cardkey(h)) for h,w in zip(new['hands'][i],node['w'][i],strict=True) if w>1e-4} for i in range(2)]
                current={tuple(x) for x in gate[r] if x[0] in seats[0] and x[1] in seats[1]}
                live_pairs[board]=current if mode=='gto' else live_pairs[board]&current
            results[mode]=dict(rows=rows,source_sha256=sha((loc/'result.json').read_bytes()),job_sha256=sha((loc/'job.json').read_bytes()),old_equal_nodes=length,lock_scope=scope,
                               displayed_pairs={b:sorted(p) for b,p in pairs.items() if p})
        common=results['exp_oop']['displayed_pairs']
        half=[b for b,p in live_pairs.items() if p and all(results[m]['rows'][b]['reach']['b50'] is not None and results[m]['rows'][b]['reach']['strict_legal_combos']>0 for m in MODES)]
        report.update(policies=results,common=common,locked_public_boards=len(results['exp_oop']['rows']),joint_halfpot_assessed=len(half),
                      halfpot_candidates=sum(all(results[m]['rows'][b]['reach']['b50']['candidate'] for m in MODES) for b in half),
                      positive_distinct_flops=int(bool(common)),joint_river_pair_counts={b:len(v) for b,v in live_pairs.items()})
        (folder/'proof.json').write_bytes(json_bytes(report))
        print(json.dumps({k:report[k] for k in ('flop','turn','locked_public_boards','joint_halfpot_assessed','halfpot_candidates','positive_distinct_flops')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--solver',type=Path);p.add_argument('--driver',type=Path)
    run(p.parse_args())
