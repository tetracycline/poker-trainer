#!/usr/bin/env python3
"""B285: exact authenticated B279 original 100bb rank46 CO-IP zero strict
actor combos; B280 21m CANCELLED and second source audit SKIPPED (verified
by GitHub API in workflow). No partial or unverified original GTO counts,
no third CERT board, all V41 590 exact board source locks immutable.
"""
import gzip,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
PRIOR=D/'nl2_hu_b278_v41_238_approx_rank46_and_71_oneflop_true_sourceblind.json'
PIN=D/'nl2_hu_b279_rank46_lmp_KsJh4d_gto_parent_pin.json'
INDEX=D/'solver_evidence/NL2_MULTIBOARD_B279_R46_KSJH4D_GTO.index.json'
GZ=D/'solver_evidence/NL2_MULTIBOARD_B279_R46_KSJH4D_GTO.json.gz'
OUT=D/'nl2_hu_b285_v41_rank46_b279_zero_b280_cancelled_failclosed.json'
MD=DOC/'NL2_HU_B285_R46_B279_ZERO_B280_CANCELLED_SOURCE_FAILCLOSED.md'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
  status,prior=load(STATUS),load(PRIOR)
  assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(154,238,0,392)
  assert prior['current_V41_status_sha256']==sha(STATUS)
  assert [z['rank'] for z in prior['one_flop_short_sourceblind_priorities']]==[46,71]
  assert status['records']['ln-iso-lmp_t_model-17z0wyl']['label']=='APPROX'
  p,i=load(PIN),load(INDEX)
  assert p['schema']=='NL2_HU_B279_RANK46_LMP_KSJH4D_GTO_PARENT_PIN_V1'
  assert (p['source_run_id'],i['run_id'])==(44937413659,44937413659)
  assert (p['target_rank'],p['model_id'])==(46,'ln-iso-lmp_t_model-17z0wyl')
  assert (p['spot'],p['flop'],p['turn'],p['flop_line'],p['turn_line'])==(
    'LMP_CO_BB','KsJh4d','2h','x b50 c','x x')
  assert p['assumed_limped_169class'] is True and p['observed_preflop_ranges'] is False
  assert (p['target_exact_actor_IP_turn_nodes'],p['target_exact_actor_IP_strict_combos'])==(0,0)
  assert p['direct_nl2_lock_source_present'] is False and p['no_generic_model_certification'] is True
  assert i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
  assert i['batch']=='B279_R46_KSJH4D_GTO'
  assert (i['gto_cases'],i['locked_cases'],i['verified_cases'])==(1,0,1)
  assert (i['target_line'],i['turn'],i['frozen_high_frequency_rank'])==('x b50 c/x','2h',46)
  assert i['exact_target_actor_IP_strict_combos']==0
  assert i['no_generic_model_certification'] and i['immediate_CERT_upgrades']==0
  assert i['gzip_sha256']==sha(GZ)
  assert i['source_sha256']==hashlib.sha256(gzip.decompress(GZ.read_bytes())).hexdigest()
  assert (i['original_parent_GTO_root_SHA256'],i['original_parent_GTO_job_SHA256'],
      i['original_parent_GTO_manifest_SHA256'])==(
      p['original_gto_root_sha256'],p['original_gto_job_sha256'],p['original_gto_manifest_sha256'])
  body=json.loads(gzip.decompress(GZ.read_bytes()))
  assert body['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
  assert not body['errors'] and body['source_run_id']==44937413659
  assert (body['exact_board_gto_sources'],body['imputed_pool_locked_sources'])==(1,0)
  assert len(body['artifacts'])==1 and len(body['artifacts'][0]['cases'])==1
  c=body['artifacts'][0]['cases'][0]
  assert c['flop']=='KsJh4d' and c['turn']=='2h' and c['flop_line']=='x b50 c'
  assert c['gto_exploitability_pct']<=.5
  assert not [z for z in c['nodes'] if z['exact_node_line']=='x b50 c/x'
      and z['acting_seat']==1 and z['strictly_reachable_combos']>0]
  # Original Rust B280 full GTO job cancelled; its partial or skipped output must not
  # be treated as original GTO or NL2 locked source without a complete pinned archive.
  b280=D/'nl2_hu_b280_rank46_lmp_QsJh4d_gto_parent_pin.json'
  b280idx=D/'solver_evidence/NL2_MULTIBOARD_B280_R46_QSJH4D_GTO.index.json'
  b280gz=D/'solver_evidence/NL2_MULTIBOARD_B280_R46_QSJH4D_GTO.json.gz'
  assert not any(x.exists() for x in (b280,b280idx,b280gz))
  check=audit(status)
  assert (check['cert_multiboard'],check['approx'],check['EST'])==(154,238,0)
  assert (check['aggregate']['named_board_proofs'],
      check['aggregate']['paired_hero_locked_source_variants'],
      check['aggregate']['board_examples_with_b50_candidate'])==(590,682,134)
  assert check['not_generalized_handclass_GTO'] and check['not_actual_NL2_earnings']
  out=dict(schema='NL2_HU_B285_R46_B279_ZERO_GTO_B280_CANCELLED_STRICT_FAILCLOSED_V1',
    V41_status_sha256=sha(STATUS),B278_sourceblind_sha256=sha(PRIOR),
    rank=46,spot='LMP_CO_BB',target='x b50 c/x',actor='CO_IP',model_SPR=19.55,
    B279=dict(original_GTO_run=44937413659,flop='KsJh4d',turn='2h',
       original_GTO_source_sha256=i['source_sha256'],
       original_GTO_gzip_sha256=sha(GZ),
       full_GTO_original_solved_cases=1,legal_actor_turn_nodes=0,
       legal_actor_strict_combos=0,authentic_real_NL2_hero_lock=False,
       cannot_count_as_third_certified_board=True),
    B280=dict(original_GTO_run=44937484979,flop='QsJh4d',
       original_Rust_job_conclusion='cancelled',independent_source_verify_job='skipped',
       no_complete_source_pin_or_gzip_or_index=True,
       no_authentic_real_NL2_hero_lock=True,cannot_count_as_third_certified_board=True),
    still_only_two_true_GTO_plus_CO_IP_NL2_rank46_flops=['8s8h3d','9s6h3d'],
    exact_flop_turn_only_not_other_turn_rejection=True,
    V41_CERT_MULTIBOARD=154,V41_APPROX=238,V41_EST=0,TOTAL=392,
    existing_genuine_named_boards=590,existing_actor_NL2_hero_locks=682,
    b50_exact_board_research_candidates_only=134,
    no_partial_solve_certification=True,no_nl2_private_card_data_fabricated=True,
    PR2_Draft_NEVER_MERGE=True)
  OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
  MD.write_text('# B285: rank46 original GTO zero / cancelled source fail-closed\n\n'
    'B279 real Rust full 100bb original GTO KsJh4d/2h completed with pinned SHA, '
    'but actor CO-IP x b50 c/x has ZERO strict reachable combos and cannot yield '
    'a third actor-matched NL2 board. B280 QsJh4d original Rust GTO job was '
    'cancelled, independent verifier skipped, and no original SHA-complete '
    'source exists in PR branch. Neither source may become CERT.\n\n'
    'Keep rank46 APPROX with two authentic older flops 8s8h3d and 9s6h3d; '
    'unknown NL2 private-card action frequency is not empirical. '
    'Do not reject different turn/tree on the basis of this exact failure. '
    'V41 remains 154 CERT / 238 APPROX /0 EST, 590 named GTO/actor NL2 lock '
    'boards and 682 source variants. HU2475 independent Actions required, '
    'PR #2 Draft NEVER MERGE.\n')
  print('PASS B285 B279 original exact 0 legal COIP actor, B280 cancelled failclosed',flush=True)
if __name__=='__main__':main()
