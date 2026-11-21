#!/usr/bin/env python3
"""B258 frozen source-blind rank of all 240 remaining V39 APPROX HU cells.
No automatic CERT, no reconstructed actor rate, no future-run artifacts accepted.
The B175 historical source audit is only a floor for valid original proofs;
later parent GTO runs cannot be called paired NL2 locks without actor verification.
"""
import csv,hashlib,json,pathlib,collections
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v39_b247_rank30.json'
HISTORY=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
FROZEN=D/'nl2_hu_b172_v32_248_APPROX_true_sourceblind_gaps.json'
OUT=D/'nl2_hu_b258_v39_240_approx_frequency_sourceblind_queue.json'
CSV=D/'nl2_hu_b258_v39_240_approx_frequency_sourceblind_queue.csv'
MD=DOC/'NL2_HU_B258_V39_240_APPROX_REAL_3BOARD_SOURCE_PRIORITY.md'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=load(STATUS);h=load(HISTORY);f=load(FROZEN)
 assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30'
 assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(152,240,0,392)
 assert len(s['records'])==392
 assert len(h['rows'])==248 and len(f['rows'])==248
 by_id={z['model_id']:z for z in h['rows']}
 freq={z['model_id']:z for z in f['rows']}
 assert len(by_id)==len(freq)==248
 records=[x for x in s['records'].values() if x['label']=='APPROX']
 assert len(records)==240
 counts=collections.Counter();rows=[]
 for v in records:
    mid=v['model_id'];rank=v['frequency_rank']
    assert mid in by_id and mid in freq,(mid,rank)
    old=by_id[mid];q=freq[mid]
    assert old['rank']==rank and q['rank']==rank
    assert old['hero_seat'] in (0,1)
    paired=sorted(set(old['distinct_GTO_plus_NL2_hero_flops']))
    independent=sorted(set(old['distinct_real_GTO_flops']))
    assert set(paired).issubset(independent)
    assert len(paired)<3
    only_gto=sorted(set(independent)-set(paired))
    need=max(0,3-len(paired))
    if len(paired)==2:cohort='ONE_DISTINCT_AUTHENTIC_FLOP_PLUS_ACTOR_LOCK_SHORT'
    elif len(paired)==1:cohort='TWO_MORE_DISTINCT_TRUE_GTO_AND_ACTOR_LOCK_PAIRS'
    else:cohort='ZERO_GENUINE_PAIRED_FLOPS_NEED_THREE'
    # Frozen priority: genuine near-complete before total abstract frequency;
    # for equal gaps highest empirical proxy first, never by future outcomes.
    row=dict(rank=rank,model_id=mid,spot=q['spot'],family=q['family'],
       hero_seat=q['hero_actor'],source_history=old['model_history'],
       frozen_frequency_proxy=q['frozen_frequency_proxy'],
       genuine_historical_GTO_flops=independent,
       actor_legal_GTO_plus_REAL_NL2_locked_flops=paired,
       GTO_but_hero_NL2_lock_missing=only_gto,
       genuine_paired_flop_count=len(paired),
       minimum_remaining_new_exact_flop_actor_lock_pairs=need,
       priority_cohort=cohort,
       historical_source_audit_SHA256=sha(HISTORY),
       historical_snapshot_may_understate_later_GTO_only_evidence=True,
       candidate_cert_really_ready=False,
       no_observed_private_hand_NL2_frequencies_claimed=True,
       no_generic_texture_GTO_claimed=True)
    rows.append(row);counts[cohort]+=1
 assert sum(counts.values())==240
 rows.sort(key=lambda z:(z['minimum_remaining_new_exact_flop_actor_lock_pairs'],
    -z['frozen_frequency_proxy'],z['rank']))
 assert rows[0]['rank'] in (71,313) and rows[1]['rank'] in (71,313)
 assert {z['rank'] for z in rows[:2]}=={71,313}
 assert all(z['minimum_remaining_new_exact_flop_actor_lock_pairs']>=1 for z in rows)
 for i in range(1,len(rows)):
    assert (rows[i-1]['minimum_remaining_new_exact_flop_actor_lock_pairs'],
      -rows[i-1]['frozen_frequency_proxy'])<=(
      rows[i]['minimum_remaining_new_exact_flop_actor_lock_pairs'],
      -rows[i]['frozen_frequency_proxy'])
 assert s['records']['ln-opfr-t_model-1hmsxaw']['label']=='CERT-MULTIBOARD'
 for mid in ['ln-iso-lmp_r_model-vlgh2t','ln-iso-lmp_r_model-wpg493',
             'ln-ipfr-t_model-hxdit','ln-ipfr-t_model-qpx6tn']:
    assert s['records'][mid]['label']=='APPROX'
 existing=audit(s)
 assert (existing['cert_multiboard'],existing['approx'],existing['EST'])==(152,240,0)
 assert (existing['aggregate']['named_board_proofs'],
    existing['aggregate']['paired_hero_locked_source_variants'],
    existing['aggregate']['board_examples_with_b50_candidate'])==(584,676,133)
 spec={'B248':dict(run_id=44901633548,rank=71,flop='6s5h3d'),
       'B250':dict(run_id=44901784001,rank=313,flop='6s5h3d'),
       'B251':dict(run_id=44902084841,rank=60,flop='KsQh4d'),
       'B252':dict(run_id=44902088039,rank=60,flop='8s8h3d'),
       'B253':dict(run_id=44902146101,rank=61,flop='KsQh4d'),
       'B254':dict(run_id=44902150376,rank=61,flop='8s8h3d')}
 for b,z in spec.items():
    assert s['records'][next(r['model_id'] for r in rows if r['rank']==z['rank'])]['label']=='APPROX'
    z['status']='RUN_PENDING_NOT_ACCEPTED_AS_GTO_OR_NL2_CERT_SOURCE'
 # Source-blind queue cannot let still-running source-candidates become certification proof.
 output=dict(schema='NL2_HU_B258_V39_240_APPROX_FROZEN_REAL_SOURCEBLIND_PRIORITY_V1',
    V39_status_sha256=sha(STATUS),original_B175_provenance_sha256=sha(HISTORY),
    original_B172_source_gap_sha256=sha(FROZEN),
    CERT_MULTIBOARD=152,APPROX=240,EST=0,TOTAL=392,
    frozen_frequency_priorities=True,pending_B248_B254_unverified=spec,
    one_flop_short=[z for z in rows if z['minimum_remaining_new_exact_flop_actor_lock_pairs']==1],
    all_240_approx_source_gaps=rows,cohort_counts=dict(counts),
    existing_true_cert_named_boards=584,existing_NL2_actor_lock_variants=676,
    existing_exact_board_50pct_nonpolarized_research_cases=133,
    no_new_real_GTO_proofs_claimed=True,no_new_NL2_actor_locks_claimed=True,
    no_false_GTO_or_CERT_upgrade=True,
    no_unknown_NL2_private_card_rates_imputed_as_observed=True,
    PR2_Draft_NEVER_MERGE=True)
 OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 fields=['rank','model_id','spot','family','hero_seat','frozen_frequency_proxy',
   'genuine_paired_flop_count','minimum_remaining_new_exact_flop_actor_lock_pairs',
   'priority_cohort','source_history']
 with CSV.open('w',newline='',encoding='utf8') as fp:
    w=csv.DictWriter(fp,fieldnames=fields,extrasaction='ignore')
    w.writeheader();w.writerows(rows)
 md=['# B258 V39: all 240 remaining HU APPROX source-blind 3-5 true-board priority','',
     '152 CERT / 240 APPROX / 0 EST. 584 existing exact named original GTO boards, '
     '676 genuine NL2 actor locks, 133 exact nonpolarized 50%-pot research flags.','',
     'Use original B175 source records as **historical floor**, not a claim that '
     'later GTO-only experiments added matched NL2 pairs. '
     'A canceled, partial or running B248–B254 remains unverified and is not counted.','',
     '## Strict source-gap cohorts','']
 for k,v in counts.items():md.append(f'- {k}: {v}')
 md+=['','|Frozen rank|Spot|Original genuine GTO+actor lock flops|Needed|Frozen frequency proxy|',
    '|---:|---|---|---:|---:|']
 for x in rows[:50]:
    md.append(f"|{x['rank']}|{x['spot']}|{', '.join(x['actor_legal_GTO_plus_REAL_NL2_locked_flops']) or 'none'}|"
      f"{x['minimum_remaining_new_exact_flop_actor_lock_pairs']}|{x['frozen_frequency_proxy']:.6f}|")
 md+=['','No source labels changed, no certificate awarded; strict 584 named GTO/lock '
       'source checks and 2475 HU navigation must pass before commit. '
       'PR #2 Draft NEVER MERGE.']
 MD.write_text('\n'.join(md)+'\n')
 print('PASS B258 V39 source-blind APPROX cohort',json.dumps(
    dict(counts,cert=152,approx=240,historic_paired_one_short=[z['rank'] for z in rows[:2]])),flush=True)
if __name__=='__main__':main()
