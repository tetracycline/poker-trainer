"""B817: archive the original B816 successes without new native solves."""
import argparse,json,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b816_rank75_new_monotone as w816

CASES=[
 (45475530525,'d66c4fda58e299b4693a26d53511f13895bd996a',
  '.github/workflows/nl2-hu-b816-rank75-new-monotone.yml','tools/hu_b816_rank75_new_monotone.py',
  [(138734624486,'solve (9d8d5d)'),(138734625253,'solve (9d8d7d)')],
  ['Verify original CO donk and BTN call witnesses, monotone UI and both preflop ranges','Build the pinned native solver','Solve each genuinely new full-menu original once','Preserve the completed original before conditional work','Read the saved original and verify both policies at reachable turn decisions','Preserve the conditional jobs and original decisions'],
  [(14960635290,'B816-R75-9d8d5d','aa74052755589eb2bb5d631855771dae820ab7c088867d8de5d8cfcaf3278b60'),
   (14958429151,'B816-root-R75-9d8d5d','4a927a2d2f01f364ab62c169230299f919477ce8d1aa08335c66faed1feb14f5'),
   (14960050484,'B816-R75-9d8d7d','954fee301b6399c381701d43ec9bfff704f1968db32fbe76fe0deadc11ca32c3'),
   (14960185303,'B816-root-R75-9d8d7d','5e812c8b58d3c983af73a995e9029387a14ba24e7412a6c726df69365f71ae8a')])]
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
    with TemporaryDirectory(prefix='b817-') as tmp:
        tmp=Path(tmp)
        for i in range(0,len(pins),2):
            unpacked=[]
            for aid,name,digest in pins[i:i+2]:
                raw=(a.archives/(str(aid)+'.zip')).read_bytes()
                assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in receipt['artifacts'])
                flop=name.split('-')[-1]
                dest=tmp/str(aid);dest.mkdir()
                names=unpack_original(raw,dest)
                archive='NL2_B816_'+('ROOT_' if '-root-' in name else '')+'R75_'+flop.upper()+'.zip'
                (ev/archive).write_bytes(raw)
                hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
                unpacked.append((dest,names,archive,hashes,aid,digest,flop))
            dest,names,archive,hashes,aid,digest,flop=unpacked[0]
            root,root_names,root_archive,root_hashes,root_id,root_digest,root_flop=unpacked[1]
            assert root_flop==flop
            assert {'checkpoint.json','flop/job.json','flop/result.json'}<=root_names
            claim=read(dest/'proof.json')
            assert claim['flop']==flop and claim['rank']==75 and claim['new_flop_solve_invocations']==1
            assert read(root/'checkpoint.json')==claim['origin']
            for n in ('flop/job.json','flop/result.json'):
                assert (root/n).read_bytes()==(dest/n).read_bytes()
            expected={'proof.json','flop/job.json','flop/result.json'}
            for row in claim['turns']:
                for mode in row['policies']:
                    expected.update(row['turn']+'-'+mode+'/'+leaf for leaf in ('job.json','result.json'))
            assert expected<=names
            w816.run(SimpleNamespace(solver=a.solver,output=dest,flop=flop,driver=None,preflight=False,checkpoint_only=False,checkpoint=None))
            actual=read(dest/'proof.json')
            assert actual==claim and actual['positive_distinct_flops']==0 and not any(x['shared_displayed_pairs'] for x in actual['turns'])
            count=[actual[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')]
            assert count==([2,2,0] if flop=='9d8d5d' else [1,1,0])
            totals=[x+y for x,y in zip(totals,count)]
            assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
            assert all(sha((root/n).read_bytes())==h for n,h in root_hashes.items())
            observations.append(dict(flop=flop,job=jobs[i//2][0],archive=archive,artifact=aid,sha256=digest,native_file_sha256=hashes,root_archive=root_archive,root_artifact=root_id,root_sha256=root_digest,root_file_sha256=root_hashes,proof=claim))
    assert totals==[3,3,0]
    result=dict(rank=75,source_run=run,source_head=head,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=totals[0],joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in pins])
    (stage/'nl2_hu_b817_source_receipts.json').write_bytes(json_bytes(receipt))
    (stage/'nl2_hu_b817_results.json').write_bytes(json_bytes(result))
    (partial/'b817_rank75_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
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
