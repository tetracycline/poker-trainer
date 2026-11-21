#!/usr/bin/env python3
"""B267 failclosed all 587 V40 named exact-board GTO+true NL2 actor locks.
Verify 584 V39 original immutable sources, separately authenticate three
rank313 new sources, preserve observed pool marginals vs assumed/UNKNOWN and
50%-pot nonpolarization as exact board research, not all hand classes.
No generic model upgrades, no invented private-card NL2 conditional rates.
"""
import collections,csv,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create

ROOT=pathlib.Path('data');DOC=pathlib.Path('docs')
OLDSTATUS=ROOT/'nl2_hu_multiboard_status_v39_b247_rank30.json'
NEWSTATUS=ROOT/'nl2_hu_multiboard_status_v40_b265_rank313.json'
MATRIX=ROOT/'nl2_hu_cert_lock_medium_matrix_v40_b265.json'
PRIOR=ROOT/'nl2_hu_b249_v39_all_584_measured_lock_medium_source_gaps.json'
OUT=ROOT/'nl2_hu_b267_v40_all_587_lock_rate_source_nonpolar_priority.json'
CSV=ROOT/'nl2_hu_b267_v40_all_587_lock_rate_source_nonpolar_priority.csv'
MD=DOC/'NL2_HU_B267_V40_ALL_587_TRUE_GTO_NL2_LOCK_RATE_AND_MEDIUM_SOURCE.md'

def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def key(x):return (x['model_id'],x['flop'],x['turn'],x['exact_action_line'],x['actor_seat'])

