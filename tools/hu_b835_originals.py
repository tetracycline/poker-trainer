"""B835: archive two successful B833 native zero-certificate results.
Replays original raw GTO and measured partial NL2 decisions under fixed source
pins and refuses certification without three distinct jointly displayed flops.
"""
import argparse,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b833_rank75_new_monotone as worker

RUN=45518585298
HEAD='e6f29a285a5ed45dbfc6971e3c861b2c17712be2'
WF='.github/workflows/nl2-hu-b833-rank75-new-monotone.yml'
WORKER='tools/hu_b833_rank75_new_monotone.py'
JOBS=[(138884346711,'solve (9d8d2d)'),(138884347079,'solve (Td8d6d)')]
STEPS=['Preflight exact actor/size/mono displayed QJo turn checks',
       'Build pinned native solver',
       'Solve each original root once and preserve its checkpoint',
       'Run actions/upload-artifact@v4',
       'Reuse exact original root and solve GTO plus measured NL2 partial locks']
PINS=[
 (14978347517,'B833-R75-9d8d2d','1530afff356e39a892fef55d8760817d1f2a6336d7fa172537b74a584b786f7a'),
 (14978187821,'B833-root-R75-9d8d2d','dedabe72ce14eb62eed6832a7ff117b0e7bed49a0e147101bb7c2a907c59635a'),
 (14979422613,'B833-R75-Td8d6d','cdf2dc65dd9e98e11b06b07b5149fc11e1334b62bf8027e6a5f073e2c2799e13'),
 (14979685591,'B833-root-R75-Td8d6d','38673a0d92d7c6fb5d7aa7f927d9d15bf260fe544d64d9d77aae872eaee5a095'),
]
def read(p):return json.loads(p.read_bytes())
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    ep='actions/runs/'+str(RUN)
    r=run_receipt(json.loads(api(ep)),RUN,HEAD,WF)
    assert r['run_attempt']==1 and r['conclusion']=='success'
    jobs=json.loads(api(ep+'/jobs?per_page=100'))
    ars=json.loads(api(ep+'/artifacts?per_page=100'))
    assert jobs['total_count']==len(JOBS) and ars['total_count']==len(PINS)
    receipt=dict(run=r,jobs=[],artifacts=[],blobs={})
    for jid,name in JOBS:
        j,=[x for x in jobs['jobs'] if x['id']==jid]
        receipt['jobs'].append(job_receipt(j,r,jid,name,STEPS))
    for path in (WF,WORKER):
        pin=json.loads(api('contents/'+path+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        receipt['blobs'][path]=pin
    for aid,name,digest in PINS:
        raw,=[x for x in ars['artifacts'] if x['id']==aid]
        a=artifact_receipt(raw,r,aid,name,digest)
        b=api('actions/artifacts/'+str(aid)+'/zip')
        assert sha(b)==digest and len(b)==a['size_in_bytes']
        (folder/(str(aid)+'.zip')).write_bytes(b)
        receipt['artifacts'].append(a)
    (folder/'receipt.json').write_bytes(json_bytes(receipt))
def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    rec=read(a.archives/'receipt.json')
    assert (rec['run']['id'],rec['run']['head_sha'])==(RUN,HEAD)
    totals=[0,0,0];observations=[]
    with TemporaryDirectory(prefix='b835-') as tmp:
        tmp=Path(tmp);paths=[]
        for aid,name,digest in PINS:
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in rec['artifacts'])
            dest=tmp/str(aid);dest.mkdir();names=unpack_original(raw,dest)
            flop=name.split('-')[-1].upper()
            archive='NL2_B833_R75_'+flop+('_ROOT' if '-root-' in name else '')+'.zip'
            (ev/archive).write_bytes(raw)
            paths.append((dest,names,archive))
        for i,flop in enumerate(('9d8d2d','Td8d6d')):
            dest,names,archive=paths[2*i];root,rnames,rootarchive=paths[2*i+1]
            assert rnames=={'flop/job.json','flop/result.json','checkpoint.json'}
            assert all((root/n).read_bytes()==(dest/n).read_bytes() for n in ('flop/job.json','flop/result.json'))
            hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
            claim=read(dest/'proof.json')
            assert read(root/'checkpoint.json')==claim['origin']
            worker.run(SimpleNamespace(solver=a.solver,output=dest,flop=flop,driver=None,checkpoint=None,checkpoint_only=False,preflight=False))
            actual=read(dest/'proof.json')
            assert actual==claim and actual['positive_distinct_flops']==0
            count=[actual[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')]
            assert count==[0,0,0]
            totals=[a+b for a,b in zip(totals,count)]
            assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
            observations.append(dict(flop=flop,job=JOBS[i][0],archives=[archive,rootarchive],native_file_sha256=hashes,proof=claim))
    result=dict(rank=75,source_run=RUN,source_head=HEAD,positive_distinct_flops=0,
                cert_eligible_ranks=[],locked_public_boards=totals[0],
                joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],
                unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in PINS])
    (stage/'nl2_hu_b835_source_receipts.json').write_bytes(json_bytes(rec))
    (stage/'nl2_hu_b835_results.json').write_bytes(json_bytes(result))
    (partial/'b835_rank75_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    assert before==registry.read_bytes()
    print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
