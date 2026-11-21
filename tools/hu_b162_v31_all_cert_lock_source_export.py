#!/usr/bin/env python3
"""B162: once V31 B161 has really committed, export every genuine NL2
hero-side lock variant on all 557 exact named CERT boards, including
pooled observed/assumed/UNKNOWN villain source provenance and 50% exact
non-polar research status. No generic strategy, no new certification.
"""
import collections,csv,hashlib,io,json,pathlib,re
D=pathlib.Path('data')
STATUS=D/'nl2_hu_multiboard_status_v31_b161_rank150.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v31_b161.json'
CSV=D/'nl2_hu_b162_v31_all_557_named_board_hero_lock_sources.csv'
INDEX=D/'nl2_hu_b162_v31_all_557_named_board_hero_lock_sources.index.json'
DOC=pathlib.Path('docs/NL2_HU_B162_V31_ALL_557_NAMED_BOARD_LOCK_SOURCE_PROVENANCE.md')
COLUMNS=[
 'rank','model_id','spot','pot_family','street','flop','turn',
 'public_board','exact_action_line','hero_actor_seat','true_spr',
 'estimated_spr_relative_error_pct','genuine_GTO_gap_pct',
 'strict_full_sequence_legal_combo_count','original_GTO_run','original_GTO_sha256',
 'LMP_ISO_preflop_range_assumed','NL2_lock_variant_ordinal',
 'NL2_lock_total_variants_for_board','NL2_lock_run','NL2_lock_version',
 'NL2_lock_source_scope','NL2_lock_street_scope','NL2_lock_sha256',
 'observed_NL2_pool_marginal_nodes','assumed_default_nodes',
 'unmatched_unlocked_villain_nodes','observed_fraction_source_nodes_pct',
 'historical_source_denominators_unknown','any_assumed_default_disclosed',
 'NL2_pool_rate_origin_class','b50_exact_board_nonpolar_research_flag',
 'b50_eligible_strict_legal_combo_count','model_hero_gain_bb_not_real_profit',
 'no_generic_texture_GTO','no_private_card_conditional_NL2_rate',
 'not_a_bet_size_recommendation']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def chksha(x):assert isinstance(x,str) and re.fullmatch('[0-9a-f]{64}',x)
