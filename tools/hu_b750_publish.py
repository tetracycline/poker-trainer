"""Replay six UTG turn barrels, all original river decisions and their actual rendered hands."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b749_rank109 as native
import hu_b750_collect as receipt
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b710_publish import unpack_original
from hu_sequential_cfr_reach import accepted,cardkey,game_reach


def read(p):return json.loads(p.read_bytes())


def verify_policy(root,sub,turn,route,reported):
    """Require the same UTG cards at every street and an actual card-disjoint CO caller."""
    nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    utg,co=(nodes[s] for s in ('','x'))
    assert (utg['player'],co['player'],utg['pot'],co['pot'],utg['bets'],co['bets'])==(0,1,650,650,[0,0],[0,0])
    checked=[accepted(utg,root['hands'],'x'),accepted(co,root['hands'],'x')]
    ns={n['line']:n for n in sub['nodes'] if len(n['board'])==8}
    opening,facing=ns['x x/'],ns['x x/b75']
    assert (opening['player'],opening['pot'],opening['bets'],facing['player'],facing['pot'],facing['bets'])==(0,650,[0,0],1,1138,[488,0])
    turn_hands=[accepted(opening,sub['hands'],'b75'),accepted(facing,sub['hands'],'c')]
    sub.update(line0='x x',turn=turn,rivers=[b[-2:] for b in reported])
    masks=game_reach(root,sub)[0]
    out={}
    for n in (v for v in sub['nodes'] if v['line']==native.LINE):
        public=n['board'];dead=native.public_cards(public)
        assert len(dead)==5 and public[6:8]==turn and (n['player'],n['pot'],n['bets'])==(0,1626,[488,488])
        row=native.proof(root,sub,n,masks)
        assert row==reported[public]['reach']
        live=[{cardkey(h) for h,w in zip(sub['hands'][i],n['w'][i],strict=True) if w>1e-4 and dead.isdisjoint(cardkey(h))} for i in (0,1)]
        hhs=live[0]&checked[0]&turn_hands[0]&accepted(n,sub['hands'],'b75')
        opp=live[1]&checked[1]&turn_hands[1]
        actual={}
        bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        hotel={cardkey(h):(i,b) for i,(h,b) in enumerate(zip(sub['hands'][0],bits,strict=True))}
        for h in sorted(hhs):
            cells=[native.hand_cell(''.join(h),public[:end]) for end in (6,8,10)]
            if not (cells[0][0] in route['flop'] and cells[1][0] in route['turn'] and route['river'].get(cells[2][0])=='下注 ¾'):continue
            witness=next((v for v in sorted(opp) if set(h).isdisjoint(v)),None)
            if not witness:continue
            i,mask=hotel[h];actions=n['acts']
            assert mask & (1<<actions.index('b75'))
            weights=[max(0.,n['strat'][a*len(bits)+i]) for a in range(len(actions))];den=sum(weights);assert den>0
            actual[''.join(h)]=dict(classes=[c[1] for c in cells],compatible_co_hand=''.join(witness),displayed_suggestion='下注 ¾',
                policy=dict(action_order=actions,accepted_mask=mask,accepted_actions=[a for k,a in enumerate(actions) if mask&(1<<k)],
                            strategy={a:round(w/den,7) for a,w in zip(actions,weights,strict=True)}))
        assert sorted(actual)==reported[public]['displayed_b75_hands']
        out[public]=(row,actual)
    assert set(out)==set(reported)
    return out


def worker(flop,folder,archive,route,rawroute,pipeline,ranges,pool,solver):
    aid,digest=receipt.PINS[flop];assert sha(archive)==digest
    names=unpack_original(archive,folder);raw=(folder/'proof.json').read_bytes();report=json.loads(raw)
    assert (report['rank'],report['flop'],report['model_id'],report['actor'],report['line'])==(109,flop,native.MODEL,0,native.LINE)
    assert (folder/'rendered-routes.json').read_bytes()==rawroute and set(report['native_files'])==names-{'proof.json'}
    assert all(sha((folder/p).read_bytes())==h for p,h in report['native_files'].items())
    native.run(SimpleNamespace(flop=flop,solver=solver,output=folder,driver=None,preflight=False))
    assert (folder/'proof.json').read_bytes()==raw
    template=native.template_jobs();root,origin=native.original(flop,template,ranges)
    assert origin==report['original']
    old=read(Path('data/solver_evidence/reverified/rank110.json'));rootpin,=[p for p in old['pins'] if p['flop']==flop]
    assert rootpin['archive_sha256']==origin['archive_sha256'] and rootpin['source_run_id']==45178881476
    source_run=rootpin['source_run_id']
    assert report['selected'] is None and report['positive_distinct_flops']==0
    turns=[]
    expected_paths={'proof.json','rendered-routes.json'}
    for tr in report['turns']:
        turn=tr['turn'];boundary,stats,cards=native.gate(root,turn,route);assert stats==tr['gate']
        gj=native.turn_job(template,root,boundary,cards);gj.update(turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',
            extract=[dict(prefix=[],street=True)]+[dict(prefix=['b75','c',r],street=False) for r in cards])
        for i,k in enumerate(('oop_w','ip_w')):assert gj[k]==[[h,w] for h,w in zip(root['hands'][i],boundary['wr'][i],strict=True) if w>1e-4]
        ej,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='UTG_CO')),job=gj),'exp_oop',pool,pipeline);ej['out']='result.json'
        policies=[];rec=dict(turn=turn,boundary_sha256=sha(compact(boundary)),policies={},common={})
        for version,key,target in [('gto','gto',gj),('exp_oop','nl2',ej)]:
            if version=='exp_oop' and not tr['nl2']:continue
            part=folder/(turn+'-'+version)
            expected_paths|={part.name+'/'+s for s in ('job.json','result.json')}
            assert read(part/'job.json')==target
            game=read(part/'result.json');srcsha=sha((part/'result.json').read_bytes())
            obs=None
            if version=='exp_oop':
                obs=native.audit_patterns(game,target,dict(locks=rules),pool,0);assert obs==tr['measured_lock_application']
            pol=verify_policy(root,game,turn,route,tr[key]);policies.append(pol)
            rec['policies'][key]=dict(source_sha256=srcsha,job_sha256=sha((part/'job.json').read_bytes()),
                measured_lock=obs,boards={b:dict(reach=r,displayed_hands=h) for b,(r,h) in pol.items()})
        if len(policies)==2:
            for b,(r,h) in sorted(policies[0].items()):
                common=sorted(h.keys()&policies[1][b][1].keys())
                if common:rec['common'][b]=common
            assert rec['common']==tr['common']
        else:assert not any(h for r,h in policies[0].values()) and not tr['common']
        turns.append(rec)
    assert expected_paths==names and set(native.FLOPS[flop])=={t['turn'] for t in turns}
    locked=[b['reach'] for t in turns for b in t['policies'].get('nl2',{}).get('boards',{}).values()]
    assessed=[r for r in locked if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None]
    counters=dict(positive_distinct_flops=0,native_locked_public_boards=len(locked),
            joint_halfpot_assessed=len(assessed),nonpolarized_candidates=sum(r['b50']['candidate'] for r in assessed))
    assert not any(t['common'] for t in turns) and all(report[k]==v for k,v in counters.items())
    return dict(flop=flop,worker_id=receipt.JOBS[flop],artifact_id=aid,archive_sha256=digest,proof_sha256=sha(raw),original_flop=origin,
                selected=None,original_flop_source_run=source_run,turns=turns,**counters)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for p,s in receipt.FILES.items():assert subprocess.check_output(['git','hash-object',p],text=True).strip()==s
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pipeline.SPOTS.update(native.EXTRA_SPOTS);ranges.SPOTS.update(native.EXTRA_SPOTS)
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    routes=subprocess.check_output(['node',native.ROUTE,'619']);route=json.loads(routes)['109']
    reg=read(Path('data/nl2_hu_multiboard_status_current.json'));model=reg['records'][native.MODEL]
    assert (model['frequency_rank'],model['label'],model['assumed_model_node_spr'])==(109,'APPROX',5.7)
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][native.MODEL]
    assert (contract['seat'],contract['streets'])==(0,['x x','b75 c',''])
    stage=a.output.resolve();assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    evidence=stage/'solver_evidence';partial=evidence/'partial';partial.mkdir(parents=True)
    auth=receipt.validate(read(a.receipts));(stage/'nl2_hu_b750_source_receipts.json').write_bytes(json_bytes(auth))
    counts=[]
    with TemporaryDirectory(prefix='b750-replay-') as temp:
        for f,(aid,digest) in receipt.PINS.items():
            name='NL2_B749_R109_'+f.upper()+'.zip';p=a.archives/f'{aid}.zip';raw=(p if p.exists() else a.archives/name).read_bytes()
            assert sha(raw)==digest;(evidence/name).write_bytes(raw)
            result=worker(f,Path(temp)/f,raw,route,routes,pipeline,ranges,pool,solver)
            (partial/('b750_rank109_'+f.lower()+'.json')).write_bytes(json_bytes(result))
            counts.append({k:v for k,v in result.items() if k!='turns'})
    assert not any(w['positive_distinct_flops'] for w in counts)
    totals={k:sum(r[k] for r in counts) for k in ('native_locked_public_boards','joint_halfpot_assessed','nonpolarized_candidates')}
    summary=dict(rank=109,source_run=receipt.RUN,source_head=receipt.HEAD,workers=counts,new_original_flop_solves=0,
        original_roots_reused=3,native_turn_gto_jobs=6,distinct_positive_flops=0,cert_eligible_ranks=[],publisher_native_solves_repeated=0,**totals)
    assert totals==dict(native_locked_public_boards=32,joint_halfpot_assessed=15,nonpolarized_candidates=0)
    (stage/'nl2_hu_b750_summary.json').write_bytes(json_bytes(summary));print(json.dumps(dict(positive_flops=0,**totals)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--solver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--archives',type=Path,default=Path('data/solver_evidence'));p.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b750_source_receipts.json'))
    publish(p.parse_args())

