"""Resume the already audited B685 artifact; never re-solve or repeat its full suite."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time
from zipfile import ZipFile

REPO='tetracycline/poker-trainer'
REPO_ID=1438346845
BRANCH='fix/nl2-hu-lines-audit-20261118'
RUN=45310712824
HEAD='30c81f5d06a94610cdb2b9aa3100f4c495352c5f'
JOB=138165446421
ARTIFACT=14883710970
DIGEST='80ef27ca8633d1f705d1ed4aa73f14587a612deac6a5ea327409e3c168b17df5'
WORKFLOW='.github/workflows/nl2-hu-b685-rank84-negatives.yml'
REQUIRED={
    'Authenticate the completed source jobs and replay all original negative paths',
    'Preserve the authenticated raw negatives without changing any registry record',
    'Run the complete source, lock, medium-size and navigation audit',
    'Run actions/upload-artifact@v4',
}
FAILED_CANDIDATE='Create the verified data-only candidate without moving a branch'
CENTRAL=(
    'data/nl2_hu_multiboard_status_current.json',
    'data/nl2_hu_verified_extensions.json',
    'data/nl2_hu_model_history_crosswalk.json',
    'data/nl2_hu_model_source_references.json',
    'nl2_hu_model.js','nl2.js',
)
FILES=(
    'nl2_hu_b685_rank84_results.json',
    'nl2_hu_b685_rank84_workers.json',
    'nl2_hu_b685_registry_guard.json',
    'solver_evidence/NL2_B685_R84_KD7S2H.zip',
    'solver_evidence/NL2_B685_R84_QH9C4S.zip',
    'solver_evidence/NL2_B685_R84_QS8H3D.zip',
    'solver_evidence/b685_receipts/14882521642.json',
    'solver_evidence/b685_receipts/14883145231.json',
    'solver_evidence/b685_receipts/14883285189.json',
    'solver_evidence/b685_receipts/job-138161325019.json',
    'solver_evidence/b685_receipts/job-138161325264.json',
    'solver_evidence/b685_receipts/job-138161325271.json',
    'solver_evidence/b685_receipts/source-files.json',
    'solver_evidence/b685_receipts/source-run.json',
    'solver_evidence/b685_receipts/workers.json',
    'solver_evidence/partial/B685_locked_medium.json',
    'solver_evidence/partial/B685_rank84.json',
)
PREFIX='b685-replayed/data/'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_sha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def canonical_sha(value):
    return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())


def api(path):
    for attempt in range(4):
        result=subprocess.run(['gh','api','repos/'+REPO+'/'+path],capture_output=True)
        if result.returncode==0:return result.stdout
        if attempt==3:raise RuntimeError(result.stderr.decode(errors='replace')[-800:])
        time.sleep(2*(attempt+1))


def authenticate(run,job,receipt):
    assert (run['id'],run['head_sha'],run['head_branch'],run['path'],run['status'],run['conclusion'])==(
        RUN,HEAD,BRANCH,WORKFLOW,'completed','failure')
    assert (run['repository']['id'],run['repository']['full_name'])==(REPO_ID,REPO)
    assert (job['id'],job['run_id'],job['head_sha'],job['name'],job['status'],job['conclusion'])==(
        JOB,RUN,HEAD,'replay-negatives','completed','failure')
    assert run['run_attempt']==job['run_attempt']==1
    passed={step['name']for step in job['steps']if(step['status'],step['conclusion'])==('completed','success')}
    failed={step['name']for step in job['steps']if step['conclusion']=='failure'}
    assert REQUIRED<=passed and failed=={FAILED_CANDIDATE}
    origin=receipt['workflow_run']
    assert (receipt['id'],receipt['name'],receipt['digest'],origin['id'],origin['head_sha'],origin['repository_id'])==(
        ARTIFACT,'B685-authenticated-rank84-negatives','sha256:'+DIGEST,RUN,HEAD,REPO_ID)
    assert not receipt['expired']


def verified_payload(raw):
    assert sha(raw)==DIGEST,'Audited artifact SHA changed'
    with ZipFile(io.BytesIO(raw))as archive:
        expected={PREFIX+name for name in FILES}|{'b685-summary.json','b685-medium-coverage.json'}
        assert len(archive.namelist())==len(expected) and set(archive.namelist())==expected
        assert all(not item.is_dir() and (item.external_attr>>16)&0o170000!=0o120000 for item in archive.infolist())
        payload={name:archive.read(PREFIX+name)for name in FILES}
        report=json.loads(payload['nl2_hu_b685_rank84_results.json'])
        summary=json.loads(archive.read('b685-summary.json'))
        assert summary=={key:value for key,value in report.items()if key not in ('workers','registry_generation_requires_active_price_pair')}
        assert report['source_run']==45309479062 and report['source_head']=='b63c9e753b68036c0935a209daa1e77095151da3'
        assert report['boards']==0 and not report['cert_eligible']
        assert report['source_flops']==report['negative_flops']==report['retained_original_archives']==3
        assert report['gto_turns_assessed']==12
        assert report['actor_locked_boards']==report['half_pot_assessed']==report['gto_half_pot_assessed']==report['half_pot_candidates']==0
        group=json.loads(payload['solver_evidence/partial/B685_rank84.json'])
        assert group['rank']==84 and group['boards']==group['pins']==[]
        medium=json.loads(payload['solver_evidence/partial/B685_locked_medium.json'])
        assert medium['references']==medium['gto_references']=={}
        coverage=json.loads(archive.read('b685-medium-coverage.json'))
        assert coverage['certified_models']==report['protected_cert_records']==147
    return payload,report


def check_registry(payload,current):
    guard=json.loads(payload['nl2_hu_b685_registry_guard.json'])
    assert guard['schema']=='NL2_HU_B685_PROTECTED_CERT_RECORDS_V1'
    assert guard['registry_sha256']==sha(current),'The current registry differs from the fully audited B685 registry'
    registry=json.loads(current)
    certs={mid:canonical_sha(record)for mid,record in registry['records'].items()if record['label']=='CERT-MULTIBOARD'}
    assert certs==guard['protected_cert_record_sha256'] and len(certs)==147
    assert registry['records'][guard['target_model_id']]['label']=='APPROX'


def main(args):
    run=json.loads(api('actions/runs/'+str(RUN)))
    job=json.loads(api('actions/jobs/'+str(JOB)))
    receipt=json.loads(api('actions/artifacts/'+str(ARTIFACT)))
    authenticate(run,job,receipt)
    baseline={name:Path(name).read_bytes()for name in CENTRAL}
    for name,raw in baseline.items():
        source=json.loads(api('contents/'+name+'?ref='+HEAD))
        assert source['type']=='file' and source['path']==name
        assert source['sha']==blob_sha(raw),(name,'changed since the successful full audit')
    raw=api('actions/artifacts/'+str(ARTIFACT)+'/zip')
    payload,report=verified_payload(raw)
    check_registry(payload,baseline[CENTRAL[0]])
    output=args.output.resolve();data=output/'data';central=Path('data').resolve()
    assert data!=central and central not in data.parents and not data.exists(),'Use an isolated fresh staging directory'
    for name,raw in payload.items():
        path=data/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        assert path.read_bytes()==raw
    assert len(list(data.rglob('*')))>len(FILES)
    assert len([path for path in data.rglob('*')if path.is_file()])==len(FILES)==17
    assert all(Path(name).read_bytes()==raw for name,raw in baseline.items())
    result=dict(schema='NL2_HU_B692_RESUMED_AUDITED_ARTIFACT_V1',source_run=RUN,source_head=HEAD,source_job=JOB,
        artifact_id=ARTIFACT,artifact_sha256=DIGEST,restored_files=17,certified_models=147,approx_models=245,
        new_actor_locked_boards=0,new_half_pot_assessed=0,original_native_solves_repeated=0,completed_full_suites_repeated=0,
        prior_full_audit_step_verified=True,registry_and_ui_byte_identical=True,
        files={name:sha(raw)for name,raw in payload.items()})
    (output/'resume-report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items()if key!='files'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
