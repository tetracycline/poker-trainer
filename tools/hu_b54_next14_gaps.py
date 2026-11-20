#!/usr/bin/env python3
"""B54: preregister the next fourteen ranks (42-55) by frozen NL2 frequency ONLY.

CFR source inspection is strictly after source-blind selection. This is not
permission to relax any frozen V1, V2 or V3 certification evidence gate.
Do not label unproven nodes CERT or pool marginals as private-combo observations.
"""
import collections
import hashlib
import json
import pathlib
from hu_multiboard_promote import candidates, choose_3_5, build_source_index, texture

ROOT=pathlib.Path('data')
OUT=ROOT/'nl2_hu_b54_next14_sourceblind_gaps.json'
DOC=pathlib.Path('docs/NL2_HU_B54_NEXT14_GAPS.md')
RANKS=list(range(42,56))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rank_path=ROOT/'nl2_hu_multiboard_prerank.json'
    v4_path=ROOT/'nl2_hu_multiboard_status_v4_batch50.json'
    b39_path=ROOT/'nl2_hu_b39_frequency_tie_prereg.json'
    queue_path=ROOT/'nl2_hu_stage2_queue.json'
    rank=json.loads(rank_path.read_text())
    v4=json.loads(v4_path.read_text())
    b39=json.loads(b39_path.read_text())
    queue=json.loads(queue_path.read_text())
    assert v4['CERT_MULTIBOARD']==33 and v4['APPROX']==359 and v4['TOTAL']==392
    assert v4['source_blind_tie_ranks']==b39['tie_ranks']==[25,26]
    assert rank['cutoff']['N']==24
    ordering={n['rank_by_empirically_grounded_frequency_proxy']:dict(n) for n in rank['nodes']}
    assert len(ordering)==392
    # Freeze the *entire* cohort before reading any CFR sources / profitability.
    target=[ordering[i] for i in RANKS]
    assert all(not n['high_frequency_priority'] for n in target)
    assert all(v4['records'][n['model_id']]['label']=='APPROX' for n in target)
    assert all(target[i]['estimated_NL2_hand_opportunity_fraction']>=
               target[i+1]['estimated_NL2_hand_opportunity_fraction']
               for i in range(len(target)-1))
    model={n['model_id']:n for n in queue['records']}
    paths=[pathlib.Path(x) for x in v4['source_evidence']['source_files']]
    assert len(paths)>=20 and all(p.is_file() for p in paths)
    gto,locked,summ=build_source_index(ROOT,paths)
    rows=[]
    for n in target:
        m=model[n['model_id']]
        n['preflop_text']=m['preflop_text']
        n['abstract_action_history']=m['abstract_action_history']
        refs,err=candidates(n,gto,locked,None)
        byflop=collections.defaultdict(list)
        for z in refs:byflop[z['flop']].append(z)
        matched={f:vals for f,vals in byflop.items()
                 if any(z['nl2_locked_variants'] for z in vals)}
        proofs,why=choose_3_5(refs) if err is None else ([],err)
        samples=[]
        for f,vals in sorted(byflop.items()):
            best=sorted(vals,key=lambda z:(-len(z['nl2_locked_variants']),
                 z['relative_spr_error_pct'],-z['strict_full_street_combo_reachable']))[0]
            samples.append(dict(flop=f,turn=best['turn'],
                line=best['actual_exact_action_line'],
                GTO_run=best['source_run_id'],GTO_sha256=best['source_sha256'],
                acting_seat=best['acting_seat'],actual_spr=best['actual_spr'],
                strict_legal_combo_count=best['strict_full_street_combo_reachable'],
                hero_lock_runs=sorted({v['run_id'] for z in vals
                       for v in z['nl2_locked_variants']})))
        rows.append(dict(rank=n['rank_by_empirically_grounded_frequency_proxy'],
            model_id=n['model_id'],spot=n['spot'],street=n['street'],
            model_spr=n['approx_spr'],frequency_proxy=n['estimated_NL2_hand_opportunity_fraction'],
            history=n['abstract_action_history'],current_label='APPROX',
            matching_true_GTO_flops=sorted(byflop),
            matched_hero_side_NL2_lock_flops=sorted(matched),
            distinct_matched_flop_count=len(matched),
            missing_to_three_flops=max(0,3-len(matched)),
            candidate_3_5_flops=[x['flop'] for x in proofs],
            meets_named_board_certification_evidence=bool(proofs),
            proof_gate_reason=why,
            lock_flop_textures=sorted({texture(f) for f in matched}),
            source_samples=samples))
    assert [r['rank'] for r in rows]==RANKS
    result=dict(schema='NL2_HU_B54_SOURCE_BLIND_NEXT14_GAP_AUDIT_V1',
       source_blind_preselection_ranks=RANKS,
       selection='EXACT_NEXT_9_FROZEN_NL2_FREQUENCY_RANKS_AFTER_B39_TIES',
       fixed_rank_sha256=sha(rank_path),
       frozen_v4_sha256=sha(v4_path),
       b39_prereg_sha256=sha(b39_path),
       original_v1_frozen_cutoff=24,
       source_files=len(paths),
       sources=summ,
       status_v4_cert=33,status_v4_approx=359,
       no_current_reclassification=True,
       no_source_outcome_based_rank_selection=True,
       no_private_combo_NL2_empirical_rates=True,
       rows=rows)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    lines=['# B54 | Frozen NL2 ranks42–55 source-blind gap audit','',
       'PR #2 stays Draft. Current V4 33 CERT / 359 APPROX; V1 24/368 and V2 26/366 unchanged.',
       'Source-blind cohort: exactly fourteen consecutive original ranks 42–55.',
       'Frozen rank chosen before any CFR/source inspection, not by EV/profit.','',
       '| Rank | Spot | Model | matched GTO flops | GTO+correct hero lock flops | Missing to 3 | Pre-existing evidence qualifies |',
       '| ---: | --- | --- | ---: | ---: | ---: | --- |']
    for r in rows:
        lines.append('| '+str(r['rank'])+' | '+r['spot']+' | '+r['model_id']+
           ' | '+str(len(r['matching_true_GTO_flops']))+
           ' | '+str(r['distinct_matched_flop_count'])+
           ' | '+str(r['missing_to_three_flops'])+
           ' | '+('YES' if r['meets_named_board_certification_evidence'] else 'NO')+' |')
    lines+=['','Each exact board has independently pinned GTO SHA, strict legal reach, pot/SPR and actor-correct hero-side lock.',
       'No absent or invalid source is certified; results are not a generic texture GTO strategy.',
       'NEXT: certify existing authentic 3–5 boards for any qualifying preregistered model; first solve/lock ones missing only one board.',
       'Use another independently approved overlay rather than altering the original V1, V2 or V3 registers.',
       'Do NOT merge Draft PR #2.','']
    DOC.write_text('\n'.join(lines))
    print(json.dumps({'cohort':RANKS,
       'gaps':{r['rank']:r['missing_to_three_flops'] for r in rows},
       'source_proof_ready':[r['rank'] for r in rows if r['meets_named_board_certification_evidence']],
       'CERT':33,'APPROX':359},ensure_ascii=False))

if __name__=='__main__':main()
