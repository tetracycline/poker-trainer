#!/usr/bin/env python3
"""B273 V41 evidence-first exact 590 named real GTO + actor-matched NL2 locks.
All 587 V40 board/source proofs remain identical, 3 genuine rank61 CO-IP
GTO + downstream real Rust NL2 proofs are appended. Aggregate measured
NL2 POOL marginals, assumed defaults and historical UNKNOWN remain separate.
134 medium50 nonpolar research cases are exact-board ONLY.
"""
import collections,csv,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create

D=pathlib.Path('data');DOC=pathlib.Path('docs')
OLD_STATUS=D/'nl2_hu_multiboard_status_v40_b265_rank313.json'
STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v41_b271.json'
OLD=D/'nl2_hu_b267_v40_all_587_lock_rate_source_nonpolar_priority.json'
OUT=D/'nl2_hu_b273_v41_all_590_exact_lock_rate_medium_gap_priority.json'
CSV=D/'nl2_hu_b273_v41_all_590_exact_lock_rate_medium_gap_priority.csv'
MD=DOC/'NL2_HU_B273_V41_ALL_590_EXACT_NL2_LOCK_POOL_UNKNOWN_NONPOLAR.md'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(z):return (z['model_id'],z['flop'],z['turn'],z['exact_action_line'],z['actor_seat'])

