"""B831: collect the successful B830 matrix job, preserving failed preflight as non-native."""
import argparse,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import fields,job_receipt,artifact_receipt,BRANCH
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b830_rank75_new_monotone as worker

RUN=45505657024
HEAD='55f863e6533d0fe09f65665643e356427f93169e'
WF='.github/workflows/nl2-hu-b830-rank75-new-monotone.yml'
WORKER='tools/hu_b830_rank75_new_monotone.py'
JOB=138840080435
FAIL=138840080915
PINS=[(14972832275,'B830-R75-Td8d7d','cf03a4ba48dcbf91ba19de5117297c78f0e4f657e413baedfded489cd4bf7fda'),
      (14972737258,'B830-root-R75-Td8d7d','068e4579031d1a1bff68c2bd5c07fd1b5f4eede4d1ede10fc6b1df858c78146c')]
STEPS=['Verify original CO donk and BTN call witnesses, monotone UI and both preflop ranges',
       'Build the pinned native solver','Solve each genuinely new full-menu original once',
       'Preserve the completed original before conditional work',
       'Read the saved original and verify both policies at reachable turn decisions',
       'Preserve the conditional jobs and original decisions']
def read(p):return json.loads(p.read_bytes())
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    ep='actions/runs/'+str(RUN)
    raw=json.loads(api(ep))
    r=fields(raw,'id head_sha head_branch path status conclusion run_attempt')
    r['repository']=fields(raw['repository'],'id full_name')
    assert r['repository']==dict(id=1438346845,full_name='tetracycline/poker-trainer')
    assert (r['id'],r['head_sha'],r['head_branch'],r['path'],r['status'],r['conclusion'],r['run_attempt'])==(RUN,HEAD,BRANCH,WF,'completed','failure',1)
    jobs=json.loads(api(ep+'/jobs?per_page=100'))
    ar=json.loads(api(ep+'/artifacts?per_page=100'))
    assert jobs['total_count']==2 and ar['total_count']==2
    good,=[x for x in jobs['jobs'] if x['id']==JOB]
    bad,=[x for x in jobs['jobs'] if x['id']==FAIL]
    assert (bad['run_id'],bad['head_sha'],bad['run_attempt'],bad['name'],bad['conclusion'])==(RUN,HEAD,1,'solve (Td9d6d)','failure')
    assert any(s['name']==STEPS[0] and s['conclusion']=='failure' for s in bad['steps'])
    assert all(s['conclusion']!='success' for s in bad['steps'] if s['name']==STEPS[2])
    receipt=dict(run=r,jobs=[job_receipt(good,r,JOB,'solve (Td8d7d)',STEPS)],failed_preflight=fields(bad,'id run_id head_sha run_attempt name status conclusion steps'),artifacts=[],blobs={})
    for path in (WF,WORKER):
        pin=json.loads(api('contents/'+path+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        receipt['blobs'][path]=pin
    for aid,name,digest in PINS:
        raw,=[x for x in ar['artifacts'] if x['id']==aid]
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
    receipt=read(a.archives/'receipt.json')
    assert receipt['run']['id']==RUN and receipt['run']['head_sha']==HEAD
    with TemporaryDirectory(prefix='b831-') as tmp:
        tmp=Path(tmp);paths=[]
        for aid,name,digest in PINS:
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in receipt['artifacts'])
            dest=tmp/str(aid);dest.mkdir();names=unpack_original(raw,dest)
            archive='NL2_B830_R75_TD8D7D'+('_ROOT' if '-root-' in name else '')+'.zip'
            (ev/archive).write_bytes(raw)
            paths.append((dest,names,dict(artifact=aid,archive=archive,sha256=digest)))
        dest,names,archive=paths[0];root,rnames,rootarchive=paths[1]
        assert rnames=={'flop/job.json','flop/result.json','checkpoint.json'}
        assert all((root/n).read_bytes()==(dest/n).read_bytes() for n in ('flop/job.json','flop/result.json'))
        hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
        claim=read(dest/'proof.json')
        assert read(root/'checkpoint.json')==claim['origin']
        worker.run(SimpleNamespace(solver=a.solver,output=dest,flop='Td8d7d',driver=None,checkpoint=None,checkpoint_only=False,preflight=False))
        actual=read(dest/'proof.json')
        assert actual==claim and actual['positive_distinct_flops']==0
        totals=[actual[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')]
        assert totals==[0,0,0]
        assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
        observation=dict(flop='Td8d7d',job=JOB,archives=[archive,rootarchive],native_file_sha256=hashes,proof=claim)
    result=dict(rank=75,source_run=RUN,source_head=HEAD,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=totals[0],joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in PINS],failed_preflight_not_native=['Td9d6d'])
    (stage/'nl2_hu_b831_source_receipts.json').write_bytes(json_bytes(receipt))
    (stage/'nl2_hu_b831_results.json').write_bytes(json_bytes(result))
    (partial/'b831_rank75_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=[observation])))
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
