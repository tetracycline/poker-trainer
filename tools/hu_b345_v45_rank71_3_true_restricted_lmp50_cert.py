#!/usr/bin/env python3
"""B345: conditional rank71 V45 exact-source certification of genuine 100bb
restricted LMP b50-only GTO + true NL2 BB-OOP lock on three DIFFERENT flops
and >=2 textures, with original 40/70 actor, SPR, SHA, full board provenance.
No generic GTO, unrestricted-size, or observed private-hand NL2 rate claims.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import texture
from hu_cert_lock_medium_coverage_matrix import create,write_md
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data'); DOC=pathlib.Path('docs')
MID='ln-iso-lmp_r_model-vlgh2t';SPOT='LMP_CO_BB';LINE='b50 c/x b50 c/';SPR=9.916
PARENT=D/'nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json'
NEW=D/'nl2_hu_multiboard_status_v45_b345_rank71.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v45_b345.json'
PROOF=D/'nl2_hu_b345_v45_rank71_three_gto_nl2_source_gate.json'
FRESH=D/'nl2_hu_b343_rank71_three_real_lmp50_GTO_NL2_actor_reach.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def authentic_archive(batch,run):
    idx=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.index.json'
    gz=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.json.gz'
    ix=read(idx); data=gzip.decompress(gz.read_bytes())
    assert ix['run_id']==run and ix['gzip_sha256']==sha(gz)
    assert ix['source_sha256']==hashlib.sha256(data).hexdigest()
    result=json.loads(data)
    assert result['source_run_id']==run and not result['errors']
    return result,dict(run=run,index_sha256=sha(idx),archive_sha256=sha(gz))
def find_case(source,flop,turn,version):
    records=[]
    for a in source['artifacts']:
        if (a['spot'],a['flop'],a['version'])!=(SPOT,flop,version):continue
        assert not a['errors']
        records.extend(c for c in a['cases']
           if (c['flop_line'],c['turn'])==('b50 c',turn))
    assert len(records)==1,('unverified candidate case',flop,turn,version)
    c=records[0]
    assert c['empirical_scope']=='ASSUMED_PREFLOP_RANGES'
    assert c['flop_root_pot_bb']==2.5 and c['flop_root_stack_bb']==99
    assert len(c['source_sha256'])==64 and c['gto_exploitability_pct']<=.5
    return c
def actor_nodes(c):
    return {n['public_board']:n for n in c['nodes'] if
       n['exact_node_line']==LINE and n['acting_seat']==0
       and len(n['public_board'])==10 and n['strictly_reachable_combos']>0
       and abs(n['node_spr']-SPR)/SPR<=.05}
def board_pair(g,e,flop,turn,run):
    assert g['run_id']==e['run_id']==run
    if e['locked_hero_gap_pct'] is not None:assert e['locked_hero_gap_pct']<=.5
    original,locked=actor_nodes(g),actor_nodes(e)
    both=set(original)&set(locked)
    assert both,('GTO not same actor/model/board/SPR as actual NL2',flop,turn)
    public=sorted(both,key=lambda b:(-original[b]['strictly_reachable_combos'],b))[0]
    n=original[public];ne=locked[public]
    assert n['strictly_reachable_combos']>0 and ne['strictly_reachable_combos']>0
    assert n['source_actions'] and ne['source_actions']
    assert abs(n['node_spr']-ne['node_spr'])<=.01
    medium=int(n.get('medium_50pct_eligible_combos') or 0)
    research=bool(n.get('b50_nonpolarized_relative_equity_research_candidate',False))
    if research:assert medium>0
    lock=dict(version='exp_oop',run_id=run,sha256=e['source_sha256'],
      source_scope='AUTHENTIC_RUST_NL2_BB_OOP_PARTIAL_POOLED_STREET_SIZE_MARGINAL_RESTRICTED_LMP50',
      villain_observed_pattern_node_share_pct=None,
      source_not_real_per_combo_observation=True,
      unknown_history_frequency_filled_with_default=True,
      observed_marginal_source_nodes=None,assumed_default_source_nodes=None,
      unlocked_source_nodes=None,hero_model_gain_bb=None)
    return dict(flop=flop,turn=turn,public_board=public,
      actual_exact_action_line=LINE,acting_seat=0,exact_flop_action='b50 c',
      actual_pot_bb=n['pot_bb'],actual_effective_stack_bb=n['remaining_bb'],
      actual_spr=n['node_spr'],model_assumed_spr=SPR,
      relative_spr_error_pct=round(100*abs(n['node_spr']-SPR)/SPR,5),
      genuine_gto_exploitability_pct=g['gto_exploitability_pct'],
      source_run_id=run,source_sha256=g['source_sha256'],
      source_kind='ASSUMED_PREFLOP_RANGES',assumed_preflop_ranges=True,
      exact_combo_reachable=n['source_reachable_combos'],
      strict_full_street_combo_reachable=n['strictly_reachable_combos'],
      exact_node_actions=n['source_actions'],
      medium_50pct_eligible_combos=medium,
      b50_nonpolarized_relative_equity_research_candidate=research,
      flop_texture=texture(flop),nl2_locked_variants=[lock])
def main():
    old=read(PARENT)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V44_B331_RANK60_FOUR'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(156,236,0,392)
    assert old['records'][MID]['label']=='APPROX'
    assert old['records'][MID]['assumed_model_node_spr']==SPR
    newest=read(FRESH)
    assert newest['schema']=='NL2_HU_B343_ORIGINAL_RESTRICTED_50_GTO_PLUS_REAL_NL2_BB_OOP_V1'
    assert newest['original_restricted_game_tree_identical_to_B19_B26']
    assert newest['authenticated_independent_new_named_flops']==3
    eligible=newest['new_rank71_legal_genuine_GTO_NL2_pair_flops']
    assert eligible and eligible==[r['flop'] for r in newest['tested'] if r['third_flop_candidate']]
    third=eligible[0]  # preregistered first-eligible source order, not EV optimization
    info=next(r for r in newest['tested'] if r['flop']==third)
    turn=info['GTO']['turn']
    assert turn==info['authentic_partial_NL2_OOP_lock']['turn']
    run=newest['original_GTO_run_id']
    refs=[('4s4h2d','8s','B19_LMP50_RESTRICTED',44762388523),
          ('7s5h3d','6c','B26_LMP_NONPAIRED',44769773770),
          (third,turn,'B343_LMP50_LEGAL',run)]
    cache={};boards=[];links=[]
    for flop,turn,batch,jobid in refs:
        if batch not in cache:cache[batch]=authentic_archive(batch,jobid)
        archive,anchor=cache[batch]
        gt=find_case(archive,flop,turn,'gto')
        nl=find_case(archive,flop,turn,'exp_oop')
        if batch=='B343_LMP50_LEGAL':
            assert gt['source_sha256']==info['GTO']['actual_rust_turn_river_sha256']
            assert nl['source_sha256']==info['authentic_partial_NL2_OOP_lock']['actual_rust_turn_river_sha256']
        boards.append(board_pair(gt,nl,flop,turn,jobid))
        links.append(dict(flop=flop,turn=turn,batch=batch,original_GTO_run=jobid,
            original_gto_case_sha256=gt['source_sha256'],
            real_NL2_actor_partial_case_sha256=nl['source_sha256'],**anchor))
    assert len(boards)==3 and len({x['flop'] for x in boards})==3
    assert len({x['flop_texture'] for x in boards})>=2
    assert all(x['relative_spr_error_pct']<=5 and x['strict_full_street_combo_reachable']>0 and
        x['acting_seat']==0 and x['actual_exact_action_line']==LINE and x['assumed_preflop_ranges']
        and x['nl2_locked_variants'] and len(x['nl2_locked_variants'][0]['sha256'])==64 for x in boards)
    newer=copy.deepcopy(old)
    newer['records'][MID].update(label='CERT-MULTIBOARD',high_frequency_preregistered=True,
      original_top24_high_frequency_preregistered=False,source_blind_expansion_rank=71,
      prereg_cohort='ORIGINAL_B19_B26_R71_TWO_REAL_PAIRS_PLUS_FIRST_GENUINE_B343_POSITIVE_50_ONLY_RUST',
      certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
      blocked_reason=None,
      source_credibility='3_AUTHENTIC_DIFFERENT_LMP50_100BB_RUST_GTO_AND_NL2_BB_OOP_SHA_WITH_2_TEXTURES')
    assert {k for k in old['records'] if old['records'][k]!=newer['records'][k]}=={MID}
    newer.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V45_B345_RANK71',
      CERT_MULTIBOARD=157,APPROX=235,EST=0,TOTAL=392,
      parent_v44_sha256=sha(PARENT),
      source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{71}),
      supplementary_cert_count=old['supplementary_cert_count']+1,
      B345_rank71_true_3_flop_GTO_NL2_OOP_evidence=dict(
        third_flop=third,third_turn=turn,source_run=run,
        flops=[x['flop'] for x in boards],
        textures=sorted({x['flop_texture'] for x in boards}),
        original_archive_provenance=links,
        source_tree='RESTRICTED_LMP_50_ONLY_100BB_ASSUMED_PREFLOP',
        never_claim_unrestricted_game_or_private_hand_NL2_observation=True))
    assert sum(x['label']=='CERT-MULTIBOARD' for x in newer['records'].values())==157
    assert sum(x['label']=='APPROX' for x in newer['records'].values())==235
    matrix=create(newer)
    assert (len(matrix['boards']),len(matrix['models']))==(600,157)
    assert (matrix['strict_aggregate']['named_board_proofs'],
            matrix['strict_aggregate']['hero_lock_variants'])==(600,692)
    audited=audit(newer)
    assert (audited['cert_multiboard'],audited['approx'],audited['EST'])==(157,235,0)
    assert (audited['aggregate']['named_board_proofs'],
            audited['aggregate']['paired_hero_locked_source_variants'])==(600,692)
    assert audited['not_generalized_handclass_GTO'] and audited['not_actual_NL2_earnings']
    NEW.write_text(json.dumps(newer,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V45_B345',
      parent_v45_status_sha256=sha(NEW),
      partial_NL2_locks_are_not_whole_flop_GTO=True,
      NL2_private_combo_conditional_rates_not_observed=True,
      unknown_source_denominators_are_not_zero_or_empirical=True,
      only_exact_board_b50_nonpolarized_research=True,PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    PROOF.write_text(json.dumps(dict(schema='NL2_HU_B345_V45_RANK71_GENUINE_3_GTO_NL2_SOURCE_CERT_V1',
      source_B343_sha256=sha(FRESH),parent_V44_sha256=sha(PARENT),
      V45_sha256=sha(NEW),matrix_sha256=sha(MATRIX),
      source_details=links,certified_flops=[x['flop'] for x in boards],
      two_plus_textures=sorted({x['flop_texture'] for x in boards}),
      third_flop=third,CERT=157,APPROX=235,EST=0,TOTAL=392,
      named_boards=600,actual_actor_NL2_lock_source_variants=692,
      source_is_real_restricted_LMP50_not_unrestricted=True,
      no_observed_private_hand_NL2_rates=True,HU2475_audit_required_before_commit=True,
      PR2_Draft_NEVER_MERGE=True),ensure_ascii=False,indent=2)+'\n')
    DOC.mkdir(exist_ok=True)
    (DOC/'NL2_HU_B345_V45_RANK71_THREE_REAL_GTO_NL2_CERT.md').write_text(
      '# B345 V45 genuine restricted LMP50 three-flop rank71 certificate\n\n'
      'Exact public boards: '+', '.join(x['flop']+'/'+x['turn'] for x in boards)+'. '
      'Only these named boards have true 100bb LMP-50-only original GTO plus actor-correct real NL2 Rust partially locked source with source SHA and >=40%/70% prior actions, SPR9.916 +-5%, two textures. '
      'Explicit assumed 169-class preflop, pooled street-size NL2 marginal rates NOT measured per-private-card conditional villain data, no unrestricted/full-tree generic GTO. '
      'V45 157 CERT /235 APPROX /0 EST, 600 authenticated named board proofs, 692 genuine actor partial locks. '
      'Full HU 2475/2475 independent audit required before push; PR2 Draft NEVER MERGE.\n')
    print('PASS B345 V45',third,'CERT157/APPROX235',flush=True)
if __name__=='__main__':main()