def main():
    old_status,status=load(OLD_STATUS),load(STATUS)
    prior=load(OLD);mat=load(MATRIX)
    assert (old_status['CERT_MULTIBOARD'],old_status['APPROX'],old_status['EST'])==(153,239,0)
    assert status['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61'
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(154,238,0,392)
    assert status['parent_v40_sha256']==sha(OLD_STATUS)
    assert prior['schema']=='NL2_HU_B267_V40_ALL_587_GENUINE_GTO_ACTOR_NL2_LOCK_MEDIUM_SOURCE_V1'
    assert prior['V40_status_sha256']==sha(OLD_STATUS)
    assert prior['genuine_named_boards']==587 and prior['real_hero_NL2_lock_variants']==679
    assert mat['parent_v41_status_sha256']==sha(STATUS)
    assert {k for k in old_status['records'] if old_status['records'][k]!=status['records'][k]}=={
       'ln-ipfr-t_model-qpx6tn'}
    m=create(status)
    assert (m['CERT_MULTIBOARD'],m['APPROX'],m['EST'])==(154,238,0)
    assert len(m['models'])==154 and len(m['boards'])==590
    assert m['models']==mat['models'] and m['boards']==mat['boards']
    assert m['strict_aggregate']==mat['strict_aggregate']
    assert (m['strict_aggregate']['named_board_proofs'],m['strict_aggregate']['hero_lock_variants'],
            m['strict_aggregate']['b50_research_candidate_boards'])==(590,682,134)
    audited=audit(status)
    assert (audited['cert_multiboard'],audited['approx'],audited['EST'])==(154,238,0)
    assert (audited['aggregate']['named_board_proofs'],audited['aggregate']['paired_hero_locked_source_variants'],
            audited['aggregate']['board_examples_with_b50_candidate'])==(590,682,134)
    assert audited['not_generalized_handclass_GTO'] and audited['not_actual_NL2_earnings']
    previous={key(z):z for z in prior['per_exact_board_source_provenance']}
    current={key(z):z for z in m['boards']}
    assert len(previous)==587 and len(current)==590
    assert set(previous).issubset(current)
    newly=[z for k,z in current.items() if k not in previous]
    assert len(newly)==3
    assert {z['flop'] for z in newly}=={'Js9h5d','KsQh4d','QsJh4d'}
    mid='ln-ipfr-t_model-qpx6tn'
    assert all(z['model_id']==mid and z['spot']=='CO_BB' and
      z['exact_action_line']=='x b100 c/x' and z['actor_seat']==1 and
      z['strictly_reachable_combo_count']>0 and z['hero_lock_proofs'] and
      not z['assumed_preflop_ranges'] and z['spr_relative_error_pct']<=5
      for z in newly)
    proven={'KsQh4d':(44902146101,44902973337,65),
            'Js9h5d':(44902831383,44903478906,110),
            'QsJh4d':(44934430727,44935281174,80)}
    for z in newly:
        gto,lock,strict=proven[z['flop']]
        assert z['GTO_run_id']==gto and z['strictly_reachable_combo_count']==strict
        assert len(z['hero_lock_proofs'])==1 and z['hero_lock_proofs'][0]['source_run_id']==lock
        assert z['hero_lock_proofs'][0]['version']=='exp_ip'
        assert z['hero_lock_proofs'][0]['lock_scope']=='DOWNSTREAM_TURN_RIVER_ONLY'
        assert z['hero_lock_proofs'][0]['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN'
        assert all(v is None for v in z['hero_lock_proofs'][0]['source_node_counts'].values())
    resultrows=[];counts=collections.Counter()
    for k,b in current.items():
        assert b['strictly_reachable_combo_count']>0 and b['hero_lock_proofs']
        assert len(b['GTO_sha256'])==64 and b['genuine_GTO_exploitability_pct']<=.5
        assert b['spr_relative_error_pct']<=5
        assert b['generic_handclass_texture_policy_is_not_GTO'] and b['no_general_bet_size_recommendation']
        observed=assumed=unmatched=unknown=0
        for proof in b['hero_lock_proofs']:
            assert proof['version'] in ('exp_ip','exp_oop')
            assert proof['source_run_id']>0 and len(proof['source_sha256'])==64
            assert proof['EV_is_model_estimate_not_real_winnings']
            source=proof['source_node_counts']
            if proof['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN':
                assert all(source.get(x) is None for x in ('observed_marginal','assumed_default','unmatched_unlocked'))
                unknown+=1
            else:
                assert proof['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
                assert all(isinstance(source.get(x),int) and source[x]>=0
                  for x in ('observed_marginal','assumed_default','unmatched_unlocked'))
                observed+=source['observed_marginal'];assumed+=source['assumed_default']
                unmatched+=source['unmatched_unlocked']
        b50=b['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE'
        if b50:assert b['b50_eligible_combo_count']>0
        else:assert b['b50_research_status']=='NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'
        if k in previous:
            o=previous[k]
            assert (o['genuine_GTO_run'],o['genuine_GTO_sha256'],o['strict_hero_combos'])==(
              b['GTO_run_id'],b['GTO_sha256'],b['strictly_reachable_combo_count'])
            assert (o['observed_NL2_pool_marginal_nodes'],o['assumed_default_nodes'],
                o['unmatched_villain_nodes'],o['historical_unknown_lock_variants'])==(
                observed,assumed,unmatched,unknown)
            assert o['real_NL2_hero_lock_runs']==[z['source_run_id'] for z in b['hero_lock_proofs']]
            assert o['exact_board_only_50pct_depolarization_research']==b50
            assert o['medium_bet_eligible_strict_combos']==b['b50_eligible_combo_count']
        else:
            assert b['model_id']==mid and unknown==1
            assert (observed,assumed,unmatched)==(0,0,0)
        category=('HISTORICAL_UNKNOWN_PRESENT' if unknown else
                  'ASSUMED_DEFAULT_PRESENT' if assumed else
                  'POOL_MARGINAL_ONLY_NOT_PRIVATE_CARD' if observed else 'NO_MEASURED_RATE')
        row=dict(rank=b['rank'],model_id=b['model_id'],spot=b['spot'],
            flop=b['flop'],turn=b['turn'],exact_action_line=b['exact_action_line'],
            actor_seat=b['actor_seat'],strict_hero_combos=b['strictly_reachable_combo_count'],
            genuine_GTO_run=b['GTO_run_id'],genuine_GTO_sha256=b['GTO_sha256'],
            real_NL2_hero_lock_runs=[z['source_run_id'] for z in b['hero_lock_proofs']],
            lock_variant_count=len(b['hero_lock_proofs']),
            observed_NL2_pool_marginal_nodes=observed,assumed_default_nodes=assumed,
            unmatched_villain_nodes=unmatched,historical_unknown_lock_variants=unknown,
            provenance_category=category,
            measured_rate_incomplete=bool(assumed or unknown or not observed),
            exact_50pct_depolarized_board_research_only=b50,
            b50_eligible_combo_count=b['b50_eligible_combo_count'],
            all_private_card_conditional_NL2_rates_unobserved=True,
            no_generalized_50_pct_advice=True,no_generic_handclass_CERT=True)
        resultrows.append(row)
        counts['named_boards']+=1;counts['genuine_actor_NL2_lock_variants']+=len(b['hero_lock_proofs'])
        counts['observed_pool_marginal_nodes']+=observed;counts['assumed_default_nodes']+=assumed
        counts['unmatched_villain_nodes']+=unmatched;counts['unknown_source_denominator_variants']+=unknown
        counts['b50_named_board_research_only']+=int(b50)
        counts['boards_with_incomplete_measured_source_rate']+=int(row['measured_rate_incomplete'])
    assert (counts['named_boards'],counts['genuine_actor_NL2_lock_variants'],counts['b50_named_board_research_only'])==(590,682,134)
    prior_counts=prior['counts']
    for newfield,oldfield in [('observed_pool_marginal_nodes','observed_pool_marginal_source_nodes'),
         ('assumed_default_nodes','assumed_default_source_nodes'),
         ('unmatched_villain_nodes','unmatched_villain_nodes')]:
        assert counts[newfield]==prior_counts[oldfield]
    assert counts['unknown_source_denominator_variants']==prior_counts['unknown_lock_source_variant_denominators']+3
    assert counts['boards_with_incomplete_measured_source_rate']==prior_counts['boards_with_missing_measured_rate_evidence']+3
    resultrows.sort(key=lambda x:(x['rank'],-x['historical_unknown_lock_variants'],
        -x['assumed_default_nodes'],x['flop'],x['turn']))
    fields=['rank','model_id','spot','flop','turn','exact_action_line','actor_seat',
      'strict_hero_combos','genuine_GTO_run','lock_variant_count',
      'observed_NL2_pool_marginal_nodes','assumed_default_nodes','unmatched_villain_nodes',
      'historical_unknown_lock_variants','provenance_category','measured_rate_incomplete',
      'exact_50pct_depolarized_board_research_only','b50_eligible_combo_count']
    with CSV.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(resultrows)
    out=dict(schema='NL2_HU_B273_V41_ALL_590_AUTHENTIC_NAMED_GTO_NL2_LOCK_MEDIUM_SOURCE_V1',
       V40_status_sha256=sha(OLD_STATUS),V41_status_sha256=sha(STATUS),
       V41_matrix_sha256=sha(MATRIX),V40_587_source_prior_sha256=sha(OLD),
       CERT_MULTIBOARD=154,APPROX=238,EST=0,TOTAL=392,
       certified_models=154,all_named_boards=590,all_actor_NL2_lock_variants=682,
       counts=dict(counts),three_additional_rank61_true_GTO_NL2_flops=sorted(z['flop'] for z in newly),
       unchanged_prior_V40_587_real_board_source_SHA_and_NL2_locks=True,
       per_exact_board_source_provenance=resultrows,
       highest_frequency_incomplete_pool_measured_source_priority=[
          z for z in resultrows if z['measured_rate_incomplete']][:60],
       pool_marginal_does_not_equal_private_hand_conditionals=True,
       UNKNOWN_never_reclassified_as_observed=True,
       50pct_only_proven_exact_board_nonpolarized_research=True,
       no_unverified_generic_strategy_certification=True,PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    md=['# B273 V41 true GTO+NL2 actor-lock / 50% pot per-board evidence gaps','',
        '**154 CERT / 238 APPROX / 0 EST**, 590 authenticated named public boards and '
        '682 genuine original Rust actor-matched NL2 partial lock variants. '
        'The 587 V40 sources are byte-for-byte provenance-identical, and rank61 adds '
        'KsQh4d/Tc, Js9h5d/Ah and QsJh4d/7s, each only its real actor/line/SPR.',
        '',
        f"Observed NL2 pool marginal nodes: {counts['observed_pool_marginal_nodes']}; "
        f"assumed fallback nodes: {counts['assumed_default_nodes']}; unmatched villain nodes: "
        f"{counts['unmatched_villain_nodes']}; historical UNKNOWN lock-denominator variants: "
        f"{counts['unknown_source_denominator_variants']}.",
        f"50% pot nonpolarized exact-board-only research candidates: {counts['b50_named_board_research_only']}; "
        f"incomplete measured rate provenance on {counts['boards_with_incomplete_measured_source_rate']} named boards.",
        'NEVER treat observed pool marginals as card-conditional opponent behavior, '
        'assumed defaults as measured data or UNKNOWN as zero. No universal 50% pot advice.','',
        '|Rank|Named board|Exact line|Observed / assumed / unmatched|Unknown|50% research|',
        '|---:|---|---|---:|---:|---|']
    for z in out['highest_frequency_incomplete_pool_measured_source_priority'][:45]:
        md.append(f"|{z['rank']}|{z['flop']} / {z['turn']}|{z['exact_action_line']}|"
          f"{z['observed_NL2_pool_marginal_nodes']}/{z['assumed_default_nodes']}/{z['unmatched_villain_nodes']}|"
          f"{z['historical_unknown_lock_variants']}|"
          f"{'exact-board candidate' if z['exact_50pct_depolarized_board_research_only'] else 'not proven'}|")
    md.extend(['','Every existing and new source must pass independent V41 GTO/NL2 provenance and HU2475/2475 full regression before commit.',
      'PR #2 Draft NEVER MERGE.'])
    MD.write_text('\n'.join(md)+'\n')
    print('PASS B273 V41',json.dumps(dict(counts),ensure_ascii=False),flush=True)
if __name__=='__main__':
    main()
