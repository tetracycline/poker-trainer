#!/usr/bin/env python3
"""B278: independently SHA-reconcile original B3 GTO/B209 pin and actual B210
NL2 actor-IP locked rank46 9s6h3d, then source-blind reprioritize the 238
V41 APPROX without changing any certification or GTO/lock action selection.
No historical snapshot rewrite, no extrapolation or measured private-card rates.
"""
import collections,csv,gzip,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
ORIGINAL=D/'nl2_hu_b277_v41_238_approx_true_sourceblind_queue.json'
HISTORY=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
GTO_PIN=D/'nl2_hu_b209_rank46_lmp_9s6h3d_original_b3_gto_pin.json'
GTO_INDEX=D/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
GTO_ARCHIVE=D/'solver_evidence/NL2_MULTIBOARD_B3.json.gz'
LOCK_INDEX=D/'solver_evidence/NL2_MULTIBOARD_B210_R46_B3_EXP_IP.index.json'
LOCK_ARCHIVE=D/'solver_evidence/NL2_MULTIBOARD_B210_R46_B3_EXP_IP.json.gz'
OUT=D/'nl2_hu_b278_v41_238_approx_rank46_and_71_oneflop_true_sourceblind.json'
CSV=D/'nl2_hu_b278_v41_238_approx_rank46_and_71_oneflop_true_sourceblind.csv'
MD=DOC/'NL2_HU_B278_V41_R46_B209_B210_REAL_GTO_NL2_PAIR_SOURCEBLIND_PRIORITY.md'
def ld(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    s=ld(STATUS);frozen=ld(ORIGINAL);history=ld(HISTORY)
    gp,gi,li=ld(GTO_PIN),ld(GTO_INDEX),ld(LOCK_INDEX)
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(154,238,0,392)
    assert frozen['V41_status_sha256']==sha(STATUS)
    assert (frozen['CERT_MULTIBOARD'],frozen['APPROX'])==(154,238)
    assert len(frozen['all_238_approx_source_gaps'])==238
    assert gp['schema']=='NL2_HU_B209_RANK46_ORIGINAL_B3_9S6H3D_GTO_PARENT_PIN_V1'
    assert gp['source_run_id']==gi['run_id']==li['original_GTO_B3_run_id']==44666294821
    assert (gp['target_rank'],gp['model_id'],gp['actor'])==(46,'ln-iso-lmp_t_model-17z0wyl',1)
    assert (gp['spot'],gp['flop'],gp['turn'])==('LMP_CO_BB','9s6h3d','Ts')
    assert (gp['original_GTO_flop_line'],gp['exact_turn_line'])==('x b50 c','x b50 c/x')
    assert gp['strict_original_GTO_actor_IP_combos']==1
    assert gp['original_full_GTO_flop_not_recomputed'] is True
    assert gp['assumed_preflop_169class_not_observed'] is True
    assert gp['original_B3_archive_sha256']==sha(GTO_ARCHIVE)==gi['gzip_sha256']
    assert gp['original_B3_index_sha256']==sha(GTO_INDEX)
    assert gi['source_sha256']==hashlib.sha256(gzip.decompress(GTO_ARCHIVE.read_bytes())).hexdigest()
    assert (gi['gto_cases'],gi['locked_cases'])==(43,90)
    assert li['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert (li['batch'],li['run_id'])==('B210_R46_B3_EXP_IP',44882669727)
    assert li['original_B209_GTO_pin_sha256']==sha(GTO_PIN)
    assert (li['original_B3_root_SHA256'],li['original_B3_manifest_SHA256'],
        li['original_B3_job_SHA256'])==(
        gp['original_gto_root_sha256'],gp['original_gto_manifest_sha256'],
        gp['original_gto_job_sha256'])
    assert li['source_sha256']==hashlib.sha256(gzip.decompress(LOCK_ARCHIVE.read_bytes())).hexdigest()
    assert li['gzip_sha256']==sha(LOCK_ARCHIVE)
    assert (li['verified_cases'],li['gto_cases'],li['locked_cases'])==(1,0,1)
    assert (li['rank'],li['model_id'],li['acting_seat'],li['exact_actor_IP_turn_line'])==(
        46,'ln-iso-lmp_t_model-17z0wyl',1,'x b50 c/x')
    assert li['genuine_NL2_actor_IP_turn_nodes']==1 and li['strict_actor_IP_combos']==1
    assert li['NL2_rates_pooled_marginals_and_assumed_defaults_only']
    assert li['original_preflop_169_class_ASSUMED']
    assert li['immediate_CERT_upgrades']==0 and li['no_generic_MODEL_certification']
    assert li['reason_if_zero'] is None
    past=next(z for z in history['rows'] if z['rank']==46)
    assert past['model_id']==li['model_id'] and past['hero_seat']==1
    assert past['distinct_GTO_plus_NL2_hero_flops']==['8s8h3d']
    assert sorted(past['distinct_real_GTO_flops'])==['8s8h3d','9s6h3d']
    matching=[z for z in past['exact_authentic_gto_source_proofs'] if z['flop']=='9s6h3d']
    assert len(matching)==1 and matching[0]['source_sha']==gp['original_GTO_case_SHA256']
    assert matching[0]['true_NL2_actor_locked'] is False  # historical B175 snapshot only, before B210
    assert matching[0]['actor']==1 and matching[0]['exact_line']=='x b50 c/x'
    assert matching[0]['strict_legal_combos']==1 and matching[0]['SPR_error_pct']<=5
    assert matching[0]['GTO_gap_pct']<=.5
    rows=[];cohorts=collections.Counter()
    for old in frozen['all_238_approx_source_gaps']:
        z=dict(old)
        if z['rank']==46:
            assert z['model_id']=='ln-iso-lmp_t_model-17z0wyl'
            assert z['actor_legal_GTO_plus_REAL_NL2_locked_flops']==['8s8h3d']
            assert z['GTO_but_hero_NL2_lock_missing']==['9s6h3d']
            assert z['minimum_remaining_new_exact_flop_actor_lock_pairs']==2
            z['actor_legal_GTO_plus_REAL_NL2_locked_flops']=['8s8h3d','9s6h3d']
            z['GTO_but_hero_NL2_lock_missing']=[]
            z['genuine_paired_flop_count']=2
            z['minimum_remaining_new_exact_flop_actor_lock_pairs']=1
            z['priority_cohort']='ONE_DISTINCT_AUTHENTIC_FLOP_PLUS_ACTOR_LOCK_SHORT'
            z['B210_authenticated_actor_pair_newer_than_frozen_B175']=True
            z['newer_actor_lock_original_GTO_run']=44666294821
            z['newer_actor_lock_run']=44882669727
            z['newer_exact_board_authentic_SHA']=matching[0]['source_sha']
        assert s['records'][z['model_id']]['label']=='APPROX'
        assert z['minimum_remaining_new_exact_flop_actor_lock_pairs']>=1
        cohorts[z['priority_cohort']]+=1
        rows.append(z)
    assert len(rows)==238
    rows.sort(key=lambda x:(x['minimum_remaining_new_exact_flop_actor_lock_pairs'],
        -x['frozen_frequency_proxy'],x['rank']))
    ones=[z for z in rows if z['minimum_remaining_new_exact_flop_actor_lock_pairs']==1]
    assert [z['rank'] for z in ones]==[46,71]  # rank46 higher source-blind frequency than rank71
    assert [z['frozen_frequency_proxy'] for z in ones]==sorted(
        [z['frozen_frequency_proxy'] for z in ones],reverse=True)
    assert (cohorts['ONE_DISTINCT_AUTHENTIC_FLOP_PLUS_ACTOR_LOCK_SHORT'],
        cohorts['TWO_MORE_DISTINCT_TRUE_GTO_AND_ACTOR_LOCK_PAIRS'],
        cohorts['ZERO_GENUINE_PAIRED_FLOPS_NEED_THREE'])==(2,29,207)
    assert sum(cohorts.values())==238
    a=audit(s)
    assert (a['cert_multiboard'],a['approx'],a['EST'])==(154,238,0)
    assert (a['aggregate']['named_board_proofs'],
        a['aggregate']['paired_hero_locked_source_variants'],
        a['aggregate']['board_examples_with_b50_candidate'])==(590,682,134)
    assert a['not_generalized_handclass_GTO'] and a['not_actual_NL2_earnings']
    out=dict(schema='NL2_HU_B278_V41_238_APPROX_NEW_B210_R46_AUTHENTIC_ACTOR_PAIR_SOURCEBLIND_V1',
        current_V41_status_sha256=sha(STATUS),original_B277_sourceblind_sha256=sha(ORIGINAL),
        historic_B175_sha256=sha(HISTORY),cert=154,approx=238,est=0,total=392,
        newly_verified_B210_rank46_true_GTO_plus_NL2_actor_IP=dict(
            rank=46,spot='LMP_CO_BB',flop='9s6h3d',turn='Ts',line='x b50 c/x',
            actor=1,original_GTO_run=44666294821,real_NL2_child_run=44882669727,
            original_GTO_case_SHA256=gp['original_GTO_case_SHA256'],
            original_B3_archive_SHA256=sha(GTO_ARCHIVE),
            original_B209_GTO_parent_pin_SHA256=sha(GTO_PIN),
            authentic_B210_NL2_child_SHA256=li['source_sha256'],
            GTO_legal_actor_combos=1,NL2_legal_actor_combos=1,
            no_measured_NL2_private_card_conditional_rates=True,
            no_new_generic_model_CERT=True),
        one_flop_short_sourceblind_priorities=ones,
        remaining_238_APPROX_gap_rows=rows,cohort_counts=dict(cohorts),
        current_rank71_queued_GTO_only_proofs_not_promoted=
            frozen['current_rank71_preregistered_original_GTO_artifact_audit'],
        no_new_GTO_only_counted_as_hero_actor_locked=True,
        original_historic_B175_snapshot_not_rewritten=True,
        no_future_2026_strategy_reoptimization=True,
        no_unsupported_generic_GTO_recommendations=True,
        no_unknown_NL2_rate_imputed_as_empirical=True,
        frozen_source_frequency_ranking_unchanged=True,
        existing_590_cert_boards_unmodified=True,
        PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    fields=['rank','model_id','spot','hero_seat','frozen_frequency_proxy','genuine_paired_flop_count',
        'minimum_remaining_new_exact_flop_actor_lock_pairs','priority_cohort','source_history']
    with CSV.open('w',encoding='utf8',newline='') as fp:
        writer=csv.DictWriter(fp,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    lines=['# B278: original GTO and real actor NL2 source makes rank46 additionally one-flop-short',
      '','**V41 unchanged: 154 CERT /238 APPROX /0 EST.** '
      'All 590 verified exact named board source locks and 134 b50 research-only proofs unchanged.',
      'B209 original true B3 100bb LMP 9s6h3d/Ts GTO source (run 44666294821) '
      'has exactly 1 strict CO-IP turn combo, with original GTO SHA pinned. '
      'B210 separate authentic Rust NL2 CO-IP partial lock (run 44882669727) has '
      'exact same actor/line and 1 strictly reachable combo. '
      'Original 169-class limped preflop ranges are ASSUMED; observed street/size pooled '
      'marginals and defaults are NOT private-hand NL2 action frequencies.',
      'This authentic *second* paired rank46 flop was completed after original frozen B175 snapshot '
      'and is added without altering the historical report. Rank46 still APPROX, '
      'needs an independent third flop plus real actor lock.',
      'Source-blind one-flop short priority now rank46 (frequency 0.00911) then rank71 (0.00630).',
      '','|Frozen rank|True GTO + actor NL2 paired flops|Remaining real pairs required|Frozen opportunity proxy|',
      '|---:|---|---:|---:|']
    for z in rows[:50]:
        lines.append(f"|{z['rank']}|{', '.join(z['actor_legal_GTO_plus_REAL_NL2_locked_flops']) or 'none'}|"
            f"{z['minimum_remaining_new_exact_flop_actor_lock_pairs']}|{z['frozen_frequency_proxy']:.8f}|")
    lines.extend(['','No current existing CERT source, NL2 unknown/default flags or nonpolarized research claim changed. '
       'Full 590 original GTO/actor NL2 medium/unknown audit and 2475 HU contract must PASS before commit. '
       'Draft PR #2, NEVER MERGE.'])
    MD.write_text('\n'.join(lines)+'\n')
    print('PASS B278',json.dumps(dict(cert=154,approx=238,one_short_ranks=[46,71],
        cohorts=dict(cohorts),source_b210_true_lock_strict=1)),flush=True)
if __name__=='__main__':main()
