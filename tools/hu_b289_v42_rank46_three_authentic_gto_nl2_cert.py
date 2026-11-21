#!/usr/bin/env python3
"""B289 V42 rank46 ONLY, fail closed until three different genuine 100bb
LMP GTO named flops and correct actor CO-IP NL2 Rust partial locks meet
exact x b50 c/x action, same SPR19.55 ±5%, 40/70 sequential per-combo.
Limped 169-class preflop distribution is ASSUMED, not measured private-hand.
No GTO generalization beyond three public board/turn/history/actor examples.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import texture
from hu_cert_lock_medium_coverage_matrix import create,write_md
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
OLD=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
STATUS=D/'nl2_hu_multiboard_status_v42_b289_rank46.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v42_b289.json'
REPORT=DOC/'NL2_HU_B289_V42_RANK46_THREE_ACTUAL_GTO_NL2_COIP_CERT.md'
MATDOC=DOC/'NL2_HU_B289_V42_ALL_593_REAL_NAMED_NL2_LOCK_MEDIUM.md'
B3=D/'solver_evidence/NL2_MULTIBOARD_B3.json.gz'
B3_IDX=D/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
B175=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
B209=D/'nl2_hu_b209_rank46_lmp_9s6h3d_original_b3_gto_pin.json'
B210=D/'solver_evidence/NL2_MULTIBOARD_B210_R46_B3_EXP_IP.json.gz'
B210_IDX=D/'solver_evidence/NL2_MULTIBOARD_B210_R46_B3_EXP_IP.index.json'
B278=D/'nl2_hu_b278_v41_238_approx_rank46_and_71_oneflop_true_sourceblind.json'
B286_PIN=D/'nl2_hu_b286_rank46_lmp_7s7h2d_gto_parent_pin.json'
B286_GTO=D/'solver_evidence/NL2_MULTIBOARD_B286_R46_7S7H2D_GTO.json.gz'
B286_IDX=D/'solver_evidence/NL2_MULTIBOARD_B286_R46_7S7H2D_GTO.index.json'
B288_NL2=D/'solver_evidence/NL2_MULTIBOARD_B288_R46_7S7H2D_EXP_IP.json.gz'
B288_IDX=D/'solver_evidence/NL2_MULTIBOARD_B288_R46_7S7H2D_EXP_IP.index.json'
MID='ln-iso-lmp_t_model-17z0wyl';LINE='x b50 c/x';SPR=19.55
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ld(p):return json.loads(p.read_text())
def gz(p):return json.loads(gzip.decompress(p.read_bytes()))
def case_find(data,flop,turn,version,expected_sha=None):
    matches=[]
    for art in data['artifacts']:
        if (art['spot'],art['flop'],art['version'])!=('LMP_CO_BB',flop,version):continue
        assert not art.get('errors')
        for c in art['cases']:
            if (c['flop_line'],c['turn'])!=('x b50 c',turn):continue
            if expected_sha is not None and c['source_sha256']!=expected_sha:continue
            matches.append(c)
    assert len(matches)==1,(flop,turn,version,len(matches))
    c=matches[0]
    assert c['gto_exploitability_pct'] is not None and c['gto_exploitability_pct']<=.5 if version=='gto' else True
    assert c['flop_root_pot_bb']==2.5 and c['flop_root_stack_bb']==99.0
    return c
def actor_nodes(case):
    return [n for n in case['nodes'] if n['exact_node_line']==LINE
       and n['acting_seat']==1 and len(n['public_board'])==8
       and n['strictly_reachable_combos']>0
       and abs(n['node_spr']-SPR)/SPR<=.05]
def sample(c,flop,turn,run,strict,lock_run,lock_sha,scope,expected_raw_sha=None):
    assert (c['flop'],c['turn'],c['flop_line'])==(flop,turn,'x b50 c')
    assert c['run_id']==run
    assert c['gto_exploitability_pct']<=.5
    assert str(c['empirical_scope']).startswith('ASSUMED')  # original SHA-pinned B3/B286 full GTO, never observed private hand
    if expected_raw_sha is not None:assert c['source_sha256']==expected_raw_sha
    nodes=actor_nodes(c)
    assert len(nodes)==1
    n=nodes[0]
    # The canonical Rust public-board serialization may reorder flop cards.
    # Match the frozen flop/turn at case level and require the actual turn
    # suffix on this exact 8-char solver board (same as B271 source gate).
    assert len(n['public_board'])==8 and n['public_board'].endswith(turn)
    assert n['strictly_reachable_combos']==strict
    assert n['source_reachable_combos']>=strict>0
    assert n['source_actions']
    assert len(lock_sha)==64 and lock_run>0
    medium=int(n.get('medium_50pct_eligible_combos') or 0)
    research=bool(n.get('b50_nonpolarized_relative_equity_research_candidate',False))
    if research:assert medium>0
    return dict(flop=flop,turn=turn,public_board=n['public_board'],
        actual_exact_action_line=LINE,acting_seat=1,exact_flop_action='x b50 c',
        actual_pot_bb=n['pot_bb'],actual_effective_stack_bb=n['remaining_bb'],
        actual_spr=n['node_spr'],model_assumed_spr=SPR,
        relative_spr_error_pct=round(100*abs(n['node_spr']-SPR)/SPR,4),
        genuine_gto_exploitability_pct=c['gto_exploitability_pct'],
        source_run_id=run,source_sha256=c['source_sha256'],
        source_kind=c['empirical_scope'],assumed_preflop_ranges=True,
        exact_combo_reachable=n['source_reachable_combos'],
        strict_full_street_combo_reachable=n['strictly_reachable_combos'],
        exact_node_actions=n['source_actions'],
        medium_50pct_eligible_combos=medium,
        b50_nonpolarized_relative_equity_research_candidate=research,
        flop_texture=texture(flop),
        nl2_locked_variants=[dict(version='exp_ip',run_id=lock_run,sha256=lock_sha,
          source_scope=scope,villain_observed_pattern_node_share_pct=None,
          source_not_real_per_combo_observation=True,
          unknown_history_frequency_filled_with_default=True,
          observed_marginal_source_nodes=None,assumed_default_source_nodes=None,
          unlocked_source_nodes=None,hero_model_gain_bb=None)])
def main():
    prior=ld(OLD);assert prior['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61'
    assert (prior['CERT_MULTIBOARD'],prior['APPROX'],prior['EST'],prior['TOTAL'])==(154,238,0,392)
    assert prior['records'][MID]['label']=='APPROX'
    assert prior['no_generic_texture_GTO'] and prior['no_observed_private_card_NL2_rates']
    assert prior['records']['ln-iso-lmp_r_model-wpg493']['label']=='CERT-MULTIBOARD'
    assert prior['records']['ln-ipfr-t_model-qpx6tn']['label']=='CERT-MULTIBOARD'
    historic=ld(B175);h=next(z for z in historic['rows'] if z['rank']==46)
    assert (h['model_id'],h['hero_seat'],h['model_SPR'])==(MID,1,SPR)
    assert h['distinct_GTO_plus_NL2_hero_flops']==['8s8h3d']
    frozen={z['flop']:z for z in h['exact_authentic_gto_source_proofs']}
    assert frozen['8s8h3d']['true_NL2_actor_locked'] and frozen['8s8h3d']['strict_legal_combos']==10
    assert frozen['9s6h3d']['strict_legal_combos']==1 and frozen['9s6h3d']['true_NL2_actor_locked'] is False
    check=ld(B278)
    assert check['newly_verified_B210_rank46_true_GTO_plus_NL2_actor_IP']['NL2_legal_actor_combos']==1
    assert [z['rank'] for z in check['one_flop_short_sourceblind_priorities']]==[46,71]
    b3idx=ld(B3_IDX);b3=gz(B3)
    assert b3idx['run_id']==b3['source_run_id']==44666294821
    assert b3idx['gzip_sha256']==sha(B3)
    assert b3idx['source_sha256']==hashlib.sha256(gzip.decompress(B3.read_bytes())).hexdigest()
    assert (b3idx['gto_cases'],b3idx['locked_cases'])==(43,90)
    c8=case_find(b3,'8s8h3d','5s','gto',frozen['8s8h3d']['source_sha'])
    exp8=case_find(b3,'8s8h3d','5s','exp_ip')
    assert actor_nodes(exp8) and sum(n['strictly_reachable_combos'] for n in actor_nodes(exp8))>0
    assert frozen['8s8h3d']['paired_lock_runs']==[44666294821]
    board8=sample(c8,'8s8h3d','5s',44666294821,10,
       44666294821,exp8['source_sha256'],
       'HISTORIC_TRUE_NL2_ACTOR_IP_PARTIALLY_LOCKED_SOURCE_UNKNOWN_MARGINAL_DENOMINATORS')
    pin209,li=ld(B209),ld(B210_IDX)
    assert pin209['source_run_id']==li['original_GTO_B3_run_id']==44666294821
    assert pin209['original_B3_archive_sha256']==sha(B3)
    assert li['original_B209_GTO_pin_sha256']==sha(B209)
    assert li['gzip_sha256']==sha(B210)
    assert li['source_sha256']==hashlib.sha256(gzip.decompress(B210.read_bytes())).hexdigest()
    assert (li['acting_seat'],li['strict_actor_IP_combos'])==(1,1)
    assert (li['original_B3_root_SHA256'],li['original_B3_manifest_SHA256'],
      li['original_B3_job_SHA256'])==(
      pin209['original_gto_root_sha256'],pin209['original_gto_manifest_sha256'],
      pin209['original_gto_job_sha256'])
    c9=case_find(b3,'9s6h3d','Ts','gto',frozen['9s6h3d']['source_sha'])
    lock210=gz(B210)
    c210=case_find(lock210,'9s6h3d','Ts','exp_ip')
    assert actor_nodes(c210) and sum(n['strictly_reachable_combos'] for n in actor_nodes(c210))==1
    board9=sample(c9,'9s6h3d','Ts',44666294821,1,44882669727,
       c210['source_sha256'],'TURN_ONLY_GENUINE_NL2_POOL_MARGINAL_PARTIAL_RUST_LOCK')
    pin286,gi,li288=ld(B286_PIN),ld(B286_IDX),ld(B288_IDX)
    assert (pin286['source_run_id'],gi['run_id'])==(44939456600,44939456600)
    assert pin286['target_exact_actor_IP_strict_combos']==12
    assert gi['source_sha256']==hashlib.sha256(gzip.decompress(B286_GTO.read_bytes())).hexdigest()
    assert gi['gzip_sha256']==sha(B286_GTO)
    assert li288['schema']=='NL2_HU_B288_R46_AUTHENTIC_ORIGINAL_B286_GTO_PLUS_RUST_NL2_COIP_V1'
    assert li288['original_GTO_source_run']==44939456600 and li288['original_100bb_GTO_strict_actor_IP_combos']==12
    assert (li288['NL2_strict_actor_IP_combos'],li288['NL2_actor_IP_model_SPR_eligible_combos'])==(12,12)
    assert li288['genuine_same_exact_board_actor_line_SPR_paired']
    assert li288['original_GTO_parent_pin_sha256']==sha(B286_PIN)
    assert li288['original_GTO_index_sha256']==sha(B286_IDX)
    assert li288['original_GTO_archive_sha256']==sha(B286_GTO)
    assert li288['NL2_actual_Rust_gzip_sha256']==sha(B288_NL2)
    assert li288['NL2_actual_Rust_source_sha256']==hashlib.sha256(gzip.decompress(B288_NL2.read_bytes())).hexdigest()
    assert (li288['flop'],li288['turn'],li288['exact_line'],li288['acting_seat'],li288['model_SPR'])==('7s7h2d','3s',LINE,1,SPR)
    assert li288['observed_NL2_per_private_card_frequencies'] is False
    assert li288['only_downstream_turn_river_locked']
    assert li288['no_automatic_CERT_upgrade'] and li288['no_generic_texture_CERT']
    cb=case_find(gz(B286_GTO),'7s7h2d','3s','gto')
    board7=sample(cb,'7s7h2d','3s',44939456600,12,li288['source_run_id'],
       li288['NL2_actual_Rust_source_sha256'],
       'TURN_ONLY_GENUINE_NL2_POOL_MARGINAL_PARTIAL_RUST_LOCK')
    boards=[board8,board9,board7]
    assert {z['flop'] for z in boards}=={'8s8h3d','9s6h3d','7s7h2d'}
    assert len({z['flop_texture'] for z in boards})>=2
    assert all(z['actual_exact_action_line']==LINE and z['acting_seat']==1 and
       z['relative_spr_error_pct']<=5 and z['strict_full_street_combo_reachable']>0
       and z['genuine_gto_exploitability_pct']<=.5 and z['nl2_locked_variants'] and
       z['assumed_preflop_ranges'] for z in boards)
    result=copy.deepcopy(prior)
    result['records'][MID].update(label='CERT-MULTIBOARD',
       high_frequency_preregistered=True,
       original_top24_high_frequency_preregistered=False,
       source_blind_expansion_rank=46,
       prereg_cohort='B3_HISTORIC_8S8H3D_PLUS_B209_B210_9S6H3D_PLUS_B286_B288_7S7H2D',
       certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
       blocked_reason=None,
       source_credibility='3_DIFFERENT_REAL_100BB_ASSUMED_LMP_GTO_SHA_WITH_AUTHENTIC_ACTOR_COIP_NL2_PARTIAL_LOCK')
    assert {k for k in prior['records'] if prior['records'][k]!=result['records'][k]}=={MID}
    assert sum(v['label']=='CERT-MULTIBOARD' for v in result['records'].values())==155
    assert sum(v['label']=='APPROX' for v in result['records'].values())==237
    result.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46',
       CERT_MULTIBOARD=155,APPROX=237,EST=0,TOTAL=392,
       parent_v41_sha256=sha(OLD),
       source_blind_expansion_ranks=sorted(set(prior['source_blind_expansion_ranks'])|{46}),
       supplementary_cert_count=prior['supplementary_cert_count']+1,
       B289_rank46_three_true_GTO_NL2_CO_IP_flops=dict(
          rank=46,model_id=MID,flops=sorted(z['flop'] for z in boards),
          exact_line=LINE,actor='CO_IP',model_SPR=SPR,
          assumed_limped_169class_preflop_not_observed_NL2_private_cards=True,
          third_B286_original_GTO_strict_combos=12,
          third_B288_actual_NL2_actor_SPR_strict_combos=12,
          genuine_GTO_runs={'8s8h3d':44666294821,'9s6h3d':44666294821,'7s7h2d':44939456600},
          real_NL2_actor_lock_runs={'8s8h3d':44666294821,'9s6h3d':44882669727,'7s7h2d':li288['source_run_id']},
          GTO_and_NL2_source_shas=[dict(flop=z['flop'],turn=z['turn'],
             GTO_run=z['source_run_id'],GTO_case_sha=z['source_sha256'],
             NL2_run=z['nl2_locked_variants'][0]['run_id'],
             NL2_raw_case_sha=z['nl2_locked_variants'][0]['sha256'],
             strict_GTO_actor_combos=z['strict_full_street_combo_reachable']) for z in boards]),
       B289_original_B3_B210_B286_B288_source_ledger_SHA=dict(
          B3=sha(B3),B175=sha(B175),B209=sha(B209),
          B210=sha(B210),B278=sha(B278),B286=sha(B286_GTO),B288=sha(B288_NL2)),
       no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
       PR2_remains_draft_never_merge=True)
    for z in boards:
        q=z['nl2_locked_variants'][0]
        print('B289_BOARD_DIAGNOSTIC',json.dumps(dict(
            flop=z['flop'],turn=z['turn'],history=z['actual_exact_action_line'],
            seat=z['acting_seat'],assumed=z['assumed_preflop_ranges'],
            spr_error=z['relative_spr_error_pct'],gto_gap=z['genuine_gto_exploitability_pct'],
            source_kind=z['source_kind'],gto_sha_length=len(z['source_sha256']),
            num_locks=len(z['nl2_locked_variants']),lock_version=q['version'],
            lock_sha_length=len(q['sha256'])),ensure_ascii=False),flush=True)
    STATUS.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    matrix=create(result)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'],matrix['EST'])==(155,237,0)
    assert (len(matrix['models']),len(matrix['boards']))==(155,593)
    ag=matrix['strict_aggregate']
    assert (ag['named_board_proofs'],ag['hero_lock_variants'])==(593,685)
    assert ag['b50_research_candidate_boards']>=134
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0 and
       z['no_general_bet_size_recommendation'] for z in matrix['boards'])
    audited=audit(result)
    assert (audited['cert_multiboard'],audited['approx'],audited['EST'])==(155,237,0)
    assert (audited['aggregate']['named_board_proofs'],audited['aggregate']['paired_hero_locked_source_variants'])==(593,685)
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V42_B289',
       parent_v42_status_sha256=sha(STATUS),
       unknown_source_denominators_are_not_zero_or_empirical=True,
       only_exact_board_50pct_research=True,PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    REPORT.write_text('# B289 V42 rank46 three authentic original 100bb GTO + real NL2 CO-IP Rust locks\n\n'
       '**155 CERT-MULTIBOARD / 237 APPROX / 0 EST**; exactly rank46 upgraded. '
       'Three independent named flops: 8s8h3d/5s original B3 GTO+true actor-IP NL2; '
       '9s6h3d/Ts original B3 GTO+separate B210 CO-IP Rust partial lock; '
       '7s7h2d/3s original B286 GTO+separate B288 Rust CO-IP partial lock. '
       'Correct CO-IP actor line x b50 c/x and 100bb SPR19.55 ±5% '
       'with original full-street 40%/70% sequential reach (GTO combos 10,1,12). '
       'Every original GTO case SHA and real NL2 lock case SHA is independently checked. '
       'Limped preflop weights of 169 hand classes are **ASSUMED**, '
       'not observed opponent private-hand behavior. Source only applies to '
       'these public board/turn/action histories; full flop GTO plus '
       'partially locked downstream NL2 does not make a whole-game locked strategy. '
       'Other 590 V41 named boards and 682 actor NL2 source variants unchanged; '
       'V42 adds exactly 3 boards and 3 authentic actor-locked sources. '
       '50% pot nonpolarized flags are only exact public-board research, '
       'not general optimal bet sizes. Full 593 source/HU2475 Actions must PASS '
       'and PR#2 stay Draft NEVER MERGE.\n')
    MATDOC.write_text('# B289 V42 593 authenticated GTO/NL2 actor-locked named boards\n\n'+write_md(matrix))
    print('PASS B289 rank46 V42',json.dumps(dict(CERT=155,APPROX=237,
      flops=sorted(z['flop'] for z in boards),
      GTO_strict=[z['strict_full_street_combo_reachable'] for z in boards],
      boards=593,locks=ag['hero_lock_variants'],
      b50=ag['b50_research_candidate_boards']),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
