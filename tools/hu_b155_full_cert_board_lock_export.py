#!/usr/bin/env python3
"""B155: evidence-only immutable V30 per-board / per-lock-source provenance.

Exports ONE CSV row for each genuinely verified NL2 hero lock source variant on
each of the 554 named CERT boards. An empirically observed pooled marginal
counts only as pooled NL2 street/bet-size information, NEVER as hole-card-,
board-, or opponent-conditional measured behavior. Null remains unknown.
No new CERT, model EV or model-wide medium-pot bet recommendation.
"""
import collections,csv,hashlib,io,json,pathlib,re

ROOT=pathlib.Path('data')
STATUS=ROOT/'nl2_hu_multiboard_status_v30_b145_rank47.json'
MATRIX=ROOT/'nl2_hu_cert_lock_medium_matrix_v30_b145.json'
OUT=ROOT/'nl2_hu_b155_v30_all_554_named_board_lock_sources.csv'
INDEX=ROOT/'nl2_hu_b155_v30_all_554_named_board_lock_sources.index.json'
DOC=pathlib.Path('docs/NL2_HU_B155_ALL_554_BOARDS_NL2_LOCK_AND_B50_PROVENANCE.md')
FIELDS=[
 'model_rank','model_id','pot_family','spot','street','named_flop','named_turn',
 'exact_public_board','exact_action_line','actor_seat','actual_spr',
 'spr_relative_error_pct','true_gto_gap_pct','strict_reachable_combo_count',
 'gto_run_id','gto_sha256','preflop_ranges_assumed','nl2_hero_lock_source_idx',
 'nl2_hero_lock_source_variant_count','nl2_hero_lock_run_id','nl2_lock_version',
 'nl2_lock_source_scope','nl2_lock_scope','nl2_lock_sha256',
 'observed_pool_marginal_node_count','assumed_default_node_count',
 'unmatched_unlocked_villain_node_count','observed_fraction_source_nodes_pct',
 'observed_aggregate_nl2_pool_coverage_pct','unknown_historical_source_counts',
 'any_assumed_default_disclosed','rate_data_status',
 'b50_exact_board_research_status','b50_eligible_combo_count',
 'model_hero_gain_bb_not_real_winnings','no_general_texture_or_bucket_gto',
 'no_actual_private_hand_conditional_nl2_rate'
]

