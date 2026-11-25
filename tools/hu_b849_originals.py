"""B849: independently archive successful B846 Td8d5d, no native rerun."""
import argparse,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import job_receipt,artifact_receipt,fields
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b846_rank75_unseen_monotone as worker

RUN=45550112376
HEAD='d1a61d541d2ab12d4ae5cd01b5c31b3791b21cdd'
WF='.github/workflows/nl2-hu-b846-rank75-unseen-monotone.yml'
FLOP='Td8d5d'
JOB=138988999309
FAILED=138988998929
PINS=[
 (14992964370,'B846-root-R75-Td8d5d','80e71aa41c209964de0e383b6d4ab6f39846a7482881f2f69c05a635ef33b039'),
 (14992699643,'B846-R75-Td8d5d','b5fb31b3a1b4082fd44b8c09ecaafee862b5f9416d56c681d77b9b7fc6311aad')]
STEPS=['Preflight exact actor/size/mono displayed QJo turn checks','Build pinned native solver','Solve each original root once and preserve its checkpoint','Reuse exact original root and solve GTO plus measured NL2 partial locks','Run actions/upload-artifact@v4']
def read(p): return json.loads(p.read_bytes())
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    ep='actions/runs/'+str(RUN)
    raw=json.loads(api(ep))
    run=fields(raw,'id head_sha head_branch path status conclusion run_attempt')
    run['repository']=fields(raw['repository'],'id full_name')
    assert run['repository']==dict(id=1438346845,full_name='tetracycline/poker-trainer')
    assert (run['id'],run['head_sha'],run['head_branch'],run['path'],run['status'],run['conclusion'],run['run_attempt'])==(RUN,HEAD,'fix/nl2-hu-lines-audit-20261118',WF,'completed','failure',1)
    good=job_receipt(json.loads(api('actions/jobs/'+str(JOB))),run,JOB,'solve ('+FLOP+')',STEPS)
    bad=json.loads(api('actions/jobs/'+str(FAILED)))
    assert (bad['id'],bad['run_id'],bad['head_sha'],bad['status'],bad['conclusion'],bad['name'])==(FAILED,RUN,HEAD,'completed','failure','solve (Td9d4d)')
    assert any(s['name']==STEPS[0] and s['conclusion']=='failure' for s in bad['steps'])
    assert all(s['conclusion']=='skipped' for s in bad['steps'] if s['name'] in STEPS[1:4])
    rec=dict(run=run,successful_job=good,blocked_sibling=fields(bad,'id run_id head_sha name status conclusion steps'),artifacts=[],blobs={})
    for path in (WF,'tools/hu_b846_rank75_unseen_monotone.py','tools/hu_b833_rank75_new_monotone.py','tools/hu_b830_rank75_new_monotone.py'):
        pin=json.loads(api('contents/'+path+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        rec['blobs'][path]=pin
    for aid,name,digest in PINS:
        a=artifact_receipt(json.loads(api('actions/artifacts/'+str(aid))),run,aid,name,digest)
        raw=api('actions/artifacts/'+str(aid)+'/zip')
        assert sha(raw)==digest and len(raw)==a['size_in_bytes']
        (folder/(str(aid)+'.zip')).write_bytes(raw)
        rec['artifacts'].append(a)
    (folder/'receipt.json').write_bytes(json_bytes(rec))
def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    status=json.loads(before)
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['TOTAL'])==(158,234,392)
    rec=read(a.archives/'receipt.json')
    assert (rec['run']['id'],rec['run']['head_sha'],rec['successful_job']['id'])==(RUN,HEAD,JOB)
    observations=[]
    with TemporaryDirectory(prefix='b849-') as tmp:
        for aid,name,digest in PINS:
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in rec['artifacts'])
            dest=Path(tmp)/str(aid);dest.mkdir()
            names=unpack_original(raw,dest)
            hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
            archive='NL2_B846_R75_TD8D5D'+('_ROOT' if 'root' in name else '')+'.zip'
            (ev/archive).write_bytes(raw)
            observations.append(dict(artifact=aid,archive=archive,sha256=digest,native_file_sha256=hashes))
        root=Path(tmp)/str(PINS[0][0]);dest=Path(tmp)/str(PINS[1][0])
        for f in ('job.json','result.json'):
            assert (root/'flop'/f).read_bytes()==(dest/'flop'/f).read_bytes()
        claim=read(dest/'proof.json')
        assert read(root/'checkpoint.json')==claim['origin']
        worker.run(SimpleNamespace(solver=a.solver,output=dest,flop=FLOP,driver=None,preflight=False,checkpoint_only=False,checkpoint=None))
        actual=read(dest/'proof.json')
        assert actual==claim and actual['flop']==FLOP
        assert all(actual[k]==0 for k in ('positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates'))
        assert all(not t['shared_displayed_pairs'] for t in actual['turns'])
        assert all(sha((dest/n).read_bytes())==v for n,v in observations[1]['native_file_sha256'].items())
    result=dict(source_run=RUN,successful_job=JOB,blocked_sibling=FAILED,source_artifacts=[x['artifact'] for x in observations],rank=75,flop=FLOP,positive_distinct_flops=0,cert_eligible_ranks=[],native_repeated=0,locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,unchanged_registry_sha256=sha(before),model_node_opportunity_coverage_pct=84.700987)
    (stage/'nl2_hu_b849_source_receipts.json').write_bytes(json_bytes(rec))
    (stage/'nl2_hu_b849_results.json').write_bytes(json_bytes(result))
    (partial/'b849_b846_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations,proof=actual)))
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
