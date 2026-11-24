"""Replay B758's three original rank75 decisions without invoking a native solver."""
import argparse
import base64
from collections import Counter
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import hu_b758_rank75_monotone as worker
import hu_b761_collect as source
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b710_publish import unpack_original
from hu_b747_rank150_replay import materialize
from hu_sequential_cfr_reach import cardkey

PINNED_RECEIPT='22752dee531ceb18778e5270aec03c39d5f1bd58'
MODEL=worker.native.MODEL
LINE=worker.native.LINE


def read(path):
    return json.loads(path.read_bytes())


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)


def verify_root(raw,folder,flop,claim):
    with ZipFile(io.BytesIO(raw)) as archive:
        members=[p for p in archive.namelist() if not p.endswith('/')]
        assert len(members)==3 and set(members)=={'checkpoint.json','flop/job.json','flop/result.json'}
        checkpoint=json.loads(archive.read('checkpoint.json'))
        assert (checkpoint['flop'],checkpoint['worker_blob'])==(flop,source.WORKER_BLOB)
        for name,key,worker_key in (('flop/job.json','job_sha256','root_job_sha256'),('flop/result.json','root_sha256','root_sha256')):
            original=archive.read(name)
            assert original==(folder/name).read_bytes() and sha(original)==checkpoint[key]==claim[worker_key]
    root=read(folder/'flop/result.json');ver=worker.verify_root(flop,root)
    assert ver==claim['root_verification'] and all(checkpoint[k]==v for k,v in ver.items())
    assert ver['previous_nodes_identical']==(37 if flop==worker.OLD else 0)
    return ver


def diagnose(folder,claim,record,route):
    turn=record['turn'];flop=claim['flop'];node=claim['actual_decisions'][turn]['gto']
    assert record['gto_executed'] and record['root_gate']['rendered_hero_combos']>0
    assert record['gto_rendered_hands']==0 and record['shared_hands']==[] and not record['paired']
    assert set(claim['actual_decisions'][turn])=={'gto'} and not node['rendered_hands']
    game=read(folder/(turn+'-gto')/'result.json')
    assert sha((folder/(turn+'-gto')/'result.json').read_bytes())==record['gto_sha256']
    n,=[n for n in game['nodes'] if (n['line'],n['player'])==(LINE,1)]
    public=n['board'];reach=node['reach']
    assert (public,n['pot'],n['bets'],game['stack'])==(record['public_board'],2740,[0,0],8705)
    assert reach['public_board']==public and reach['strict_legal_combos']==record['gto_reach']
    masks=base64.b64decode(reach['compatible_action_mask_b64'],validate=True)
    assert sum(bool(v) for v in masks)==reach['strict_legal_combos']
    assert (reach['compatible_hole_card_pairs']>0)==(reach['strict_legal_combos']>0)
    intersection={};actions=Counter()
    for h,bits in zip(game['hands'][1],masks,strict=True):
        h=''.join(cardkey(h))
        if not bits or h not in record['root_gate']['rendered_hands']:continue
        f=worker.native.hcls(h,public[:6]);t=worker.native.hcls(h,public)
        if f not in route['routes']['mono']['parents']:continue
        displayed=route['routes']['mono']['decisions'].get(t)
        if displayed is None:continue
        accepted=[a for i,a in enumerate(n['acts']) if bits & (1<<i)]
        assert accepted and worker.native.ACTIONS[displayed] not in accepted
        actions.update(accepted)
        intersection[h]=dict(flop_class=f,turn_class=t,displayed=displayed,accepted=accepted)
    return dict(turn=turn,public_board=public,original_root_reached_ui_hands=record['root_gate']['rendered_hero_combos'],
        original_gto_sha256=record['gto_sha256'],strict_gto_combos=reach['strict_legal_combos'],
        compatible_gto_pairs=reach['compatible_hole_card_pairs'],displayed_hands_remaining_before_action=len(intersection),
        actual_accepted_action_counts=dict(sorted(actions.items())),hands_and_original_accepted_actions=intersection,
        genuine_gto_half_pot=reach['b50'],matching_displayed_gto_hands=0,lock_executed=False,
        reason='ZERO_TWO_SEAT_TURN_REACH' if not reach['strict_legal_combos'] else (
            'NO_DISPLAYED_PRIVATE_HAND_IN_TURN_REACH' if not intersection else 'DISPLAYED_ACTION_OUTSIDE_ACCEPTED_MASK'))


