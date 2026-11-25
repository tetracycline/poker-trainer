"""B878: authenticate B877 native originals and incomplete B876 receipts. No solver reruns."""
import json,os,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from hu_b864_originals import authenticated,read,BRANCH
from hu_b859_limp_boundaries import api
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import sha,json_bytes

HEAD='c17a0d254cfad9da8ee1b53b098baf7f941be0de'
RUN=45721198494
AUDIT=45721198403
WF='.github/workflows/nl2-hu-b877-rank57-new-originals.yml'
WORKER='tools/hu_b877_rank57_new_originals.py'
PINS=[
 ('Kh5s5d',['2c','3h','7s'],139579670250,15072163235,671365,'1a3f8bc004187ceb1e4ea83b358510ef96c1732fba27ff33c8ee91322181e642'),
 ('Ts6h6d',['3c','4s','8h'],139579670793,15072352695,745938,'118d0d14fd4aa244901745e65b64c9aa40f065da39cb516ab700cd84cb1f7e0a')]
CANCEL_HEAD='3e10f29814ec2872ad95185beadbf759e3b85c16'
CANCEL_RUN=45721122214
CANCEL_AUDIT=45721122046
CANCEL_PINS=[
 ('Jh9d5c',139579411195,15073073572,'d7de2b7d45d110f620cd9f888d903c412cf940490c7e32ed0a9298d32072427e'),
 ('Ts8d4c',139579411550,15073342745,'a946d083c30a8220bbf3ac7cfec904216aab255b56dac4db85de30e9860a25d2')]
def blob(path,ref=None):
    cmd=['git','rev-parse',ref+':'+path] if ref else ['git','hash-object',path]
    return subprocess.check_output(cmd,text=True).strip()

