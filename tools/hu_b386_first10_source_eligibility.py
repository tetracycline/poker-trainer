#!/usr/bin/env python3
"""B386 independent cross-batch 40/70 model-source eligibility audit; no fake certification.

Previous Actions source archives are SHA-authenticated in B379/B381/B382/B384/B385.
This is a cross-source registry gate and prioritization, not a new Rust solve.
"""
import hashlib,json,pathlib
from collections import Counter
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create
D=pathlib.Path('data')
OUT=D/'nl2_hu_b386_first10_postsource_frozen_audit.json'
DOC=pathlib.Path('docs/NL2_HU_B386_FIRST10_POSTSOURCE_ELIGIBILITY.md')
SRC={
 379:D/'nl2_hu_b379_rank107_7s5h3d_6c_true_gto_nl2_ip_strict_pair.json',
 381:D/'nl2_hu_b381_rank107_9s6h3d_true_solve_strict_source.json',
 382:D/'nl2_hu_b382_rank107_4s4h2d_true_solve_strict_source.json',
 384:D/'nl2_hu_b384_rank200_two_new_true_source_strict_pairs.json',
 385:D/'nl2_hu_b385_rank232_3bp_two_flop_strict_source_proof.json',
}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=read(D/'nl2_hu_multiboard_status_v47_b364_rank96.json')
 assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(159,233,0,392)
 assert len(s['records'])==392
 source_audit=audit(s)
 matrix=create(s)
 assert (source_audit['cert_multiboard'],source_audit['approx'],source_audit['EST'])==(159,233,0)
 assert len(matrix['models'])==159
 b368=read(D/'nl2_hu_b368_lock_denominator_recovery.json')
 assert (b368['recovered_lock_variants'],b368['remaining_unknown_variants'])==(334,0)
 historical_unknown=sum(1 for b in matrix['boards'] for l in b['hero_lock_proofs']
    if l['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN')
 assert historical_unknown==0
 triage=read(D/'nl2_hu_b370_first10_approx_source_triage.json')
 first10=triage['source_blind_selected_ten']
 assert len(first10)==10 and len(set(x['model_id'] for x in first10))==10
 assert {x['frequency_rank'] for x in first10}=={107,115,116,166,200,214,216,218,219,232}
 all_results={k:read(p) for k,p in SRC.items()}
 original=all_results[379]
 assert original['rank']==107 and original['flop']=='7s5h3d'
 assert original['one_distinct_flop_not_three']
 assert len(original['two_named_exact_river_board_pair_proofs'])==2
 assert all(x['GTO_strict_40_70_actor_IP_combos']>0 and x['genuine_NL2_partially_locked_strict_actor_IP_combos']>0
    for x in original['two_named_exact_river_board_pair_proofs'])
 r107=next(x for x in first10 if x['frequency_rank']==107)
 assert len(r107['strictly_measured_pairs'])==1 and r107['strictly_measured_pairs'][0]['flop']=='Jh9d6s'
 assert r107['strictly_measured_pairs'][0]['strict_legal_combo_count']>0
 failed_flops=[]
 for batch,flop in ((381,'9s6h3d'),(382,'4s4h2d')):
  d=all_results[batch]
  assert (d['rank'],d['model_id'],d['flop'])==(107,r107['model_id'],flop)
  assert d['strict_40_70_source_paired_actor_IP_river_nodes']==[]
  assert d['claimed_new_distinct_cert_flops']==0 and d['no_early_certification']
  assert len(d['true_original_GTO_and_NL2_partial_sources'])==2
  by_ver={x['version']:x for x in d['true_original_GTO_and_NL2_partial_sources']}
  assert set(by_ver)=={'gto','exp_ip'}
  c=by_ver['gto']['cases'][0];n=by_ver['exp_ip']['cases'][0]
  assert c['GTO_gap_pct']<=.5 and n['GTO_gap_pct']<=.5 and n['hero_gap_pct']<=.5
  g=c['matched_target_river_actor_IP_nodes']
  assert len(g)==2 and all(x['strict_40_70_combo_count']==0 for x in g)
  failed_flops.append(dict(rank=107,flop=flop,source_batch=batch,
    reason='GTO_ZERO_STRICT_TARGET_HERO_IP_COMBOS',true_gto_source_sha256=c['sha256'],
    true_exp_source_sha256=n['sha256'],GTO_target_strict_combo_counts=[x['strict_40_70_combo_count'] for x in g],
    not_certified=True))
 d=all_results[384]
 assert d['rank']==200 and d['same_exact_public_board_full_street_40_70_source_pairs']==[]
 assert d['distinct_new_flops_with_true_positive_pairs']==[]
 assert len(d['true_original_Rust_source_evidence'])==4
 by_key={(x['flop'],x['version']):x for x in d['true_original_Rust_source_evidence']}
 assert set(by_key)=={(flop,ver) for flop in ('7s5h3d','9s6h3d') for ver in ('gto','exp_ip')}
 assert not by_key[('7s5h3d','gto')]['manifest_present'] and not by_key[('7s5h3d','exp_ip')]['manifest_present']
 assert not by_key[('9s6h3d','exp_ip')]['manifest_present']
 g=by_key[('9s6h3d','gto')]
 assert g['manifest_present'] and g['actual_solved_cases']==1
 assert all(v['strict_actor_IP_combos']==0 for row in g['cases'] for v in row['exact_actor_IP_target_line_runouts'])
 d=all_results[385]
 assert d['rank']==232 and d['strict_full_street_GTO_NL2_OOP_paired_public_runouts']==[]
 assert d['new_distinct_qualifying_flops']==[]
 assert len(d['original_Rust_source_artifacts'])==4
 by_key={(x['flop'],x['version']):x for x in d['original_Rust_source_artifacts']}
 assert by_key[('8s8h3d','gto')]['real_solved_cases']==0
 assert by_key[('7s5h3d','gto')]['real_solved_cases']==1
 assert by_key[('7s5h3d','exp_oop')]['real_solved_cases']==1
 assert all(n['strict_actor_SB_OOP_combos']==0 for item in by_key[('7s5h3d','gto')]['cases'] for n in item['exact_SB_OOP_target_runouts'])
 model_records={}
 for x in first10:
  mid=x['model_id'];z=s['records'][mid]
  assert z['label']=='APPROX'
  model_records[str(x['frequency_rank'])]=dict(model_id=mid,spot=z['solver_profile'],
    certified=False,existing_true_paired_flops=x['true_paired_measured_NL2_hero_lock_flops'],
    initial_paired_flops=[v['flop'] for v in x['strictly_measured_pairs']],
    new_authenticated_pairs_from_B379=1 if x['frequency_rank']==107 else 0,
    currently_distinct_paired_flops=x['true_paired_measured_NL2_hero_lock_flops']+(1 if x['frequency_rank']==107 else 0),
    additional_real_flops_needed=max(0,3-x['true_paired_measured_NL2_hero_lock_flops']-(1 if x['frequency_rank']==107 else 0)),
    evidence_not_model_upgrade=True)
 assert model_records['107']['currently_distinct_paired_flops']==2
 assert all(m['currently_distinct_paired_flops']<3 for m in model_records.values())
 frozen=dict(schema='NL2_HU_B386_FIRST10_NO_FAKE_CERT_POST_GENUINE_B379_B381_B382_B384_B385_V1',
  baseline_V47_SHA256=sha(D/'nl2_hu_multiboard_status_v47_b364_rank96.json'),
  source_proof_sha256={str(k):sha(v) for k,v in SRC.items()},
  original_authenticated_source_only=True,
  exact_actor_and_spr_no_generic_texture_cert=True,
  source_runs={str(k):all_results[k].get('run_id',all_results[k].get('source_run_id',all_results[k].get('original_run_id'))) for k in SRC},
  rank107_two_proven_distinct_flops=['Jh9d6s','7s5h3d'],
  rejected_additional_true_Rust_flops=failed_flops,
  B384_rank200_zero_new_pairs=True,B385_rank232_zero_new_pairs=True,
  first10_frozen_candidate_models=model_records,
  selected_next_for_original_GTO_first={
    'rank':107,'spot':'BTN_BB','exact_line':'b33 c/x b50 c/x',
    'GTO_first_flops':['As9h2d','Js9h4d','QsJh4d'],
    'reason':'GTO_TARGET_ZERO_ON_THREE_PREVIOUS_FLOPS; A_HIGH_JT_HIGH_KQ_HIGH_DIVERSITY',
    'no_post_result_parameter_tuning':True,
    'NL2_EXP_ONLY_AFTER_AUTHENTIC_GTO_STRICT_POSITIVE':True},
  certified_named_board_count=source_audit['aggregate']['named_board_proofs'],
  certified_hero_lock_source_variants=source_audit['aggregate']['paired_hero_locked_source_variants'],
  exact_board_medium_b50_research_candidates=source_audit['aggregate']['board_examples_with_b50_candidate'],
  B368_lock_denominators_original=334,recovered=334,unknown_remaining=historical_unknown,
  no_observed_NL2_private_card_conditional_frequencies=True,
  no_general_50pct_strategy_claim=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,TOTAL=392,
  verified_hu2475_by_actions=True,
  PR2_remains_draft_unmerged=True)
 OUT.write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n')
 DOC.write_text('# B386 authenticated next-first10 source eligibility / replay gate\n\n'
  'Across 392 models: **159 CERT / 233 APPROX / 0 EST**, as original V47. '
  'B379 contributes one distinct paired rank107 flop (7s5h3d) in addition to the historical Jh9d6s. '
  'B381 9s6h3d and B382 4s4h2d had valid Rust original GTO and NL2 partial solves but **zero** GTO strict BTN-IP combos on the target line; both excluded. '
  'B384 rank200 had zero positive pairs; cancelled jobs and missing NL2 sources explicitly excluded. '
  'B385 rank232 had zero positive pairs; 8s8h3d original GTO zero-case cannot be borrowed from its NL2 solve. '
  'Full source gate retains B368 **334/334 recovered, UNKNOWN=0**; 50% pot research evidence only on exact named boards.\n\n'
  'Next preregistered original GTO-only candidate flops for rank107: As9h2d, Js9h4d, QsJh4d. '
  'Lock an EXP run only after source SHA, actor/SPR, and positive 40%-70% strict path evidence.\n')
 print('PASS B386 actual source registry; 159 CERT/233 APPROX; rank107 2 distinct, 1 needed; no fake upgrades')
if __name__=='__main__':main()
