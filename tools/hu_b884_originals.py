"""B884: archive B882 successful originals despite sibling preflight failure; replay B883 staging. No native invocation or live price change."""
import json,os,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO
from zipfile import ZipFile
from hu_b864_originals import authenticated,read,BRANCH
from hu_b859_limp_boundaries import api
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import sha,json_bytes

HEAD='1cbe1de9d3c6fe806014083830ca2ce1e1762bfe'
RUN=45755111223
AUDIT=45755111059
WF='.github/workflows/nl2-hu-b882-rank29-twotone.yml'
WORKER='tools/hu_b882_rank29_new_twotone.py'
PINS=[
 ('KcTc6h',['2c','3c','4c','7c'],139691797469,15087895864,147563,'18c00ed22da1ccb9ebecc99359c97314ea6c179086398f90c954b23077a65758'),
 ('Qh8h4s',['2h','3h','5h','7h'],139691797719,15088000121,144775,'1a419959dfe334f7fabab081a126ce4f0bb1a32cc1bc29135ce2e72a94cba3a6')]
PRICE_HEAD='5dcca80ea4cd6afa4b846640177cf4cc66b434dc'
PRICE_WORKER='tools/hu_b883_utg_price_candidate.cjs'
PRICE=dict(run=45757586187,audit=45757586169,head=PRICE_HEAD,job=139699744792,artifact=15088826165,size=10000,digest='df0db9b5cfeb92e5a0da9ea282ae99ee1763614c193b80c192eebde5a9953261',name='B883-staged-UTG-price-candidate',workflow='.github/workflows/nl2-hu-b883-utg-price-candidate.yml')
def blob(path,ref=None):
    return subprocess.check_output(['git','rev-parse',ref+':'+path] if ref else ['git','hash-object',path],text=True).strip()
def check_pinned(paths,head):
    for path in paths: assert blob(path)==blob(path,head),path
