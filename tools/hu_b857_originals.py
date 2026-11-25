"""B857: preserve three completed original native jobs and isolate the cancelled sibling. No native driver."""
import argparse,json,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from io import BytesIO
from hu_b805_original import api
from hu_b738_collect import job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha

BRANCH='fix/nl2-hu-lines-audit-20261118'
SOURCES=[
 (45589898657,'c871e745c597081c24a7509e085bf859d0322aa3','.github/workflows/nl2-hu-b854-rank109-broadway.yml','tools/hu_b854_rank109_broadway.py',109,'success',[
 ('AcQcJc',139120988553,15010447166,'e048ffbe0b302df533ceb3ceebb255f111834ed355af49fee613eb6c203ec201','success',(0,16,0,0)),
 ('KdJdTd',139120988470,15009573704,'6c3a2a19b82e4591aad7eef4fd10b747b699146569b92a403824502494e0112b','success',(0,0,0,0))]),
 (45590176466,'d6eb1f58584dda04b3ed40bfcf7dd4648f37e83a','.github/workflows/nl2-hu-b856-rank114-midhigh.yml','tools/hu_b856_rank114_midhigh.py',114,'cancelled',[
 ('Th5d2c',139121985503,15011744107,'7378184b15fffab6db9224c16a27d778738ee9d36bf9b56c839f32be6dd04b31','success',(1,16,15,5)),
 ('Jh8d6c',139121985196,15012482543,'152df3c7ced2321286dbdc2accbe5469b086a3ba046f6fceb35b0223907bbf4f','cancelled',None)])]
STEPS={109:['Build pinned native solver','Gate fresh original, solve and replay actual same two-seat pairs','Run actions/upload-artifact@v4'],
114:['Check the original ranges, branch prices and displayed middle pairs','Compile the pinned native solver','Solve the missing river trees and replay both policies','Run actions/upload-artifact@v4']}
ORIGINAL=14600026283
def read(path):return json.loads(path.read_bytes())
def get(path):return json.loads(api(path))
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    rec=[]
    for rid,head,wf,worker,rank,conclusion,pins in SOURCES:
        ep=f'actions/runs/{rid}';r=get(ep)
        assert (r['id'],r['head_sha'],r['head_branch'],r['path'],r['status'],r['conclusion'],r['run_attempt'])==(rid,head,BRANCH,wf,'completed',conclusion,1)
        assert r['repository']['full_name']=='tetracycline/poker-trainer' and r['repository']['id']==1438346845
        run={k:r[k] for k in ('id','head_sha','head_branch','path','status','conclusion','run_attempt')}
        jobs=get(ep+'/jobs?per_page=100');arts=get(ep+'/artifacts?per_page=100')
        assert jobs['total_count']==arts['total_count']==len(pins)
        blobs={}
        for f in (wf,worker):
            pin=get('contents/'+f+'?ref='+head)['sha']
            assert subprocess.check_output(['git','hash-object',f],text=True).strip()==pin
            blobs[f]=pin
        for flop,jid,aid,digest,state,expected in pins:
            j,=[x for x in jobs['jobs'] if x['id']==jid]
            assert (j['id'],j['run_id'],j['head_sha'],j['name'],j['status'],j['conclusion'])==(jid,rid,head,'solve ('+flop+')','completed',state)
            if state=='success':job=job_receipt(j,run,jid,'solve ('+flop+')',STEPS[rank])
            else:
                job={k:j[k] for k in ('id','run_id','head_sha','name','status','conclusion','steps')}
                assert any(s['conclusion']=='cancelled' for s in job['steps'])
            a,=[x for x in arts['artifacts'] if x['id']==aid]
            a=artifact_receipt(a,run,aid,('B854-R109-' if rank==109 else 'B856-R114-')+flop,digest)
            raw=api(f'actions/artifacts/{aid}/zip')
            assert sha(raw)==digest and len(raw)==a['size_in_bytes']
            (folder/f'{aid}.zip').write_bytes(raw)
            rec.append(dict(rank=rank,flop=flop,run=run,job=job,artifact=a,source_blobs=blobs))
    m=get(f'actions/artifacts/{ORIGINAL}')
    raw=api(f'actions/artifacts/{ORIGINAL}/zip')
    assert sha(raw)=='7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e'
    (folder/f'{ORIGINAL}.zip').write_bytes(raw)
    (folder/f'{ORIGINAL}.json').write_bytes(json_bytes(m))
    (folder/'receipt.json').write_bytes(json_bytes(rec))

