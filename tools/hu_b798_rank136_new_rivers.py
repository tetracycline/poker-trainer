"""Extract only previously unseen rank136 river decisions from the fixed B792 turn games."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b792_rank136_chance_turns as original
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b637_rank57 import solve
from hu_sequential_cfr_reach import accepted,cardkey

RUN=45351501007
HEAD='693a5d7cf92ba22c5f4e8da4f6ee29312c5779d3'
ARCHIVES={
    'Ac8h5d':(14900322317,'82dae00ffed0eb673730383819d91d28b5e16a8156d9a976c0b3c0ba58fdb21b'),
    'Ah8d4s':(14900951010,'63778af66077e76bbd6f9d90a98d49becf116c3d6a663363071d498f68f95d28'),
}
RIVERS={
    ('Ac8h5d','Js'):'4c 4d 4h 4s Tc Td Th Ts',
    ('Ac8h5d','2h'):'4d 4s',
    ('Ah8d4s','Qc'):'Jc Jd Jh Js Kc Kd Kh Ks',
    ('Ah8d4s','Jc'):'Qc Qd Qh Qs Kc Kd Kh Ks',
}
BASE_BLOB='488b12838334851343f01255b5f0448804073d2a'


def read_archive(raw,flop,t):
    with ZipFile(BytesIO(raw)) as z:
        read=lambda name:json.loads(z.read(name))
        claim=read('proof.json')
        assert claim['flop']==flop and claim['selected'] is None and claim['actor']==1 and claim['line']==original.LINE
        previous,=(v for v in claim['turns'] if v['turn']==t);assert set(previous['policies'])=={'gto','exp_ip'}
        assert not previous['common'] and not previous['policies']['exp_ip']['common_deal_candidates']
        assert sha(z.read('original-b652.zip'))==claim['origin']['artifact_sha256']
        with ZipFile(BytesIO(z.read('original-b652.zip'))) as parent,ZipFile(BytesIO(parent.read('source.zip'))) as source:
            root=source.read('root.json');assert sha(root)==claim['origin']['original_root_sha256']
        jobs={};games={}
        for mode,entry in previous['policies'].items():
            folder=t+'-'+mode+'/'
            job=z.read(folder+'job.json');result=z.read(folder+'result.json')
            assert (sha(job),sha(result))==(entry['job_sha256'],entry['source_sha256'])
            jobs[mode]=json.loads(job);games[mode]=json.loads(result)
            assert jobs[mode]['extract']==[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in previous['river_gate']]
        return json.loads(root),jobs,games,claim,previous,z.read('rendered-routes.json')


def preflight(root,jobs,games,previous,flop,t,route):
    upper=flop+t
    raw={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    live=[accepted(raw[''],root['hands'],'x')&accepted(raw['x b75'],root['hands'],'c'),
          accepted(raw['x'],root['hands'],'b75')]
    for mode,game in games.items():
        turn={n['line']:n for n in game['nodes'] if len(n['board'])==8}
        for i,(line,field) in enumerate(((original.CHILD,'oop_w'),(original.CHILD+'x','ip_w'))):
            assert turn[line]['player']==i
            weighted={cardkey(h) for h,w in jobs[mode][field] if w>1e-4}
            live[i]&=weighted&accepted(turn[line],game['hands'],'x')
    bb,btn=live
    btn={h for h in btn if all(original.hand_cell(''.join(h),upper[:end])[0] in route[street] for end,street in ((6,'flop'),(8,'turn')))}
    gate={}
    for r in original.DECK:
        if r in original.public_cards(upper) or r in previous['river_gate']:continue
        hands=sorted(''.join(h) for h in btn if r not in h and route['river'].get(original.hand_cell(''.join(h),upper+r)[0])=='過'
                     and any(r not in v and set(h).isdisjoint(v) for v in bb))
        if hands:gate[r]=hands
    assert list(gate)==RIVERS[flop,t].split() and gate
    return bb,gate


def added_job(old,rivers):
    extra=[dict(prefix=['x','x',r]+end,street=False) for r in rivers for end in ([],['x'])]
    assert not any(a['prefix']==b['prefix'] for a in extra for b in old['extract'])
    return dict(old,extract=old['extract']+extra)


def verify_extension(old,new,rivers):
    for key in ('flop','pot','stack','hands'):assert old[key]==new[key]
    assert set(old)==set(new) and set(old['info'])==set(new['info'])
    assert {k:v for k,v in old['info'].items() if k!='secs'}=={k:v for k,v in new['info'].items() if k!='secs'}
    length=len(old['nodes']);assert len(new['nodes'])==length+2*len(rivers)
    assert compact(new['nodes'][:length])==compact(old['nodes'])
    head=[n for n in new['nodes'] if len(n['board'])==8]
    extra=new['nodes'][length:]
    for i,r in enumerate(rivers):
        oop,ip=extra[2*i:2*i+2]
        assert (oop['line'],oop['player'],ip['line'],ip['player'])==('x b75 c/x x/',0,original.LINE,1)
        assert oop['board']==ip['board'] and ip['board'][8:]==r and ip['pot']==oop['pot']==1376
    return dict(new,nodes=head+extra)


def run(a):
    assert sys.version_info[:2]==(3,11);solver=a.solver.resolve();native=solver/'postflop/py'
    git=lambda *v:subprocess.check_output(['git',*v],text=True).strip()
    assert git('-C',str(solver),'rev-parse','HEAD')==original.SOLVER
    assert git('hash-object','tools/hu_b792_rank136_chance_turns.py')==BASE_BLOB
    assert git('hash-object',str(solver/'postflop/pfdriver/src/main.rs'))==original.DRIVER_SOURCE
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and git('-C',str(solver/'postflop/postflop-solver'),'rev-parse','HEAD')==original.RUST
    assert (sha((native/'pipeline.py').read_bytes()),sha((native/'ranges.py').read_bytes()))==(original.PIPELINE,original.RANGES)
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==original.POOL
    sys.path.insert(0,str(native));import pipeline
    pool=json.loads(poolraw)['NL2'];f,t=a.flop,a.turn
    aid,digest=ARCHIVES[f];raw=a.archive.read_bytes();assert sha(raw)==digest
    root,jobs,games,claim,previous,route_raw=read_archive(raw,f,t)
    assert subprocess.check_output(['node',original.ROUTE])==route_raw
    route=json.loads(route_raw)['136']
    assert (route['id'],route['turn'],route['river'])==(original.MODEL,['A_high:4'],{'A_high:4':'過'})
    bb,gate=preflight(root,jobs,games,previous,f,t,route)
    assert all((g['pot'],g['stack'],g['flop'])==(1376,9337,f) for g in games.values())
    gto=jobs['gto'];locked,rules=original.prepare_job(dict(source=dict(root=root,version='gto',manifest=dict(spot='BTN_BB')),job=gto),'exp_ip',pool,pipeline)
    locked['out']='result.json';assert compact(locked)==compact(jobs['exp_ip'])
    if a.preflight:
        print(json.dumps(dict(flop=f,turn=t,previous_nodes={m:len(v['nodes']) for m,v in games.items()},frozen_turn_check_bb=len(bb),new_gate=gate)));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').exists()
    out.mkdir(parents=True,exist_ok=True)
    if a.driver:(out/'original-b792.zip').write_bytes(raw)
    else:assert (out/'original-b792.zip').read_bytes()==raw
    result=dict(rank=136,model_id=original.MODEL,flop=f,turn=t,actor=1,line=original.LINE,old_run=RUN,old_head=HEAD,
        old_artifact=aid,old_archive_sha256=digest,origin=claim['origin'],old_extractions=list(previous['river_gate']),new_gate=gate,
        exact_same_preceding_bb_checks=len(bb),original_flop_native_solves_repeated=0,engine_reconstruction='ORIGINAL_TURN_INPUTS_WITH_ONLY_NEW_RIVER_EXTRACTS',
        route_sha256=sha(route_raw),pool_sha256=original.POOL,policies={},common={},locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0)
    matched={}
    for mode in ('gto','exp_ip'):
        target=added_job(jobs[mode],gate)
        loc=out/mode;full=solve(loc,target,a.driver);filtered=verify_extension(games[mode],full,gate)
        applied=None
        if mode=='exp_ip':
            applied=original.audit_patterns(full,target,dict(locks=rules),pool,1)
            assert any(v>0 for k,v in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
        rows,found=original.observe(root,filtered,t,gate,bb)
        matched[mode]=found
        result['policies'][mode]=dict(
            original_job_sha256=previous['policies'][mode]['job_sha256'],original_result_sha256=previous['policies'][mode]['source_sha256'],
            job_sha256=sha((loc/'job.json').read_bytes()),source_sha256=sha((loc/'result.json').read_bytes()),
            original_equal_nodes=len(games[mode]['nodes']),original_nodes_sha256=sha(compact(games[mode]['nodes'])),
            applied_lock=applied,boards=rows,displayed_two_seat_deals=found)
        if mode=='gto' and not found:break
        if mode=='exp_ip':
            half=[r for r in rows.values() if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and 'b50' in r['source_actions'] and r['b50'] is not None]
            result.update(locked_public_boards=len(rows),joint_halfpot_assessed=len(half),halfpot_candidates=sum(r['b50']['candidate'] for r in half))
    for public,btn in matched['gto'].items():
        locked=matched.get('exp_ip',{}).get(public,{})
        common={h:sorted(set(v)&set(locked.get(h,[]))) for h,v in btn.items() if set(v)&set(locked.get(h,[]))}
        if common:result['common'][public]=common
    result['positive_distinct_flops']=int(bool(result['common']))
    (out/'proof.json').write_bytes(json_bytes(result))
    print(json.dumps({k:result[k] for k in ('flop','turn','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('archive','solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=ARCHIVES,required=True);p.add_argument('--turn',required=True)
    p.add_argument('--preflight',action='store_true');p.add_argument('--driver',type=Path);run(p.parse_args())