def main(stage,solver):
    stage=stage.resolve();solver=solver.resolve()
    assert not stage.exists()
    partial=stage/'solver_evidence'/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    before=registry.read_bytes();status=json.loads(before)
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(158,234,0,392)
    priority=json.loads(Path('data/nl2_hu_b838_234_approx_frequency_priority.json').read_bytes())
    assert priority['source_status_git_blob_sha']==blob(str(registry))=='996fc513406c8a1207d50bc300453858909493d9'
    row,=[x for x in priority['rows'] if x['rank']==29]
    assert row['passes_min_0_2_pct_frequency'] and status['records'][row['model_id']]['label']=='APPROX'
    assert priority['current_certified_opportunity_share_pct']==84.700987
    check_pinned([WF,WORKER,'tools/hu_b703_rank29_highcards.py','tools/hu_b703_rank29_routes.cjs'],HEAD)
    run=read(f'actions/runs/{RUN}');audit=read(f'actions/runs/{AUDIT}')
    assert (run['id'],run['head_sha'],run['head_branch'],run['status'],run['conclusion'],run['path'])==(RUN,HEAD,BRANCH,'completed','failure',WF)
    assert (audit['head_sha'],audit['status'],audit['conclusion'],audit['name'])==(HEAD,'completed','success','NL2 full batch audit')
    failure=read('actions/jobs/139691797892')
    assert (failure['run_id'],failure['head_sha'],failure['name'],failure['conclusion'])==(RUN,HEAD,'solve (Jd9d3c)','failure')
    steps={s['name']:s['conclusion'] for s in failure['steps']}
    assert steps['Preflight distinct frozen rank29 textures, exact rendered sizes, original SHA and physical cards']=='failure'
    assert steps['Solve original GTO and authentic matched NL2 partial lock, independent file replay']=='skipped'
    listing=read(f'actions/runs/{RUN}/artifacts')
    assert {a['id'] for a in listing['artifacts']}=={p[3] for p in PINS}
    (partial/'b882_r29_preflight_blocked.json').write_bytes(json_bytes(dict(run=run,audit=audit,job=failure,source_status='BLOCKED_PREFLIGHT_NOT_NATIVE_NOT_ZERO_REACH',flop='Jd9d3c')))
    observations=[]
    for f,turns,j,aid,size,digest in PINS:
        job=read(f'actions/jobs/{j}');meta=read(f'actions/artifacts/{aid}')
        assert (job['run_id'],job['head_sha'],job['name'],job['status'],job['conclusion'])==(RUN,HEAD,f'solve ({f})','completed','success')
        assert all(s['conclusion']=='success' for s in job['steps'])
        assert (meta['id'],meta['name'],meta['digest'],meta['size_in_bytes'],meta['expired'])==(aid,'B882-R29-'+f,'sha256:'+digest,size,False)
        assert (meta['workflow_run']['id'],meta['workflow_run']['head_sha'])==(RUN,HEAD)
        raw=api(f'actions/artifacts/{aid}/zip');assert len(raw)==size and sha(raw)==digest
        with TemporaryDirectory(prefix='b884-r29-') as td:
            d=Path(td);names=unpack_original(raw,d)
            required={'proof.json','rendered-routes.json','original-manifest.json','flop/job.json','flop/result.json'}
            assert names==required,names
            hashes={n:sha((d/n).read_bytes()) for n in names}
            proof=json.loads((d/'proof.json').read_bytes())
            assert (proof['schema'],proof['rank'],proof['model_id'],proof['flop'],proof['line'],proof['actor'])==('NL2_B882_R29_THREE_FROZEN_TWOTONE_ORIGINALS_V1',29,row['model_id'],f,'b50 c/b75 c/',0)
            assert (proof['root_pot'],proof['root_stack'],proof['turn_pot'],proof['turn_stack'],proof['river_pot'],proof['river_stack'],proof['river_spr'])==(250,9900,500,9775,1250,9400,7.52)
            assert proof['root_sha256']==hashes['flop/result.json']
            assert proof['native_file_sha256']=={k:v for k,v in hashes.items() if k!='proof.json'}
            assert [t['turn'] for t in proof['turns']]==turns
            assert all(t['negative_stage']=='ROOT_TWO_SEAT_UI_INTERSECTION_ZERO' and not t['gto_solved'] and not t['actor_locked'] and not t['checks'] and t['root_gate']['legal_river_count']==0 for t in proof['turns'])
            assert all(proof[k]==0 for k in ('positive_distinct_flops','gto_turn_subgames','actor_locked_turn_subgames','gto_half_pot_river_nodes','nl2_half_pot_river_nodes','true_river_pair_candidate_count'))
            for seed in ('23','867'):
                subprocess.run([sys.executable,WORKER,'--solver',str(solver),'--flop',f,'--output',str(d)],check=True,env=dict(os.environ,PYTHONHASHSEED=seed))
                assert all(sha((d/n).read_bytes())==v for n,v in hashes.items())
        name='NL2_B882_R29_'+f.upper()+'.zip'
        (partial.parent/name).write_bytes(raw)
        (partial/('b882_r29_'+f+'_receipts.json')).write_bytes(json_bytes(dict(run=run,audit=audit,job=job,artifact=meta)))
        observations.append(dict(flop=f,archive=name,archive_sha256=digest,artifact=aid,member_sha256=hashes,proof=proof))
    check_pinned([PRICE['workflow'],PRICE_WORKER],PRICE_HEAD)
    raw,files,receipts=authenticated(PRICE)
    assert set(files)=={'nl2_hu_model.candidate.js','report.json'}
    report=json.loads(files['report.json'])
    assert report['candidate_only'] and report['active_registry_unchanged'] and report['unchanged_other_model_nodes']==388
    assert sorted(r['rank'] for r in report['changed'])==[68,157,158,205]
    assert len(report['existing_rank68_certificates'])==3
    assert report['candidate_sha256']==sha(files['nl2_hu_model.candidate.js'])
    assert report['original_sha256']==sha(Path('nl2_hu_model.js').read_bytes())
    with TemporaryDirectory(prefix='b884-price-') as td:
        for suffix in ('a','b'):
            out=Path(td)/suffix
            subprocess.run(['node',PRICE_WORKER,str(out)],check=True)
            assert {p.name:p.read_bytes() for p in out.iterdir()}==files
    (partial.parent/'NL2_B883_UTG_PRICE_STAGED.zip').write_bytes(raw)
    (partial/'b883_price_receipts.json').write_bytes(json_bytes(receipts))
    (partial/'b883_price_staged_report.json').write_bytes(files['report.json'])
    result=dict(schema='NL2_B884_R29_ORIGINALS_AND_PRICE_STAGE_V1',source_run=RUN,source_audit=AUDIT,successful_original_flops=2,root_boundary_tests=8,positive_flops=0,preflight_blocked_flops=1,preflight_blocked_not_zero_reach=True,price_stage_replayed=True,price_stage_live_publication=False,cert_promotions=0,native_repeated=0,formal_new_lock_variants=0,formal_new_nonpolarized=0,model_node_opportunity_coverage_pct=priority['current_certified_opportunity_share_pct'],unchanged_registry_sha256=sha(before),scope='Rank29 exact tested root boundaries only; no turn/river solve or joint reach certificate. Rank68 original certificate records unchanged; staging is not live publication.')
    (partial/'b884_rank29_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    (stage/'nl2_hu_b884_results.json').write_bytes(json_bytes(result))
    assert registry.read_bytes()==before
    print(json.dumps(result))
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
