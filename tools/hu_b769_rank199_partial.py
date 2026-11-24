"""Replay B767's three native turn workers and retain B764's proven CO/BB river deal."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b764_collect as prior_receipt
import hu_b764_rank199_partial as prior
import hu_b767_rank199_new_turns as native
import hu_b769_collect as receipt
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b514_turn_stab import rates
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible

EV=Path('data/solver_evidence')
OLD_GROUP=EV/'partial/b764_rank199.json'


def read(path):
    return json.loads(path.read_bytes())


def retained(temp,solver,routefile,pipeline,pool):
    assert subprocess.check_output(['git','hash-object',OLD_GROUP],text=True).strip()=='afb1feda557c56a72db93df903a863bc4e2b4e0d'
    p=Path('data/nl2_hu_b764_source_receipts.json')
    assert subprocess.check_output(['git','hash-object',p],text=True).strip()=='f7f63bf8c07b444060b8574c34864f1d96f93b3b'
    prior_receipt.validate(read(p))
    group=read(OLD_GROUP);b,=group['boards'];pin,=group['pins']
    assert (b['flop'],b['turn'],b['public_board'])==('7h6d4s','8d','4s6d7h8d2h')
    ar=(EV/'NL2_B762_R199_7H6D4S_8D.zip').read_bytes()
    item,common,sources,claim=prior.worker('8d',temp/'b764',ar,EV/'NL2_B755_R151_7H6D4S.zip',routefile,solver,pipeline,pool)
    board=b['public_board']
    assert item['positive_rivers']==3 and list(common[board].values())==pin['rendered_decision_hands']
    assert pin['viewer_sha256']==sha((EV/('NL2_MULTIBOARD_'+pin['viewer_archive_code']+'.json.gz')).read_bytes())
    assert b['source_run_id']==prior_receipt.RUN and b['source_sha256']==sources['gto']['source_sha256']
    assert len(pin['rendered_decision_hands'])==2 and all(w['compatible_bb_hand']=='4c9c' for w in pin['rendered_decision_hands'])
    return group


def inspect(aid,digest,archive,folder,flop,turn,routefile,solver,pipeline,pool):
    assert sha(archive)==digest
    names=unpack_original(archive,folder);raw=(folder/'proof.json').read_bytes();report=json.loads(raw)
    assert (report['flop'],report['turn'],report['rank'],report['model_id'],report['line'],report['actor'])==(flop,turn,199,native.MODEL,native.LINE,1)
    assert report['flop_recomputed'] is False and (folder/'rendered-routes.json').read_bytes()==routefile.read_bytes()
    assert names=={'proof.json','rendered-routes.json'}|{mode+'/'+f for mode in report['policies'] for f in ('job.json','result.json')}
    native.run(SimpleNamespace(solver=solver,output=folder,routes=routefile,driver=None,preflight=False,flop=flop,turn=turn))
    assert (folder/'proof.json').read_bytes()==raw
    route=read(routefile)['199']
    root,parent,template,m,eligible,pin=native.original(flop,turn,route)
    assert pin==report['original']
    gj=native.turn_job(root,parent,template,turn,eligible)
    ej,rules=native.base.prepare_job(dict(source=dict(root=root,version='gto',manifest=m),job=gj),'exp_ip',pool,pipeline)
    ej['out']='result.json'
    code='B767_R199_'+flop.upper()+'_'+turn.upper()
    modes={};sources={}
    for mode,record in report['policies'].items():
        target=gj if mode=='gto' else ej
        assert read(folder/mode/'job.json')==target
        game=read(folder/mode/'result.json')
        assert (record['job_sha256'],record['source_sha256'])==(sha((folder/mode/'job.json').read_bytes()),sha((folder/mode/'result.json').read_bytes()))
        game.update(line0='x b50 c',turn=turn,rivers=list(eligible))
        modes[mode]=prior.policy(root,game,turn,record,route,parent['wr'])
        assert all(set(h)==set(record['boards'][board]['displayed_hands']) for board,(h,bb) in modes[mode].items())
        s=dict(version=mode,run=receipt.RUN,source_sha256=record['source_sha256'],root=root,subgame=game,
            root_sha256=sha(compact(root)),archive_code=code,archive_sha256=digest,manifest=dict(m,locks=[]))
        if mode=='exp_ip':
            applied=native.base.audit_patterns(game,target,dict(locks=rules),pool,hero_seat=1)
            assert applied==record['applied_lock']
            s['manifest'].update(locks=rules,gto_parent_source_run_id=native.gates.RUN,gto_parent_source_sha256=s['root_sha256'])
            s.update(verified_gto_parent=dict(run=native.gates.RUN,sha256=s['root_sha256']),measured_lock_application=applied,applied_rust_rates=game['info']['lock_stats'])
        sources[mode]=s
    common={}
    if 'exp_ip' in modes:
        for board,(g,gv) in modes['gto'].items():
            e,ev=modes['exp_ip'][board]
            for row in comparisons(g,e):
                bb=next((o for o in sorted(gv&ev) if native.base.cards(row['hand']).isdisjoint(o)),None)
                if bb:common.setdefault(board,[]).append(dict(row,compatible_bb_hand=''.join(bb)))
    assert {b:{w['hand']:w['compatible_bb_hand'] for w in hs} for b,hs in common.items()}==report['common_physical_co_bb']
    locked=[v['reach'] for v in report['policies'].get('exp_ip',{}).get('boards',{}).values()]
    half=[v for v in locked if v['compatible_hole_card_pairs'] and v['strict_legal_combos'] and 'b50' in v['source_actions'] and v['b50'] is not None]
    assert (len(locked),len(half),sum(bool(v['b50']['candidate']) for v in half))==(report['locked_public_boards'],report['joint_halfpot_assessed'],report['halfpot_candidates'])
    row=dict(flop=flop,turn=turn,worker_job=receipt.JOBS[flop+'-'+turn],artifact_id=aid,archive_sha256=digest,
        original_root_sha256=pin['root_raw_sha256'],original_boundary_sha256=pin['boundary_sha256'],
        gto_public_rivers=len(eligible),locked_public_boards=len(locked),joint_halfpot_assessed=len(half),
        halfpot_candidates=report['halfpot_candidates'],positive_rivers=len(common))
    return row,report,sources,common


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,digest in receipt.FILES.items():
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==digest
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    pool=read(solver/'inputs/pool_stats.json')['NL2']
    reg=Path('data/nl2_hu_multiboard_status_current.json');raw_registry=reg.read_bytes()
    model=json.loads(raw_registry)['records'][native.MODEL]
    assert (model['label'],model['frequency_rank'],model['assumed_model_node_spr'])==('APPROX',199,11.53)
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][native.MODEL]
    stage=a.output.resolve();assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    pairs.EVIDENCE=ev
    routefile=partial/'b769_rank199_routes.json';routefile.write_bytes(subprocess.check_output(['node',native.ROUTE]))
    auth=receipt.validate(read(a.receipts));(stage/'nl2_hu_b769_source_receipts.json').write_bytes(json_bytes(auth))
    workers=[];details={}
    with TemporaryDirectory(prefix='b769-native-') as tmp:
        temp=Path(tmp);group=retained(temp,solver,routefile,pipeline,pool)
        proven={group['boards'][0]['flop']}
        for flop,turn in native.CASES:
            case=flop+'-'+turn
            aid,digest=receipt.PINS[case]
            name='NL2_B767_R199_'+flop.upper()+'_'+turn.upper()+'.zip'
            path=a.archives/(str(aid)+'.zip');archive=(path if path.exists() else a.archives/name).read_bytes()
            row,report,sources,common=inspect(aid,digest,archive,temp/case,flop,turn,routefile,solver,pipeline,pool)
            workers.append(row);details[case]=dict(original_report=report,same_private_pairs=common);(ev/name).write_bytes(archive)
            if common and flop not in proven:
                public=sorted(common)[0];g,e=sources['gto'],sources['exp_ip']
                b,p=pairs.emit_board(model,g,e,public,native.LINE,texture(flop),viewer_code='B769_R199_'+flop.upper())
                assert compatible(contract,b) and (b['actual_pot_bb'],b['actual_effective_stack_bb'],b['acting_seat'])==(8.3,96.1,1)
                assert abs(b['actual_spr']-9610/830)<1e-6 and p['pool_observed_marginal_lock_nodes']>0
                b['nl2_locked_variants'][0].update(origin_solve_run_id=receipt.RUN,pool_sha256=native.base.POOL,applied_street_rates=rates(e),
                    gto_parent_source_run_id=native.gates.RUN,gto_parent_source_sha256=e['root_sha256'])
                p.update(rendered_decision_hands=common[public],worker_artifact=aid,worker_sha256=digest,worker_head=receipt.HEAD,
                         original_job_id=row['worker_job'],original_boundary_sha256=row['original_boundary_sha256'])
                group['boards'].append(b);group['pins'].append(p);proven.add(flop)
    assert len(proven)==len(group['boards'])==len({native.base.suit_isomorphism_class(f) for f in proven})<3
    (partial/'b769_rank199.json').write_bytes(json_bytes(group));(partial/'b769_rank199_turns.json').write_bytes(json_bytes(details))
    total={k:sum(r[k] for r in workers) for k in ('gto_public_rivers','locked_public_boards','joint_halfpot_assessed','halfpot_candidates','positive_rivers')}
    summary=dict(rank=199,model_id=native.MODEL,source_run=receipt.RUN,source_head=receipt.HEAD,retained_run=prior_receipt.RUN,
                 workers=workers,prior_positive_flops=1,new_positive_distinct_flops=len(proven)-1,total_positive_distinct_flops=len(proven),
                 cert_eligible_ranks=[],original_flops_recomputed=0,publisher_native_solves_repeated=0,**total)
    assert total['gto_public_rivers']==47
    (stage/'nl2_hu_b769_summary.json').write_bytes(json_bytes(summary));assert reg.read_bytes()==raw_registry
    print(json.dumps(dict(total_positive_distinct_flops=len(proven),**total)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archives',type=Path,default=EV)
    p.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b769_source_receipts.json'))
    p.add_argument('--solver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    publish(p.parse_args())
