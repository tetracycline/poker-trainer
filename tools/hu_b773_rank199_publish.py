"""Publish rank 199 only after revalidating its two historical flops and a third independent physical deal."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b764_collect as receipt764
import hu_b764_rank199_partial as b764
import hu_b769_collect as receipt769
import hu_b769_rank199_partial as b769
import hu_b771_rank199_third_flop as worker
import hu_b773_collect as receipt
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b514_turn_stab import rates
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_board_reach_corrections import source_key,summarize
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import game_reach
from hu_trainer_route_gate import compatible
from verify_hu_multiboard_100bb import lock_scope

EV=Path('data/solver_evidence')
PRIOR=EV/'partial/b769_rank199.json'
PRIOR_BLOB='520c8e9e295524e60e29245b4f20374c6b5cd74c'
M=worker.MODEL
LINE=worker.LINE


def read(p):
    return json.loads(p.read_bytes())


def sha1(p):
    return subprocess.check_output(['git','hash-object',p],text=True).strip()


def medium_row(s,public,expected,decisions):
    root=s['root'];sub=s['subgame']
    n,=[n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,LINE,1)]
    assert len(public)==10 and (n['pot'],n['bets'],sub['pot'],sub['stack'])==(830,[165,165],500,9775)
    row=worker.source.base.proof(root,sub,n,game_reach(root,sub)[0])
    assert row==expected and row['strict_legal_combos']>0 and row['compatible_hole_card_pairs']>0
    version=s['version'];scope=lock_scope(sub,s['manifest']['locks'],version)
    assert version=='gto' or scope['observed_marginal_source_nodes']>0
    row.update(version=version,spot=s['manifest']['spot'],family=s['manifest']['pot_family'],flop=sub['flop'],turn=sub['turn'],
        source_run_id=s['run'],source_sha256=s['source_sha256'],archive_sha256=s['archive_sha256'],root_sha256=s['root_sha256'],
        gto_gap_pct=sub['info']['gto_expl_pct'],locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
        root_gto_stage_gap_pct=root['info']['gto_expl_pct'],root_locked_hero_gap_pct=root['info'].get('hero_gap_pct'),
        root_applied_rust_lock_nodes=sum(v['nodes'] for v in root['info'].get('lock_stats',{}).values()),
        subgame_applied_rust_lock_nodes=sum(v['nodes'] for v in sub['info'].get('lock_stats',{}).values()),
        lock_scope={k:v for k,v in scope.items() if k not in ('matching_examples','caveat')},rendered_decision_hands=decisions)
    summarize(row)
    return row


def attach_medium(target,sources,public,report,decisions):
    for mode,label in [('gto','gto_references'),('exp_ip','references')]:
        row=medium_row(sources[mode],public,report['policies'][mode]['boards'][public]['reach'],decisions)
        key=source_key(M,row);assert key not in target[label];target[label][key]=row


def historical(temp,routefile,solver,pipeline,pool,medium):
    assert sha1(PRIOR)==PRIOR_BLOB
    group=read(PRIOR)
    assert group['rank']==199 and group['model_id']==M and len(group['boards'])==len(group['pins'])==2
    receipt764.validate(read(Path('data/nl2_hu_b764_source_receipts.json')))
    receipt769.validate(read(Path('data/nl2_hu_b769_source_receipts.json')))
    assert group['boards'][0]==read(b769.OLD_GROUP)['boards'][0] and group['pins'][0]==read(b769.OLD_GROUP)['pins'][0]
    g_code='NL2_B762_R199_7H6D4S_8D.zip';raw=(EV/g_code).read_bytes()
    stat,common,pols,claim=b764.worker('8d',temp/'b764',raw,EV/'NL2_B755_R151_7H6D4S.zip',routefile,solver,pipeline,pool)
    b,p=group['boards'][0],group['pins'][0];public=b['public_board']
    assert (b['flop'],public)==('7h6d4s','4s6d7h8d2h') and len(common[public])==2
    assert list(common[public].values())==p['rendered_decision_hands'] and stat['archive_sha256']==p['archive_sha256']
    assert p['original_GTO_SHA256']==pols['gto']['source_sha256'] and p['actual_NL2_SHA256']==pols['exp_ip']['source_sha256']
    attach_medium(medium,pols,public,claim,p['rendered_decision_hands'])
    f,t='7h6h4c','Qc';aid,digest=receipt769.PINS[f+'-'+t]
    raw=(EV/'NL2_B767_R199_7H6H4C_QC.zip').read_bytes()
    row,claim,pols,common=b769.inspect(aid,digest,raw,temp/'b769',f,t,routefile,solver,pipeline,pool)
    b,p=group['boards'][1],group['pins'][1];public=b['public_board']
    assert (b['flop'],public)==(f,'4c6h7hQc3d') and len(common[public])==2
    assert common[public]==p['rendered_decision_hands'] and row['archive_sha256']==p['archive_sha256']
    assert p['original_GTO_SHA256']==pols['gto']['source_sha256'] and p['actual_NL2_SHA256']==pols['exp_ip']['source_sha256']
    attach_medium(medium,pols,public,claim,p['rendered_decision_hands'])
    for b,p in zip(group['boards'],group['pins'],strict=True):
        assert sha((EV/('NL2_MULTIBOARD_'+p['viewer_archive_code']+'.json.gz')).read_bytes())==p['viewer_sha256']
        assert sha((EV/('NL2_'+p['archive_code']+'.zip')).read_bytes())==p['archive_sha256']
        assert p['pool_observed_marginal_lock_nodes']>0 and len(b['nl2_locked_variants'])==1
    return group


def replay_new(folder,archive,routefile,solver,pipeline,pool):
    aid,digest=receipt.PINS[worker.FLOP];assert sha(archive)==digest
    names=unpack_original(archive,folder);raw=(folder/'proof.json').read_bytes();claim=json.loads(raw)
    assert (claim['rank'],claim['model_id'],claim['flop'],claim['actor'],claim['line'])==(199,M,worker.FLOP,1,LINE)
    assert (folder/'rendered-routes.json').read_bytes()==routefile.read_bytes()
    expected={'rendered-routes.json','flop/result.json','flop/job.json','proof.json'}
    expected|={t['turn']+'-'+m+'/'+n for t in claim['turns'] for m in t['policies'] for n in ('job.json','result.json')}
    assert names==expected
    worker.run(SimpleNamespace(solver=solver,output=folder,routes=routefile,driver=None,preflight=False))
    assert (folder/'proof.json').read_bytes()==raw
    route=read(routefile)['199']
    old,template,manifest,pin,rootjob,static=worker.original(route)
    root=read(folder/'flop/result.json');bounds=worker.source.base.compare_extraction(old,root,worker.TURNS)
    assert read(folder/'flop/job.json')==rootjob and claim['original']==pin and claim['original_nodes_unchanged']==len(old['nodes'])==15
    assert [t['turn'] for t in claim['turns']]==worker.TURNS[:len(claim['turns'])]
    records=[];selected=None;totals=dict(locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,positive_rivers=0)
    for t in claim['turns']:
        turn=t['turn'];parent=bounds[turn]
        assert sha(compact(parent))==t['original_parent_sha256']
        allow,_,gate=worker.source.base.routes(root,turn,route,parent)
        assert list(allow)==t['all_rivers'] and t['gate']==gate
        gj=worker.source.turn_job(root,parent,template,turn,allow)
        ej,rules=worker.source.base.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=gj),'exp_ip',pool,pipeline)
        ej['out']='result.json';assert ej['hero']==1
        policies={};deals={}
        for mode,record in t['policies'].items():
            d=folder/(turn+'-'+mode);sub=read(d/'result.json');job=read(d/'job.json')
            assert job==(gj if mode=='gto' else ej)
            assert (sha((d/'job.json').read_bytes()),sha((d/'result.json').read_bytes()))==(record['job_sha256'],record['source_sha256'])
            sub.update(line0='x b50 c',turn=turn,rivers=list(allow))
            deals[mode]=b764.policy(root,sub,turn,record,route,parent['wr'])
            assert all(set(heroes)==set(record['boards'][b]['displayed_hands']) for b,(heroes,bb) in deals[mode].items())
            s=dict(root=root,subgame=sub,version=mode,run=receipt.RUN,source_sha256=record['source_sha256'],root_sha256=sha(compact(root)),
                manifest=dict(manifest,locks=[]),archive_code='B771_R199_'+worker.FLOP.upper(),archive_sha256=digest)
            if mode=='exp_ip':
                applied=worker.source.base.audit_patterns(sub,job,dict(locks=rules),pool,hero_seat=1)
                assert applied==record['applied_lock']
                s['manifest'].update(locks=rules,gto_parent_source_run_id=receipt.RUN,gto_parent_source_sha256=s['root_sha256'])
                s.update(verified_gto_parent=dict(run=receipt.RUN,sha256=s['root_sha256']),measured_lock_application=applied,
                    applied_rust_rates=sub['info']['lock_stats'])
            policies[mode]=s
        common={}
        if 'exp_ip' in policies:
            for public,(g,gv) in deals['gto'].items():
                e,ev=deals['exp_ip'][public]
                for row in comparisons(g,e):
                    bb=next((o for o in sorted(gv&ev) if worker.source.base.cards(row['hand']).isdisjoint(o)),None)
                    if bb:common.setdefault(public,[]).append(dict(row,compatible_bb_hand=''.join(bb)))
        assert {b:{w['hand']:w['compatible_bb_hand'] for w in hs} for b,hs in common.items()}==t['common_physical_co_bb']
        locked=[v['reach'] for v in t['policies'].get('exp_ip',{}).get('boards',{}).values()]
        half=[v for v in locked if v['compatible_hole_card_pairs'] and v['strict_legal_combos'] and v['b50'] is not None and 'b50' in v['source_actions']]
        assert (len(locked),len(half),sum(bool(v['b50']['candidate']) for v in half))==(t['locked_public_boards'],t['joint_halfpot_assessed'],t['halfpot_candidates'])
        stat=dict(turn=turn,locked_public_boards=len(locked),joint_halfpot_assessed=len(half),halfpot_candidates=t['halfpot_candidates'],positive_rivers=len(common))
        records.append(dict(stats=stat,same_private_pairs=common,original_turn=t))
        for k in totals:totals[k]+=stat[k]
        if common:
            assert selected is None and turn==claim['turns'][-1]['turn']==claim['selected_turn']
            public=sorted(common)[0];selected=(public,common[public],policies,t)
    assert claim['positive_distinct_flops']==int(selected is not None)
    assert all(totals[k]==claim[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates'))
    return records,totals,selected,claim


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for f,blob in receipt.FILES.items():assert sha1(f)==blob
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    pool=read(solver/'inputs/pool_stats.json')['NL2']
    reg=Path('data/nl2_hu_multiboard_status_current.json');original=reg.read_bytes()
    model=json.loads(original)['records'][M]
    assert (model['label'],model['frequency_rank'],model['assumed_model_node_spr'])==('APPROX',199,11.53)
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][M]
    stage=a.output.resolve();assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    pairs.EVIDENCE=ev
    routefile=partial/'b773_rank199_routes.json';routefile.write_bytes(subprocess.check_output(['node',worker.ROUTE]))
    auth=receipt.validate(read(a.receipts));(stage/'nl2_hu_b773_source_receipts.json').write_bytes(json_bytes(auth))
    medium=dict(schema='NL2_HU_B773_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    with TemporaryDirectory(prefix='b773-native-') as tmp:
        temp=Path(tmp);group=historical(temp,routefile,solver,pipeline,pool,medium)
        frozen=deepcopy(group)
        aid,digest=receipt.PINS[worker.FLOP];name='NL2_B771_R199_'+worker.FLOP.upper()+'.zip'
        p=a.archives/(str(aid)+'.zip');archive=(p if p.exists() else a.archives/name).read_bytes()
        turns,totals,selected,claim=replay_new(temp/'b771',archive,routefile,solver,pipeline,pool)
        (ev/name).write_bytes(archive)
        if selected:
            public,decisions,sources,turn=selected;g,e=sources['gto'],sources['exp_ip']
            b,p=pairs.emit_board(model,g,e,public,LINE,texture(worker.FLOP),viewer_code='B773_R199_'+worker.FLOP.upper())
            assert compatible(contract,b) and (b['actual_pot_bb'],b['actual_effective_stack_bb'],b['acting_seat'])==(8.3,96.1,1)
            assert abs(b['actual_spr']-9610/830)<1e-6 and p['pool_observed_marginal_lock_nodes']>0
            b['nl2_locked_variants'][0].update(origin_solve_run_id=receipt.RUN,pool_sha256=worker.source.base.POOL,applied_street_rates=rates(e),
                gto_parent_source_run_id=receipt.RUN,gto_parent_source_sha256=e['root_sha256'])
            p.update(rendered_decision_hands=decisions,worker_artifact=aid,worker_sha256=digest,worker_head=receipt.HEAD,
                original_job_id=receipt.JOBS[worker.FLOP],original_boundary_sha256=turn['original_parent_sha256'],original_flop_sha256=claim['original']['root_sha256'])
            attach_medium(medium,sources,public,turn,decisions)
            group['boards'].append(b);group['pins'].append(p)
    count=len(group['boards']);cert=count==3
    assert count in (2,3) and len({worker.source.base.suit_isomorphism_class(b['flop']) for b in group['boards']})==count
    assert group['boards'][:2]==frozen['boards'] and group['pins'][:2]==frozen['pins']
    group_path=ev/'reverified/rank199.json' if cert else partial/'b773_rank199.json'
    medium_path=stage/'nl2_hu_b773_locked_medium.json' if cert else partial/'b773_selected_medium.json'
    group_path.parent.mkdir(parents=True,exist_ok=True);group_path.write_bytes(json_bytes(group));medium_path.write_bytes(json_bytes(medium))
    (partial/'b773_rank199_turns.json').write_bytes(json_bytes(dict(source_proof=claim,turns=turns)))
    b764summary=read(Path('data/nl2_hu_b764_summary.json'));b769summary=read(Path('data/nl2_hu_b769_summary.json'))
    prior_counts={k:b764summary[k]+b769summary[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}
    assert prior_counts==dict(locked_public_boards=24,joint_halfpot_assessed=24,halfpot_candidates=11)
    summary=dict(rank=199,model_id=M,source_head=receipt.HEAD,source_run=receipt.RUN,original_job_id=receipt.JOBS[worker.FLOP],
        original_15_nodes_confirmed=True,prior_positive_flops=2,positive_distinct_flops=count,selected_turn=claim['selected_turn'],
        cert_eligible_ranks=[199] if cert else [],historical_replayed_counts=prior_counts,publisher_native_solves_repeated=0,**totals)
    (stage/'nl2_hu_b773_summary.json').write_bytes(json_bytes(summary));assert reg.read_bytes()==original
    print(json.dumps(dict(positive_distinct_flops=count,selected_turn=claim['selected_turn'],**totals)))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--archives',type=Path,default=EV)
    cli.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b773_source_receipts.json'))
    cli.add_argument('--output',type=Path,required=True);cli.add_argument('--solver',type=Path,required=True)
    publish(cli.parse_args())
