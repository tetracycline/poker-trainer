#!/usr/bin/env python3
"""B49 rank31: independently verify new original Rust GTO+OOP lock for a third
preselected UTG_CO flop, without relabeling any old or new MODEL. The rank31
research cohort was frozen by NL2 frequency in B42 before this run existed.
"""
import gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5
ROOT=pathlib.Path('data')
INDEX=ROOT/'solver_evidence/NL2_MULTIBOARD_B43_UTG_B75.index.json'
ARCHIVE=ROOT/'solver_evidence/NL2_MULTIBOARD_B43_UTG_B75.json.gz'
OUT=ROOT/'nl2_hu_b49_rank31_third_flop_proof.json'
DOC=pathlib.Path('docs/NL2_HU_B49_RANK31_PROOF.md')
def sha(x):return hashlib.sha256(x).hexdigest()
def main():
    idx=json.loads(INDEX.read_text())
    raw=gzip.decompress(ARCHIVE.read_bytes())
    archive=json.loads(raw)
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B43_UTG_B75' and idx['run_id']==44806967313
    assert idx['actual_spot_flop_version_jobs']==2
    assert idx['gto_cases']>=1 and idx['locked_cases']>=1
    assert idx['source_sha256']==sha(raw) and idx['gzip_sha256']==sha(ARCHIVE.read_bytes())
    assert archive['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1' and not archive['errors']
    assert len(archive['artifacts'])==2 and archive['source_run_id']==idx['run_id']
    assert {(a['spot'],a['flop'],a['version']) for a in archive['artifacts']}=={
         ('UTG_CO','9s6h3d','gto'),('UTG_CO','9s6h3d','exp_oop')}
    b42=json.loads((ROOT/'nl2_hu_b42_next6_sourceblind_gaps.json').read_text())
    v3=json.loads((ROOT/'nl2_hu_multiboard_status_v3_rank28.json').read_text())
    rank=json.loads((ROOT/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((ROOT/'nl2_hu_stage2_queue.json').read_text())
    assert b42['source_blind_preselection_ranks']==list(range(27,33))
    chosen=[x for x in b42['rows'] if x['rank']==31]
    assert len(chosen)==1 and chosen[0]['missing_to_three_flops']==1
    r=next(dict(x) for x in rank['nodes'] if x['model_id']==chosen[0]['model_id'])
    model=next(x for x in queue['records'] if x['model_id']==r['model_id'])
    assert r['rank_by_empirically_grounded_frequency_proxy']==31
    assert model['solver_profile']=='UTG_CO' and model['family']=='SRP'
    assert v3['records'][r['model_id']]['label']=='APPROX'
    r['preflop_text']=model['preflop_text']
    r['abstract_action_history']=model['abstract_action_history']
    paths=[pathlib.Path(x) for x in v3['source_evidence']['source_files']]
    assert ARCHIVE not in paths and all(p.is_file() for p in paths)
    exact,locked,_=build_source_index(ROOT,paths+[ARCHIVE])
    sources,reason=candidates(r,exact,locked,None)
    if reason:raise ValueError(reason)
    proofs,why=choose_3_5(sources)
    if why:raise ValueError(why)
    assert len(proofs)==3 and len({p['flop_texture'] for p in proofs})>=2
    assert {x['flop'] for x in proofs}=={'AsKh3d','Ks7h2d','9s6h3d'}
    fresh=[x for x in proofs if x['flop']=='9s6h3d']
    assert len(fresh)==1
    f=fresh[0]
    assert f['actual_exact_action_line']=='b75 c/' and f['source_run_id']==idx['run_id']
    assert f['acting_seat']==0 and f['strict_full_street_combo_reachable']>0
    assert f['relative_spr_error_pct']<=5 and f['genuine_gto_exploitability_pct']<=0.5
    assert f['source_kind']=='PINNED_POKER_SOLVER_PREFLOP_CFR_OFFICIAL' or f['source_kind']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert any(x['run_id']==idx['run_id'] and x['version']=='exp_oop' for x in f['nl2_locked_variants'])
    result=dict(schema='NL2_HU_B49_AUTHENTIC_RANK31_THIRD_BOARD_PROOF_V1',
       current_V3_cert=27,current_V3_approx=365,
       source_blind_B42_rank=31,model_id=r['model_id'],
       original_Rust_run_id=idx['run_id'],verified_archive_sha256=idx['gzip_sha256'],
       real_GTO_and_hero_lock_flops=[dict(flop=p['flop'],turn=p['turn'],
          exact_line=p['actual_exact_action_line'],GTO_run_id=p['source_run_id'],
          GTO_SHA256=p['source_sha256'],
          strict_combo_count=p['strict_full_street_combo_reachable'],
          hero_lock_runs=[v['run_id'] for v in p['nl2_locked_variants']])
          for p in proofs],
       qualifies_for_next_separate_versioned_CERT=True,
       no_generic_class_texture_GTO=True,no_private_combo_pool_frequency_claim=True,
       no_immediate_reclassification=True,never_merge=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B49 | Rank31 third actual GTO + NL2 hero-lock flop\n\n'+
      'Preselected rank31 (UTG_CO, b75-call) now has three real, different matching flop runs.\n'+
      'Fresh genuine pinned source: B43 44806967313 UTG_CO 9s6h3d GTO plus EXP_OOP.\n'+
      'GTO gap <=0.5%, strict legal combo reach >0, source SHA and SPR within 5% verified.\n'+
      'No generic texture GTO, no private-card NL2 measured policy. V3 remains 27/365 pending separate certification.\n'+
      'PR #2 Draft, never merge.\n')
    print(json.dumps({'PASS':True,'rank31':r['model_id'],
      'three_flops':[x['flop'] for x in proofs],
      'new_strict_combos':f['strict_full_street_combo_reachable'],
      'status_CERT':27,'status_APPROX':365},ensure_ascii=False))
if __name__=='__main__':main()
