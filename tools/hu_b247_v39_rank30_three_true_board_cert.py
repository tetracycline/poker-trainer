#!/usr/bin/env python3
"""B247 V39 fail-closed rank30 TRUE 3-board UTG_CO/UTG-OOP CERT promotion.

ONLY after authentic original Rust GTO + separately actor-OOP NL2 partially
locked TURN/RIVER on 3 named distinct flops, same spot/preflop-CFR/100bb,
full 40%+70% prior-action sequential reach, <=0.5% GTO and SPR <=5%.
No per-hole-card NL2 observations, generalized GTO hand class, implied
real-world winnings, or unsupported 50%-pot betting.
"""
import copy,gzip,hashlib,json,pathlib,sys
from hu_multiboard_promote import hero_seat,tokenize,texture
from hu_cert_lock_medium_coverage_matrix import create,write_md
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data');DOC=pathlib.Path('docs')
PARENT=D/'nl2_hu_multiboard_status_v38_b206_rank190.json'
OUT=D/'nl2_hu_multiboard_status_v39_b247_rank30.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v39_b247.json'
REPORT=DOC/'NL2_HU_B247_V39_R30_THREE_AUTHENTIC_UTG_CO_OOP_CERT.md'
MATDOC=DOC/'NL2_HU_B247_V39_ALL_584_NAMED_BOARD_LOCK_MEDIUM.md'
MID='ln-opfr-t_model-1hmsxaw';LINE='b50 c/';SPOT='UTG_CO'
SPECS=[
 dict(flop='KsQh4d',turn='Tc',gto='B235',gto_run=44894369547,
      lock='B238',lock_run=44895095589),
 dict(flop='Js9h4d',turn='Ts',gto='B240',gto_run=44895186652,
      lock='B242',lock_run=44900532333),
 dict(flop='QsJh4d',turn='7s',gto='B243',gto_run=44900567417,
      lock='B246',lock_run=44900938891),
]
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cards(s):
    assert len(s)%2==0
    return set(s[i:i+2] for i in range(0,len(s),2))
