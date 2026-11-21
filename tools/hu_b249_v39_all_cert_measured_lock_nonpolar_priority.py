#!/usr/bin/env python3
"""B249 V39 source provenance audit for EVERY newly updated 584 exact-board CERT.
Recompute all 676 actual actor-NL2 lock source variants without inferring private
hole-card conditional rates or generalized 50%-pot/depolarized recommendations.
"""
import collections,csv,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create

D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v39_b247_rank30.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v39_b247.json'
OLD=D/'nl2_hu_b244_v38_all_581_measured_lock_nonpolar_gap_priority.json'
OUT=D/'nl2_hu_b249_v39_all_584_measured_lock_medium_source_gaps.json'
CSV=D/'nl2_hu_b249_v39_all_584_lock_medium_source_gap_priority.csv'
MD=DOC/'NL2_HU_B249_V39_ALL_584_NAMED_BOARD_LOCK_MEDIUM_EVIDENCE_GAPS.md'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(z):return (z['model_id'],z['flop'],z['turn'],z['exact_action_line'],z['actor_seat'])

def main():
    s=load(STATUS);prior=load(OLD);oldmatrix=load(MATRIX)
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(152,240,0,392)
    assert (prior['CERT_MULTIBOARD'],prior['APPROX'],prior['EST'])==(151,241,0)
    assert oldmatrix['parent_v39_status_sha256']==sha(STATUS)
    m=create(s)
    assert (m['CERT_MULTIBOARD'],m['APPROX'])==(152,240)
    assert m['boards']==oldmatrix['boards'] and m['models']==oldmatrix['models']
    assert m['strict_aggregate']==oldmatrix['strict_aggregate']
    assert len(m['boards'])==584 and len(m['models'])==152
    ag=m['strict_aggregate']
    assert (ag['named_board_proofs'],ag['hero_lock_variants'],ag['b50_research_candidate_boards'])==(584,676,133)
    assert (ag['observed_marginal_pattern_nodes'],ag['assumed_pattern_nodes'],
            ag['unmatched_opponent_nodes'])==(4510,2139,3850)
    independent=audit(s)
    assert (independent['cert_multiboard'],independent['approx'],independent['EST'])==(152,240,0)
    assert (independent['aggregate']['named_board_proofs'],
      independent['aggregate']['paired_hero_locked_source_variants'],
      independent['aggregate']['board_examples_with_b50_candidate'])==(584,676,133)
    assert independent['not_generalized_handclass_GTO'] and independent['not_actual_NL2_earnings']
    old={key(z):z for z in prior['all_581_board_source_rows']}
    assert len(old)==581
    current={key(z):z for z in m['boards']}
    assert len(current)==584 and set(old).issubset(current)
    # All 581 authentic V38 names, action lines and locked-source categories
    # remain untouched; the only additions are rank30's 3 genuine thin boards.
    rank30=[x for x in current.values() if x['model_id']=='ln-opfr-t_model-1hmsxaw']
    assert len(rank30)==3 and {z['flop'] for z in rank30}=={'KsQh4d','Js9h4d','QsJh4d'}
    assert all(z['actor_seat']==0 and z['exact_action_line']=='b50 c/' and
      len(z['hero_lock_proofs'])==1 and z['strictly_reachable_combo_count']==1
      for z in rank30)
    rows=[];tot=collections.Counter()
    for k,b in current.items():
        assert b['strictly_reachable_combo_count']>0 and b['hero_lock_proofs']
        assert len(b['GTO_sha256'])==64 and b['genuine_GTO_exploitability_pct']<=.5
        assert b['spr_relative_error_pct']<=5
        assert b['generic_handclass_texture_policy_is_not_GTO'] and b['no_general_bet_size_recommendation']
        nobs=nass=nunm=nunknown=0
        for lock in b['hero_lock_proofs']:
            assert lock['source_run_id']>0 and len(lock['source_sha256'])==64
            assert lock['EV_is_model_estimate_not_real_winnings']
            counts=lock['source_node_counts']
            if lock['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN':
                assert all(z is None for z in counts.values())
                nunknown+=1
            else:
                assert lock['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
                assert all(isinstance(z,int) and z>=0 for z in counts.values())
                nobs+=counts['observed_marginal']
                nass+=counts['assumed_default']
                nunm+=counts['unmatched_unlocked']
        is50=(b['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE')
        if is50:assert b['b50_eligible_combo_count']>0
        else:assert b['b50_research_status']=='NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'
        if k in old:
            x=old[k]
            assert (x['GTO_source_run'],x['GTO_source_sha256'],x['strict_hero_combos'])==(
              b['GTO_run_id'],b['GTO_sha256'],b['strictly_reachable_combo_count'])
            assert (x['measured_NL2_street_size_marginal_nodes'],x['assumed_default_nodes'],
              x['unmatched_villain_nodes'],x['historical_unknown_lock_variants'])==(
              nobs,nass,nunm,nunknown)
            assert x['b50_exact_board_nonpolarized_research_only']==is50
        else:
            assert b['model_id']=='ln-opfr-t_model-1hmsxaw' and nunknown==1
            assert (nobs,nass,nunm)==(0,0,0)
            assert not is50
            assert b['assumed_preflop_ranges'] is False
            assert b['GTO_run_id'] in (44894369547,44895186652,44900567417)
        typ=('HISTORICAL_UNKNOWN_PRESENT' if nunknown else
          'ASSUMED_DEFAULT_PRESENT' if nass else
          'POOL_MARGINAL_ONLY_NOT_PRIVATE_CARD' if nobs else 'NO_MEASURED_RATE')
        line=dict(rank=b['rank'],model_id=b['model_id'],spot=b['spot'],
          flop=b['flop'],turn=b['turn'],exact_action_line=b['exact_action_line'],
          actor_seat=b['actor_seat'],true_strict_hero_combos=b['strictly_reachable_combo_count'],
          genuine_GTO_run=b['GTO_run_id'],genuine_GTO_sha256=b['GTO_sha256'],
          real_NL2_hero_lock_runs=[z['source_run_id'] for z in b['hero_lock_proofs']],
          real_NL2_hero_lock_variants=len(b['hero_lock_proofs']),
          observed_NL2_pool_street_size_marginal_nodes=nobs,assumed_default_nodes=nass,
          unmatched_villain_nodes=nunm,historical_unknown_lock_variants=nunknown,
          rate_provenance=typ,
          exact_named_board_50pct_nonpolar_research_only=is50,
          b50_strict_eligible_combos=b['b50_eligible_combo_count'],
          new_empirical_NL2_private_card_conditional_rates=0,
          universal_50pct_recommendation=False)
        rows.append(line)
        tot['boards']+=1;tot['locks']+=len(b['hero_lock_proofs']);tot['observed_nodes']+=nobs
        tot['assumed_nodes']+=nass;tot['unmatched_nodes']+=nunm
        tot['historical_unknown_lock_variants']+=nunknown
        tot['b50_exact_named_only']+=int(is50)
        tot['board_has_assumed_or_unknown_or_no_observed_marginal']+=int(bool(nass or nunknown or not nobs))
        tot['board_has_historical_unknown']+=int(bool(nunknown))
    assert (tot['boards'],tot['locks'],tot['b50_exact_named_only'])==(584,676,133)
    assert (tot['observed_nodes'],tot['assumed_nodes'],
       tot['unmatched_nodes'],tot['historical_unknown_lock_variants'])==(4510,2139,3850,318)
    assert tot['board_has_assumed_or_unknown_or_no_observed_marginal']==570
    rows.sort(key=lambda x:(x['rank'],-x['historical_unknown_lock_variants'],
                              -x['assumed_default_nodes'],x['flop']))
    with CSV.open('w',newline='',encoding='utf8') as f:
        fields=['rank','model_id','spot','flop','turn','exact_action_line','actor_seat',
            'true_strict_hero_combos','genuine_GTO_run','real_NL2_hero_lock_variants',
            'observed_NL2_pool_street_size_marginal_nodes','assumed_default_nodes',
            'unmatched_villain_nodes','historical_unknown_lock_variants',
            'rate_provenance','exact_named_board_50pct_nonpolar_research_only',
            'b50_strict_eligible_combos']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(rows)
    result=dict(schema='NL2_HU_B249_V39_ALL_584_TRUE_CERT_BOARD_NL2_LOCK_MEDIUM_GAP_V1',
        parent_status_sha256=sha(STATUS),original_V39_lock_matrix_sha256=sha(MATRIX),
        original_V38_B244_priority_sha256=sha(OLD),
        CERT_MULTIBOARD=152,APPROX=240,EST=0,TOTAL=392,
        genuine_named_boards=584,real_hero_NL2_lock_variants=676,
        exact_50pct_only_research_candidates=133,counts=dict(tot),
        rank30_3_new_true_actor_GTO_partial_NL2_boards_with_unknown_pattern_denominators=3,
        old_581_V38_exact_board_GTO_and_NL2_source_provenance_identical=True,
        per_exact_board_source_provenance=rows,
        highest_frequency_missing_measured_rate_priority=[z for z in rows
          if z['assumed_default_nodes'] or z['historical_unknown_lock_variants'] or
          not z['observed_NL2_pool_street_size_marginal_nodes']][:60],
        all_new_NL2_private_hand_conditional_rates_unmeasured=True,
        b50_never_generalized_to_all_textures=True,
        no_generic_model_certification_inferred_from_research=True,
        PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    docs=['# B249 V39 all 584 true named GTO/NL2 actor-lock rate evidence audit','',
      '**152 CERT /240 APPROX /0 EST**. Every newly certified rank30 board and '
      'all 581 unchanged previous certified boards were rechecked against the original '
      '584-row evidence matrix and genuine NL2 partial actor-lock source SHA.',
      f"Lock variants: {tot['locks']}; observed NL2 **pool marginal** source nodes "
      f"{tot['observed_nodes']}; assumed defaults {tot['assumed_nodes']}; "
      f"unmatched opponent nodes {tot['unmatched_nodes']}; historical unknown "
      f"source variants {tot['historical_unknown_lock_variants']}.",
      f"Source rate gaps: {tot['board_has_assumed_or_unknown_or_no_observed_marginal']}/584 "
      "boards; only 133 exact-board 50%-pot depolarization research candidates. "
      "The three new rank30 sources each have only one reachable combo and UNKNOWN "
      "opponent per-node source denominators — do not substitute assumed numbers.",
      '',
      '|rank|named flop / turn|actor|measured pool / assumed / unmatched|unknown source variants|50% pot research|',
      '|---:|---|---|---:|---:|---|']
    for z in result['highest_frequency_missing_measured_rate_priority'][:45]:
        docs.append(f"|{z['rank']}|{z['flop']} / {z['turn']}|{'OOP' if z['actor_seat']==0 else 'IP'}|"
          f"{z['observed_NL2_pool_street_size_marginal_nodes']}/"
          f"{z['assumed_default_nodes']}/{z['unmatched_villain_nodes']}|"
          f"{z['historical_unknown_lock_variants']}|"
          f"{'exact-board only' if z['exact_named_board_50pct_nonpolar_research_only'] else 'not proven'}|")
    docs+=['','This does not represent measured board-/opponent-private-hand conditional NL2 rates, '
      'universal 50%-pot recommendations, full-flop NL2 locks or live NL2 winnings.',
      'Full 584 named board and 2475/2475 HU independent GitHub Actions must pass before commit.',
      'PR#2 Draft, NEVER MERGE.']
    MD.write_text('\n'.join(docs)+'\n')
    print('PASS B249',json.dumps(dict(tot),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