def publish(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve()
    original=a.receipts.read_bytes()
    assert worker.checked.blob(a.receipts)==PINNED_RECEIPT
    auth=read(a.receipts);assert source.validate(auth)==auth and original==json_bytes(auth)
    assert auth['run']['conclusion']=='success' and len(auth['artifacts'])==6
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    model=json.loads(before)['records'][MODEL]
    assert (model['frequency_rank'],model['label'],model['assumed_model_node_spr'],model['solver_profile'])==(75,'APPROX',3.177,'CO3_BTN')
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    write(out/'nl2_hu_b761_source_manifest.json',original)
    route_cmd=['node','tools/hu_b674_threebet_call_routes.cjs']
    route=json.loads(subprocess.check_output(route_cmd))['75']
    write(partial/'b761_rank75_routes.json',json_bytes(route))
    assert worker.checked.blob(Path(worker.__file__))==source.WORKER_BLOB
    for path,pin in ((source.WORKER,source.WORKER_BLOB),(source.WORKFLOW,source.WORKFLOW_BLOB)):
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==pin
    rows=[]
    with TemporaryDirectory(prefix='b761-exact-') as tmp:
        d=Path(tmp);frozen=d/'source';materialize(source.HEAD,frozen)
        assert json.loads(subprocess.check_output(route_cmd,cwd=frozen))['75']==route
        for flop,jid in source.JOBS.items():
            originals={}
            for kind,prefix,name in [('worker','B758-R75-','B758_R75_'),('checkpoint','B758-root-R75-','B758_ROOT_R75_')]:
                meta,=[x for x in auth['artifacts'] if x['name']==prefix+flop]
                raw=(a.archives/(str(meta['id'])+'.zip')).read_bytes()
                assert len(raw)==meta['size_in_bytes'] and sha(raw)==meta['digest'][7:]
                write(ev/('NL2_'+name+flop.upper()+'.zip'),raw);originals[kind]=(meta,raw)
            folder=d/flop;names=unpack_original(originals['worker'][1],folder)
            proof_raw=(folder/'proof.json').read_bytes();claim=json.loads(proof_raw)
            assert (claim['schema'],claim['source_worker_blob'],claim['flop'],claim['rank'],claim['line'],claim['actor'])==(
                'NL2_B758_R75_MONOTONE_ORIGINAL_V1',source.WORKER_BLOB,flop,75,LINE,1)
            files=claim['native_files_sha256']
            expect={'flop/job.json','flop/result.json'}|{t+'-gto/'+name for t in worker.CASES[flop] for name in ('job.json','result.json')}
            assert names==set(files)|{'proof.json'} and set(files)==expect
            assert all(sha((folder/p).read_bytes())==v for p,v in files.items())
            ver=verify_root(originals['checkpoint'][1],folder,flop,claim)
            subprocess.run([sys.executable,str(frozen/source.WORKER),'--solver',str(solver),'--flop',flop,'--output',str(folder)],
                cwd=frozen,check=True)
            assert (folder/'proof.json').read_bytes()==proof_raw and all(sha((folder/p).read_bytes())==v for p,v in files.items())
            assert claim['positive_distinct_flops']==0 and [x['turn'] for x in claim['turns']]==worker.CASES[flop]
            write(partial/('b761_'+flop.lower()+'_proof.json'),proof_raw)
            outcomes=[diagnose(folder,claim,t,route) for t in claim['turns']]
            rows.append(dict(flop=flop,job_id=jid,worker_artifact=originals['worker'][0]['id'],worker_sha256=sha(originals['worker'][1]),
                checkpoint_artifact=originals['checkpoint'][0]['id'],checkpoint_sha256=sha(originals['checkpoint'][1]),
                original_root_job_sha256=claim['root_job_sha256'],original_root_sha256=claim['root_sha256'],
                proof_sha256=sha(proof_raw),root_verification=ver,original_source_witness=claim['original_donor'],
                turns=outcomes,serialized_job_bytes_verified=True,original_proof_replayed_byte_identically=True))
    turns=[t for row in rows for t in row['turns']]
    assert len(turns)==12 and sum(t['strict_gto_combos']>0 for t in turns)==7
    group=dict(model_id=MODEL,rank=75,boards=[],pins=[])
    write(partial/'b761_rank75.json',json_bytes(group))
    write(partial/'b761_rank75_locked_medium.json',json_bytes(dict(schema='NL2_HU_B761_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})))
    summary=dict(schema='NL2_B761_R75_AUTHENTICATED_ORIGINAL_DECISIONS_V1',rank=75,model_id=MODEL,source_run=source.RUN,source_head=source.HEAD,
        workers=rows,new_distinct_flops=2,prior_root_with_new_extractions=1,all_previous_exported_nodes_identical=37,
        native_gto_turn_jobs=12,gto_joint_reachable_turns=7,gto_zero_joint_turns=5,
        reachable_rendered_gto_commands=0,native_locked_turn_jobs=0,actor_locked_joint_boards=0,half_pot_assessed_joint_boards=0,
        half_pot_nonpolarized_candidates=0,positive_distinct_flops=0,changed_registry_records=0)
    write(out/'nl2_hu_b761_results.json',json_bytes(summary));assert registry.read_bytes()==before
    print(json.dumps({k:v for k,v in summary.items() if k!='workers'}))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','archives','receipts','output'):cli.add_argument('--'+key,type=Path,required=True)
    publish(cli.parse_args())
