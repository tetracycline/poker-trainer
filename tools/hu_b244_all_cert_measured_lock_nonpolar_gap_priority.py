#!/usr/bin/env python3
"""B244 source-first 581 true CERT board / 673 existing NL2 lock-source and
exact-board nonpolarized-50% evidence reconciliation.

Never invent empirical card-specific NL2 rates, promote GTO textures, replace
unknown with zeros, change a UI strategy, or manufacture new Rust solves.
"""
import collections,csv,hashlib,json,pathlib,sys
from hu_cert_lock_medium_coverage_matrix import create
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data')
DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v38_b206_rank190.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v38_b206.json'
OLD=D/'nl2_hu_b215_v38_581_exact_lock_provenance.json'
JSON_OUT=D/'nl2_hu_b244_v38_all_581_measured_lock_nonpolar_gap_priority.json'
CSV_OUT=D/'nl2_hu_b244_v38_all_581_board_lock_gap_priority.csv'
MD_OUT=DOC/'NL2_HU_B244_V38_EXACT_581_LOCK_MEASURED_DEFAULT_UNKNOWN_AND_MEDIUM.md'

def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    s=load(STATUS);previous=load(OLD);original=load(MATRIX)
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V38_B206_RANK190'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(151,241,0,392)
    assert previous['V38_sha256']==sha(STATUS)
    assert original['parent_v38_status_sha256']==sha(STATUS)
    assert previous['original_B206_medium_matrix_sha256']==sha(MATRIX)
    matrix=create(s)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(151,241)
    assert matrix['boards']==original['boards']
    assert matrix['models']==original['models']
    assert matrix['strict_aggregate']==original['strict_aggregate']
    assert len(matrix['boards'])==581 and len(matrix['models'])==151
    assert (matrix['strict_aggregate']['hero_lock_variants'],
            matrix['strict_aggregate']['b50_research_candidate_boards'])==(673,133)
    aud=audit(s)
    assert (aud['cert_multiboard'],aud['approx'],aud['EST'])==(151,241,0)
    assert (aud['aggregate']['named_board_proofs'],
            aud['aggregate']['paired_hero_locked_source_variants'],
            aud['aggregate']['board_examples_with_b50_candidate'])==(581,673,133)
    assert aud['not_generalized_handclass_GTO'] and aud['not_actual_NL2_earnings']
    source_counts=previous['source_coverage_counts']
    assert (source_counts['measured_source_nodes'],source_counts['assumed_default_nodes'],
      source_counts['unmatched_villain_nodes'],source_counts['historical_unknown_source_variants'])==(
      4510,2139,3850,315)
    key=lambda z:(z['model_id'],z['flop'],z['turn'],
                  z.get('exact_line',z.get('exact_action_line','')),z['actor_seat'])
    old={key(x):x for x in previous['all_exact_board_proofs']}
    current={key(x):x for x in matrix['boards']}
    assert len(old)==len(current)==581 and old.keys()==current.keys()
    rows=[];tot=collections.Counter();by_model=collections.defaultdict(list)
    for k,b in current.items():
        z=old[k]
        assert (b['GTO_run_id'],b['GTO_sha256'],
           b['strictly_reachable_combo_count'])==(
           z['GTO_run_id'],z['GTO_sha256'],z['strict_reachable_combos'])
        assert len(b['GTO_sha256'])==64 and b['hero_lock_proofs']
        assert b['strictly_reachable_combo_count']>0
        assert b['genuine_GTO_exploitability_pct']<=.5
        assert b['spr_relative_error_pct']<=5
        if b['assumed_preflop_ranges']:
            assert b['spot'] in ('ISO_BTN_CO','LMP_CO_BB')
        observed=assumed=unmatched=unknown=0
        for l in b['hero_lock_proofs']:
            assert l['version'] in ('exp_ip','exp_oop')
            assert l['source_run_id']>0 and len(l['source_sha256'])==64
            assert l['EV_is_model_estimate_not_real_winnings'] is True
            counts=l['source_node_counts']
            if l['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN':
                assert all(v is None for v in counts.values())
                unknown+=1
            else:
                assert l['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
                assert all(isinstance(v,int) and v>=0 for v in counts.values())
                observed+=counts['observed_marginal']
                assumed+=counts['assumed_default']
                unmatched+=counts['unmatched_unlocked']
        assert (observed,assumed,unmatched,unknown)==(
            z['measured_aggregate_pool_source_nodes'],
            z['assumed_default_source_nodes'],
            z['unknown_unmatched_villain_source_nodes'],
            z['historical_source_proofs_missing_denominator'])
        medium=b['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE'
        assert medium==z['nonpolar50_exact_board_research']
        if medium:
            assert b['b50_eligible_combo_count']>0
            assert z['b50_strict_eligible_combo_count']==b['b50_eligible_combo_count']
        else:
            assert b['b50_research_status']=='NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'
        assert b['generic_handclass_texture_policy_is_not_GTO'] is True
        assert b['no_general_bet_size_recommendation'] is True
        assert z['no_observed_private_card_conditional_NL2_rate'] is True
        if unknown:rate_status='HISTORICAL_UNKNOWN_PRESENT'
        elif assumed:rate_status='ASSUMED_DEFAULT_PRESENT'
        elif observed:rate_status='POOL_MARGINAL_ONLY_NOT_CONDITIONAL'
        else:rate_status='NO_MEASURED_RATE'
        num=observed+assumed
        share=round(100*observed/num,3) if num else None
        risk_score=100*bool(unknown)+10*bool(assumed)+int(not bool(observed))
        line=dict(rank=b['rank'],model_id=b['model_id'],spot=b['spot'],
            flop=b['flop'],turn=b['turn'],exact_action_line=b['exact_action_line'],
            actor_seat=b['actor_seat'],strict_hero_combos=b['strictly_reachable_combo_count'],
            GTO_source_run=b['GTO_run_id'],GTO_source_sha256=b['GTO_sha256'],
            real_hero_lock_run_ids=[a['source_run_id'] for a in b['hero_lock_proofs']],
            lock_variant_count=len(b['hero_lock_proofs']),
            measured_NL2_street_size_marginal_nodes=observed,
            assumed_default_nodes=assumed,unmatched_villain_nodes=unmatched,
            historical_unknown_lock_variants=unknown,
            measured_share_of_known_source_nodes_pct=share,
            rate_status=rate_status,measured_rate_replacement_priority_score=risk_score,
            b50_exact_board_nonpolarized_research_only=medium,
            b50_strict_eligible_combos=b['b50_eligible_combo_count'],
            new_real_NL2_measured_private_hand_conditionals=0,
            universal_50pct_bet_recommendation=False,
            CERT_scope_only_exact_board_and_action=True)
        rows.append(line);by_model[b['model_id']].append(line)
        tot['boards']+=1;tot['hero_lock_variants']+=len(b['hero_lock_proofs'])
        tot['measured_nodes']+=observed;tot['assumed_nodes']+=assumed
        tot['unmatched_nodes']+=unmatched;tot['historical_unknown_lock_variants']+=unknown
        tot['50pct_exact_only']+=int(medium)
        tot['boards_missing_pure_measured_evidence']+=int(bool(unknown or assumed or not observed))
        tot['boards_unknown_lock_source']+=int(bool(unknown))
        tot['boards_with_defaults']+=int(bool(assumed))
        tot['boards_with_no_observed_marginal_nodes']+=int(not observed)
    assert (tot['boards'],tot['hero_lock_variants'],tot['50pct_exact_only'])==(581,673,133)
    assert (tot['measured_nodes'],tot['assumed_nodes'],tot['unmatched_nodes'],
      tot['historical_unknown_lock_variants'])==(4510,2139,3850,315)
    assert tot['boards_missing_pure_measured_evidence']==567
    assert all(3<=len(v)<=5 for v in by_model.values()) and len(by_model)==151
    rows.sort(key=lambda z:(z['rank'],-z['measured_rate_replacement_priority_score'],
      z['flop'],z['turn']))
    filename_fields=['rank','model_id','spot','flop','turn','exact_action_line',
       'actor_seat','strict_hero_combos','GTO_source_run','lock_variant_count',
       'measured_NL2_street_size_marginal_nodes','assumed_default_nodes',
       'unmatched_villain_nodes','historical_unknown_lock_variants',
       'measured_share_of_known_source_nodes_pct','rate_status',
       'b50_exact_board_nonpolarized_research_only','b50_strict_eligible_combos']
    with CSV_OUT.open('w',encoding='utf-8',newline='') as fp:
        writer=csv.DictWriter(fp,fieldnames=filename_fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    target=[x for x in rows if x['rate_status']!='POOL_MARGINAL_ONLY_NOT_CONDITIONAL']
    ranked=sorted(target,key=lambda x:(x['rank'],-x['measured_rate_replacement_priority_score'],
         -(x['assumed_default_nodes']+x['historical_unknown_lock_variants'])))
    output=dict(schema='NL2_HU_B244_V38_ALL_581_EXACT_BOARD_NL2_RATE_SOURCE_MEDIUM50_PRIORITY_V1',
        parent_status_sha256=sha(STATUS),parent_V38_lock_matrix_sha256=sha(MATRIX),
        parent_B215_provenance_sha256=sha(OLD),
        CERT_MULTIBOARD=151,APPROX=241,EST=0,TOTAL=392,
        distinct_certified_models=151,aggregate=dict(tot),
        exact_named_board_count=581,
        all_581_board_source_rows=rows,highest_frequency_rate_source_upgrade_queue=ranked[:60],
        50pct_nonpolarized_only_true_exact_board_research_candidates=133,
        all_581_have_real_actor_matched_NL2_lock_source=True,
        observed_rate_is_pool_marginal_not_hole_card_conditional=True,
        UNKNOWN_and_ASSUMED_not_reclassified_as_observed=True,
        no_new_observed_NL2_private_card_rates=True,
        no_new_hero_NL2_locked_sources=True,
        no_unsupported_model_CERT_upgrade=True,
        all_2475_HU_links_must_pass_before_commit=True,PR2_Draft_NEVER_MERGE=True)
    JSON_OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    lines=['# B244 exact 581 CERT-board NL2 lock-frequency and medium50 audit','',
        '**151 CERT-MULTIBOARD / 241 APPROX / 0 EST**: all 581 named boards have '
        'genuine source-matched hero-side NL2 partial locks; 673 lock variants. '
        'The status of each source is explicitly measured *pool marginal*, '
        'assumed default, unmatched or historical unknown.',
        '',
        f"Observed marginal source nodes: {tot['measured_nodes']}; "
        f"assumed defaults: {tot['assumed_nodes']}; unmatched villain nodes: "
        f"{tot['unmatched_nodes']}; historical unknown lock variants: "
        f"{tot['historical_unknown_lock_variants']}.",
        f"Named boards requiring improved source rates: {tot['boards_missing_pure_measured_evidence']}/581. "
        f"Exact-board nonpolarized 50%-pot research candidates: {tot['50pct_exact_only']}/581.",
        'This DOES NOT observe per-hole-card conditional opponent frequencies, '
        'add new real locks, recommend universal 50%-pot bets or certify generic '
        'handclass/texture actions. UNKNOWN is not zero; assumed is not measured.','',
        '## Frozen highest-frequency exact-board rate-source priorities','',
        '| Rank | Real board + turn | Exact history | Observed / assumed / unmatched | Unknown lock variants | b50 exact research |',
        '|---:|---|---|---:|---:|---|']
    for z in ranked[:45]:
        lines.append(f"|{z['rank']}|{z['flop']} {z['turn']}|{z['exact_action_line']}|"
          f"{z['measured_NL2_street_size_marginal_nodes']} / {z['assumed_default_nodes']} / "
          f"{z['unmatched_villain_nodes']}|{z['historical_unknown_lock_variants']}|"
          f"{'candidate only' if z['b50_exact_board_nonpolarized_research_only'] else 'not evidenced'}|")
    lines.extend(['','Complete per-board CSV and JSON are in data/nl2_hu_b244_v38_all_581_*.',
      'No CERT or policy changed; all 581 source proofs, 673 locks, 133 b50 candidates '
      'and HU2475 independent Actions must pass before this report is committed.',
      'PR #2 Draft, NEVER MERGE.',''])
    MD_OUT.write_text('\n'.join(lines))
    print('PASS B244',json.dumps(dict(tot),flush=True))
if __name__=='__main__':
    main()