def main(stage,solver):
    stage=stage.resolve();solver=solver.resolve()
    assert not stage.exists()
    partial=stage/'solver_evidence'/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    before=registry.read_bytes();status=json.loads(before)
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(158,234,0,392)
    priority=json.loads(Path('data/nl2_hu_b838_234_approx_frequency_priority.json').read_bytes())
    assert priority['source_status_git_blob_sha']==blob(str(registry))=='996fc513406c8a1207d50bc300453858909493d9'
    assert priority['current_certified_opportunity_share_pct']==84.700987
    row,=[x for x in priority['rows'] if x['rank']==57]
    assert row['passes_min_0_2_pct_frequency'] and status['records'][row['model_id']]['label']=='APPROX'
    for path in (WF,WORKER,'tools/hu_b664_rank57_bottom_pair.py','tools/hu_b637_rank57.py'):
        assert blob(path)==blob(path,HEAD)
    observations=[]
    for f,turns,job,aid,size,digest in PINS:
        pin=dict(run=RUN,audit=AUDIT,head=HEAD,job=job,artifact=aid,size=size,digest=digest,name='B877-R57-'+f,workflow=WF)
        raw,files,receipts=authenticated(pin)
        assert receipts['job']['name']==f'solve ({f})'
        assert all(s['conclusion']=='success' for s in receipts['job']['steps'])
        proof=json.loads(files['proof.json'])
        assert (proof['schema'],proof['rank'],proof['model_id'],proof['flop'],proof['line'])==('NL2_B877_R57_TWO_FRESH_LOW_PAIRED_ORIGINALS_V1',57,row['model_id'],f,'x b50 c/b75 c/')
        assert (proof['actual_river_pot_bb'],proof['actual_river_effective_stack_bb'])==(30,85)
        assert proof['new_certifications']==0 and proof['genuine_original_flop']
        assert [t['turn'] for t in proof['turns']]==turns and not any(t['checks'] for t in proof['turns'])
        names={'proof.json','flop/job.json','flop/result.json'}
        for t in proof['turns']:
            for mode in ('gto','exp_oop') if t['paired_policies'] else ('gto',):
                names|={t['turn']+'-'+mode+'/'+n for n in ('job.json','result.json')}
        assert set(files)==names
        hashes={n:sha(v) for n,v in files.items()}
        with TemporaryDirectory(prefix='b878-') as td:
            d=Path(td)
            assert unpack_original(raw,d)==names
            for seed in ('23','867'):
                subprocess.run([sys.executable,WORKER,'--solver',str(solver),'--flop',f,'--output',str(d)],check=True,env=dict(os.environ,PYTHONHASHSEED=seed))
                assert all(sha((d/n).read_bytes())==v for n,v in hashes.items())
        name='NL2_B877_R57_'+f.upper()+'.zip'
        (partial.parent/name).write_bytes(raw)
        (partial/('b877_r57_'+f+'_receipts.json')).write_bytes(json_bytes(receipts))
        observations.append(dict(flop=f,archive=name,archive_sha256=digest,artifact=aid,member_sha256=hashes,proof=proof,
             gto_turns=len(turns),paired_nl2_turns=sum(t['paired_policies'] for t in proof['turns']),common_displayed_public_boards=0))
    run=read(f'actions/runs/{CANCEL_RUN}');audit=read(f'actions/runs/{CANCEL_AUDIT}')
    assert (run['head_sha'],run['head_branch'],run['status'],run['conclusion'])==(CANCEL_HEAD,BRANCH,'completed','cancelled')
    assert (audit['head_sha'],audit['status'],audit['conclusion'])==(CANCEL_HEAD,'completed','success')
    cancellations=[]
    for f,j,aid,digest in CANCEL_PINS:
        job=read(f'actions/jobs/{j}');meta=read(f'actions/artifacts/{aid}')
        assert (job['run_id'],job['head_sha'],job['name'],job['conclusion'])==(CANCEL_RUN,CANCEL_HEAD,f'solve ({f})','cancelled')
        assert any(s['name']=='Solve the missing river trees and replay both policies' and s['conclusion']=='cancelled' for s in job['steps'])
        assert (meta['name'],meta['digest'],meta['size_in_bytes'])==('B876-R114-'+f,'sha256:'+digest,849)
        assert meta['workflow_run']['id']==CANCEL_RUN and meta['workflow_run']['head_sha']==CANCEL_HEAD
        raw=api(f'actions/artifacts/{aid}/zip')
        assert len(raw)==849 and sha(raw)==digest
        with TemporaryDirectory(prefix='b878-cancel-') as td:
            names=unpack_original(raw,Path(td))
            # Do not infer zero reach or complete root from cancelled jobs.
            assert names
        name='NL2_B876_R114_'+f.upper()+'_INCOMPLETE.zip'
        (partial.parent/name).write_bytes(raw)
        cancellations.append(dict(flop=f,job=job,artifact=meta,archive=name,members=sorted(names),status='BLOCKED_INCOMPLETE_NATIVE_JOB_NOT_ZERO_REACH'))
    (partial/'b876_r114_cancelled_receipts.json').write_bytes(json_bytes(dict(run=run,audit=audit,workers=cancellations)))
    result=dict(schema='NL2_HU_B878_R57_ORIGINALS_AND_R114_INCOMPLETE_V1',
       source_run=RUN,source_audit=AUDIT,source_head=HEAD,rank57_distinct_original_flops=2,
       rank57_gto_turns=sum(x['gto_turns'] for x in observations),
       rank57_paired_nl2_turns=sum(x['paired_nl2_turns'] for x in observations),
       rank57_positive_distinct_flops=0,rank114_cancelled_workers=2,
       cert_promotions=0,native_repeated=0,formal_new_lock_variants=0,formal_new_nonpolarized=0,
       model_node_opportunity_coverage_pct=priority['current_certified_opportunity_share_pct'],
       unchanged_registry_sha256=sha(before),
       scope='Only these preregistered turns and paired river extracts; a GTO failure may skip NL2 lock. Rank114 cancellation is incomplete evidence, not a negative reach result.')
    (partial/'b878_rank57_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    (stage/'nl2_hu_b878_results.json').write_bytes(json_bytes(result))
    assert registry.read_bytes()==before
    print(json.dumps(result))
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
