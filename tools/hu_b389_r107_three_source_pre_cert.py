#!/usr/bin/env python3
"""B389 source-only three-distinct-flop readiness gate for rank107.
Never upgrades registry without next independent original-source/matrix/UI gate.
"""
import hashlib,json,pathlib
D=pathlib.Path('data')
OUT=D/'nl2_hu_b389_rank107_three_true_flop_pre_cert_gate.json'
DOC=pathlib.Path('docs/NL2_HU_B389_RANK107_THREE_SOURCE_PRE_CERT.md')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=read(D/'nl2_hu_multiboard_status_v47_b364_rank96.json')
 assert (s['schema'],s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(
  'NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96',159,233,0,392)
 model='ln-ipfr-r_model-ujl14x'
 m=s['records'][model]
 assert (m['frequency_rank'],m['solver_profile'],m['family'],m['street'],m['label'])==(
  107,'BTN_BB','SRP',2,'APPROX')
 assert abs(m['assumed_model_node_spr']-4.968)<1e-6
 t=read(D/'nl2_hu_b370_first10_approx_source_triage.json')
 r=next(x for x in t['source_blind_selected_ten'] if x['frequency_rank']==107)
 assert r['model_id']==model and r['true_paired_measured_NL2_hero_lock_flops']==1
 old=r['strictly_measured_pairs']
 assert len(old)==1 and old[0]['flop']=='Jh9d6s'
 assert old[0]['strict_legal_combo_count']>0
 assert old[0]['exact_line']=='b33 c/x b50 c/x'
 assert old[0]['gto_source_run_id']>0 and old[0]['nl2_hero_lock_run_id']>0
 assert len(old[0]['gto_source_sha256'])==len(old[0]['nl2_hero_lock_sha256'])==64
 assert abs(old[0]['actual_spr']-m['assumed_model_node_spr'])/old[0]['actual_spr']<=.05
 previous=read(D/'nl2_hu_b379_rank107_7s5h3d_6c_true_gto_nl2_ip_strict_pair.json')
 assert previous['model_id']==model and previous['rank']==107 and previous['flop']=='7s5h3d'
 assert previous['spot']=='BTN_BB' and previous['one_distinct_flop_not_three']
 b379=previous['two_named_exact_river_board_pair_proofs']
 assert len(b379)==2
 for row in b379:
  assert row['exact_hero_actor']=='BTN_IP' and row['exact_history']=='b33 c/x b50 c/x'
  assert row['GTO_strict_40_70_actor_IP_combos']>0 and row['genuine_NL2_partially_locked_strict_actor_IP_combos']>0
  assert abs(row['actual_SPR']-m['assumed_model_node_spr'])/row['actual_SPR']<=.05
 g=previous['genuine_original_full_flop_GTO_and_NL2_hero_IP_sources']
 assert set(g)=={'gto','exp_ip'}
 for v in g.values():
  assert v['source_run_id']==45017142943 and len(v['original_flop_source_sha256'])==64
  assert len(v['genuine_turn_river_source_sha256'])==64
  assert v['gto_gap_pct']<=.5
 assert g['exp_ip']['hero_gap_pct']<=.5 and g['gto']['hero_gap_pct'] is None
 current=read(D/'nl2_hu_b388_rank107_qsjh4d_real_gto_nl2_ip_pair.json')
 assert current['schema']=='NL2_HU_B388_RANK107_GENUINE_GTO_AND_ACTUAL_NL2_IP_QSJH4D_PARTIAL_V1'
 assert current['model_id']==model and current['rank']==107
 assert (current['flop'],current['turn'],current['spot'],current['actor'])==('QsJh4d','7s','BTN_BB','BTN_IP')
 assert current['exact_history']=='b33 c/x b50 c/x'
 assert current['source_run_B387_GTO']==45023132316 and current['source_run_B388_EXP']>0
 assert current['original_GTO_source']['original_flop_SHA256']=='f60ffafdea6058eb23ac0f314be28eac14d4ff97e5ac8c92faf2e84a031c2bcf'
 assert current['original_GTO_source']['subgames'][0]['original_subgame_SHA256']=='ebfd419f66fcbeca371b4542e57838474d404f1ab566c01c607192ddb80337b7'
 assert current['real_NL2_partial_source'] is not None
 assert current['real_NL2_partial_source']['genuine_Rust_solved_cases']==1
 assert not current['real_NL2_partial_source']['failures']
 assert current['real_NL2_partial_source']['subgames'][0]['gto_gap_pct']<=.5
 assert current['real_NL2_partial_source']['subgames'][0]['hero_gap_pct']<=.5
 assert current['partial_lock_is_NL2_pool_marginal_proxy_not_private_hand_observation']
 b388=current['exact_paired_legal_river_nodes']
 assert b388,'No authenticated new QsJh4d original GTO+NL2 legal pair; rank107 stays APPROX'
 for row in b388:
  assert row['flop']=='QsJh4d' and row['turn']=='7s'
  assert row['actor']=='BTN_IP' and row['exact_line']=='b33 c/x b50 c/x'
  assert row['GTO_strict_40_70_combos']>0 and row['NL2_IP_strict_40_70_combos']>0
  assert row['original_GTO_sha256']=='ebfd419f66fcbeca371b4542e57838474d404f1ab566c01c607192ddb80337b7'
  assert len(row['new_actual_partial_NL2_sha256'])==64
  assert abs(row['original_GTO_SPR']-row['partial_NL2_SPR'])<1e-5
  assert abs(row['original_GTO_SPR']-m['assumed_model_node_spr'])/row['original_GTO_SPR']<=.05
 distinct=['Jh9d6s','7s5h3d','QsJh4d']
 assert len(set(distinct))==3
 assert {old[0]['flop'],previous['flop'],current['flop']}==set(distinct)
 r388_sha=sha(D/'nl2_hu_b388_rank107_qsjh4d_real_gto_nl2_ip_pair.json')
 out=dict(schema='NL2_B389_RANK107_THREE_TRUE_GTO_NL2_SOURCES_INDEPENDENT_PRE_CERT_V1',
  parent_status_sha256=sha(D/'nl2_hu_multiboard_status_v47_b364_rank96.json'),
  B370_first10_prior_source_sha256=sha(D/'nl2_hu_b370_first10_approx_source_triage.json'),
  B379_true_pair_sha256=sha(D/'nl2_hu_b379_rank107_7s5h3d_6c_true_gto_nl2_ip_strict_pair.json'),
  B388_true_pair_sha256=r388_sha,
  frozen_source_flops=distinct,distinct_verified_original_GTO_and_NL2_hero_lock_flops=3,
  selected_exact_named_boards=[
   dict(flop='Jh9d6s',board=old[0]['exact_public_board'],GTO_source_sha256=old[0]['gto_source_sha256'],
        NL2_hero_lock_source_sha256=old[0]['nl2_hero_lock_sha256'],GTO_run_id=old[0]['gto_source_run_id']),
   dict(flop='7s5h3d',board=b379[0]['exact_public_board'],
        GTO_source_sha256=g['gto']['genuine_turn_river_source_sha256'],
        NL2_hero_lock_source_sha256=g['exp_ip']['genuine_turn_river_source_sha256'],
        GTO_run_id=45017142943),
   dict(flop='QsJh4d',board=sorted(b388,key=lambda z:(-z['GTO_strict_40_70_combos']*z['NL2_IP_strict_40_70_combos'],z['exact_public_board']))[0]['exact_public_board'],
        GTO_source_sha256=b388[0]['original_GTO_sha256'],
        NL2_hero_lock_source_sha256=b388[0]['new_actual_partial_NL2_sha256'],
        GTO_run_id=45023132316)
  ],correct_spot='BTN_BB',correct_actor='BTN_IP',correct_line='b33 c/x b50 c/x',
  full_street_40_70_legal_combo_positive_each=True,no_generic_texture_CERT=True,
  no_observed_opponent_NL2_private_card_conditionals=True,
  no_early_upgrade_before_next_independent_raw_artifacts_and_UI_Actions=True,
  provisional_ready_for_independent_V48_source_promotion=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,PR2_draft_never_merge=True)
 assert len({z['flop'] for z in out['selected_exact_named_boards']})==3
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 DOC.write_text('# B389 rank107 three source-authenticated exact flops — independent pre-cert gate\n\n'
  'Source-blind first-ten rank107 has three distinct public flops, only on their exact original GTO and genuine NL2 IP paired actor board/line, root 100bb and SPR tolerance. '
  'This audit is NOT a registry upgrade: requires independent original-source artifact SHA reinspection, matrix, frontend and HU2475 Actions before 160/232 may be claimed. '
  'Pre-cert state: 159 CERT / 233 APPROX / 0 EST; no extrapolation to generic textures.\n')
 print('PASS B389 three distinct genuine original GTO + partially NL2-locked BTN-IP source flops; no early CERT')
if __name__=='__main__':main()