def read(p):return json.loads(p.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def checksha(v):
    assert isinstance(v,str) and re.fullmatch(r'[0-9a-f]{64}',v),v

def main():
    status=read(STATUS); matrix=read(MATRIX)
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(142,250,0,392)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'],matrix['EST'])==(142,250,0)
    assert matrix['schema']=='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V30_B145'
    assert matrix['parent_v30_status_sha256']==sha(STATUS)
    assert status['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    assert status['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    assert len(matrix['models'])==142 and len(matrix['boards'])==554
    assert matrix['strict_aggregate']['named_board_proofs']==554
    assert matrix['strict_aggregate']['hero_lock_variants']==646
    assert matrix['strict_aggregate']['b50_research_candidate_boards']==131
    assert matrix['policy']['scope'].find('NOT whole-flop NL2-lock GTO')>=0

    counts=collections.Counter()
    per_model=collections.Counter()
    per_board={}
    exact_board_sources={}
    seen=set()
    output=[]
    for b in sorted(matrix['boards'],key=lambda x:(
            x['rank'],x['model_id'],x['flop'],x['turn'],x['exact_action_line'])):
        key=(b['model_id'],b['flop'])
        assert key not in seen,('duplicate named model/flop',key)
        seen.add(key)
        assert b['model_id'] in matrix['models']
        model=matrix['models'][b['model_id']]
        assert model['rank']==b['rank']
        assert status['records'][b['model_id']]['label']=='CERT-MULTIBOARD'
        assert b['strictly_reachable_combo_count']>0
        assert b['spr_relative_error_pct']<=5 and b['genuine_GTO_exploitability_pct']<=.5
        assert b['generic_handclass_texture_policy_is_not_GTO'] is True
        assert b['no_general_bet_size_recommendation'] is True
        assert b['b50_eligible_combo_count']>=0
        checksha(b['GTO_sha256'])
        per_model[b['model_id']]+=1
        locks=b['hero_lock_proofs']
        assert locks and isinstance(locks,list)
        medium=b['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE'
        assert medium or b['b50_research_status']=='NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'
        assert not medium or b['b50_eligible_combo_count']>0
        counts['named_boards']+=1
        counts['b50_candidate_boards']+=int(medium)
        counts['b50_unproven_boards']+=int(not medium)
        counts['total_b50_eligible_combos_across_named_boards']+=b['b50_eligible_combo_count']
        exact_board_sources[key]=[]
        for i,lock in enumerate(locks,1):
            checksha(lock['source_sha256'])
            assert lock['version'] in ('exp_ip','exp_oop')
            assert lock['EV_is_model_estimate_not_real_winnings'] is True
            nodes=lock['source_node_counts']
            keys=('observed_marginal','assumed_default','unmatched_unlocked')
            assert set(nodes)==set(keys)
            known=all(nodes[k] is not None for k in keys)
            assert known or all(nodes[k] is None for k in keys)
            if known:
                assert all(isinstance(nodes[k],int) and nodes[k]>=0 for k in keys)
                counts['measured_source_nodes']+=nodes['observed_marginal']
                counts['assumed_default_source_nodes']+=nodes['assumed_default']
                counts['unmatched_unlocked_villain_source_nodes']+=nodes['unmatched_unlocked']
                counts['lock_variants_with_source_node_counts']+=1
                expected_share=(round(100*nodes['observed_marginal']/sum(nodes.values()),3)
                                if sum(nodes.values()) else None)
                assert lock['observed_fraction_of_source_nodes_pct']==expected_share
                assert lock['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
            else:
                assert lock['observed_fraction_of_source_nodes_pct'] is None
                assert lock['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN'
                counts['lock_variants_historical_counts_unknown']+=1
            if lock['any_disclosed_default']:
                counts['lock_variants_with_disclosed_default']+=1
            assert lock['lock_scope'] in ('PARTIALLY_LOCKED_SOURCE','DOWNSTREAM_TURN_RIVER_ONLY')
            counts['downstream_only_lock_variants']+=int(lock['lock_scope']=='DOWNSTREAM_TURN_RIVER_ONLY')
            counts['hero_lock_variants']+=1
            assert isinstance(lock['source_run_id'],int) and lock['source_run_id']>0
            assert isinstance(b['GTO_run_id'],int) and b['GTO_run_id']>0
            gain=lock['hero_model_gain_bb']
            if gain is not None: assert isinstance(gain,(int,float))
            entry=dict(
                model_rank=b['rank'],model_id=b['model_id'],pot_family=b['pot_family'],
                spot=b['spot'],street=b['street'],named_flop=b['flop'],
                named_turn=b['turn'],exact_public_board=b['exact_public_board'],
                exact_action_line=b['exact_action_line'],actor_seat=b['actor_seat'],
                actual_spr=b['actual_spr'],spr_relative_error_pct=b['spr_relative_error_pct'],
                true_gto_gap_pct=b['genuine_GTO_exploitability_pct'],
                strict_reachable_combo_count=b['strictly_reachable_combo_count'],
                gto_run_id=b['GTO_run_id'],gto_sha256=b['GTO_sha256'],
                preflop_ranges_assumed=b['assumed_preflop_ranges'],
                nl2_hero_lock_source_idx=i,nl2_hero_lock_source_variant_count=len(locks),
                nl2_hero_lock_run_id=lock['source_run_id'],
                nl2_lock_version=lock['version'],nl2_lock_source_scope=lock['source_scope'],
                nl2_lock_scope=lock['lock_scope'],nl2_lock_sha256=lock['source_sha256'],
                observed_pool_marginal_node_count=nodes['observed_marginal'],
                assumed_default_node_count=nodes['assumed_default'],
                unmatched_unlocked_villain_node_count=nodes['unmatched_unlocked'],
                observed_fraction_source_nodes_pct=lock['observed_fraction_of_source_nodes_pct'],
                observed_aggregate_nl2_pool_coverage_pct=lock['aggregate_NL2_pool_coverage_pct'],
                unknown_historical_source_counts=not known,
                any_assumed_default_disclosed=lock['any_disclosed_default'],
                rate_data_status=lock['node_rate_data_status'],
                b50_exact_board_research_status=b['b50_research_status'],
                b50_eligible_combo_count=b['b50_eligible_combo_count'],
                model_hero_gain_bb_not_real_winnings=gain,
                no_general_texture_or_bucket_gto=True,
                no_actual_private_hand_conditional_nl2_rate=True)
            assert set(entry)==set(FIELDS)
            output.append(entry)
            exact_board_sources[key].append(lock['source_run_id'])
    assert len(per_model)==142 and all(3<=v<=5 for v in per_model.values())
    assert all(per_model[k]==v['example_count'] for k,v in matrix['models'].items())
    assert len(output)==646 and counts['hero_lock_variants']==646
    assert counts['named_boards']==554
    assert counts['b50_candidate_boards']==131
    assert counts['b50_unproven_boards']==423
    parent_totals=matrix['strict_aggregate']
    for a,b in (('hero_lock_variants','hero_lock_variants'),
                ('named_boards','named_board_proofs'),
                ('b50_candidate_boards','b50_research_candidate_boards'),
                ('measured_source_nodes','observed_marginal_pattern_nodes'),
                ('assumed_default_source_nodes','assumed_pattern_nodes'),
                ('unmatched_unlocked_villain_source_nodes','unmatched_opponent_nodes'),
                ('lock_variants_with_disclosed_default','lock_variants_with_default_flag'),
                ('downstream_only_lock_variants','turn_river_only_locks')):
        assert counts[a]==parent_totals[b],(a,counts[a],parent_totals[b])
    buff=io.StringIO(newline='')
    writer=csv.DictWriter(buff,fieldnames=FIELDS,lineterminator='\n',
                          extrasaction='raise',restval='')
    writer.writeheader()
    for row in output:writer.writerow(row)
    OUT.write_text(buff.getvalue(),encoding='utf-8')
    index=dict(
        schema='NL2_HU_B155_V30_ALL_CERT_NAMED_BOARD_NL2_HERO_LOCK_EVIDENCE_EXPORT_V1',
        status_version='V30_B145',status_sha256=sha(STATUS),
        parent_matrix_sha256=sha(MATRIX),csv_sha256=sha(OUT),
        csv_columns=FIELDS,rows=len(output),source_lock_scope='PER_GENUINE_LOCK_VARIANT',
        declared_CERT=142,declared_APPROX=250,declared_EST=0,
        named_boards=554,genuine_hero_lock_variants=646,
        original_source_batch_E_run=44732810327,
        aggregate=dict(counts),
        named_board_3_to_5_distinct_exact_flops_required=True,
        observed_rate_policy='NL2 pooled action-size/street marginals only, NOT private-hand or exact-villain conditional frequencies',
        assumed_rate_policy='Preserve source defaults and all unknown denominators distinctly; never map unknown to zero',
        nonpolarized_50pct_policy='Research flag only on 131 individually verified named boards; 423 without such evidence are NOT endorsed',
        realized_profit_not_verified=True,no_new_CERT_upgrades=True,
        all_554_boards_have_true_source_and_lock=True,
        PR2_remains_draft_never_merge=True)
    INDEX.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    DOC.parent.mkdir(parents=True,exist_ok=True)
    DOC.write_text(
        '# B155 | Every V30 CERT named board and NL2 hero-lock source (full provenance)\n\n'
        '**Formal status: 142 CERT-MULTIBOARD / 250 APPROX / 0 EST; 392 models.**\n\n'
        '**554 exact named boards; 646 genuine lock-source variants**. Every one is individually '
        'exported into [the B155 CSV](../data/nl2_hu_b155_v30_all_554_named_board_lock_sources.csv) '
        'with original GTO SHA, NL2 lock SHA, explicit actor, complete street action, '
        'SPR, combo reach, and source scope. This includes *all* lock variants on a board, '
        'not just the first one.\n\n'
        '**Measured-versus-assumed source nodes:** pooled observed NL2 bet-size/street '
        'marginal node patterns '+str(counts['measured_source_nodes'])+
        ', assumed fallback patterns '+str(counts['assumed_default_source_nodes'])+
        ', unmatched/unlocked villain nodes '+str(counts['unmatched_unlocked_villain_source_nodes'])+
        '. Historical source variants lacking detailed source-node denominators: '+
        str(counts['lock_variants_historical_counts_unknown'])+'. '
        'Unknown denominators stay blank; blanks are not zeros. '
        'NL2 *private-card-conditional* actual action frequencies are not observed.\n\n'
        '**50% pot nonpolarized research:** 131 exact named boards have evidence-only '
        'candidate flags; the other **423 named boards** do **not** have that proof. '
        'A candidate on one public runout is not a general betting-size recommendation '
        'on a texture, hand class, or another street.\n\n'
        'Partial NL2 node locks are not a whole-flop NL2-locked GTO equilibrium. '
        'Reported hero gain in bb is a solver model estimate, NOT realized NL2 profit. '
        'Limp preflop 169-class ranges explicitly remain ASSUMED.\n\n'
        '**Integrity:** SHA-256 of V30 status '+sha(STATUS)+'; '
        'of source matrix '+sha(MATRIX)+'; '
        'of per-source export '+sha(OUT)+'. '
        'Batch E verified, full HU navigation independently audited 2,475/2,475. '
        '**PR #2 Draft, NEVER MERGE.**\n',encoding='utf-8')
    print(json.dumps(dict(PASS=True,CERT=142,APPROX=250,EST=0,
        boards=counts['named_boards'],lock_source_rows=counts['hero_lock_variants'],
        b50_exact_candidates=counts['b50_candidate_boards'],
        b50_no_proof=counts['b50_unproven_boards'],
        measured_pool_nodes=counts['measured_source_nodes'],
        assumed_default_nodes=counts['assumed_default_source_nodes'],
        unmatched_villain_nodes=counts['unmatched_unlocked_villain_source_nodes'],
        unknown_source_variants=counts['lock_variants_historical_counts_unknown'],
        csv_sha256=sha(OUT)),ensure_ascii=False))
if __name__=='__main__': main()