def main():
    old,new=read(OLDSTATUS),read(NEWSTATUS)
    original=read(PRIOR);stored_matrix=read(MATRIX)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30'
    assert new['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(152,240,0,392)
    assert (new['CERT_MULTIBOARD'],new['APPROX'],new['EST'],new['TOTAL'])==(153,239,0,392)
    assert new['parent_v39_sha256']==sha(OLDSTATUS)
    assert original['parent_status_sha256']==sha(OLDSTATUS)
    assert stored_matrix['parent_v40_status_sha256']==sha(NEWSTATUS)
    mid='ln-iso-lmp_r_model-wpg493'
    assert {k for k in old['records'] if old['records'][k]!=new['records'][k]}=={mid}
    assert old['records'][mid]['label']=='APPROX'
    assert new['records'][mid]['label']=='CERT-MULTIBOARD'
    assert new['records'][mid]['proven_exact_board_count']==3
    m=create(new)
    assert (m['CERT_MULTIBOARD'],m['APPROX'],m['EST'])==(153,239,0)
    assert len(m['models'])==153 and len(m['boards'])==587
    assert m['boards']==stored_matrix['boards'] and m['models']==stored_matrix['models']
    assert m['strict_aggregate']==stored_matrix['strict_aggregate']
    assert (m['strict_aggregate']['named_board_proofs'],
       m['strict_aggregate']['hero_lock_variants'])==(587,679)
    assert m['strict_aggregate']['b50_research_candidate_boards']>=133
    independently=audit(new)
    assert (independently['cert_multiboard'],independently['approx'],independently['EST'])==(153,239,0)
    assert (independently['aggregate']['named_board_proofs'],
         independently['aggregate']['paired_hero_locked_source_variants'])==(587,679)
    assert independently['not_generalized_handclass_GTO'] and independently['not_actual_NL2_earnings']
    original_rows={key(z):z for z in original['per_exact_board_source_provenance']}
    current_rows={key(z):z for z in m['boards']}
    assert len(original_rows)==584 and len(current_rows)==587
    assert set(original_rows).issubset(current_rows)
    newkeys=set(current_rows)-set(original_rows)
    assert len(newkeys)==3
    newboards=[current_rows[k] for k in newkeys]
    assert {x['flop'] for x in newboards}=={'6s5h3d','9s6h3d','KsQh4d'}
    assert all(z['model_id']==mid and z['actor_seat']==1 and
      z['exact_action_line']=='b75 r c/x b50 c/x' and
      z['spot']=='LMP_CO_BB' and z['assumed_preflop_ranges'] and
      z['strictly_reachable_combo_count']>0 and
      z['genuine_GTO_exploitability_pct']<=.5 and
      z['spr_relative_error_pct']<=5 and z['hero_lock_proofs']
      for z in newboards)
    assert next(z for z in newboards if z['flop']=='6s5h3d')['GTO_run_id']==44901784001
    assert any(z['source_run_id']==44903333583
      for z in next(z for z in newboards if z['flop']=='6s5h3d')['hero_lock_proofs'])
    assert all(len(z['hero_lock_proofs'])==1 for z in newboards)
    rows=[];count=collections.Counter()
    for k,b in current_rows.items():
        assert b['strictly_reachable_combo_count']>0 and b['hero_lock_proofs']
        assert len(b['GTO_sha256'])==64
        assert b['genuine_GTO_exploitability_pct']<=.5
        assert b['spr_relative_error_pct']<=5
        assert b['generic_handclass_texture_policy_is_not_GTO'] is True
        assert b['no_general_bet_size_recommendation'] is True
        obs=assumed=unmatched=unknown=0
        for lock in b['hero_lock_proofs']:
            assert lock['version'] in ('exp_ip','exp_oop')
            assert lock['source_run_id']>0 and len(lock['source_sha256'])==64
            assert lock['EV_is_model_estimate_not_real_winnings'] is True
            z=lock['source_node_counts']
            if lock['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN':
                assert all(z.get(field) is None for field in ('observed_marginal','assumed_default','unmatched_unlocked'))
                unknown+=1
            else:
                assert lock['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
                assert all(isinstance(z.get(field),int) and z[field]>=0
                  for field in ('observed_marginal','assumed_default','unmatched_unlocked'))
                obs+=z['observed_marginal']
                assumed+=z['assumed_default']
                unmatched+=z['unmatched_unlocked']
        research=b['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE'
        if research: assert b['b50_eligible_combo_count']>0
        else: assert b['b50_research_status']=='NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'
        if k in original_rows:
            old=original_rows[k]
            assert (old['genuine_GTO_run'],old['genuine_GTO_sha256'],
               old['true_strict_hero_combos'])==(
               b['GTO_run_id'],b['GTO_sha256'],b['strictly_reachable_combo_count'])
            assert old['real_NL2_hero_lock_runs']==[z['source_run_id'] for z in b['hero_lock_proofs']]
            assert (old['observed_NL2_pool_street_size_marginal_nodes'],
              old['assumed_default_nodes'],old['unmatched_villain_nodes'],
              old['historical_unknown_lock_variants'])==(obs,assumed,unmatched,unknown)
            assert old['exact_named_board_50pct_nonpolar_research_only']==research
            assert old['b50_strict_eligible_combos']==b['b50_eligible_combo_count']
        else:
            assert b['model_id']==mid
            assert b['assumed_preflop_ranges'] is True
        kind=('HISTORICAL_UNKNOWN_PRESENT' if unknown else
              'ASSUMED_DEFAULT_PRESENT' if assumed else
              'POOL_MARGINAL_ONLY_NOT_PRIVATE_CARD' if obs else 'NO_MEASURED_RATE')
        z=dict(rank=b['rank'],model_id=b['model_id'],spot=b['spot'],
            flop=b['flop'],turn=b['turn'],exact_action_line=b['exact_action_line'],
            actor_seat=b['actor_seat'],strict_hero_combos=b['strictly_reachable_combo_count'],
            genuine_GTO_run=b['GTO_run_id'],genuine_GTO_sha256=b['GTO_sha256'],
            real_NL2_hero_lock_runs=[n['source_run_id'] for n in b['hero_lock_proofs']],
            lock_variants=len(b['hero_lock_proofs']),
            observed_NL2_pool_marginal_nodes=obs,assumed_default_nodes=assumed,
            unmatched_villain_nodes=unmatched,historical_unknown_lock_variants=unknown,
            rate_provenance=kind,rank_specific_source_rate_gap=(unknown>0 or assumed>0 or obs==0),
            exact_board_only_50pct_depolarization_research=research,
            medium_bet_eligible_strict_combos=b['b50_eligible_combo_count'],
            observed_NL2_private_card_conditionals=False,
            generic_texture_certification=False,universal_50pct_recommendation=False)
        rows.append(z)
        count['boards']+=1;count['locks']+=len(b['hero_lock_proofs'])
        count['observed_pool_marginal_source_nodes']+=obs
        count['assumed_default_source_nodes']+=assumed
        count['unmatched_villain_nodes']+=unmatched
        count['unknown_lock_source_variant_denominators']+=unknown
        count['exact_board_50pct_research_candidate_only']+=int(research)
        count['boards_with_missing_measured_rate_evidence']+=int(z['rank_specific_source_rate_gap'])
    assert (count['boards'],count['locks'])==(587,679)
    assert count['exact_board_50pct_research_candidate_only']>=133
    priorcounts=original['counts']
    assert count['observed_pool_marginal_source_nodes']>=priorcounts['observed_nodes']
    assert count['assumed_default_source_nodes']>=priorcounts['assumed_nodes']
    assert count['unmatched_villain_nodes']>=priorcounts['unmatched_nodes']
    assert count['unknown_lock_source_variant_denominators']>=priorcounts['historical_unknown_lock_variants']
    assert count['boards_with_missing_measured_rate_evidence']>=priorcounts['board_has_assumed_or_unknown_or_no_observed_marginal']+3
    rows.sort(key=lambda z:(z['rank'],-z['historical_unknown_lock_variants'],
        -z['assumed_default_nodes'],z['flop'],z['turn']))
    fields=['rank','model_id','spot','flop','turn','exact_action_line','actor_seat',
        'strict_hero_combos','genuine_GTO_run','lock_variants',
        'observed_NL2_pool_marginal_nodes','assumed_default_nodes','unmatched_villain_nodes',
        'historical_unknown_lock_variants','rate_provenance','rank_specific_source_rate_gap',
        'exact_board_only_50pct_depolarization_research','medium_bet_eligible_strict_combos']
    with CSV.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(rows)
    result=dict(schema='NL2_HU_B267_V40_ALL_587_GENUINE_GTO_ACTOR_NL2_LOCK_MEDIUM_SOURCE_V1',
        V39_parent_status_sha256=sha(OLDSTATUS),
        V40_status_sha256=sha(NEWSTATUS),
        V40_matrix_sha256=sha(MATRIX),
        original_B249_V39_gap_sha256=sha(PRIOR),
        CERT_MULTIBOARD=153,APPROX=239,EST=0,TOTAL=392,
        genuine_named_boards=587,real_hero_NL2_lock_variants=679,
        exact_board_b50_candidates=count['exact_board_50pct_research_candidate_only'],
        counts=dict(count),additive_rank313_three_named_flops=sorted(z['flop'] for z in newboards),
        unchanged_V39_584_exact_GTO_SHA_and_actor_NL2_locks=True,
        per_exact_board_source_provenance=rows,
        highest_frequency_incomplete_measured_rate_priority=[z for z in rows if z['rank_specific_source_rate_gap']][:60],
        all_private_card_NL2_conditionals_unmeasured=True,
        unknown_and_assumed_never_treated_as_observed=True,
        b50_only_exact_board_not_all_textures=True,
        no_generic_handclass_GTO_or_CERT_inferred=True,
        PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    docs=['# B267 V40 all 587 genuine named GTO + NL2 actor-locked board rate sources',
        '', '**153 CERT / 239 APPROX / 0 EST**. ',
        'V39 original 584 distinct GTO+NL2 actor-board SHA proofs remain exact and untouched. '
        'V40 adds three separate LMP rank313 real actor-IP GTO + partial NL2 lock boards. '
        'Original limped 169-class preflop weights are assumed, not measured NL2 private cards.',
        '',
        f"Current boards: {count['boards']}; actor-locked source variants {count['locks']}; "
        f"observed pooled marginal source nodes {count['observed_pool_marginal_source_nodes']}, "
        f"assumed {count['assumed_default_source_nodes']}, unmatched {count['unmatched_villain_nodes']}, "
        f"historical unknown-rate lock variants {count['unknown_lock_source_variant_denominators']}.",
        f"50% pot nonpolarized research only on {count['exact_board_50pct_research_candidate_only']} named boards, "
        'never a general hand-class bet size recommendation.', '',
        '|Rank|Exact flop / turn|Exact line|Observed / assumed / unmatched|Unknown lock source|50%-pot research|',
        '|---:|---|---|---|---:|---|']
    for z in result['highest_frequency_incomplete_measured_rate_priority'][:45]:
        docs.append(f"|{z['rank']}|{z['flop']} / {z['turn']}|{z['exact_action_line']}|"
          f"{z['observed_NL2_pool_marginal_nodes']}/{z['assumed_default_nodes']}/"
          f"{z['unmatched_villain_nodes']}|{z['historical_unknown_lock_variants']}|"
          f"{'named-board candidate' if z['exact_board_only_50pct_depolarization_research'] else 'not evidenced'}|")
    docs.extend(['','No fabricated private-card NL2 frequencies. Unknown remains unknown, '
      'not zero or measured; unlocked branches retain their scope. '
      'Full 587 original source locks and HU2475 must pass independently before commit. '
      'Draft PR #2 NEVER MERGE.'])
    MD.write_text('\n'.join(docs)+'\n')
    print('PASS B267 V40',json.dumps(dict(count),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