def one_board(spec,approx_spr):
    flop,turn=spec['flop'],spec['turn'];gto,lock=spec['gto'],spec['lock']
    parent=D/f'nl2_hu_{gto.lower()}_rank30_utgco_{flop}_gto_parent_pin.json'
    gidx=D/f'solver_evidence/NL2_MULTIBOARD_{gto}_R30_{flop.upper()}_GTO.index.json'
    garchive=D/f'solver_evidence/NL2_MULTIBOARD_{gto}_R30_{flop.upper()}_GTO.json.gz'
    lidx=D/f'solver_evidence/NL2_MULTIBOARD_{lock}_R30_{flop.upper()}_EXP_OOP.index.json'
    larchive=D/f'solver_evidence/NL2_MULTIBOARD_{lock}_R30_{flop.upper()}_EXP_OOP.json.gz'
    assert all(p.is_file() for p in (parent,gidx,garchive,lidx,larchive))
    pin,gi,li=load(parent),load(gidx),load(lidx)
    assert (pin['schema'],pin['source_run_id'])==(
      f'NL2_HU_{gto}_RANK30_UTGCO_{flop.upper()}_GTO_PARENT_PIN_V1',spec['gto_run'])
    assert (pin['spot'],pin['flop'],pin['turn'],pin['flop_line'],pin['turn_line'])==(SPOT,flop,turn,'b50 c','')
    assert (pin['target_rank'],pin['model_id'])==(30,MID)
    assert pin['preflop_CFR_pinned_not_observed_NL2_private_card'] is True
    assert pin['original_full_100bb_utgco_gto_source_pinned'] is True
    assert pin['direct_nl2_lock_source_present'] is False
    assert pin['target_exact_actor_OOP_turn_nodes']==1
    assert pin['target_exact_actor_OOP_turn_strict_combos']>0
    assert gi['run_id']==spec['gto_run'] and gi['target_line']==LINE
    assert (gi['gto_cases'],gi['locked_cases'],gi['verified_cases'])==(1,0,1)
    assert gi['exact_target_actor_OOP_turn_strict_combos']==pin['target_exact_actor_OOP_turn_strict_combos']
    assert gi['source_sha256']==hashlib.sha256(gzip.decompress(garchive.read_bytes())).hexdigest()
    assert gi['gzip_sha256']==sha(garchive)
    assert (gi['original_parent_GTO_root_SHA256'],gi['original_parent_GTO_job_SHA256'],
      gi['original_parent_GTO_manifest_SHA256'])==(
      pin['original_gto_root_sha256'],pin['original_gto_job_sha256'],pin['original_gto_manifest_sha256'])
    gsource=json.loads(gzip.decompress(garchive.read_bytes()))
    assert gsource['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert not gsource['errors'] and gsource['source_run_id']==spec['gto_run']
    assert gsource['exact_board_gto_sources']==1 and gsource['imputed_pool_locked_sources']==0
    assert len(gsource['artifacts'])==1 and len(gsource['artifacts'][0]['cases'])==1
    a=gsource['artifacts'][0];c=a['cases'][0]
    assert (a['spot'],a['flop'],a['version'])==(SPOT,flop,'gto') and not a['errors']
    assert (c['flop'],c['turn'],c['flop_line'],c['spot'],c['pot_family'])==(
        flop,turn,'b50 c',SPOT,'SRP')
    assert (c['flop_root_pot_bb'],c['flop_root_stack_bb'])==(6.5,97.5)
    assert c['gto_exploitability_pct'] is not None and c['gto_exploitability_pct']<=0.5
    assert c['empirical_scope']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert len(c['source_sha256'])==64
    legal=[n for n in c['nodes'] if n['exact_node_line']==LINE and
      n['acting_seat']==0 and len(n['public_board'])==8 and n['strictly_reachable_combos']>0 and
      abs(n['node_spr']-approx_spr)/max(1.,n['node_spr'])<=.05]
    assert len(legal)==1 and len({x['public_board'] for x in legal})==1
    n=legal[0]
    assert n['strictly_reachable_combos']==pin['target_exact_actor_OOP_turn_strict_combos']>0
    assert n['source_reachable_combos']>=n['strictly_reachable_combos']
    assert cards(n['public_board'])==cards(flop+turn)
    assert texture(flop) in ('KQ_HIGH','JT_HIGH')
    assert (li['schema'],li['source_run_id'])==(
       f'NL2_HU_{lock}_RANK30_EXACT_{gto}_GTO_PLUS_REAL_NL2_PARTIAL_LOCK_V1',spec['lock_run'])
    assert (li['original_B'+gto[1:]+'_GTO_source_run_id'],
            li['original_B'+gto[1:]+'_GTO_source_index_sha256'],
            li['original_B'+gto[1:]+'_GTO_parent_pin_sha256'])==(
       spec['gto_run'],sha(gidx),sha(parent))
    assert li['original_GTO_root_sha256']==pin['original_gto_root_sha256']
    assert li['original_GTO_job_sha256']==pin['original_gto_job_sha256']
    assert li['original_preflop_CFR_pinned_not_observed_NL2_private_card'] is True
    assert li['original_GTO_target_turn_strict_combos']>0
    assert (li['spot'],li['rank'],li['model_id'],li['flop'],li['turn'],
       li['exact_line'],li['hero_actor'],li['version'])==(SPOT,30,MID,flop,turn,LINE,0,'exp_oop')
    assert li['authentic_same_hero_board_paired_source'] is True
    assert li['new_actor_OOP_turn_exact_SPR_eligible_combos']>0
    assert li['new_actor_OOP_turn_strict_combos']>=li['new_actor_OOP_turn_exact_SPR_eligible_combos']
    assert li['only_downstream_turn_river_NL2_locked'] and not li['no_new_full_flop_NL2_lock']
    # 'no_new_full_flop_NL2_lock' is a disclosure flag, NOT positive evidence
    assert li['no_observed_per_hole_card_conditionals'] and li['no_generic_texture_CERT']
    assert li['immediate_CERT_upgrades']==0
    assert li['new_Rust_NL2_partial_source_gzip_sha256']==sha(larchive)
    assert li['new_real_NL2_partial_Rust_source_sha256']==hashlib.sha256(gzip.decompress(larchive.read_bytes())).hexdigest()
    assert len(li['new_real_NL2_partial_Rust_source_sha256'])==64
    matched=[q for q in li['true_actor_node_examples'] if q['strict_combos']>0 and
       q['relative_spr_error_pct']<=5 and cards(q['board'])==cards(n['public_board'])]
    assert matched and sum(q['strict_combos'] for q in matched)==li['new_actor_OOP_turn_exact_SPR_eligible_combos']
    assert li['pooled_NL2_marginal_or_assumed_lock_patterns']
    # The genuine Rust locked source has observed *pooled* marginals but does
    # not disclose verified per-pattern decision-node counts; preserve UNKNOWN.
    variant=dict(version='exp_oop',run_id=spec['lock_run'],
      sha256=li['new_real_NL2_partial_Rust_source_sha256'],
      source_scope='TURN_ONLY_DOWNSTREAM_PARTIAL_NL2_POOL_MARGINAL_PROXY_PLUS_ASSUMED_DEFAULT_FROM_PINNED_GTO',
      villain_observed_pattern_node_share_pct=None,
      source_not_real_per_combo_observation=True,
      unknown_history_frequency_filled_with_default=True,
      observed_marginal_source_nodes=None,assumed_default_source_nodes=None,
      unlocked_source_nodes=None,hero_model_gain_bb=None)
    medium=bool(n.get('b50_nonpolarized_relative_equity_research_candidate',False))
    eligible=int(n.get('medium_50pct_eligible_combos',0) or 0)
    # ONE strict hero combo on these flops cannot justify a depolarized 50% distribution.
    assert not medium and n['strictly_reachable_combos']<20
    relative=100*abs(n['node_spr']-approx_spr)/max(1.,n['node_spr'])
    result=dict(flop=flop,turn=turn,public_board=n['public_board'],
       actual_exact_action_line=LINE,acting_seat=0,exact_flop_action='b50 c',
       actual_pot_bb=n['pot_bb'],actual_effective_stack_bb=n['remaining_bb'],
       actual_spr=n['node_spr'],model_assumed_spr=approx_spr,
       relative_spr_error_pct=round(relative,4),
       genuine_gto_exploitability_pct=c['gto_exploitability_pct'],
       source_run_id=spec['gto_run'],source_sha256=c['source_sha256'],
       source_kind='PINNED_POKER_SOLVER_PREFLOP_CFR',
       assumed_preflop_ranges=False,exact_combo_reachable=n['source_reachable_combos'],
       strict_full_street_combo_reachable=n['strictly_reachable_combos'],
       exact_node_actions=n['source_actions'],
       medium_50pct_eligible_combos=eligible,
       b50_nonpolarized_relative_equity_research_candidate=False,
       nl2_locked_variants=[variant])
    return result,dict(gto_run=spec['gto_run'],lock_run=spec['lock_run'],
        gto_archive_sha256=sha(garchive),nl2_archive_sha256=sha(larchive),
        gto_pin_sha256=sha(parent),nl2_index_sha256=sha(lidx),
        exact_board=n['public_board'],gto_strict=n['strictly_reachable_combos'],
        nl2_strict=li['new_actor_OOP_turn_exact_SPR_eligible_combos'])
def main():
    parent=load(PARENT)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V38_B206_RANK190'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['EST'],parent['TOTAL'])==(151,241,0,392)
    original=parent['records'][MID]
    assert original['label']=='APPROX' and original['frequency_rank']==30
    assert original['solver_profile']==SPOT and original['family']=='SRP' and original['street']==1
    assert hero_seat(original['preflop_text'])==0
    h=original['abstract_action_history'].split('|')
    assert len(h)==2 and 'b50 c' in tokenize(h[0]) and '' in tokenize(h[1])
    approx=float(original['assumed_model_node_spr'])
    assert abs(approx-7.25)<.01
    boards=[];proof={}
    for spec in SPECS:
        row,pr=one_board(spec,approx)
        boards.append(row);proof[spec['flop']]=pr
    assert len(boards)==3 and len({b['flop'] for b in boards})==3
    assert len({texture(b['flop']) for b in boards})>=2
    assert all(b['strict_full_street_combo_reachable']>0 and
               len(b['nl2_locked_variants'])==1 and b['nl2_locked_variants'][0]['version']=='exp_oop'
               for b in boards)
    status=copy.deepcopy(parent);item=status['records'][MID]
    item.update(label='CERT-MULTIBOARD',high_frequency_preregistered=True,
      original_top24_high_frequency_preregistered=False,
      source_blind_expansion_rank=30,
      prereg_cohort='B235_B240_B243_FROZEN_ORIGINAL_100BB_PRE_FLOP_CFR_GTO_B238_B242_B246_ACTOR_OOP_NL2',
      certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
      blocked_reason=None,source_credibility='THREE_SHA_PINNED_ORIGINAL_GTO_PLUS_THREE_REAL_RUST_PARTIAL_NL2_UTG_OOP_TURN')
    assert {k for k in parent['records'] if parent['records'][k]!=status['records'][k]}=={MID}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in status['records'].values())==152
    assert sum(x['label']=='APPROX' for x in status['records'].values())==240
    batchledger=status.setdefault('independently_verified_completed_batches',{})
    for spec in SPECS:
        code=f"{spec['gto']}_R30_{spec['flop'].upper()}_GTO"
        assert code not in batchledger
        batchledger[code]=dict(status='VERIFIED',run_id=spec['gto_run'],
            source_kind='PINNED_POKER_SOLVER_PREFLOP_CFR',
            exact_public_board_only=True,no_generic_texture_certification=True)
    status.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30',
       CERT_MULTIBOARD=152,APPROX=240,EST=0,TOTAL=392,
       parent_v38_sha256=sha(PARENT),
       source_blind_expansion_ranks=sorted(set(parent.get('source_blind_expansion_ranks',[]))|{30}),
       supplementary_cert_count=parent['supplementary_cert_count']+1,
       B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops=dict(
          rank=30,model_id=MID,flops=sorted(z['flop'] for z in SPECS),
          exact_line=LINE,actor='UTG_OOP',
          original_GTO_runs={z['flop']:z['gto_run'] for z in SPECS},
          real_NL2_actor_OOP_lock_runs={z['flop']:z['lock_run'] for z in SPECS},
          strict_GTO_NL2_pair_provenance_sha256s=proof,
          preflop_CFR_pinned_not_observed_NL2_private_hand=True,
          all_source_NL2_villain_private_hand_conditionals_unknown=True,
          no_generic_hand_class_GTO=True,
          exact_board_b50_nonpolarized_evidence_not_claimed=True),
       B247_new_exact_sources_not_in_frozen_V38_generic_source_evidence=proof,
       B247_new_exact_source_archives_separate_from_V38_immutable_ledger=True,
       no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
       PR2_remains_draft_never_merge=True)
    OUT.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    matrix=create(status)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'],matrix['EST'])==(152,240,0)
    assert len(matrix['models'])==152 and len(matrix['boards'])==584
    agg=matrix['strict_aggregate']
    assert (agg['named_board_proofs'],agg['hero_lock_variants'],
       agg['b50_research_candidate_boards'])==(584,676,133)
    assert agg['observed_marginal_pattern_nodes']==4510
    assert agg['assumed_pattern_nodes']==2139
    assert agg['unmatched_opponent_nodes']==3850
    assert all(q['no_general_bet_size_recommendation'] and q['strictly_reachable_combo_count']>0
               and q['hero_lock_proofs'] for q in matrix['boards'])
    report=audit(status)
    assert (report['cert_multiboard'],report['approx'],report['EST'])==(152,240,0)
    assert report['aggregate']['named_board_proofs']==584
    assert report['aggregate']['paired_hero_locked_source_variants']==676
    assert report['aggregate']['board_examples_with_b50_candidate']==133
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V39_B247',
      parent_v39_status_sha256=sha(OUT),
      all_new_turn_only_NL2_pool_pattern_counts_unknown_not_fabricated=True,
      no_general_bet_size_advice=True,
      no_observed_private_card_conditionals=True,PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    REPORT.write_text('# B247 V39 | rank30 UTG_CO UTG-OOP exact three-flop true GTO + partial NL2 CERT\n\n'
      '**152 CERT-MULTIBOARD /240 APPROX /0 EST**, across the original 392 nodes. '
      'Only rank30 changes; all 3 original 100bb, 5% rake/cap10bb, '
      'frozen preflop-CFR roots and exact flop b50-call / UTG-OOP TURN are separately '
      'SHA verified. Genuine original B235/B240/B243 GTO and authentic Rust '
      'B238/B242/B246 partial NL2 actor-OOP turn+river lock were paired by public board, '
      'actor, line and SPR. Each board has **one** full-street strictly reachable GTO '
      'hero combo (fragile evidence), all <=0.5% GTO exploitability, SPR <=5% error.\n\n'
      'Representative exact flops: KsQh4d/Tc, Js9h4d/Ts, QsJh4d/7s. '
      'The true NL2 lock is partial downstream only; pattern source counts are '
      'historically UNKNOWN where not verifiable, pooled street/size rates are '
      'not observed board- or private-hand conditional frequencies. '
      'No general texture/hand-class GTO claim and no exact 50%-pot nonpolar '
      'recommendation for these thin boards.\n\n'
      'All prior 581 authentic named boards and 673 lock variants are unchanged; '
      'total 584 boards and 676 locks, still only 133 exact-board 50%-pot '
      'nonpolarized research candidates. Keep UI as exact-board scope only. '
      'Original generic V38 source ledgers remain frozen; B247 new proven source '
      'archives are disclosed separately. Full 2475/2475 independent HU links '
      'must pass before commit. PR#2 Draft. NEVER MERGE.\n')
    MATDOC.write_text('# B247 V39 all 584 exact GTO/partial NL2 lock and medium evidence\n\n'+write_md(matrix))
    print('PASS B247',json.dumps(dict(CERT=152,APPROX=240,named=584,locks=676,
       new_rank=30,flops=sorted(x['flop'] for x in boards)),ensure_ascii=False),flush=True)
if __name__=='__main__': main()
