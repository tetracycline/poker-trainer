#!/usr/bin/env python3
"""B292 V42: source-blind 237 remaining APPROX rank/priority after genuine
B289 rank46 promotion. Historical B278 frequency is immutable, rank71 is
only one true GTO+NL2 actor-flop short; include nine exact verified zero
rank71 GTO actor proofs without claiming a broad texture rejection.
"""
import collections,csv,gzip,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v42_b289_rank46.json'
OLD=D/'nl2_hu_b278_v41_238_approx_rank46_and_71_oneflop_true_sourceblind.json'
NEGATIVE=D/'nl2_hu_b281_v41_rank71_sha_zero_legal_actor_flop_dedup.json'
OUT=D/'nl2_hu_b292_v42_237_approx_sourceblind_real_pair_gap_priority.json'
CSV=D/'nl2_hu_b292_v42_237_approx_sourceblind_real_pair_gap_priority.csv'
MD=DOC/'NL2_HU_B292_V42_237_APPROX_RANK71_ONE_PAIR_SHORT_QUEUE.md'
RECENT=[
  ('B274','KsJh4d','2h',44936238647),
  ('B275','8s7h5d','3d',44936370769),
  ('B276','9s6h3d','Ts',44936829955),
]
def ld(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    st=ld(STATUS);old=ld(OLD);negative=ld(NEGATIVE)
    assert st['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46'
    assert (st['CERT_MULTIBOARD'],st['APPROX'],st['EST'],st['TOTAL'])==(155,237,0,392)
    assert (old['cert'],old['approx'],old['est'],old['total'])==(154,238,0,392)
    assert old['current_V41_status_sha256']==sha(D/'nl2_hu_multiboard_status_v41_b271_rank61.json')
    assert len(old['remaining_238_APPROX_gap_rows'])==238
    assert [z['rank'] for z in old['one_flop_short_sourceblind_priorities']]==[46,71]
    assert st['records']['ln-iso-lmp_t_model-17z0wyl']['label']=='CERT-MULTIBOARD'
    assert st['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert negative['V41_status_sha256']==old['current_V41_status_sha256']
    assert negative['zero_legal_actor_known_exact_flop_turn_pairs']==6
    assert negative['prior_rank71_two_genuine_GTO_plus_NL2_hero_pair_flops']==['4s4h2d','7s5h3d']
    rows=[];cohorts=collections.Counter()
    for prev in old['remaining_238_APPROX_gap_rows']:
        mid=prev['model_id'];rank=prev['rank']
        if rank==46:
            assert mid=='ln-iso-lmp_t_model-17z0wyl'
            assert prev['minimum_remaining_new_exact_flop_actor_lock_pairs']==1
            continue
        assert st['records'][mid]['label']=='APPROX'
        assert st['records'][mid]['frequency_rank']==rank
        assert prev['minimum_remaining_new_exact_flop_actor_lock_pairs']>=1
        z=dict(prev)
        z['no_future_source_outcome_used_for_rank']=True
        z['V42_status_label']='APPROX'
        rows.append(z);cohorts[z['priority_cohort']]+=1
    assert len(rows)==237 and len({z['model_id'] for z in rows})==237
    rows.sort(key=lambda z:(z['minimum_remaining_new_exact_flop_actor_lock_pairs'],
      -z['frozen_frequency_proxy'],z['rank']))
    assert rows[0]['rank']==71
    assert [z['rank'] for z in rows if z['minimum_remaining_new_exact_flop_actor_lock_pairs']==1]==[71]
    assert (cohorts['ONE_DISTINCT_AUTHENTIC_FLOP_PLUS_ACTOR_LOCK_SHORT'],
       cohorts['TWO_MORE_DISTINCT_TRUE_GTO_AND_ACTOR_LOCK_PAIRS'],
       cohorts['ZERO_GENUINE_PAIRED_FLOPS_NEED_THREE'])==(1,29,207)
    neg=[]
    known={(x['flop'],x['turn']) for x in negative['exact_rank71_OOP_river_negative_100bb_GTO_sources']}
    assert len(known)==6
    for batch,flop,turn,run in RECENT:
        pinpath=D/f'nl2_hu_{batch.lower()}_rank71_lmp_{flop}_gto_parent_pin.json'
        indexpath=D/f'solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.index.json'
        gzpath=D/f'solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.json.gz'
        assert all(x.is_file() for x in (pinpath,indexpath,gzpath))
        p,i=ld(pinpath),ld(indexpath)
        assert (p['source_run_id'],i['run_id'])==(run,run)
        assert (p['target_rank'],p['model_id'],p['spot'],p['flop'],p['turn'])==(
          71,'ln-iso-lmp_r_model-vlgh2t','LMP_CO_BB',flop,turn)
        assert (p['flop_line'],p['turn_line'])==('b50 c','x b50 c')
        assert (p['target_exact_actor_OOP_river_nodes'],p['target_exact_actor_OOP_strict_combos'])==(0,0)
        assert (i['gto_cases'],i['locked_cases'],i['verified_cases'])==(1,0,1)
        assert (i['exact_target_actor_OOP_river_nodes'],i['exact_target_actor_OOP_strict_combos'])==(0,0)
        assert i['source_sha256']==hashlib.sha256(gzip.decompress(gzpath.read_bytes())).hexdigest()
        assert i['gzip_sha256']==sha(gzpath)
        assert i['no_generic_model_certification'] and i['immediate_CERT_upgrades']==0
        neg.append(dict(batch=batch,flop=flop,turn=turn,run_id=run,
           source_sha256=i['source_sha256'],strict_exact_actor_OOP_combos=0,
           earlier_exact_board_duplicate=(flop,turn) in known,
           constrained_to_this_flop_turn_and_original_action_tree=True,
           no_generic_certification=True))
    assert len(neg)==3 and sum(x['earlier_exact_board_duplicate'] for x in neg)==1
    asserted=audit(st)
    assert (asserted['cert_multiboard'],asserted['approx'],asserted['EST'])==(155,237,0)
    assert (asserted['aggregate']['named_board_proofs'],
      asserted['aggregate']['paired_hero_locked_source_variants'],
      asserted['aggregate']['board_examples_with_b50_candidate'])==(593,685,134)
    assert asserted['not_generalized_handclass_GTO'] and asserted['not_actual_NL2_earnings']
    output=dict(schema='NL2_HU_B292_V42_237_APPROX_FROZEN_SOURCEBLIND_NEGATIVE_R71_V1',
      V42_status_sha256=sha(STATUS),B278_prior_238_gap_sha256=sha(OLD),
      rank71_prior_zero_six_gto_sha_report=sha(NEGATIVE),
      CERT_MULTIBOARD=155,APPROX=237,EST=0,TOTAL=392,
      newly_CERT_rank46_removed_from_prior_238=True,
      only_one_historical_actor_paired_flop_short_rank71=True,
      only_one_flop_short_rank71_flops=['4s4h2d','7s5h3d'],
      all_237_APPROX_source_gap_rows=rows,cohort_counts=dict(cohorts),
      additional_three_SHA_verified_original_GTO_zero_actor_cases=neg,
      historical_six_distinct_zero_rank71_sources_immutable=True,
      B276_exact_source_duplicate_of_B173=True,
      pending_B290_As7h3d_GTO_not_claimed_without_complete_source_and_NL2_lock=True,
      no_prior_source_frequency_reoptimized=True,
      no_original_GTO_only_sourced_as_true_NL2_actor_locked=True,
      no_unobserved_NL2_private_card_action_rates_fabricated=True,
      existing_593_named_CERT_boards_and_685_real_NL2_locks_unchanged=True,
      exact_board_50pct_nonpolar_research_only=134,
      PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    fields=['rank','model_id','spot','hero_seat','frozen_frequency_proxy',
      'genuine_paired_flop_count','minimum_remaining_new_exact_flop_actor_lock_pairs',
      'priority_cohort','source_history']
    with CSV.open('w',newline='',encoding='utf8') as fp:
        w=csv.DictWriter(fp,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(rows)
    doc=['# B292 V42 remaining 237 APPROX sourceblind authentic three-board gaps','',
      '**155 CERT / 237 APPROX / 0 EST**; rank46 was promoted by B289 and removed '
      'from the frozen sourceblind queue without reranking any remaining model. '
      'Rank71 is now the **sole historical one true paired GTO + NL2 actor flop short** '
      '(paired 4s4h2d and 7s5h3d). Other 29 spots need two genuine pairs, 207 need three.',
      '',
      'B281 original GTO SHA checked 6 exact zero BB-OOP target-action cases; '
      'B274 KsJh4d/2h, B275 8s7h5d/3d, B276 9s6h3d/Ts separately reconfirm zero '
      'strict legal actor combos, last being an exact duplicate of B173. '
      'These negatives reject only the original EXACT flop/turn/line, NOT '
      'other turns, trees or unrelated runouts.',
      '','|Rank|Still needed authentic GTO+NL2 actor flops|Frozen opportunity proxy|',
      '|---:|---:|---:|']
    for z in rows[:50]:
        doc.append(f"|{z['rank']}|{z['minimum_remaining_new_exact_flop_actor_lock_pairs']}|{z['frozen_frequency_proxy']:.8f}|")
    doc+=['','B290 A-high As7h3d is pending and MUST NOT be counted without true '
      'original Rust GTO SHA, exact actor and genuine new NL2 lock. '
      'No measured private-card opponent conditional rates invented. '
      'All 593 named original GTO/real actor NL2 locks and 2475/2475 HU '
      'navigation checks must PASS before commit. PR #2 Draft NEVER MERGE.']
    MD.write_text('\n'.join(doc)+'\n')
    print('PASS B292',json.dumps(dict(CERT=155,APPROX=237,cohorts=dict(cohorts),
       one_flop_short=71,rank71_original_zero_sources=9)),flush=True)
if __name__=='__main__':main()
