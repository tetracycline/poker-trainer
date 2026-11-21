#!/usr/bin/env python3
"""B265 V40: fail-closed rank313 LMP CO-IP THREE authentic distinct GTO+
real Rust partially NL2 locked named flop certification.

Original frozen 100bb 169-class limped preflop ranges are ASSUMED, not
observed NL2 private-card frequencies. CERT only exact public board,
actor, prior action line, SPR and SHA, NEVER all hands/textures.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
OLD=D/'nl2_hu_multiboard_status_v39_b247_rank30.json'
STAGE=D/'nl2_hu_stage2_queue.json'
PRERANK=D/'nl2_hu_multiboard_prerank.json'
HISTORY=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
GTO=D/'solver_evidence/NL2_MULTIBOARD_B250_R313_6S5H3D_GTO.json.gz'
GIDX=D/'solver_evidence/NL2_MULTIBOARD_B250_R313_6S5H3D_GTO.index.json'
PIN=D/'nl2_hu_b250_rank313_lmp_6s5h3d_gto_parent_pin.json'
LOCK=D/'solver_evidence/NL2_MULTIBOARD_B263_R313_6S5H3D_EXP_IP.json.gz'
LIDX=D/'solver_evidence/NL2_MULTIBOARD_B263_R313_6S5H3D_EXP_IP.index.json'
OUT=D/'nl2_hu_multiboard_status_v40_b265_rank313.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v40_b265.json'
REPORT=DOC/'NL2_HU_B265_V40_R313_THREE_TRUE_ORIGINAL_GTO_NL2_IP_CERT.md'
MATDOC=DOC/'NL2_HU_B265_V40_ALL_NEW_NAMED_BOARD_LOCK_MEDIUM.md'
MID='ln-iso-lmp_r_model-wpg493';LINE='b75 r c/x b50 c/x'
FLOPS={'9s6h3d','KsQh4d','6s5h3d'}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_new():
 assert all(p.is_file() for p in (GTO,GIDX,PIN,LOCK,LIDX))
 gp,gi,li=load(PIN),load(GIDX),load(LIDX)
 assert gp['schema']=='NL2_HU_B250_RANK313_LMP_6S5H3D_GTO_PARENT_PIN_V1'
 assert (gp['source_run_id'],gi['run_id'])==(44901784001,44901784001)
 assert gp['source_gto_job_id'] is None
 assert (gp['spot'],gp['flop'],gp['turn'],gp['flop_line'],gp['turn_line'])==(
   'LMP_CO_BB','6s5h3d','Qs','b75 r c','x b50 c')
 assert (gp['target_rank'],gp['model_id'])==(313,MID)
 assert gp['observed_preflop_ranges'] is False and gp['assumed_limped_169class'] is True
 assert gp['original_full_100bb_lmp_gto_not_recomputed'] is True
 assert gp['target_exact_actor_IP_river_nodes']==2
 assert gp['target_exact_actor_IP_strict_combos']==198
 assert (gi['verified_cases'],gi['gto_cases'],gi['locked_cases'])==(1,1,0)
 assert gi['exact_target_actor_IP_strict_combos']==198
 assert gi['source_sha256']==hashlib.sha256(gzip.decompress(GTO.read_bytes())).hexdigest()
 assert gi['gzip_sha256']==sha(GTO)
 assert (gi['original_parent_GTO_root_SHA256'],gi['original_parent_GTO_job_SHA256'],
  gi['original_parent_GTO_manifest_SHA256'])==(
   gp['original_gto_root_sha256'],gp['original_gto_job_sha256'],gp['original_gto_manifest_sha256'])
 assert li['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
 assert (li['batch'],li['run_id'])==('B263_R313_6S5H3D_EXP_IP',44903333583)
 assert (li['gto_cases'],li['locked_cases'],li['verified_cases'])==(0,1,1)
 assert li['source_sha256']==hashlib.sha256(gzip.decompress(LOCK.read_bytes())).hexdigest()
 assert li['gzip_sha256']==sha(LOCK)
 assert li['original_gto_parent_run']==gi['run_id']
 assert li['original_B250_full_GTO_flop_not_recomputed'] is True
 assert li['original_limped_169class_preflop_ASSUMED'] is True
 assert (li['original_parent_GTO_root_SHA256'],li['original_parent_GTO_job_SHA256'],
    li['original_parent_GTO_manifest_SHA256'])==(
    gp['original_gto_root_sha256'],gp['original_gto_job_sha256'],gp['original_gto_manifest_sha256'])
 assert (li['flop'],li['turn'],li['exact_action_line'],li['rank'])==(
   '6s5h3d','Qs',LINE,313)
 assert li['exact_actor_IP_river_nodes']==2 and li['exact_actor_IP_strict_combos']==73
 assert li['no_private_card_conditional_NL2_observation_claim'] is True
 assert li['generic_model_certification']==li['immediate_CERT_upgrades']==0
 assert li['strict_failure_reason'] is None
 g=json.loads(gzip.decompress(GTO.read_bytes()))
 e=json.loads(gzip.decompress(LOCK.read_bytes()))
 assert (g['schema'],e['schema'])==(
   'NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',)*2
 assert not g['errors'] and not e['errors']
 assert (g['source_run_id'],e['source_run_id'])==(44901784001,44903333583)
 assert (g['exact_board_gto_sources'],e['imputed_pool_locked_sources'])==(1,1)
 assert len(g['artifacts'])==len(e['artifacts'])==1
 for z,version in ((g,'gto'),(e,'exp_ip')):
  a=z['artifacts'][0]
  assert a['version']==version and a['spot']=='LMP_CO_BB' and a['flop']=='6s5h3d'
  assert not a['errors'] and len(a['cases'])==1
  c=a['cases'][0]
  assert c['flop_line']=='b75 r c' and c['turn']=='Qs'
  assert c['flop_root_pot_bb']==2.5 and c['flop_root_stack_bb']==99.0
  assert c['pot_family']=='LMP'
  if version=='gto':assert c['gto_exploitability_pct']<=.5
  actual=[n for n in c['nodes'] if n['exact_node_line']==LINE and
      n['acting_seat']==1 and n['strictly_reachable_combos']>0]
  assert len(actual)==2
  assert sum(n['strictly_reachable_combos'] for n in actual)==(
    198 if version=='gto' else 73)
 return gp,gi,li

def main():
 old=load(OLD);historical=load(HISTORY)
 assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30'
 assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(152,240,0,392)
 assert old['records'][MID]['label']=='APPROX'
 assert old['records']['ln-opfr-t_model-1hmsxaw']['label']=='CERT-MULTIBOARD'
 assert len(old['records'])==392
 z=next(t for t in historical['rows'] if t['rank']==313)
 assert z['model_id']==MID and z['hero_seat']==1
 assert set(z['distinct_GTO_plus_NL2_hero_flops'])=={'9s6h3d','KsQh4d'}
 for x in z['exact_authentic_gto_source_proofs']:
  assert x['actor']==1 and x['exact_line']==LINE
  assert x['true_NL2_actor_locked'] and x['strict_legal_combos']>0
  assert x['GTO_gap_pct']<=.5 and x['SPR_error_pct']<=5
 _,gi,li=check_new()
 archive=[pathlib.Path(p) for p in old['source_evidence']['source_files']]
 assert archive and len(archive)==len(set(archive))
 assert all(p.is_file() for p in archive)
 assert GTO not in archive and LOCK not in archive
 archive.extend((GTO,LOCK))
 gto,locked,index=build_source_index(D,archive)
 item=next(copy.deepcopy(n) for n in load(PRERANK)['nodes']
   if n['rank_by_empirically_grounded_frequency_proxy']==313)
 model=next(n for n in load(STAGE)['records'] if n['model_id']==MID)
 assert item['model_id']==MID and model['model_id']==MID
 assert (model['solver_profile'],model['family'],model['street'])==('LMP_CO_BB','LMP',2)
 assert hero_seat(model['preflop_text'])==1
 item['preflop_text']=model['preflop_text']
 item['abstract_action_history']=model['abstract_action_history']
 options,why=candidates(item,gto,locked,None)
 assert why is None,why
 boards,reason=choose_3_5(options)
 assert reason is None,reason
 assert len(boards)==3 and {b['flop'] for b in boards}==FLOPS
 assert len({b['flop_texture'] for b in boards})>=2
 assert all(b['acting_seat']==1 and b['actual_exact_action_line']==LINE and
    b['strict_full_street_combo_reachable']>0 and b['exact_combo_reachable']>0 and
    b['relative_spr_error_pct']<=5 and b['genuine_gto_exploitability_pct']<=.5 and
    any(v['version']=='exp_ip' for v in b['nl2_locked_variants']) for b in boards)
 third=next(b for b in boards if b['flop']=='6s5h3d')
 assert third['turn']=='Qs'
 assert (third['source_run_id'],third['source_sha256'])==(
     gi['run_id'],gi['source_sha256']) or third['source_run_id']==gi['run_id']
 assert third['assumed_preflop_ranges'] is True
 assert any(l['run_id']==li['run_id'] and l['sha256']==li['source_sha256']
   for l in third['nl2_locked_variants'])
 assert third['strict_full_street_combo_reachable']>0
 for b in boards:
  if b['flop']!='6s5h3d':
   assert b['turn'] in ('Ts','Tc')
   assert b['source_run_id']==44666294821
 out=copy.deepcopy(old)
 out['records'][MID].update(label='CERT-MULTIBOARD',
   high_frequency_preregistered=True,
   original_top24_high_frequency_preregistered=False,
   source_blind_expansion_rank=313,
   prereg_cohort='B175_R313_TWO_GENUINE_GTO_NL2_LMP_IP_BOARD_PLUS_B250_TRUE_GTO_B263_TRUE_NL2_THIRD',
   certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
   blocked_reason=None,
   source_credibility='3_DISTINCT_EXACT_LMP_GTO_SHA_100BB_AND_REAL_NL2_CO_IP_PARTIAL_LOCK')
 assert {mid for mid in old['records'] if old['records'][mid]!=out['records'][mid]}=={MID}
 assert sum(v['label']=='CERT-MULTIBOARD' for v in out['records'].values())==153
 assert sum(v['label']=='APPROX' for v in out['records'].values())==239
 out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313',
   CERT_MULTIBOARD=153,APPROX=239,EST=0,TOTAL=392,
   parent_v39_sha256=sha(OLD),
   source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{313}),
   supplementary_cert_count=old['supplementary_cert_count']+1,
   B265_rank313_three_true_GTO_NL2_IP_flops=dict(
     rank=313,model_id=MID,flops=sorted(FLOPS),exact_line=LINE,actor='CO_IP',
     original_GTO_runs={'9s6h3d':44666294821,'KsQh4d':44666294821,'6s5h3d':gi['run_id']},
     genuine_B263_real_NL2_IP_lock_run=li['run_id'],
     original_B250_GTO_pin_sha256=sha(PIN),
     original_B250_GTO_archive_sha256=sha(GTO),
     genuine_B263_NL2_archive_sha256=sha(LOCK),
     B263_strict_CO_IP_river_combos=73,
     LMP_explicit_169class_preflop_ASSUMED_not_observed_NL2_hand=True,
     no_observed_NL2_private_card_conditionals=True,
     only_exact_board_not_generic_handclass_certified=True),
   B265_new_SHA_verified_source_files_separate_from_original_V39_ledger=[
      str(GTO),str(LOCK)],
   B265_original_frozen_V39_source_ledger_not_mutated=True,
   no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
   PR2_remains_draft_never_merge=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 matrix=create(out)
 assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'],matrix['EST'])==(153,239,0)
 assert len(matrix['models'])==153 and len(matrix['boards'])==587
 ag=matrix['strict_aggregate']
 assert ag['named_board_proofs']==587 and ag['hero_lock_variants']>=679
 assert ag['b50_research_candidate_boards']>=133
 assert all(b['hero_lock_proofs'] and b['strictly_reachable_combo_count']>0 and
    b['no_general_bet_size_recommendation'] for b in matrix['boards'])
 audited=audit(out)
 assert (audited['cert_multiboard'],audited['approx'],audited['EST'])==(153,239,0)
 assert (audited['aggregate']['named_board_proofs'],
    audited['aggregate']['paired_hero_locked_source_variants'])==(
      587,ag['hero_lock_variants'])
 matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V40_B265',
    parent_v40_status_sha256=sha(OUT),
    only_exact_board_50pct_research_not_generalized=True,
    observed_NL2_pooled_marginal_is_not_board_hand_conditional=True,
    PR2_Draft_NEVER_MERGE=True)
 MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
 REPORT.write_text('# B265 V40 | rank313 LMP CO-IP 3 authentic GTO + NL2 partial-lock boards\n\n'
   '**153 CERT / 239 APPROX / 0 EST** across original 392 HU models; only rank313 is promoted. '
   'Original real distinct flop/turn proofs: 9s6h3d/Ts, KsQh4d/Tc, 6s5h3d/Qs. '
   'All same exact CO-IP action b75 r c/x b50 c/x, 100bb LMP root pot2.5bb, '
   'full-street max or 40%/70% policy, GTO convergence<=0.5%, SPR<=5%, '
   'real actor-matched NL2 partial Rust lock. '
   'B250 third original GTO 198 strictly legal CO-IP river combo decisions, '
   'B263 downstream partial NL2 IP locked 73 strictly reachable combos.\n\n'
   'Original limped 169-class preflop ranges are ASSUMED, not measured NL2 '
   'private-card conditional action frequencies. Any pooled NL2 pattern sources '
   'are street/size marginals, with default/UNKNOWN explicitly separate. '
   'No entire texture or handclass GTO is claimed. '
   '50% pot nonpolarized marks are only exact-board research where raw evidence supports them. '
   'V39 previous 584 original named boards and 676 lock variants remain unchanged, '
   'the 3 new GTO+NL2 named proof boards are additive. '
   'Source ledger remains frozen; B250/B263 new exact archives attached separately. '
   'Complete 2475/2475 HU source/path audit is mandatory before commit. '
   'PR#2 Draft, NEVER MERGE.\n')
 MATDOC.write_text('# B265 V40 all 587 exact GTO/NL2 actor locks and medium50 proof\n\n'+write_md(matrix))
 print('PASS B265 V40',json.dumps(dict(CERT=153,APPROX=239,rank=313,flops=sorted(FLOPS),
    named=587,locks=ag['hero_lock_variants'],exact_board_b50=ag['b50_research_candidate_boards']),
    ensure_ascii=False),flush=True)
if __name__=='__main__':main()
