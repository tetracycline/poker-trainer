"""B811: archive the original B810 successes without new native solves."""
import argparse,json,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b810_rank230_ten_seven as w810

CASES=[
 (45419684979,'49da0e1ddc98966b633a3d57dbaf0d83c0ee367f',
  '.github/workflows/nl2-hu-b810-rank230-ten-seven.yml','tools/hu_b810_rank230_ten_seven.py',
  [(138535467908,'solve (Ts7h4s)'),(138535468436,'solve (Ts7h5s)')],
  ['Verify J7 suited, its compatible BTN hand and the displayed three-street route','Build the pinned native driver','Solve the original native flop once with two statically legal checked boundaries','Preserve the completed original before turn solves','Solve reachable turns and replay real two-seat strategy checks','Preserve both strategies and all positive and negative source decisions'],
  [(14932159635,'B810-R230-Ts7h4s','8b31796f8bcdc237323df31241f5a00bfb43472c18fe6c41c19bb000824dfc24'),(14932214557,'B810-root-R230-Ts7h4s','37dc372662144e62948deda7d0f3ce902d7a1ab42450ec329768ba523b2128e0'),(14933243596,'B810-R230-Ts7h5s','5fca6d1244249d069143e403989fc197b1a175e28d9b5629d2bc3998bdcec49f'),(14932873945,'B810-root-R230-Ts7h5s','f9b0da6455a95ef21c9b796c42e774789f3cd5bb06ca120d41c4677bf967ec11')])]
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for run,head,wf,worker,jobs,steps,pins in CASES:
        endpoint='actions/runs/'+str(run)
        r=run_receipt(json.loads(api(endpoint)),run,head,wf)
        assert r['run_attempt']==1
        j=json.loads(api(endpoint+'/jobs?per_page=100'))
        ar=json.loads(api(endpoint+'/artifacts?per_page=100'))
        assert j['total_count']==len(jobs) and ar['total_count']==len(pins)
        receipt=dict(run=r,jobs=[],artifacts=[],blobs={})
        for jid,name in jobs:
            raw,=[x for x in j['jobs'] if x['id']==jid]
            receipt['jobs'].append(job_receipt(raw,r,jid,name,steps))
        for path in (wf,worker):
            pin=json.loads(api('contents/'+path+'?ref='+head))['sha']
            assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
            receipt['blobs'][path]=pin
        for aid,name,digest in pins:
            raw,=[x for x in ar['artifacts'] if x['id']==aid]
            a=artifact_receipt(raw,r,aid,name,digest)
            b=api('actions/artifacts/'+str(aid)+'/zip')
            assert sha(b)==digest and len(b)==a['size_in_bytes']
            (folder/(str(aid)+'.zip')).write_bytes(b)
            receipt['artifacts'].append(a)
        receipts.append(receipt)
    (folder/'receipt.json').write_bytes(json_bytes(receipts))
def read(p):return json.loads(p.read_bytes())
def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    receipts=read(a.archives/'receipt.json');assert len(receipts)==1
    run,head,wf,worker,jobs,steps,pins=CASES[0]
    receipt=receipts[0];assert receipt['run']['head_sha']==head and receipt['run']['id']==run
    observations=[];totals=[0,0,0]
    with TemporaryDirectory(prefix='b811-') as tmp:
        tmp=Path(tmp);paths=[]
        for aid,name,digest in pins:
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in receipt['artifacts'])
            dest=tmp/str(aid);dest.mkdir()
            names=unpack_original(raw,dest)
            flop=name.split('-')[-1]
            archive='NL2_B810_R230_'+flop.upper()+('_ROOT' if '-root-' in name else '')+'.zip'
            (ev/archive).write_bytes(raw)
            paths.append((dest,names,dict(artifact=aid,archive=archive,sha256=digest)))
        for i,flop in enumerate(('Ts7h4s','Ts7h5s')):
            dest,names,archive=paths[2*i];root,rnames,rootarchive=paths[2*i+1]
            assert rnames=={'flop/job.json','flop/result.json','root-checkpoint.json'}
            assert all((root/n).read_bytes()==(dest/n).read_bytes() for n in rnames)
            hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
            claim=read(dest/'proof.json')
            w810.run(SimpleNamespace(solver=a.solver,output=dest,flop=flop,driver=None,preflight=False,root_only=False))
            actual=read(dest/'proof.json')
            assert actual==claim and actual['selected'] is None and actual['positive_distinct_flops']==0 and not any(x['common'] for x in actual['turns'])
            count=[actual[k] for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')]
            assert count==([32,0,0] if i==0 else [32,16,0])
            totals=[x+y for x,y in zip(totals,count)]
            assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
            observations.append(dict(flop=flop,job=jobs[i][0],archives=[archive,rootarchive],native_file_sha256=hashes,proof=claim))
    assert totals==[64,16,0]
    result=dict(rank=230,source_run=run,source_head=head,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=totals[0],joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in pins])
    (stage/'nl2_hu_b811_source_receipts.json').write_bytes(json_bytes(receipt))
    (stage/'nl2_hu_b811_results.json').write_bytes(json_bytes(result))
    (partial/'b811_rank230_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    assert before==registry.read_bytes()
    print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
