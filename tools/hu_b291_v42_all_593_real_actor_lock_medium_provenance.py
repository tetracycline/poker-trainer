#!/usr/bin/env python3
"""B291: source-first V42 593 authentic named GTO + true CO-IP/OOP NL2 locks.
Preserve all original V41 590 per-public-board proofs byte-for-byte, verify
B289 rank46 3 actual GTO SHA + actor NL2 lock provenance, maintain observed
NL2 POOL marginals vs assumed defaults and UNKNOWN denominators. 50% pot
nonpolarized remains research on exact named boards only, never generic.
"""
import collections,csv,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create
D=pathlib.Path('data');DOC=pathlib.Path('docs')
OLD_STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
STATUS=D/'nl2_hu_multiboard_status_v42_b289_rank46.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v42_b289.json'
OLD=D/'nl2_hu_b273_v41_all_590_exact_lock_rate_medium_gap_priority.json'
OUT=D/'nl2_hu_b291_v42_all_593_exact_lock_rate_medium_gap_priority.json'
CSV=D/'nl2_hu_b291_v42_all_593_exact_lock_rate_medium_gap_priority.csv'
MD=DOC/'NL2_HU_B291_V42_ALL_593_TRUE_NL2_ACTOR_LOCK_RATE_MEDIUM_SOURCE.md'
MID='ln-iso-lmp_t_model-17z0wyl'
EXPECTED={'8s8h3d':(44666294821,44666294821,10),
          '9s6h3d':(44666294821,44882669727,1),
          '7s7h2d':(44939456600,44947726457,12)}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(z):return (z['model_id'],z['flop'],z['turn'],z['exact_action_line'],z['actor_seat'])