def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    status=json.loads(before)
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['TOTAL'])==(158,234,392)
    priority=read(Path('data/nl2_hu_b838_234_approx_frequency_priority.json'))
    assert priority['source_status_git_blob_sha']==subprocess.check_output(['git','hash-object',str(registry)],text=True).strip()
    assert all(status['records'][r['model_id']]['label']=='APPROX' for r in priority['rows'] if r['rank'] in (109,114))
    rec=read(a.archives/'receipt.json');assert len(rec)==4
    observations=[];quarantine=[]
    with TemporaryDirectory(prefix='b857-') as tmp:
        for rid,head,wf,worker,rank,conclusion,pins in SOURCES:
            for flop,jid,aid,digest,state,expected in pins:
                row,=[x for x in rec if x['artifact']['id']==aid]
                assert (row['rank'],row['flop'],row['run']['id'],row['job']['id'],row['job']['conclusion'])==(rank,flop,rid,jid,state)
                raw=(a.archives/f'{aid}.zip').read_bytes()
                assert sha(raw)==digest
                dest=Path(tmp)/str(aid);dest.mkdir()
                names=unpack_original(raw,dest)
                hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
                if state!='success':
                    assert 'proof.json' not in names
                    quarantine.append(dict(rank=rank,flop=flop,artifact=aid,sha256=digest,files=hashes,status='CANCELLED_NOT_CERT_NOT_REPLAYED'))
                    continue
                claim=read(dest/'proof.json')
                assert claim['native_files']=={k:v for k,v in hashes.items() if k!='proof.json'}
                args=[sys.executable,worker,'--solver',str(a.solver.resolve()),'--output',str(dest),'--flop',flop]
                if rank==114:args+=['--receipts',str(a.archives.resolve())]
                subprocess.run(args,check=True)
                actual=read(dest/'proof.json')
                assert actual==claim and actual['flop']==flop and actual['rank']==rank
                assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
                lock='locked_public_boards' if rank==109 else 'native_locked_public_boards'
                counts=tuple(actual[k] for k in ('positive_distinct_flops',lock,'joint_halfpot_assessed','nonpolarized_candidates'))
                assert counts==expected
                if counts[0]:
                    selected=actual['selected']
                    assert selected['physical_pair'] and selected['flop']==flop and len(set(sum(selected['physical_pair'],[])))==4
                else:assert actual['selected'] is None
                name=f'NL2_B{854 if rank==109 else 856}_R{rank}_{flop.upper()}.zip'
                (ev/name).write_bytes(raw)
                observations.append(dict(rank=rank,flop=flop,archive=name,artifact=aid,archive_sha256=digest,native_file_sha256=hashes,counts=counts,proof=actual))
    result=dict(source_runs=[45589898657,45590176466],cert_promotions=0,positive_distinct_flops_by_rank={'109':0,'114':1},
        locked_public_boards=sum(o['counts'][1] for o in observations),joint_halfpot_assessed=sum(o['counts'][2] for o in observations),
        halfpot_candidates=sum(o['counts'][3] for o in observations),native_repeated=0,unchanged_registry_sha256=sha(before),
        model_node_opportunity_coverage_pct=priority['current_certified_opportunity_share_pct'],cancelled_sources=quarantine)
    assert len(observations)==3 and len(quarantine)==1
    (stage/'nl2_hu_b857_results.json').write_bytes(json_bytes(result))
    (stage/'nl2_hu_b857_source_receipts.json').write_bytes(json_bytes(rec))
    (partial/'b857_b854_b856_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    assert before==registry.read_bytes()
    print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archives',type=Path,required=True);p.add_argument('--solver',type=Path);p.add_argument('--output',type=Path);p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
