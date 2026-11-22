#!/usr/bin/env python3
"""B419 exact per-board 163 CERT / 618 original named CFR boards: observed NL2
pool marginals vs assumed/unmatched, plus evidence-only 50% depolarization flags.

Never call pooled marginals observed conditional/private-card frequencies.
Never blanket-promote 50% sizing on boards with unsupported actual GTO source.
"""
import collections,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create

D=pathlib.Path('data')
S=D/'nl2_hu_multiboard_status_v50_b417_rank166.json'
M=D/'nl2_hu_cert_lock_medium_matrix_v50_b417.json'
OUT=D/'nl2_hu_b419_cert163_board618_lock710_medium_ledger.json'
DOC=pathlib.Path('docs/NL2_HU_B419_ALL_CERT_LOCK_DEPOL_163_618.md')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=read(S);m=read(M)
 assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(163,229,0,392)
 assert m['V50_status_sha256']==sha(S) and m['source_unknown_variants_after']==0
 assert (m['CERT_MULTIBOARD'],m['APPROX'],m['EST'],len(m['models']),len(m['boards']))==(
   163,229,0,163,618)
 fresh=audit(s);from_rebuild=create(s)
 assert (fresh['cert_multiboard'],fresh['approx'],fresh['EST'])==(163,229,0)
 assert (fresh['aggregate']['named_board_proofs'],fresh['aggregate']['paired_hero_locked_source_variants'])==(618,710)
 assert from_rebuild['strict_aggregate']==m['strict_aggregate']
 assert from_rebuild['boards']==m['boards'] and from_rebuild['models']==m['models']
 source=read(D/'nl2_hu_b417_rank166_three_true_source_cert_proof.json')
 assert (source['CERT_after'],source['APPROX_after'],source['named_boards_after'],source['hero_lock_variants_after'])==(163,229,618,710)
 archive=read(D/'nl2_hu_b392_rank107_persistent_original_source_archive_index.json')
 assert len(archive['verified_archives'])==3 and archive['genuine_GTO_and_NL2_partial_source_SHA_matches_160_CERT']
 rec=read(D/'nl2_hu_b368_lock_denominator_recovery.json')
 assert (rec['unknown_before'],rec['recovered_variants'],rec['unknown_after'])==(334,334,0)
 statuses=collections.Counter();totals=collections.Counter();rows=[];model_ids=collections.Counter()
 for board in sorted(m['boards'],key=lambda z:(z['rank'],z['model_id'],z['flop'],z['turn'],z['exact_public_board'])):
  mid=board['model_id'];src=s['records'][mid]
  assert src['label']=='CERT-MULTIBOARD'
  assert board['spot']==src['solver_profile']
  assert board['strictly_reachable_combo_count']>0
  assert board['spr_relative_error_pct']<=5
  assert len(board['GTO_sha256'])==64 and board['GTO_run_id']>0
  assert board['generic_handclass_texture_policy_is_not_GTO'] is True
  assert board['no_general_bet_size_recommendation'] is True
  assert board['hero_lock_proofs'] and 1<=len(board['hero_lock_proofs'])<=6
  assert board['b50_research_status'] in (
    'EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE',
    'NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE')
  medium=(board['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE')
  if medium:assert board['b50_eligible_combo_count']>0
  statuses[board['b50_research_status']]+=1
  model_ids[mid]+=1
  lock_rows=[]
  for lock in board['hero_lock_proofs']:
   n=lock['source_node_counts']
   assert lock['node_rate_data_status']=='MIXED_SOURCE_NL2_MARGINAL_PROXY'
   assert all(isinstance(n[z],int) and n[z]>=0 for z in ('observed_marginal','assumed_default','unmatched_unlocked'))
   assert lock['source_run_id']>0 and len(lock['source_sha256'])==64
   assert lock['version']==('exp_ip' if board['actor_seat']==1 else 'exp_oop')
   assert lock['EV_is_model_estimate_not_real_winnings'] is True
   assert lock['lock_scope'] in ('DOWNSTREAM_TURN_RIVER_ONLY','PARTIALLY_LOCKED_SOURCE')
   counts={z:n[z] for z in ('observed_marginal','assumed_default','unmatched_unlocked')}
   totals['observed_pool_marginal_pattern_nodes']+=counts['observed_marginal']
   totals['assumed_default_pattern_nodes']+=counts['assumed_default']
   totals['unmatched_unlocked_pattern_nodes']+=counts['unmatched_unlocked']
   totals['lock_variants']+=1
   totals['pool_marginal_present_lock_variants']+=int(counts['observed_marginal']>0)
   totals['lock_variants_with_assumed_defaults']+=int(counts['assumed_default']>0)
   lock_rows.append(dict(run_id=lock['source_run_id'],sha256=lock['source_sha256'],
    version=lock['version'],provenance_status=lock['node_rate_data_status'],
    source_scope=lock['source_scope'],lock_scope=lock['lock_scope'],
    node_counts=counts,
    empirical_frequency_scope='OBSERVED_NL2_STREET_AND_SIZE_POOL_MARGINAL_ONLY',
    not_empirical_villain_private_hand_conditional=True,
    unknown_action_rates_are_not_zero=True))
  rows.append(dict(model_id=mid,rank=board['rank'],source_spot=board['spot'],
   flop=board['flop'],turn=board['turn'],exact_public_board=board['exact_public_board'],
   exact_action_line=board['exact_action_line'],actor_seat=board['actor_seat'],
   strictly_reachable_hero_combos=board['strictly_reachable_combo_count'],
   original_GTO_run_id=board['GTO_run_id'],original_GTO_sha256=board['GTO_sha256'],
   source_SPR=board['actual_spr'],
   hero_partial_NL2_pool_lock_provenance=lock_rows,
   medium_50pct_research_status=board['b50_research_status'],
   medium_50pct_true_eligible_combos=board['b50_eligible_combo_count'],
   no_generalized_50pct_bet_strategy=True))
 assert len(rows)==618 and len(model_ids)==163
 assert all(3<=x<=5 for x in model_ids.values())
 assert totals['lock_variants']==710
 assert totals['observed_pool_marginal_pattern_nodes']==m['strict_aggregate']['observed_marginal_pattern_nodes']
 assert totals['assumed_default_pattern_nodes']==m['strict_aggregate']['assumed_pattern_nodes']
 assert totals['unmatched_unlocked_pattern_nodes']==m['strict_aggregate']['unmatched_opponent_nodes']
 assert statuses['EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE']==m['strict_aggregate']['b50_research_candidate_boards']
 assert sum(statuses.values())==618
 r107=next(x for x in s['records'].values() if x['frequency_rank']==107)
 assert r107['label']=='CERT-MULTIBOARD' and len(r107['certified_3_to_5_exact_flop_boards'])==3
 assert set(x['flop'] for x in rows if x['model_id']==r107['model_id'])=={'Jh9d6s','7s5h3d','QsJh4d'}
 for rank in (166,214,219):
  r=next(x for x in s['records'].values() if x['frequency_rank']==rank)
  assert r['label']=='CERT-MULTIBOARD' and len(r['certified_3_to_5_exact_flop_boards'])==3
  assert len([x for x in rows if x['model_id']==r['model_id']])==3
 assert s['records']['ln-ipfr-r_model-7kv23r']['label']=='APPROX'
 assert s['records']['ln-ipfr-r_model-h0c7q7']['label']=='APPROX'
 out=dict(schema='NL2_B419_ALL_163_CERT_618_EXACT_BOARDS_710_LOCK_PROVENANCE_AND_50PCT_RESEARCH_V1',
  source_status_sha256=sha(S),source_matrix_sha256=sha(M),B368_recovery_sha256=sha(D/'nl2_hu_b368_lock_denominator_recovery.json'),
  B390_exact_rank107_source_sha256=sha(D/'nl2_hu_b390_rank107_three_true_GTO_NL2_IP_cert_proof.json'),
  B417_rank166_cert_source_sha256=sha(D/'nl2_hu_b417_rank166_three_true_source_cert_proof.json'),
  B392_persisted_original_Rust_SHA_index=sha(D/'nl2_hu_b392_rank107_persistent_original_source_archive_index.json'),
  CERT_MULTIBOARD=163,APPROX=229,EST=0,TOTAL=392,
  exact_named_boards=len(rows),hero_lock_source_variants=totals['lock_variants'],
  B368_historical_unknown_before=334,B368_historical_recovered=334,unknown_remains=0,
  exact_nonpolarized_50pct_research_candidate_boards=statuses['EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE'],
  exact_50pct_unproven_boards=statuses['NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'],
  source_pool_node_totals=dict(totals),
  per_named_board_exact_source_lock_and_50pct_status=rows,
  source_rates_observed_only_by_NL2_aggregated_street_and_size=True,
  no_NL2_private_card_opponent_observation=True,
  missing_rates_explicit_assumptions_not_observed=True,
  disallow_50pct_bet_extrapolation_to_unproven_board_or_generic_handclass=True,
  PR2_remains_draft_unmerged=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 DOC.write_text('# B419: all CERT exact boards, NL2 source lock provenance and 50% research ledger\n\n'
  f"Verified **{out['CERT_MULTIBOARD']} CERT /{out['APPROX']} APPROX /0 EST**; "
  f"{len(rows)} original authenticated *named public boards* and {totals['lock_variants']} true paired partial NL2 lock proof variants. "
  f"Measured-by-source aggregate NL2 marginal nodes {totals['observed_pool_marginal_pattern_nodes']}; "
  f"disclosed assumed default nodes {totals['assumed_default_pattern_nodes']}; "
  f"unmatched/unlocked nodes {totals['unmatched_unlocked_pattern_nodes']}; UNKNOWN=0. "
  f"50%-pot nonpolarized **exact-board research candidates {out['exact_nonpolarized_50pct_research_candidate_boards']}**; "
  f"unproven exact boards {out['exact_50pct_unproven_boards']} must NOT automatically apply that sizing. "
  "All data are exact original CFR+pooled marginal/assumed source scope; NOT observed villain private-card conditional frequencies or proven actual earnings. "
  "The JSON enumerates every named board and its lock source SHAs, measured vs assumed vs unlocked denominators and sizing research status. "
  "PR #2 remains draft/unmerged; HU2475 Actions must PASS.\n")
 print('PASS B419 complete',len(model_ids),'CERT source models',len(rows),'boards',totals['lock_variants'],'locks, candidate b50',out['exact_nonpolarized_50pct_research_candidate_boards'])
if __name__=='__main__':main()
