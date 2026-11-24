"""B803: archive the successful B802 worker, not the preflight-failed worker."""
import argparse,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import hu_b802_rank230_low_connected as worker
from hu_b467_river_source_gate import json_bytes,sha
# gh sanitizes terminal escapes in workflow logs; preserve the exact bytes for SHA checks.
def api(path):
    import time
    for attempt in range(4):
        result = subprocess.run(['gh','api','--allow-escape-sequences','repos/tetracycline/poker-trainer/'+path],capture_output=True)
        if result.returncode==0: return result.stdout
        if attempt==3: raise RuntimeError(result.stderr.decode(errors='replace')[-800:])
        time.sleep(2*(attempt+1))

from hu_b710_publish import unpack_original
from hu_b738_collect import fields,job_receipt,artifact_receipt

RUN=45369874573
HEAD='6f2f6138d91d744e44e592dd2b608ab264404b07'
WORKFLOW='.github/workflows/nl2-hu-b802-rank230-low-connected.yml'
WORKER='tools/hu_b802_rank230_low_connected.py'
JOB=138361059355
FAILED=138361059769
FLOP='9s7h5s'
PINS=[(14908343621,'B802-R230-9s7h5s','2e46edcb13e3d76f79059220e20a7df9d6063661650ee786f90d81dd5566c480'),(14908852551,'B802-root-R230-9s7h5s','0684f1de62c990a72feef86277e7c455bb3a16f69446a2c9a82c101e8fd3c95c')]
STEPS=['Verify J7 suited, its compatible BTN hand and the displayed three-street route','Build the pinned native driver','Solve the original native flop once with three registered checked boundaries','Preserve the completed original before turn solves','Solve reachable turns and replay real two-seat strategy checks','Preserve both strategies and all positive and negative source decisions']

def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    endpoint='actions/runs/'+str(RUN)
    raw=json.loads(api(endpoint))
    r=fields(raw,'id head_sha head_branch path status conclusion run_attempt')
    r['repository']=fields(raw['repository'],'id full_name')
    assert r==dict(id=RUN,head_sha=HEAD,head_branch='fix/nl2-hu-lines-audit-20261118',path=WORKFLOW,status='completed',conclusion='failure',run_attempt=1,repository=dict(id=1438346845,full_name='tetracycline/poker-trainer'))
    jobs=json.loads(api(endpoint+'/jobs?per_page=100'))
    arts=json.loads(api(endpoint+'/artifacts?per_page=100'))
    assert jobs['total_count']==arts['total_count']==2
    good,=[j for j in jobs['jobs'] if j['id']==JOB]
    bad,=[j for j in jobs['jobs'] if j['id']==FAILED]
    failed=fields(bad,'id run_id head_sha run_attempt name status conclusion')
    assert failed==dict(id=FAILED,run_id=RUN,head_sha=HEAD,run_attempt=1,name='solve (8s7h6s)',status='completed',conclusion='failure')
    failed['steps']=[fields(s,'number name status conclusion') for s in bad['steps']]
    outcome={s['name']:s['conclusion'] for s in failed['steps']}
    assert outcome[STEPS[0]]=='failure' and all(outcome[s]=='skipped' for s in STEPS[1:5])
    log=api('actions/jobs/'+str(FAILED)+'/logs')
    assert b"AssertionError: ('8s7h6s', '3c')" in log
    receipt=dict(run=r,successful_job=job_receipt(good,r,JOB,'solve (9s7h5s)',STEPS),failed_job=failed,failed_preflight="AssertionError: ('8s7h6s', '3c')",failed_log_sha256=sha(log),artifacts=[],blobs={})
    for path in (WORKFLOW,WORKER):
        pin=json.loads(api('contents/'+path+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        receipt['blobs'][path]=pin
    for aid,name,digest in PINS:
        art,=[a for a in arts['artifacts'] if a['id']==aid]
        ar=artifact_receipt(art,r,aid,name,digest)
        receipt['artifacts'].append(ar)
        b=api('actions/artifacts/'+str(aid)+'/zip')
        assert sha(b)==digest and len(b)==ar['size_in_bytes']
        (folder/(str(aid)+'.zip')).write_bytes(b)
    (folder/'receipt.json').write_bytes(json_bytes(receipt))

def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    stage.mkdir(parents=True)
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    receipt=json.loads((a.archives/'receipt.json').read_bytes())
    assert receipt['run']['head_sha']==HEAD and receipt['successful_job']['id']==JOB
    (stage/'nl2_hu_b803_source_receipts.json').write_bytes(json_bytes(receipt))
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    with TemporaryDirectory(prefix='b803-') as tmp:
        tmp=Path(tmp)
        archives=[];destinations=[]
        for aid,name,digest in PINS:
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in receipt['artifacts'])
            dest=tmp/str(aid);dest.mkdir()
            names=unpack_original(raw,dest)
            archive='NL2_B802_R230_9S7H5S'+('_ROOT' if 'root' in name else '')+'.zip'
            (ev/archive).write_bytes(raw)
            archives.append(dict(artifact=aid,archive=archive,sha256=digest))
            destinations.append((dest,names))
        (dest,names),(root,rootnames)=destinations
        assert rootnames=={'flop/job.json','flop/result.json','root-checkpoint.json'}
        assert all((root/n).read_bytes()==(dest/n).read_bytes() for n in rootnames)
        hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
        claim=json.loads((dest/'proof.json').read_bytes())
        worker.run(SimpleNamespace(solver=a.solver,output=dest,flop=FLOP,driver=None,preflight=False,root_only=False))
        actual=json.loads((dest/'proof.json').read_bytes())
        assert actual==claim and actual['selected'] is None and actual['positive_distinct_flops']==0 and not any(x['common'] for x in actual['turns'])
        count=[actual[k] for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')]
        assert count==[15,0,0]
        assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items() if n!='proof.json')
        (partial/'b803_rank230_original_observations.json').write_bytes(json_bytes(dict(rank=230,positive_distinct_flops=0,cert_eligible_ranks=[],observations=[dict(source_run=RUN,source_head=HEAD,job=JOB,flop=FLOP,archives=archives,native_file_sha256=hashes,locked=count[0],positive_halfpot=count[1],nonpolarized=count[2],proof=claim)],failed_preflight=dict(flop='8s7h6s',turn='3c',native_root_executed=False))))
    (stage/'nl2_hu_b803_results.json').write_bytes(json_bytes(dict(rank=230,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=count[0],joint_halfpot_assessed=count[1],halfpot_candidates=count[2],unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in PINS])))
    assert before==registry.read_bytes()
    print(json.dumps(dict(B803=count,registry=json.loads(before)['CERT_MULTIBOARD'])))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
