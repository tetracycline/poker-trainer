"""Replay original B677 workers and stage rank264 exact-board evidence."""
import argparse
import base64
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b677_rank264_checks as native
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL,proof
from hu_b514_turn_stab import rates
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import cardkey,game_reach
from verify_hu_multiboard_100bb import lock_scope


def views(source,node,row,route):
    masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    actions=node['acts'];hands=source['subgame']['hands'][0]
    assert len(masks)==len(hands)
    result={}
    for index,(hole,bits)in enumerate(zip(hands,masks,strict=True)):
        if not bits&(1<<actions.index('x')):continue
        hand=''.join(cardkey(hole));cells=[hand_cell(hand,node['board'][:n])for n in (6,8,10)]
        if any(cell[0]not in route[street]for cell,street in zip(cells,('flop','turn','river'),strict=True)):continue
        weights=[max(0.,node['strat'][k*len(hands)+index])for k in range(len(actions))]
        total=sum(weights);assert total>0
        result[hand]=dict(flop_class=cells[0][1],turn_class=cells[1][1],river_class=cells[2][1],displayed_suggestion='過',
            policy=dict(action_order=actions,accepted_mask=bits,accepted_actions=[action for k,action in enumerate(actions)if bits&(1<<k)],
                strategy={action:round(value/total,7)for action,value in zip(actions,weights,strict=True)}))
    return result