def main():
    old,status=read(OLD_STATUS),read(STATUS);m=read(MATRIX);prior=read(OLD)
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(154,238,0,392)
    assert status['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46'
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(155,237,0,392)
    assert status['parent_v41_sha256']==sha(OLD_STATUS)
    assert {k for k in old['records'] if old['records'][k]!=status['records'][k]}=={MID}
    assert old['records'][MID]['label']=='APPROX'
    assert status['records'][MID]['label']=='CERT-MULTIBOARD'
    assert status['records'][MID]['proven_exact_board_count']==3
    assert prior['schema']=='NL2_HU_B273_V41_ALL_590_AUTHENTIC_NAMED_GTO_NL2_LOCK_MEDIUM_SOURCE_V1'
    assert prior['V41_status_sha256']==sha(OLD_STATUS)
    assert prior['all_named_boards']==590 and prior['all_actor_NL2_lock_variants']==682
    assert m['parent_v42_status_sha256']==sha(STATUS)
    created=create(status)
    assert (created['CERT_MULTIBOARD'],created['APPROX'],created['EST'])==(155,237,0)
    assert (len(created['models']),len(created['boards']))==(155,593)
    assert created['models']==m['models'] and created['boards']==m['boards']
    assert created['strict_aggregate']==m['strict_aggregate']
    assert (m['strict_aggregate']['named_board_proofs'],m['strict_aggregate']['hero_lock_variants'],
        m['strict_aggregate']['b50_research_candidate_boards'])==(593,685,134)
    independently=audit(status)
    assert (independently['cert_multiboard'],independently['approx'],independently['EST'])==(155,237,0)
    assert (independently['aggregate']['named_board_proofs'],
       independently['aggregate']['paired_hero_locked_source_variants'],
       independently['aggregate']['board_examples_with_b50_candidate'])==(593,685,134)
    assert independently['not_generalized_handclass_GTO'] and independently['not_actual_NL2_earnings']
    previous={key(z):z for z in prior['per_exact_board_source_provenance']}
    current={key(z):z for z in m['boards']}
    assert len(previous)==590 and len(current)==593
    assert set(previous).issubset(current)
    added=[z for k,z in current.items() if k not in previous]
    assert len(added)==3 and {z['flop'] for z in added}==set(EXPECTED)
    assert all(z['model_id']==MID and z['spot']=='LMP_CO_BB' and
      z['exact_action_line']=='x b50 c/x' and z['actor_seat']==1 and
      z['strictly_reachable_combo_count']>0 and
      z['genuine_GTO_exploitability_pct']<=.5 and z['spr_relative_error_pct']<=5 and
      z['assumed_preflop_ranges'] and len(z['hero_lock_proofs'])==1 for z in added)
    for z in added:
        gto,lock,strict=EXPECTED[z['flop']]
        assert z['GTO_run_id']==gto and z['strictly_reachable_combo_count']==strict
        l=z['hero_lock_proofs'][0]
        assert (l['source_run_id'],l['version'])==(lock,'exp_ip')
        assert l['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN'
        assert all(v is None for v in l['source_node_counts'].values())
        assert len(l['source_sha256'])==64 and len(z['GTO_sha256'])==64
    rows=[];tot=collections.Counter()
    for k,b in current.items():
        assert b['strictly_reachable_combo_count']>0 and b['hero_lock_proofs']
        assert len(b['GTO_sha256'])==64 and b['genuine_GTO_exploitability_pct']<=.5
        assert b['spr_relative_error_pct']<=5
        assert b['generic_handclass_texture_policy_is_not_GTO'] and b['no_general_bet_size_recommendation']
        measured=assumed=unmatched=unknown=0
        for l in b['hero_lock_proofs']:
            assert l['version'] in ('exp_ip','exp_oop')
            assert l['source_run_id']>0 and len(l['source_sha256'])==64
            assert l['EV_is_model_estimate_not_real_winnings']
            source=l['source_node_counts']
            if l['node_rate_data_status']=='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN':
                assert all(source.get(f) is None for f in ('observed_marginal','assumed_default','unmatched_unlocked'))
                unknown+=1
            else:
                assert l['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
                assert all(isinstance(source.get(f),int) and source[f]>=0
                   for f in ('observed_marginal','assumed_default','unmatched_unlocked'))
                measured+=source['observed_marginal']
                assumed+=source['assumed_default']
                unmatched+=source['unmatched_unlocked']
        medium=b['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE'
        if medium:assert b['b50_eligible_combo_count']>0
        else:assert b['b50_research_status']=='NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'
        if k in previous:
            oldrow=previous[k]
            assert (oldrow['genuine_GTO_run'],oldrow['genuine_GTO_sha256'],
                oldrow['strict_hero_combos'],oldrow['real_NL2_hero_lock_runs'])==(
                b['GTO_run_id'],b['GTO_sha256'],b['strictly_reachable_combo_count'],
                [z['source_run_id'] for z in b['hero_lock_proofs']])
            assert (oldrow['observed_NL2_pool_marginal_nodes'],oldrow['assumed_default_nodes'],
                oldrow['unmatched_villain_nodes'],oldrow['historical_unknown_lock_variants'])==(
                measured,assumed,unmatched,unknown)
            assert oldrow['exact_50pct_depolarized_board_research_only']==medium
            assert oldrow['b50_eligible_combo_count']==b['b50_eligible_combo_count']
        else:
            assert b['model_id']==MID and unknown==1
            assert (measured,assumed,unmatched)==(0,0,0)
        category=('HISTORICAL_UNKNOWN_PRESENT' if unknown else
                  'ASSUMED_DEFAULT_PRESENT' if assumed else
                  'POOL_MARGINAL_ONLY_NOT_PRIVATE_CARD' if measured else 'NO_MEASURED_RATE')
        z=dict(rank=b['rank'],model_id=b['model_id'],spot=b['spot'],
          flop=b['flop'],turn=b['turn'],exact_action_line=b['exact_action_line'],
          actor_seat=b['actor_seat'],strict_hero_combos=b['strictly_reachable_combo_count'],
          genuine_GTO_run=b['GTO_run_id'],genuine_GTO_sha256=b['GTO_sha256'],
          real_NL2_hero_lock_runs=[q['source_run_id'] for q in b['hero_lock_proofs']],
          lock_variant_count=len(b['hero_lock_proofs']),
          observed_NL2_pool_marginal_nodes=measured,
          assumed_default_nodes=assumed,unmatched_villain_nodes=unmatched,
          historical_unknown_lock_variants=unknown,
          provenance_category=category,
          measured_rate_incomplete=bool(assumed or unknown or not measured),
          exact_50pct_depolarized_board_research_only=medium,
          b50_eligible_combo_count=b['b50_eligible_combo_count'],
          observed_NL2_private_card_conditional_rates=False,
          all_handclass_texture_actions_certified=False,
          universal_50pct_bet_advice=False)
        rows.append(z)
        tot['named_boards']+=1;tot['genuine_actor_NL2_lock_variants']+=len(b['hero_lock_proofs'])
        tot['observed_pool_marginal_nodes']+=measured;tot['assumed_default_nodes']+=assumed
        tot['unmatched_villain_nodes']+=unmatched
        tot['unknown_source_denominator_variants']+=unknown
        tot['b50_named_board_research_only']+=int(medium)
        tot['boards_with_incomplete_measured_source_rate']+=int(z['measured_rate_incomplete'])
    assert (tot['named_boards'],tot['genuine_actor_NL2_lock_variants'],
        tot['b50_named_board_research_only'])==(593,685,134)
    for k in ('observed_pool_marginal_nodes','assumed_default_nodes','unmatched_villain_nodes'):
        assert tot[k]==prior['counts'][k]
    assert tot['unknown_source_denominator_variants']==prior['counts']['unknown_source_denominator_variants']+3
    assert tot['boards_with_incomplete_measured_source_rate']==prior['counts']['boards_with_incomplete_measured_source_rate']+3
    rows.sort(key=lambda z:(z['rank'],-z['historical_unknown_lock_variants'],
       -z['assumed_default_nodes'],z['flop'],z['turn']))
    fields=['rank','model_id','spot','flop','turn','exact_action_line','actor_seat',
      'strict_hero_combos','genuine_GTO_run','lock_variant_count',
      'observed_NL2_pool_marginal_nodes','assumed_default_nodes','unmatched_villain_nodes',
      'historical_unknown_lock_variants','provenance_category','measured_rate_incomplete',
      'exact_50pct_depolarized_board_research_only','b50_eligible_combo_count']
    with CSV.open('w',newline='',encoding='utf8') as fp:
        writer=csv.DictWriter(fp,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    result=dict(schema='NL2_HU_B291_V42_ALL_593_TRUE_GTO_NL2_LOCK_SOURCE_RATE_MEDIUM_V1',
       V41_status_sha256=sha(OLD_STATUS),V42_status_sha256=sha(STATUS),
       V42_matrix_sha256=sha(MATRIX),V41_source_gap_report_sha256=sha(OLD),
       CERT_MULTIBOARD=155,APPROX=237,EST=0,TOTAL=392,
       all_named_boards=593,all_NL2_actor_lock_variants=685,
       counts=dict(tot),new_rank46_three_true_GTO_NL2_flops=sorted(z['flop'] for z in added),
       all_previous_V41_590_board_source_SHA_and_lock_counts_unchanged=True,
       per_exact_board_source_provenance=rows,
       high_frequency_incomplete_source_rate_queue=[
          z for z in rows if z['measured_rate_incomplete']][:60],
       observed_pool_street_size_marginal_not_private_card_conditional=True,
       assumed_default_and_unknown_not_imputed_as_measured=True,
       exact_50pct_only_named_board_research_not_general_bet_strategy=True,
       no_generic_or_unseen_texture_CERT=True,
       PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    doc=['# B291 V42 593 exact original GTO + true NL2 actor locks and medium50 provenance',
      '','**155 CERT/237 APPROX/0 EST.** Source frozen: all V41 590 named board GTO SHA '
      'and actor NL2 Rust lock variants are unchanged. Three new true rank46 boards '
      '8s8h3d/5s, 9s6h3d/Ts, 7s7h2d/3s have original GTO+matched real NL2 CO-IP '
      'with strict legal combos 10, 1, 12. Original LMP 169-class preflop ranges '
      'are **ASSUMED**, not observed NL2 private cards.',
      '',
      f"Source statistics: {tot['named_boards']} authentic GTO named boards, "
      f"{tot['genuine_actor_NL2_lock_variants']} actor NL2 lock variants; "
      f"{tot['observed_pool_marginal_nodes']} pooled observed bet/street marginal nodes, "
      f"{tot['assumed_default_nodes']} assumed default nodes, "
      f"{tot['unmatched_villain_nodes']} unmatched villain nodes and "
      f"{tot['unknown_source_denominator_variants']} historical unknown rate-denominator lock variants.",
      f"50% pot nonpolarization applies only to {tot['b50_named_board_research_only']} exact named-board research candidates.",
      'No pooled marginal represents observed conditional hole-card NL2 behavior. '
      'Unknown sources remain UNKNOWN; GTO flop + locked downstream is not a whole-tree lock.',
      '','|Rank|Named exact board|Exact line|Pooled observed / assumed / unmatched|Unknown|b50 exact research|',
      '|---:|---|---|---|---:|---|']
    for z in result['high_frequency_incomplete_source_rate_queue'][:45]:
        doc.append(f"|{z['rank']}|{z['flop']} / {z['turn']}|{z['exact_action_line']}|"
          f"{z['observed_NL2_pool_marginal_nodes']}/{z['assumed_default_nodes']}/{z['unmatched_villain_nodes']}|"
          f"{z['historical_unknown_lock_variants']}|"
          f"{'named candidate' if z['exact_50pct_depolarized_board_research_only'] else 'not evidenced'}|")
    doc+=['','Full 593 named source/actor 50% research and 2475/2475 HU link Actions must PASS before this file is committed.',
      'PR#2 Draft NEVER MERGE.']
    MD.write_text('\n'.join(doc)+'\n')
    print('PASS B291 V42',json.dumps(dict(tot),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
