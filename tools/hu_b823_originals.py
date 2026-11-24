"""B823: independently archive two successful B822 native conditional results.
No new solves. Replay every original policy, preserve SHA-pinned source and
the previous certification state. Zero display intersection is not CERT."""
import argparse,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b822_rank75_b816_roots as worker

RUN=45496428979
HEAD='6c0c51805e5d5d8003c76896369af08b2774eca1'
WF='.github/workflows/nl2-hu-b822-rank75-b816-roots.yml'
WORKER='tools/hu_b822_rank75_b816_roots.py'
CASES=[
 ('9d8d5d',138808056444,14967749992,'2499605209c56027ffb410c0fa5ac610305837f6d87319182281216a088f0920'),
 ('9d8d7d',138808056855,14968572190,'182c8be9a5ca5dc4de2e64ff8a546aadeac00aa9069fe3a41b6b64530db6ec02')
]
STEPS=[
 'Reconstruct original held-out jobs and verify B809 two-seat witness',
 'Build the pinned native driver',
 'Solve the missing conditional games and replay evidence from native output',
 'Preserve original jobs, decisions and range reconstruction'
]
def read(p):return json.loads(p.read_bytes())

def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    ep='actions/runs/'+str(RUN)
    r=run_receipt(json.loads(api(ep)),RUN,HEAD,WF)
    assert r['run_attempt']==1
    jobs=json.loads(api(ep+'/jobs?per_page=100'))
    arts=json.loads(api(ep+'/artifacts?per_page=100'))
    assert jobs['total_count']==arts['total_count']==len(CASES)==2
    receipt=dict(run=r,jobs=[],artifacts=[],blobs={})
    for p in (WF,WORKER):
        pin=json.loads(api('contents/'+p+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',p],text=True).strip()==pin
        receipt['blobs'][p]=pin
    for flop,jid,aid,digest in CASES:
        j,=[x for x in jobs['jobs'] if x['id']==jid]
        receipt['jobs'].append(job_receipt(j,r,jid,'solve ('+flop+')',STEPS))
        a,=[x for x in arts['artifacts'] if x['id']==aid]
        receipt['artifacts'].append(artifact_receipt(a,r,aid,'B822-R75-'+flop,digest))
        raw=api('actions/artifacts/'+str(aid)+'/zip')
        assert len(raw)==a['size_in_bytes'] and sha(raw)==digest
        (folder/(str(aid)+'.zip')).write_bytes(raw)
    (folder/'receipt.json').write_bytes(json_bytes(receipt))

def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    before=registry.read_bytes()
    receipt=read(a.archives/'receipt.json')
    assert receipt['run']['id']==RUN and receipt['run']['head_sha']==HEAD
    assert len(receipt['jobs'])==len(receipt['artifacts'])==2
    assert receipt['blobs'][WORKER]==subprocess.check_output(['git','hash-object',WORKER],text=True).strip()
    results=[];totals=[0,0,0]
    with TemporaryDirectory(prefix='b823-') as tmp:
        for flop,jid,aid,digest in CASES:
            matching=[x for x in receipt['jobs'] if x['id']==jid and x['conclusion']=='success' and x['head_sha']==HEAD]
            assert len(matching)==1
            matched=[x for x in receipt['artifacts'] if x['id']==aid and x['digest']=='sha256:'+digest]
            assert len(matched)==1
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest
            original=Path(tmp)/flop;original.mkdir()
            names=unpack_original(raw,original)
            expected={'proof.json'}
            for turn in ('2d','3d'):
                for mode in ('gto','exp_ip'):
                    expected.add(turn+'-'+mode+'/job.json')
                    expected.add(turn+'-'+mode+'/result.json')
            assert names==expected
            original_hashes={p:sha((original/p).read_bytes()) for p in sorted(names)}
            claim=read(original/'proof.json')
            assert (claim['schema'],claim['rank'],claim['flop'])==('NL2_B822_R75_HELDOUT_B816_ROOTS_V1',75,flop)
            assert claim['new_flop_solve_invocations']==0 and claim['not_a_certification']
            assert claim['origin']['source_run']==45475530525
            assert claim['source_worker_blob']==receipt['blobs'][WORKER]
            assert len(claim['turns'])==2
            for row in claim['turns']:
                assert row['turn'] in ('2d','3d')
                assert set(row['policies'])=={'gto','exp_ip'}
                assert not row['shared_displayed_pairs']
                for mode,policy in row['policies'].items():
                    assert sha((original/(row['turn']+'-'+mode)/'job.json').read_bytes())==policy['job_sha256']
                    assert sha((original/(row['turn']+'-'+mode)/'result.json').read_bytes())==policy['source_sha256']
            assert [claim[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates','positive_distinct_flops')]==[2,2,0,0]
            worker.run(SimpleNamespace(solver=a.solver,output=original,flop=flop,driver=None,preflight=False))
            assert read(original/'proof.json')==claim
            assert all(sha((original/p).read_bytes())==v for p,v in original_hashes.items())
            archive='NL2_B822_R75_'+flop.upper()+'.zip'
            (ev/archive).write_bytes(raw)
            totals=[u+v for u,v in zip(totals,(2,2,0))]
            results.append(dict(flop=flop,run=RUN,job=jid,artifact=aid,sha256=digest,archive=archive,proof=claim,original_file_sha256=original_hashes))
    assert totals==[4,4,0]
    summary=dict(rank=75,source_run=RUN,source_head=HEAD,positive_distinct_flops=0,cert_eligible_ranks=[],
        locked_public_boards=totals[0],joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],
        unchanged_registry_sha256=sha(before),source_artifacts=[x[2] for x in CASES])
    (stage/'nl2_hu_b823_results.json').write_bytes(json_bytes(summary))
    (stage/'nl2_hu_b823_source_receipts.json').write_bytes(json_bytes(receipt))
    (partial/'b823_rank75_heldout_b816_roots.json').write_bytes(json_bytes(dict(result=summary,observations=results)))
    assert registry.read_bytes()==before
    print(json.dumps(summary))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