def main():
    status=read(STATUS);m=read(MATRIX)
    assert status['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150'
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(143,249,0,392)
    assert m['schema']=='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V31_B161'
    assert (m['CERT_MULTIBOARD'],m['APPROX'],m['EST'])==(143,249,0)
    assert m['parent_v31_status_sha256']==sha(STATUS)
    assert len(m['models'])==143 and len(m['boards'])==557
    assert m['strict_aggregate']['named_board_proofs']==557
    assert status['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    assert status['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    agg=m['strict_aggregate'];expected=agg['hero_lock_variants']
    expected_medium=agg['b50_research_candidate_boards']
    assert expected>=646 and 0<=expected_medium<=557
    counters=collections.Counter();per_model=collections.Counter()
    output=[];seen=set();rowCounts=collections.Counter()
    for sample in sorted(m['boards'],key=lambda x:(x['rank'],x['model_id'],x['flop'],x['turn'])):
        key=(sample['model_id'],sample['flop'])
        assert key not in seen,('duplicate genuine named board',key)
        seen.add(key)
        mid=sample['model_id']
        assert status['records'][mid]['label']=='CERT-MULTIBOARD'
        assert mid in m['models'] and m['models'][mid]['rank']==sample['rank']
        assert sample['generic_handclass_texture_policy_is_not_GTO'] is True
        assert sample['no_general_bet_size_recommendation'] is True
        assert sample['strictly_reachable_combo_count']>0
        assert sample['genuine_GTO_exploitability_pct']<=.5
        assert sample['spr_relative_error_pct']<=5
        chksha(sample['GTO_sha256'])
        assert int(sample['GTO_run_id'])>0
        locks=sample['hero_lock_proofs']
        assert locks and isinstance(locks,list)
        flag=sample['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE'
        assert flag or sample['b50_research_status']=='NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'
        if flag:assert sample['b50_eligible_combo_count']>0
        counters['named_board_proofs']+=1
        counters['b50_research_candidate_boards']+=int(flag)
        counters['b50_unproven_boards']+=int(not flag)
        per_model[mid]+=1
        for num,lock in enumerate(locks,1):
            chksha(lock['source_sha256'])
            assert lock['version'] in ('exp_ip','exp_oop')
            assert lock['EV_is_model_estimate_not_real_winnings'] is True
            assert lock['lock_scope'] in ('PARTIALLY_LOCKED_SOURCE','DOWNSTREAM_TURN_RIVER_ONLY')
            assert lock['source_run_id']>0
            n=lock['source_node_counts']
            assert set(n)=={'observed_marginal','assumed_default','unmatched_unlocked'}
            known=all(n[k] is not None for k in n)
            assert known or all(n[k] is None for k in n)
            if known:
                assert all(isinstance(n[k],int) and n[k]>=0 for k in n)
                denominator=sum(n.values())
                pct=round(n['observed_marginal']*100/denominator,3) if denominator else None
                assert lock['observed_fraction_of_source_nodes_pct']==pct
                assert lock['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
                counters['source_nodes_observed_pool_marginal']+=n['observed_marginal']
                counters['source_nodes_assumed_default']+=n['assumed_default']
                counters['source_nodes_unmatched_unlocked']+=n['unmatched_unlocked']
                counters['source_variants_with_counts']+=1
            else:
                assert lock['observed_fraction_of_source_nodes_pct'] is None
                assert lock['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN'
                counters['source_variants_without_historical_counts']+=1
            counters['hero_lock_variants']+=1
            counters['hero_lock_variants_with_default']+=int(lock['any_disclosed_default'])
            counters['downstream_turn_river_only_variants']+=int(lock['lock_scope']=='DOWNSTREAM_TURN_RIVER_ONLY')
            row=dict(
                rank=sample['rank'],model_id=mid,spot=sample['spot'],pot_family=sample['pot_family'],
                street=sample['street'],flop=sample['flop'],turn=sample['turn'],
                public_board=sample['exact_public_board'],exact_action_line=sample['exact_action_line'],
                hero_actor_seat=sample['actor_seat'],true_spr=sample['actual_spr'],
                estimated_spr_relative_error_pct=sample['spr_relative_error_pct'],
                genuine_GTO_gap_pct=sample['genuine_GTO_exploitability_pct'],
                strict_full_sequence_legal_combo_count=sample['strictly_reachable_combo_count'],
                original_GTO_run=sample['GTO_run_id'],original_GTO_sha256=sample['GTO_sha256'],
                LMP_ISO_preflop_range_assumed=sample['assumed_preflop_ranges'],
                NL2_lock_variant_ordinal=num,NL2_lock_total_variants_for_board=len(locks),
                NL2_lock_run=lock['source_run_id'],NL2_lock_version=lock['version'],
                NL2_lock_source_scope=lock['source_scope'],NL2_lock_street_scope=lock['lock_scope'],
                NL2_lock_sha256=lock['source_sha256'],
                observed_NL2_pool_marginal_nodes=n['observed_marginal'],
                assumed_default_nodes=n['assumed_default'],
                unmatched_unlocked_villain_nodes=n['unmatched_unlocked'],
                observed_fraction_source_nodes_pct=lock['observed_fraction_of_source_nodes_pct'],
                historical_source_denominators_unknown=not known,
                any_assumed_default_disclosed=lock['any_disclosed_default'],
                NL2_pool_rate_origin_class=lock['node_rate_data_status'],
                b50_exact_board_nonpolar_research_flag=flag,
                b50_eligible_strict_legal_combo_count=sample['b50_eligible_combo_count'],
                model_hero_gain_bb_not_real_profit=lock['hero_model_gain_bb'],
                no_generic_texture_GTO=True,
                no_private_card_conditional_NL2_rate=True,
                not_a_bet_size_recommendation=True)
            assert set(row)==set(COLUMNS)
            output.append(row);rowCounts[key]+=1
    assert len(seen)==counters['named_board_proofs']==557
    assert len(output)==counters['hero_lock_variants']==expected
    assert counters['b50_research_candidate_boards']==expected_medium
    assert counters['b50_unproven_boards']==557-expected_medium
    assert len(per_model)==143 and all(3<=n<=5 for n in per_model.values())
    assert all(per_model[k]==v['example_count'] for k,v in m['models'].items())
    assert all(rowCounts[(r['model_id'],r['flop'])]==r['NL2_lock_total_variants_for_board'] for r in output)
    for key,sourcekey in (
         ('source_nodes_observed_pool_marginal','observed_marginal_pattern_nodes'),
         ('source_nodes_assumed_default','assumed_pattern_nodes'),
         ('source_nodes_unmatched_unlocked','unmatched_opponent_nodes'),
         ('hero_lock_variants_with_default','lock_variants_with_default_flag'),
         ('downstream_turn_river_only_variants','turn_river_only_locks')):
        assert counters[key]==agg[sourcekey],(key,counters[key],agg[sourcekey])
    b=io.StringIO(newline='');w=csv.DictWriter(b,fieldnames=COLUMNS,lineterminator='\n',extrasaction='raise')
    w.writeheader();w.writerows(output);CSV.write_text(b.getvalue(),encoding='utf-8')
    index=dict(schema='NL2_HU_B162_V31_ALL_557_GENUINE_CERT_BOARD_LOCK_SOURCES_V1',
         parent_V31_status_sha256=sha(STATUS),parent_V31_matrix_sha256=sha(MATRIX),
         output_csv_sha256=sha(CSV),
         CERT=143,APPROX=249,EST=0,TOTAL=392,
         named_source_board_proofs=557,source_hero_lock_variants=len(output),
         exact_b50_research_candidate_boards=expected_medium,
         b50_unproven_named_boards=557-expected_medium,
         all_143_CERT_models_have_3_to_5_flops=True,
         source_measured_default_unknown_counts=dict(counters),
         original_Batch_E_run=44732810327,
         all_source_SHAs_64_char_lowerhex=True,
         no_real_NL2_private_card_conditional_rates_claim=True,
         source_rate_observed_only_pooled_street_size_marginals=True,
         not_a_generic_betting_recommendation=True,
         not_a_new_certification=True,
         PR2_draft_never_merge=True)
    INDEX.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    DOC.parent.mkdir(parents=True,exist_ok=True)
    DOC.write_text('# B162 | full V31 per-source NL2 locks for ALL 557 exact CERT boards\n\n'
       '**143 CERT-MULTIBOARD / 249 APPROX / 0 EST** among 392. '
       'Every one of 557 genuinely certified named boards and each of '+
       str(len(output))+' true actor-side NL2 lock variants is exported with '
       'original GTO run/SHA, NL2 lock run/SHA, exact action, actor, true SPR and '
       'sequentially legal combo count.\n\n'
       'Observed NL2 pooled street/bet-size marginal nodes: '+
       str(counters['source_nodes_observed_pool_marginal'])+
       '; ASSUMED fallback nodes: '+str(counters['source_nodes_assumed_default'])+
       '; unlocked/unmatched villain nodes: '+str(counters['source_nodes_unmatched_unlocked'])+
       '; historic source variants without denominators: '+
       str(counters['source_variants_without_historical_counts'])+'. '
       'Unknown is NEVER zero. NL2 conditional private-hand action frequencies '
       'are NOT observed; LMP limped preflop 169-class source is explicitly ASSUMED.\n\n'
       '50% pot exact nonpolar research evidence on '+str(expected_medium)+
       ' named boards; other '+str(557-expected_medium)+
       ' lack this proof. It is NOT a global texture or bet-size directive. '
       'Hero gain (bb) is model EV, NOT realized profit.\n\n'
       'Original status SHA '+sha(STATUS)+', lock matrix SHA '+sha(MATRIX)+
       ', exported CSV SHA '+sha(CSV)+'. '
       'Independently verified Batch E and full HU river link integrity '
       '2475/2475 required by Actions. PR #2 Draft; NEVER MERGE.\n')
    print(json.dumps(dict(PASS=True,CERT=143,APPROX=249,
           named_boards=557,hero_lock_variants=len(output),
           exact_b50_candidates=expected_medium,
           b50_unproven_named_boards=557-expected_medium,
           source_counts=dict(counters),csv_sha256=sha(CSV)),ensure_ascii=False))
if __name__=='__main__':main()
