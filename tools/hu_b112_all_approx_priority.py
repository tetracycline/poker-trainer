#!/usr/bin/env python3
"""B112: all remaining V26 APPROX reassessed by frozen NL2 frequency order.

Preselect the COMPLETE 255 APPROX cohort before authentic GTO/locked-source
inspection. Classify gaps ONLY from matched exact public board, actor,
full-street reach, SHA/SPR and proven NL2 hero partial lock; never tune by EV.
Status V1–V26 all remain byte-identical. No extrapolated texture policy.
"""
import collections,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,texture

R=pathlib.Path('data')
P=R/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
RANK=R/'nl2_hu_multiboard_prerank.json'
QUEUE=R/'nl2_hu_stage2_queue.json'
OUT=R/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
DOC=pathlib.Path('docs/NL2_HU_B112_V26_ALL_APPROX_GAP_QUEUE.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    status=json.loads(P.read_text())
    rank=json.loads(RANK.read_text())
    queue=json.loads(QUEUE.read_text())
    assert status['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220'
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['TOTAL'])==(137,255,392)
    assert status['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    assert status['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    ordering=sorted(rank['nodes'],key=lambda x:x['rank_by_empirically_grounded_frequency_proxy'])
    assert [x['rank_by_empirically_grounded_frequency_proxy'] for x in ordering]==list(range(1,393))
    selected=[dict(x) for x in ordering if status['records'][x['model_id']]['label']=='APPROX']
    assert len(selected)==255
    assert all(not x['high_frequency_priority'] for x in selected)
    assert all(selected[i]['estimated_NL2_hand_opportunity_fraction']>=
               selected[i+1]['estimated_NL2_hand_opportunity_fraction']
               for i in range(len(selected)-1))
    # Source-blind freeze: entire exact cohort is fixed BEFORE evidence inspection.
    ranked_ids=[(x['rank_by_empirically_grounded_frequency_proxy'],x['model_id']) for x in selected]
    models={x['model_id']:x for x in queue['records']}
    sources=[pathlib.Path(x) for x in status['source_evidence']['source_files']]
    assert len(sources)>=30 and all(x.is_file() for x in sources)
    gto,lock,summary=build_source_index(R,sources)
    rows=[]
    for n in selected:
        model=models[n['model_id']]
        assert model['solver_profile']==n['spot'] and model['family']==n['family']
        n['preflop_text']=model['preflop_text']
        n['abstract_action_history']=model['abstract_action_history']
        cand,err=candidates(n,gto,lock,None)
        byflop=collections.defaultdict(list)
        for proof in cand:byflop[proof['flop']].append(proof)
        matched={f:vals for f,vals in byflop.items() if any(x['nl2_locked_variants'] for x in vals)}
        boards,why=choose_3_5(cand) if err is None else ([],err)
        rows.append(dict(
            rank=n['rank_by_empirically_grounded_frequency_proxy'],
            model_id=n['model_id'],spot=n['spot'],street=n['street'],family=n['family'],
            abstract_history=n['abstract_action_history'],model_spr=n['approx_spr'],
            frozen_frequency_proxy=n['estimated_NL2_hand_opportunity_fraction'],
            original_label='APPROX',
            matched_real_gto_flops=sorted(byflop),
            hero_locked_flops=sorted(matched),
            distinct_matched_hero_flops=len(matched),
            missing_real_hero_flops_to_3=max(0,3-len(matched)),
            exact_source_ready=bool(boards),
            authentic_3_to_5_flops=[x['flop'] for x in boards],
            source_error_or_blocker=why,
            missing_locked_existing_GTO_flops=sorted(set(byflop)-set(matched)),
            missing_locked_known_source_samples=[
              dict(flop=f,turn=z['turn'],gto_run=z['source_run_id'],
                gto_sha256=z['source_sha256'],exact_line=z['actual_exact_action_line'],
                acting_seat=z['acting_seat'],strict_legal_combos=z['strict_full_street_combo_reachable'],
                actual_spr=z['actual_spr'],
                texture=texture(f))
              for f in sorted(set(byflop)-set(matched))
              for z in [sorted(byflop[f],key=lambda x:(
                x['relative_spr_error_pct'],-x['strict_full_street_combo_reachable']))[0]]
            ]))
    assert [(x['rank'],x['model_id']) for x in rows]==ranked_ids
    ready=[x for x in rows if x['exact_source_ready']]
    one=[x for x in rows if x['missing_real_hero_flops_to_3']==1 and not x['exact_source_ready']]
    two=[x for x in rows if x['missing_real_hero_flops_to_3']==2]
    remaining=[x for x in rows if x['missing_real_hero_flops_to_3']>=3]
    output=dict(schema='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1',
       parent_V26_sha256=sha(P),frozen_rank_sha256=sha(RANK),
       candidate_count=255,baseline_cert=137,baseline_approx=255,
       source_blind_all_APPROX_preselected=True,
       all_MODELs_evaluated_before_any_posthoc_selection=True,
       source_files=len(sources),source_summary=summary,
       source_ready_count=len(ready),one_board_short_count=len(one),
       two_board_short_count=len(two),three_or_more_missing_count=len(remaining),
       candidate_count_reconciles=(len(ready)+len(one)+len(two)+len(remaining)==255),
       source_ready_ranks=[x['rank'] for x in ready],
       one_board_short_ranks=[x['rank'] for x in one],
       no_current_reclassification=True,no_private_card_NL2_observation_claim=True,
       no_generic_texture_GTO=True,pr2_draft_never_merge=True,rows=rows)
    assert output['candidate_count_reconciles']
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    lines=['# B112 | All remaining 255 APPROX: source-blind frozen frequency reassessment','',
       'V26 remains **137 CERT / 255 APPROX / EST 0**; this report NEVER relabels a model.',
       'Exact GTO+hero partial lock is required on 3–5 *different* public flop boards, with strict actor, SPR, source SHA and reachable combo gates.',
       'Batch E run 44732810327 remains verified; unobserved NL2 hand-conditional rates are NOT empirical.',
       '## Source-grounded next priorities','',
       '| Priority | Rank | Model | Spot | Matched hero+GTO flops | Existing real GTO missing matching lock |',
       '| --- | ---: | --- | --- | ---: | --- |']
    for x in (one+ready+two)[:60]:
        label='ONE-MISSING' if x in one else 'READY-3/5' if x in ready else 'TWO-MISSING'
        lines.append('| '+label+' | '+str(x['rank'])+' | '+x['model_id']+' | '+x['spot']+' | '+
            str(x['distinct_matched_hero_flops'])+' | '+', '.join(x['missing_locked_existing_GTO_flops'])+' |')
    lines+=['','Use existing authentic GTO+actor-specific IP/OOP source before any new Rust solve; ranks reflect frozen NL2 opportunity, NOT profitability.',
      'No fabricated EST certificates, no data-driven private-card NL2 conditional frequencies, no generic texture GTO.',
      'PR #2 stays Draft and must never merge.','']
    DOC.write_text('\n'.join(lines))
    print(json.dumps(dict(PASS=True,baseline_CERT=137,baseline_APPROX=255,
       source_ready_ranks=output['source_ready_ranks'],
       one_board_short_ranks=output['one_board_short_ranks'],
       two_board_short_count=len(two),three_plus_missing=len(remaining)),ensure_ascii=False))
if __name__=='__main__':main()
