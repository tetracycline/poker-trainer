"""B808/B809: archive the original B806/B807 successes without new native solves."""
import argparse,json,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b806_rank230_seven_four as w806
import hu_b807_rank75_heldout_turns as w807

CASES=[
 (45407959432,'a67b43f671eeaa9226caec3fe852c44d1f9b6bda',
  '.github/workflows/nl2-hu-b806-rank230-seven-four.yml','tools/hu_b806_rank230_seven_four.py',
  [(138493670781,'solve (9s7h4s)'),(138493671306,'solve (8s7h4s)')],
  ['Verify J7 suited, its compatible BTN hand and the displayed three-street route','Build the pinned native driver','Solve the original native flop once with two statically legal checked boundaries','Preserve the completed original before turn solves','Solve reachable turns and replay real two-seat strategy checks','Preserve both strategies and all positive and negative source decisions'],
  [(14926577822,'B806-R230-9s7h4s','d5c54c8801f52e99e45534225caf70524ba22d5ae53a786116b1af07970bd944'),(14925708572,'B806-root-R230-9s7h4s','e50f70df35d0bcd2c2802cdb6687604fa72c541db85a29b215d5eb05b3a666c2'),(14927086014,'B806-R230-8s7h4s','33e6d6f995c4617e646da7ec1290534e3444f6a1431948d67ee1cc16ab0228d4'),(14926781734,'B806-root-R230-8s7h4s','804399bb8fc7a956ce6ec7e43dcee3c47bf7c5950cd88887a5177d5dffb0e3ea')]),
 (45408136739,'b2acf2f4d505fd03120d610083c5240ed1a9c909',
  '.github/workflows/nl2-hu-b807-rank75-heldout-turns.yml','tools/hu_b807_rank75_heldout_turns.py',
  [(138494304214,'solve')],
  ['Reconstruct four held-out original jobs and every two-seat reach weight','Build the pinned native driver','Solve the missing conditional games and replay evidence from native output','Preserve original jobs, decisions and range reconstruction'],
  [(14927416136,'B807-R75-9d8d6d','9086fd74f8a54cb3a27d4cb192057367e51d5fa8deb849d7cba1be2fc0db5648')])]
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
    receipts=read(a.archives/'receipt.json')
    assert len(receipts)==2
    results=[]
    with TemporaryDirectory(prefix='b808-b809-') as tmp:
        tmp=Path(tmp)
        for idx,(run,head,wf,worker,jobs,steps,pins) in enumerate(CASES):
            receipt=receipts[idx];assert receipt['run']['head_sha']==head and receipt['run']['id']==run
            paths=[]
            for aid,name,digest in pins:
                raw=(a.archives/(str(aid)+'.zip')).read_bytes()
                assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in receipt['artifacts'])
                dest=tmp/str(aid);dest.mkdir()
                names=unpack_original(raw,dest)
                flop=name.split('-')[-1]
                archive=('NL2_B806_R230_'+flop.upper()+('_ROOT' if '-root-' in name else '')+'.zip') if idx==0 else 'NL2_B807_R75_9D8D6D.zip'
                (ev/archive).write_bytes(raw)
                paths.append((dest,names,dict(artifact=aid,archive=archive,sha256=digest)))
            observations=[]
            if idx==0:
                for i,flop in enumerate(('9s7h4s','8s7h4s')):
                    dest,names,archive=paths[2*i];root,rnames,rootarchive=paths[2*i+1]
                    assert rnames=={'flop/job.json','flop/result.json','root-checkpoint.json'}
                    assert all((root/n).read_bytes()==(dest/n).read_bytes() for n in rnames)
                    hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
                    claim=read(dest/'proof.json')
                    w806.run(SimpleNamespace(solver=a.solver,output=dest,flop=flop,driver=None,preflight=False,root_only=False))
                    actual=read(dest/'proof.json')
                    assert actual==claim and actual['selected'] is None and actual['positive_distinct_flops']==0 and not any(x['common'] for x in actual['turns'])
                    count=[actual[k] for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')]
                    assert count==[0,0,0]
                    assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
                    observations.append(dict(flop=flop,job=jobs[i][0],archives=[archive,rootarchive],native_file_sha256=hashes,proof=claim))
                totals=[0,0,0];rank=230;positive=0
            else:
                dest,names,archive=paths[0]
                hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
                claim=read(dest/'proof.json')
                expected={f'{t}-gto/{n}.json' for t in w807.TURNS for n in ('job','result')}
                expected.update({f'{t}-exp_ip/{n}.json' for t in ('4d','5d') for n in ('job','result')});expected.add('proof.json')
                assert names==expected
                w807.run(SimpleNamespace(solver=a.solver,output=dest,driver=None,preflight=False,rust_source=None,evidence=Path('data/solver_evidence')))
                actual=read(dest/'proof.json')
                assert actual==claim and all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
                assert actual['not_a_certification'] and actual['new_flop_solve_invocations']==0
                assert actual['positive_distinct_flops']==1 and actual['actor_locked_joint_boards']==1
                assert [r['turn'] for r in actual['turns']]==list(w807.TURNS)
                assert [r['turn'] for r in actual['turns'] if r['shared_hands']]==['5d']
                totals=[actual[k] for k in ('locked_public_boards','half_pot_assessed','nonpolarized_candidates')]
                assert totals==[2,1,0]
                rank=75;positive=1
                observations.append(dict(flop='9d8d6d',job=jobs[0][0],archives=[archive],native_file_sha256=hashes,proof=claim))
            batch=808+idx
            result=dict(rank=rank,source_run=run,source_head=head,positive_distinct_flops=positive,cert_eligible_ranks=[],locked_public_boards=totals[0],joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],unchanged_registry_sha256=sha(before),source_artifacts=[x[0] for x in pins])
            (stage/f'nl2_hu_b{batch}_source_receipts.json').write_bytes(json_bytes(receipt))
            (stage/f'nl2_hu_b{batch}_results.json').write_bytes(json_bytes(result))
            (partial/f'b{batch}_rank{rank}_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
            results.append(result)
    assert before==registry.read_bytes()
    print(json.dumps(results))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
