"""B815: archive the original B814 successes without new native solves."""
import argparse,json,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b814_rank75_other_roots as w814

CASES=[
 (45463320869,'1fb879642635c0f1c736efe3454bbaa9bb217982',
  '.github/workflows/nl2-hu-b814-rank75-other-roots.yml','tools/hu_b814_rank75_other_roots.py',
  [(138691501656,'solve (8c7c5c)'),(138691500837,'solve (9h7h5h)')],
  ['Reconstruct four held-out original jobs and every two-seat reach weight','Build the pinned native driver','Solve the missing conditional games and replay evidence from native output','Preserve original jobs, decisions and range reconstruction'],
  [(14954247067,'B814-R75-8c7c5c','0ef439d2ba7ae2050a900291af31afdf2b4e633f18b0ddf07f4645367dec26e4'),(14952769397,'B814-R75-9h7h5h','b12a9c04544a28b492a245c94003c0d894fcdd267b0f140eed4b3b73707072a2')])]
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
    with TemporaryDirectory(prefix='b815-') as tmp:
        tmp=Path(tmp)
        for i,(aid,name,digest) in enumerate(pins):
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in receipt['artifacts'])
            flop=name.split('-')[-1]
            dest=tmp/str(aid);dest.mkdir()
            names=unpack_original(raw,dest)
            archive='NL2_B814_R75_'+flop.upper()+'.zip'
            (ev/archive).write_bytes(raw)
            hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
            claim=read(dest/'proof.json')
            assert claim['flop']==flop and claim['rank']==75 and claim['new_flop_solve_invocations']==0
            expected={'proof.json'}
            for row in claim['turns']:
                for mode in row['policies']:
                    expected.update(row['turn']+'-'+mode+'/'+leaf for leaf in ('job.json','result.json'))
            assert expected<=names
            w814.run(SimpleNamespace(solver=a.solver,output=dest,flop=flop,driver=None,preflight=False))
            actual=read(dest/'proof.json')
            assert actual==claim and actual['positive_distinct_flops']==0 and not any(x['shared_displayed_pairs'] for x in actual['turns'])
            count=[actual[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')]
            assert count==[0,0,0]
            totals=[x+y for x,y in zip(totals,count)]
            assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
            observations.append(dict(flop=flop,job=jobs[i][0],archive=archive,artifact=aid,sha256=digest,native_file_sha256=hashes,proof=claim))
    assert totals==[0,0,0]
    result=dict(rank=75,source_run=run,source_head=head,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=totals[0],joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in pins])
    (stage/'nl2_hu_b815_source_receipts.json').write_bytes(json_bytes(receipt))
    (stage/'nl2_hu_b815_results.json').write_bytes(json_bytes(result))
    (partial/'b815_rank75_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
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
