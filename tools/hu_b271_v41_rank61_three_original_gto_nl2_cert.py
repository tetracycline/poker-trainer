#!/usr/bin/env python3
"""B271 V41: failclosed rank61 3 REAL 100bb CO_BB original GTO SHA boards
paired to genuine separately solved Rust actor-CO-IP NL2 partially locked
TURN/RIVER children. Strict original ancestry >=40% and >=70% of best,
actor1, exact x b100 c/x, SPR within 5%, preflop solver CFR pinned.
Use only exact board/turn/seat, no generic texture or private-card rate claim.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import texture,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
OLD=D/'nl2_hu_multiboard_status_v40_b265_rank313.json'
STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v41_b271.json'
REPORT=DOC/'NL2_HU_B271_V41_R61_THREE_ORIGINAL_GTO_TRUE_COIP_NL2_CERT.md'
MATDOC=DOC/'NL2_HU_B271_V41_ALL_590_NAMED_BOARD_LOCK_MEDIUM.md'
MID='ln-ipfr-t_model-qpx6tn'
LINE='x b100 c/x'
SPR=5.576
SPECS=[
 dict(flop='KsQh4d',turn='Tc',GTO_batch='B253',GTO_run=44902146101,
      NL2_batch='B256',NL2_run=44902973337,GTO_strict=65),
 dict(flop='Js9h5d',turn='Ah',GTO_batch='B262',GTO_run=44902831383,
      NL2_batch='B264',NL2_run=44903478906,GTO_strict=110),
 dict(flop='QsJh4d',turn='7s',GTO_batch='B266',GTO_run=44934430727,
      NL2_batch='B269',NL2_run=44935281174,GTO_strict=80),
]
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bytes_json(p):return json.loads(gzip.decompress(p.read_bytes()))
def validate_pair(s):
    f=s['flop'];t=s['turn'];g=s['GTO_batch'];l=s['NL2_batch']
    pinpath=D/f'nl2_hu_{g.lower()}_rank61_cobb_{f}_gto_parent_pin.json'
    garchive=D/f'solver_evidence/NL2_MULTIBOARD_{g}_R61_{f.upper()}_GTO.json.gz'
    gindex=D/f'solver_evidence/NL2_MULTIBOARD_{g}_R61_{f.upper()}_GTO.index.json'
    larchive=D/f'solver_evidence/NL2_MULTIBOARD_{l}_R61_{f.upper()}_EXP_IP.json.gz'
    lindex=D/f'solver_evidence/NL2_MULTIBOARD_{l}_R61_{f.upper()}_EXP_IP.index.json'
    assert all(p.is_file() for p in (pinpath,garchive,gindex,larchive,lindex))
    pin,gi,li=load(pinpath),load(gindex),load(lindex)
    assert (pin['source_run_id'],gi['run_id'])==(s['GTO_run'],s['GTO_run'])
    assert (pin['spot'],pin['flop'],pin['turn'],pin['flop_line'],pin['turn_line'])==(
        'CO_BB',f,t,'x b100 c','x')
    assert (pin['target_rank'],pin['model_id'])==(61,MID)
    assert pin['preflop_CFR_pinned_not_observed_NL2_private_card'] is True
    assert pin['original_full_100bb_cobb_gto_source_pinned'] is True
    assert pin['direct_nl2_lock_source_present'] is False
    assert (pin['target_exact_actor_IP_turn_nodes'],pin['target_exact_actor_IP_turn_strict_combos'])==(1,s['GTO_strict'])
    assert (gi['verified_cases'],gi['gto_cases'],gi['locked_cases'])==(1,1,0)
    assert gi['exact_target_actor_IP_turn_strict_combos']==s['GTO_strict']
    assert gi['source_sha256']==hashlib.sha256(gzip.decompress(garchive.read_bytes())).hexdigest()
    assert gi['gzip_sha256']==sha(garchive)
    assert (gi['original_parent_GTO_root_SHA256'],gi['original_parent_GTO_job_SHA256'],
      gi['original_parent_GTO_manifest_SHA256'])==(
        pin['original_gto_root_sha256'],pin['original_gto_job_sha256'],
        pin['original_gto_manifest_sha256'])
    assert li['schema']=='NL2_HU_B257_CO_BB_EXACT_ORIGINAL_GTO_PLUS_REAL_NL2_IP_PARTIAL_LOCK_V1'
    assert (li['source_run_id'],li['source_batch'])==(s['NL2_run'],l)
    assert (li['original_GTO_batch'],li['original_GTO_source_run'])==(g,s['GTO_run'])
    assert (li['rank'],li['model_id'],li['spot'],li['flop'],li['turn'])==(
        61,MID,'CO_BB',f,t)
    assert (li['exact_line'],li['actor'],li['acting_seat'])==(LINE,'CO_IP',1)
    assert li['gto_pin_sha256']==sha(pinpath) and li['gto_index_sha256']==sha(gindex)
    assert li['gto_archive_sha256']==sha(garchive)
    assert (li['original_GTO_root_sha256'],li['original_GTO_job_sha256'])==(
        pin['original_gto_root_sha256'],pin['original_gto_job_sha256'])
    assert li['original_GTO_actor_strict_combos']==s['GTO_strict']
    assert li['NL2_actor_strict_combos']>0 and li['NL2_actor_model_SPR_eligible_combos']>0
    assert li['genuine_actor_matched_GTO_NL2_board'] is True
    assert len(li['authentic_NL2_Rust_source_sha256'])==64
    assert li['authentic_NL2_Rust_gzip_sha256']==sha(larchive)
    assert li['authentic_NL2_Rust_source_sha256']==hashlib.sha256(gzip.decompress(larchive.read_bytes())).hexdigest()
    assert li['model_SPR']==SPR
    assert li['original_preflop_CFR_not_observed_NL2_private_cards'] is True
    assert li['partial_downstream_only_not_whole_flop_lock'] is True
    assert li['no_observed_per_private_hand_NL2_conditionals'] is True
    assert li['no_generalized_nonpolar50_bet_advice'] is True
    assert li['no_generic_CERT_upgrade'] and li['PR2_Draft_NEVER_MERGE']
    for n in li['genuine_actor_node_examples']:
        assert n['strict_combos']>0 and n['relative_spr_error_pct']<=5
        assert len(n['board'])==8 and n['board'][-2:] not in ('',)
    assert sum(n['strict_combos'] for n in li['genuine_actor_node_examples'])==li['NL2_actor_strict_combos']
    graw=bytes_json(garchive)
    assert graw['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert not graw['errors'] and graw['source_run_id']==s['GTO_run']
    assert (graw['exact_board_gto_sources'],graw['imputed_pool_locked_sources'])==(1,0)
    assert len(graw['artifacts'])==1
    a=graw['artifacts'][0]
    assert (a['version'],a['spot'],a['flop'])==('gto','CO_BB',f) and not a['errors']
    assert len(a['cases'])==1
    c=a['cases'][0]
    assert (c['flop_line'],c['turn'],c['pot_family'])==('x b100 c',t,'SRP')
    assert (c['flop_root_pot_bb'],c['flop_root_stack_bb'])==(5.5,97.5)
    assert c['gto_exploitability_pct'] is not None and c['gto_exploitability_pct']<=.5
    assert c['empirical_scope']=='PINNED_PREFLOP_CFR'
    candidates=[n for n in c['nodes'] if n['exact_node_line']==LINE and n['acting_seat']==1
      and len(n['public_board'])==8 and n['strictly_reachable_combos']>0]
    assert len(candidates)==1
    n=candidates[0]
    assert n['public_board'].endswith(t)
    assert n['strictly_reachable_combos']==s['GTO_strict']
    assert n['source_reachable_combos']>0
    assert n['source_actions']
    assert abs(n['node_spr']-SPR)/SPR<=.05
    raw=bytes_json(larchive)
    assert raw['line0']=='x b100 c' and raw['turn']==t
    assert raw['info'].get('hero_gap_pct') is not None
    assert any(z['player']==1 and z['line']==LINE and
       z['board']==n['public_board'] and len(z['board'])==8 for z in raw['nodes'])
    assert n['public_board'] in [z['board'] for z in li['genuine_actor_node_examples']]
    medium=int(n.get('medium_50pct_eligible_combos') or 0)
    mid_candidate=bool(n.get('b50_nonpolarized_relative_equity_research_candidate',False))
    if mid_candidate: assert medium>0
    sample=dict(
        flop=f,turn=t,public_board=n['public_board'],
        actual_exact_action_line=LINE,acting_seat=1,
        exact_flop_action='x b100 c',
        actual_pot_bb=n['pot_bb'],actual_effective_stack_bb=n['remaining_bb'],
        actual_spr=n['node_spr'],model_assumed_spr=SPR,
        relative_spr_error_pct=round(100*abs(n['node_spr']-SPR)/SPR,4),
        genuine_gto_exploitability_pct=c['gto_exploitability_pct'],
        source_run_id=s['GTO_run'],source_sha256=c['source_sha256'],
        source_kind='PINNED_PREFLOP_CFR',assumed_preflop_ranges=False,
        exact_combo_reachable=n['source_reachable_combos'],
        strict_full_street_combo_reachable=n['strictly_reachable_combos'],
        exact_node_actions=n['source_actions'],
        medium_50pct_eligible_combos=medium,
        b50_nonpolarized_relative_equity_research_candidate=mid_candidate,
        flop_texture=texture(f),
        nl2_locked_variants=[dict(version='exp_ip',run_id=s['NL2_run'],
            sha256=li['authentic_NL2_Rust_source_sha256'],
            source_scope='TURN_ONLY_GENUINE_NL2_POOL_MARGINAL_PARTIAL_RUST_LOCK',
            villain_observed_pattern_node_share_pct=None,
            source_not_real_per_combo_observation=True,
            unknown_history_frequency_filled_with_default=True,
            observed_marginal_source_nodes=None,
            assumed_default_source_nodes=None,
            unlocked_source_nodes=None,
            hero_model_gain_bb=None)])
    return sample,dict(flop=f,turn=t,
        original_GTO_run=s['GTO_run'],source_lock_run=s['NL2_run'],
        pin_sha256=sha(pinpath),gto_index_sha256=sha(gindex),gto_archive_sha256=sha(garchive),
        NL2_index_sha256=sha(lindex),NL2_archive_sha256=sha(larchive),
        GTO_strict_actor_combos=s['GTO_strict'],
        NL2_strict_actor_combos=li['NL2_actor_strict_combos'],
        NL2_SPR_eligible_combos=li['NL2_actor_model_SPR_eligible_combos'])
def main():
    old=load(OLD)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(153,239,0,392)
    assert len(old['records'])==392
    assert old['records'][MID]['label']=='APPROX'
    assert old['records']['ln-iso-lmp_r_model-wpg493']['label']=='CERT-MULTIBOARD'
    assert old['records']['ln-opfr-t_model-1hmsxaw']['label']=='CERT-MULTIBOARD'
    assert old['no_generic_texture_GTO'] and old['no_observed_private_card_NL2_rates']
    boards,source_proofs=[],[]
    for s in SPECS:
        b,p=validate_pair(s);boards.append(b);source_proofs.append(p)
    assert len(boards)==3 and {z['flop'] for z in boards}=={'KsQh4d','Js9h5d','QsJh4d'}
    assert len({z['flop_texture'] for z in boards})>=2
    assert all(z['acting_seat']==1 and z['actual_exact_action_line']==LINE and
       z['strict_full_street_combo_reachable']>0 and z['nl2_locked_variants'] and
       z['relative_spr_error_pct']<=5 and
       z['genuine_gto_exploitability_pct']<=.5 for z in boards)
    out=copy.deepcopy(old)
    out['records'][MID].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=61,
        prereg_cohort='V40_TWO_EXACT_CO_BB_GTO_PLUS_REAL_COIP_NL2_LOCK_FLOPS_B253_B256_B262_B264_PLUS_B266_B269_THIRD',
        certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility='3_DIFFERENT_TRUE_100BB_PINNED_PREFLOP_CFR_GTO_SHA_AND_AUTHENTIC_RUST_PARTIAL_NL2_CO_IP')
    assert {k for k in old['records'] if old['records'][k]!=out['records'][k]}=={MID}
    assert sum(v['label']=='CERT-MULTIBOARD' for v in out['records'].values())==154
    assert sum(v['label']=='APPROX' for v in out['records'].values())==238
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61',
        CERT_MULTIBOARD=154,APPROX=238,EST=0,TOTAL=392,
        parent_v40_sha256=sha(OLD),
        source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{61}),
        supplementary_cert_count=old['supplementary_cert_count']+1,
        B271_rank61_three_authentic_GTO_NL2_CO_IP_flops=dict(
            rank=61,model_id=MID,flops=sorted(z['flop'] for z in boards),
            exact_line=LINE,actor='CO_IP',model_SPR=SPR,
            true_100bb_preflop_CFR_source_frozen_not_observed_NL2_private_card=True,
            only_exact_public_board_actions_actor_SPR_certified=True,
            original_GTO_and_NL2_actor_locked_source_pins=source_proofs),
        B271_authentic_sha_gto_and_NL2_new_exact_board_source_archives=[
            f"data/solver_evidence/NL2_MULTIBOARD_{x['GTO_batch']}_R61_{x['flop'].upper()}_GTO.json.gz"
            for x in SPECS]+[
            f"data/solver_evidence/NL2_MULTIBOARD_{x['NL2_batch']}_R61_{x['flop'].upper()}_EXP_IP.json.gz"
            for x in SPECS],
        B271_previous_V40_source_ledger_SHA_unchanged=True,
        no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    STATUS.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'],matrix['EST'])==(154,238,0)
    assert (len(matrix['models']),len(matrix['boards']))==(154,590)
    ag=matrix['strict_aggregate']
    assert (ag['named_board_proofs'],ag['hero_lock_variants'])==(590,682)
    assert ag['b50_research_candidate_boards']>=133
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0 and
        z['no_general_bet_size_recommendation'] for z in matrix['boards'])
    verified=audit(out)
    assert (verified['cert_multiboard'],verified['approx'],verified['EST'])==(154,238,0)
    assert (verified['aggregate']['named_board_proofs'],
        verified['aggregate']['paired_hero_locked_source_variants'])==(590,682)
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V41_B271',
        parent_v41_status_sha256=sha(STATUS),
        unknown_source_denominators_are_not_zero_or_empirical=True,
        only_exact_board_50pct_research=True,
        PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    REPORT.write_text('# B271 V41 | rank61 three real GTO + NL2 actor CO-IP locked turns\n\n'
      '**154 CERT-MULTIBOARD / 238 APPROX / 0 EST**, original 392 models, ONLY rank61 newly promoted. '
      'Exact public boards: KsQh4d/Tc, Js9h5d/Ah, QsJh4d/7s. '
      'Every source original GTO is genuine 100bb CO_BB pinned-preflop-CFR Rust, '
      'GTO gap <=0.5%, exact CO-IP x b100 c/x after 100%-pot cbet-call, '
      'SPR near 5.576 (<=5% relative error), full ancestry 40%/70% gate positive. '
      'GTO strict actor combos: 65, 110, 80. '
      'Real Rust NL2 pooled marginal/assumed partial locked CO-IP turn/river sources '
      'B256, B264, B269 are each separately original SHA/actor/SPR verified. '
      'The origin of NL2 opponent *private-hand* conditional action rates is NOT measured; '
      'these 3 downstream lock variants have per-node observed/assumed denominator UNKNOWN, '
      'not zero or genuinely observed per-combo. Full-flop root remains GTO, '
      'not a whole-tree locked NL2 computation. '
      '50%-pot nonpolarized is only supported for exact raw-public-board research candidate '
      'when eligible combos are proven; no generic handclass/texture action or earnings are GTO certified. '
      'All prior V40 587 named boards and 679 locks remain unchanged, 3 newly added. '
      'Full 590 named source/2475 HU Actions must PASS, PR2 Draft NEVER MERGE.\n')
    MATDOC.write_text('# B271 V41 590 authentic named GTO/CO-IP NL2 lock and medium50 evidence\n\n'+write_md(matrix))
    print('PASS B271 V41',json.dumps(dict(CERT=154,APPROX=238,flops=sorted(z['flop'] for z in boards),
        named=590,locks=ag['hero_lock_variants'],b50=ag['b50_research_candidate_boards']),
        ensure_ascii=False),flush=True)
if __name__=='__main__':main()
