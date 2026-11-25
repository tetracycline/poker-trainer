"""B834: archive only the authentic successful B832 job, never the failed preflight."""
import argparse,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import fields,job_receipt,artifact_receipt,BRANCH
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b832_rank230_eight_low as worker

RUN=45518401455
HEAD='4ace330b1a0ad0a69340f784a13eb77afc8ddd61'
WF='.github/workflows/nl2-hu-b832-rank230-eight-low.yml'
WORKER='tools/hu_b832_rank230_eight_low.py'
JOB=138883720388
FAIL=138883720843
PINS=[
 (14978064525,'B832-R230-8s7h2s','8dd7dd569c0312dabc3d8f56171ad1c3b9cef842ec7fb4e7cefd57e34730ce26'),
 (14979585573,'B832-root-R230-8s7h2s','ae8144664c95597430837e56f7d00d1e39757cca1a31e059fd8400a594689809'),
]
STEPS=['Validate two seats and exact J7s three-street UI route before native work',
       'Build the pinned native driver',
       'Solve a single original and its registered checked boundaries',
       'Upload a Build Artifact',
       'Solve genuine GTO and measured partial NL2 conditional turns',
       'Upload a Build Artifact']
def read(p):return json.loads(p.read_bytes())
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    ep='actions/runs/'+str(RUN)
    raw=json.loads(api(ep))
    r=fields(raw,'id head_sha head_branch path status conclusion run_attempt')
    r['repository']=fields(raw['repository'],'id full_name')
    assert r['repository']==dict(id=1438346845,full_name='tetracycline/poker-trainer')
    assert (r['id'],r['head_sha'],r['head_branch'],r['path'],r['status'],r['conclusion'],r['run_attempt'])==(RUN,HEAD,BRANCH,WF,'completed','failure',1)
    jobs=json.loads(api(ep+'/jobs?per_page=100'));ar=json.loads(api(ep+'/artifacts?per_page=100'))
    assert jobs['total_count']==2 and ar['total_count']==2
    good,=[x for x in jobs['jobs'] if x['id']==JOB]
    bad,=[x for x in jobs['jobs'] if x['id']==FAIL]
    assert (bad['run_id'],bad['head_sha'],bad['run_attempt'],bad['name'],bad['conclusion'])==(RUN,HEAD,1,'solve (8s7h5s)','failure')
    assert any(s['name']==STEPS[0] and s['conclusion']=='failure' for s in bad['steps'])
    assert all(s['conclusion']!='success' for s in bad['steps'] if s['name']==STEPS[2])
    receipt=dict(run=r,jobs=[job_receipt(good,r,JOB,'solve (8s7h2s)',STEPS)],failed_preflight=fields(bad,'id run_id head_sha run_attempt name status conclusion steps'),artifacts=[],blobs={})
    for path in (WF,WORKER):
        pin=json.loads(api('contents/'+path+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        receipt['blobs'][path]=pin
    for aid,name,digest in PINS:
        raw,=[x for x in ar['artifacts'] if x['id']==aid]
        a=artifact_receipt(raw,r,aid,name,digest)
        b=api('actions/artifacts/'+str(aid)+'/zip')
        assert sha(b)==digest and len(b)==a['size_in_bytes']
        (folder/(str(aid)+'.zip')).write_bytes(b);receipt['artifacts'].append(a)
    (folder/'receipt.json').write_bytes(json_bytes(receipt))
def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    receipt=read(a.archives/'receipt.json')
    assert (receipt['run']['id'],receipt['run']['head_sha'])==(RUN,HEAD)
    with TemporaryDirectory(prefix='b834-') as tmp:
        tmp=Path(tmp);paths=[]
        for aid,name,digest in PINS:
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in receipt['artifacts'])
            dest=tmp/str(aid);dest.mkdir();names=unpack_original(raw,dest)
            arc='NL2_B832_R230_8S7H2S'+('_ROOT' if '-root-' in name else '')+'.zip'
            (ev/arc).write_bytes(raw)
            paths.append((dest,names,arc))
        dest,names,arc=paths[0];root,rnames,rootarc=paths[1]
        assert rnames=={'flop/job.json','flop/result.json','root-checkpoint.json'}
        assert all((root/n).read_bytes()==(dest/n).read_bytes() for n in rnames)
        hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
        claim=read(dest/'proof.json')
        assert read(root/'root-checkpoint.json')==claim['origin']
        worker.run(SimpleNamespace(solver=a.solver,output=dest,flop='8s7h2s',driver=None,preflight=False,root_only=False))
        actual=read(dest/'proof.json')
        assert actual==claim and actual['selected'] is None and actual['positive_distinct_flops']==0
        assert not any(x['common'] for x in actual['turns'])
        totals=[actual[k] for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')]
        assert totals==[0,0,0]
        assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
        observation=dict(flop='8s7h2s',job=JOB,archives=[arc,rootarc],native_file_sha256=hashes,proof=claim)
    result=dict(rank=230,source_run=RUN,source_head=HEAD,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in PINS],failed_preflight_not_native=['8s7h5s'])
    (stage/'nl2_hu_b834_source_receipts.json').write_bytes(json_bytes(receipt))
    (stage/'nl2_hu_b834_results.json').write_bytes(json_bytes(result))
    (partial/'b834_rank230_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=[observation])))
    assert before==registry.read_bytes()
    print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