def publish(args):
    solver=args.solver.resolve()
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][native.MODEL]
    route=json.loads(subprocess.check_output(['node','tools/hu_b677_rank264_routes.cjs']))
    inputs=json.loads((args.receipts/'workers.json').read_bytes())
    assert len(inputs)==3 and {p['flop']for p in inputs}==set(native.CASES)
    assert len({suit_isomorphism_class(p['flop'])for p in inputs})==3
    data=args.output/'data';evidence=data/'solver_evidence';evidence.mkdir(parents=True,exist_ok=True)
    pairs.EVIDENCE=evidence
    group=dict(rank=264,model_id=native.MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B680_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    reports=[]
    template_raw=(native.EVIDENCE/native.STUDY.template).read_bytes();assert sha(template_raw)==native.STUDY.template_sha
    template=native.original_template(template_raw)
    manifest=dict(template['manifest'],spot='BB3_BTN',pot_family='3BP',locks=[])
    for pin in inputs:
        assert (pin['run'],pin['head'])==(args.run,args.head)
        receipt=json.loads((args.receipts/f'{pin["id"]}.json').read_bytes())
        job=json.loads((args.receipts/f'job-{pin["job_id"]}.json').read_bytes())
        assert (job['id'],job['run_id'],job['head_sha'],job['name'],job['status'],job['conclusion'])==(
            pin['job_id'],args.run,args.head,'solve ('+pin['flop']+')','completed','success')
        identity=receipt['workflow_run']
        assert (receipt['id'],receipt['name'],identity['id'],identity['head_sha'],identity['repository_id'])==(
            pin['id'],'B677-R264-'+pin['flop'],args.run,args.head,1438346845)
        raw=(args.receipts/f'{pin["id"]}.zip').read_bytes()
        assert receipt['digest']=='sha256:'+pin['sha256'] and sha(raw)==pin['sha256']
        with ZipFile(io.BytesIO(raw))as archive,tempfile.TemporaryDirectory()as tmp:
            output=Path(tmp);report=json.loads(archive.read('proof.json'))
            expected={'proof.json','flop/job.json','flop/result.json'}
            for turn in report['turns']:
                if turn['legal_rivers']:expected.update(turn['turn']+'-gto/'+name for name in ('job.json','result.json'))
                if turn['paired_policies']:expected.update(turn['turn']+'-exp_oop/'+name for name in ('job.json','result.json'))
            assert set(archive.namelist())==expected and len(archive.namelist())==len(expected)
            for name in expected:
                path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(name))
            native.run(SimpleNamespace(solver=solver,flop=pin['flop'],output=output,driver=None))
            assert json.loads((output/'proof.json').read_bytes())==report
            choices=[(t['turn'],c)for t in report['turns']for c in t['checks']]
            if not choices:
                reports.append(dict(flop=pin['flop'],worker_artifact=pin['id'],shared_hands=0,reason='NO_SHARED_RENDERED_CHECK'))
                continue
            turn,selected=choices[0];public=selected['board']
            code='B677_R264_'+pin['flop'].upper()
            (evidence/('NL2_'+code+'.zip')).write_bytes(raw)
            root=json.loads((output/'flop/result.json').read_bytes());root_sha=sha(compact(root))
            original_job=json.loads((output/(turn+'-gto/job.json')).read_bytes())
            import pipeline
            lock_job,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=manifest),job=original_job),'exp_oop',pool,pipeline)
            lock_job['out']='result.json'
            assert json.loads((output/(turn+'-exp_oop/job.json')).read_bytes())==json.loads(compact(lock_job))
            sources,rows,displayed={},{},{}
            for version,key in (('gto','gto_references'),('exp_oop','references')):
                native_raw=(output/(turn+'-'+version)/'result.json').read_bytes();sub=json.loads(native_raw)
                sub.update(line0='x x',turn=turn,rivers=[entry['prefix'][-1]for entry in original_job['extract'][1:]])
                source=dict(root=root,subgame=sub,version=version,run=args.run,archive_code=code,archive_sha256=pin['sha256'],
                    root_sha256=root_sha,source_sha256=sha(native_raw),manifest=dict(manifest))
                if version!='gto':
                    source['manifest'].update(locks=rules,gto_parent_source_run_id=args.run,gto_parent_source_sha256=root_sha)
                    source.update(verified_gto_parent=dict(run=args.run,sha256=root_sha),applied_rust_rates=sub['info']['lock_stats'],
                        measured_lock_application=audit_patterns(sub,lock_job,source['manifest'],pool,0))
                node,=[n for n in sub['nodes']if (n['board'],n['line'],n['player'])==(public,native.LINE,0)]
                row=proof(root,sub,node,game_reach(root,sub)[0])
                row.update(version=version,spot='BB3_BTN',family='3BP',flop=pin['flop'],turn=turn,source_run_id=args.run,
                    archive_sha256=pin['sha256'],root_sha256=root_sha,source_sha256=sha(native_raw),gto_gap_pct=sub['info']['gto_expl_pct'],
                    locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),lock_scope=lock_scope(sub,source['manifest']['locks'],version),
                    root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(s['nodes']for s in sub['info'].get('lock_stats',{}).values()))
                assert row['b50']==selected['gto_b50'if version=='gto'else'locked_b50']
                medium[key][source_key(native.MODEL,row)]=row
                sources[version]=source;rows[version]=row;displayed[version]=views(source,node,row,route)
            common=sorted(displayed['gto'].keys()&displayed['exp_oop'].keys());assert common==selected['hands'] and common
            board,proof_pin=pairs.emit_board(model,sources['gto'],sources['exp_oop'],public,native.LINE,texture(pin['flop']),viewer_code=code)
            assert board is not None
            comparisons=[]
            for hand in common:
                g,e=displayed['gto'][hand],displayed['exp_oop'][hand]
                keys=('flop_class','turn_class','river_class','displayed_suggestion')
                assert all(g[k]==e[k]for k in keys)
                comparisons.append(dict(hand=hand,**{k:g[k]for k in keys},gto=g['policy'],nl2=e['policy']))
            board.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=args.run,
                flop_bet_size_menu='33%,50%,75%')
            proof_pin.update(rendered_decision_hands=comparisons,shared_rendered_checks=common,
                worker_artifact=pin['id'],worker_sha256=pin['sha256'],original_job_id=pin['job_id'])
            board['nl2_locked_variants'][0].update(variant_label='原始 GTO 翻牌策略及 NL2 轉河牌玩家池節點鎖',
                source_run_role=board['source_run_role'],origin_solve_run_id=args.run,pool_sha256=POOL,
                measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(sources['exp_oop']),
                gto_parent_source_run_id=args.run,gto_parent_source_sha256=root_sha,
                viewer_archive_code=proof_pin['viewer_archive_code'],viewer_sha256=proof_pin['viewer_sha256'])
            group['boards'].append(board);group['pins'].append(proof_pin)
            reports.append(dict(flop=pin['flop'],public_board=public,worker_artifact=pin['id'],shared_hands=len(common),
                compatible_pairs=[rows[v]['compatible_hole_card_pairs']for v in ('gto','exp_oop')],locked_half_pot_candidate=selected['locked_b50']['candidate']))
    folder=evidence/('reverified'if len(group['boards'])>=3 else'partial');folder.mkdir(exist_ok=True)
    (folder/'rank264.json').write_bytes(json_bytes(group))
    (data/'nl2_hu_b680_rank264_workers.json').write_bytes(json_bytes(inputs))
    (data/'nl2_hu_b680_rank264_results.json').write_bytes(json_bytes(reports))
    (data/'nl2_hu_b680_locked_medium.json').write_bytes(json_bytes(medium))
    print(json.dumps(dict(boards=len(group['boards']),cert_eligible=len(group['boards'])>=3,actor_locked_boards=len(group['boards']),
        half_pot_assessed=len(group['boards']),half_pot_candidates=sum(r.get('locked_half_pot_candidate',False)for r in reports),workers=reports)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','receipts','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--run',type=int,required=True);p.add_argument('--head',required=True)
    a=p.parse_args();assert a.run>0 and len(a.head)==40
    publish(a)
