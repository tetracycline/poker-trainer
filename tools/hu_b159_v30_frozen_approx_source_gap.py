#!/usr/bin/env python3
"""B159: recompute each CURRENT V30 APPROX's 3-5 genuine exact-board gap.

SOURCE BLIND: only immutable already independently audited GTO and NL2
hero-side Rust/source archives. The separate B154 new GTO contains ZERO
strict rank46 hero-IP action reach; never count a syntactic action as CERT.
GTO source must <=0.5% convergence, legal sequential combo, exact SPR
within 5%, same actor/street/action, paired true actor-side NL2 partial.
Unobserved NL2 private-hand action frequencies are NEVER synthesized.
This task only inventories source readiness. It NEVER changes CERT count.
"""
import collections,copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat,texture
from hu_cert_lock_medium_audit import audit

ROOT=pathlib.Path('data')
STATUS=ROOT/'nl2_hu_multiboard_status_v30_b145_rank47.json'
MATRIX=ROOT/'nl2_hu_cert_lock_medium_matrix_v30_b145.json'
FROZEN=ROOT/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
RANK=ROOT/'nl2_hu_multiboard_prerank.json'
QUEUE=ROOT/'nl2_hu_stage2_queue.json'
EXTRA=ROOT/'solver_evidence/NL2_MULTIBOARD_B154_R46_4S4H2D_GTO.json.gz'
OUT=ROOT/'nl2_hu_b159_v30_250_APPROX_strict_source_gap.json'
DOC=pathlib.Path('docs/NL2_HU_B159_V30_ALL_250_APPROX_SOURCE_GAP.md')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    status=read(STATUS);matrix=read(MATRIX);frozen=read(FROZEN)
    rank=read(RANK);queue=read(QUEUE)
    assert status['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47'
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(142,250,0,392)
    assert len(matrix['boards'])==554 and len(matrix['models'])==142
    assert matrix['parent_v30_status_sha256']==sha(STATUS)
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['candidate_count']==255 and len(frozen['rows'])==255
    assert frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    assert status['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    assert status['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    assert status['records']['ln-iso-lmp_t_model-17z0wyl']['label']=='APPROX'
    assert status['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert status['records']['ln-iso-lmp_r_model-wpg493']['label']=='APPROX'
    # Independent original B154 source/INDEX/immutability before its extra
    # data can be indexed, with full target proof negative.
    ix=read(EXTRA.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(EXTRA.read_bytes());proof= json.loads(raw)
    assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert ix['batch']=='B154_R46_4S4H2D_GTO' and ix['run_id']==44855330215
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert ix['gzip_sha256']==sha(EXTRA)
    assert (ix['actual_spot_flop_version_jobs'],ix['gto_cases'],ix['locked_cases'],ix['verified_cases'])==(1,1,0,1)
    assert ix['exact_target_actor_IP_checked_turn_nodes']==0
    assert ix['exact_target_actor_IP_strict_combos']==0
    assert proof['source_run_id']==ix['run_id'] and not proof['errors']
    assert len(proof['artifacts'])==1 and proof['artifacts'][0]['version']=='gto'
    a=proof['artifacts'][0]
    assert a['spot']=='LMP_CO_BB' and a['flop']=='4s4h2d'
    assert len(a['cases'])==1
    c=a['cases'][0]
    assert (c['flop_line'],c['turn'])==('x b50 c','8s')
    assert not [n for n in c['nodes'] if n['acting_seat']==1
                and n['exact_node_line']=='x b50 c/x'
                and n['strictly_reachable_combos']>0]
    source_files=[pathlib.Path(x) for x in status['source_evidence']['source_files']]
    assert source_files and all(p.is_file() for p in source_files)
    assert EXTRA not in source_files
    source_files.append(EXTRA)
    assert len(source_files)==len(set(source_files))
    gto,locked,meta=build_source_index(ROOT,source_files)
    nodes={x['rank_by_empirically_grounded_frequency_proxy']:x for x in rank['nodes']}
    staged={x['model_id']:x for x in queue['records']}
    rows=[];counts=collections.Counter();ready=[]
    for old in sorted(frozen['rows'],key=lambda x:x['rank']):
        r=old['rank'];mid=old['model_id'];original=nodes[r]
        assert original['model_id']==mid
        current=status['records'][mid]
        if current['label']=='CERT-MULTIBOARD':
            counts['original_frozen_ALREADY_PROMOTED']+=1
            continue
        assert current['label']=='APPROX'
        assert mid in staged
        m=staged[mid]
        node=copy.deepcopy(original)
        node['preflop_text']=m['preflop_text']
        node['abstract_action_history']=m['abstract_action_history']
        assert (m['solver_profile'],m['family'],m['street'])==(old['spot'],old['family'],old['street'])
        possible,reason=candidates(node,gto,locked,None)
        hero=hero_seat(node['preflop_text'])
        gtoflops=sorted({x['flop'] for x in possible})
        pairedflops=sorted({x['flop'] for x in possible if x['nl2_locked_variants']})
        missing=max(0,3-len(pairedflops))
        textures=sorted({texture(f) for f in pairedflops})
        unique_rows={x['flop']:x for x in possible if x['nl2_locked_variants']}
        selected,selection_reason=choose_3_5(possible)
        gate_pass=bool(selected and not reason and not selection_reason)
        if gate_pass:
            ready.append(dict(rank=r,model_id=mid,matched_flops=pairedflops,
                 selected_flops=sorted(x['flop'] for x in selected)))
        counts['CURRENT_APPROX']+=1
        counts['zero_candidate_flops']+=int(not possible)
        counts['one_hero_flop_short']+=int(missing==1)
        counts['two_hero_flops_short']+=int(missing==2)
        counts['three_or_more_hero_flops_short']+=int(missing>=3)
        counts['GTO_flops_without_hero_lock']+=len(set(gtoflops)-set(pairedflops))
        rows.append(dict(rank=r,model_id=mid,
            family=old['family'],spot=old['spot'],street=old['street'],
            original_approx_spr=old['model_spr'],
            frozen_frequency_proxy=old['frozen_frequency_proxy'],
            hero_actor_seat=hero,abstract_action_history=old['abstract_history'],
            validated_GTO_and_sequential_combo_flops=gtoflops,
            validated_actor_correct_NL2_hero_locked_flops=pairedflops,
            actual_hero_lock_flops=len(pairedflops),
            remaining_DISTINCT_flops_to_3=missing,
            measured_NL2_private_combo_conditional_rates=False,
            certified_3_to_5_now=gate_pass,
            current_blocker=None if gate_pass else (selection_reason or reason or
               'INSUFFICIENT_MATCHED_REAL_GTO_ACTOR_HERO_NL2_SOURCES'),
            known_matched_textures=textures,
            missing_hero_lock_on_existing_valid_GTO_flops=sorted(set(gtoflops)-set(pairedflops)),
            additional_new_verified_B154_flop_available='4s4h2d' in gtoflops,
            GTO_case_convergence_required_pct_max=0.5,SPR_relative_error_pct_max=5,
            no_generic_texture_model_CERT=True))
    assert counts['CURRENT_APPROX']==250
    assert counts['original_frozen_ALREADY_PROMOTED']==5
    assert sum(int(x['remaining_DISTINCT_flops_to_3'] in (0,1,2,3))
               for x in rows)==250
    assert all(x['model_id']!='ln-iso-lmp_t_model-17z0wyl'
               or '4s4h2d' not in x['validated_actor_correct_NL2_hero_locked_flops']
               for x in rows)
    assert all(x['model_id']!='ln-iso-lmp_t_model-17z0wyl'
               or x['remaining_DISTINCT_flops_to_3']>=1 for x in rows)
    independent=audit(status)
    assert independent['aggregate']['named_board_proofs']==554
    assert independent['aggregate']['paired_hero_locked_source_variants']==646
    assert independent['aggregate']['board_examples_with_b50_candidate']==131
    assert independent['not_generalized_handclass_GTO'] and independent['not_actual_NL2_earnings']
    out=dict(schema='NL2_HU_B159_V30_FULL_250_APPROX_SOURCE_BLIND_STRICT_GAP_V1',
         parent_V30_sha256=sha(STATUS),parent_B112_frozen_sha256=sha(FROZEN),
         parent_GTO_B154_source_index_sha256=sha(EXTRA.with_suffix('').with_suffix('.index.json')),
         recomputed_source_count=len(source_files),source_metadata=meta,
         CERT_MULTIBOARD=142,APPROX=250,EST=0,TOTAL=392,
         existing_real_named_board_proofs=554,
         existing_NL2_lock_source_variants=646,
         existing_b50_exact_board_research_candidates=131,
         not_a_promotion=True,ready_for_independent_3_5_full_cert_gate=ready,
         count=len(rows),source_gap_counts=dict(counts),rows=rows,
         all_B154_rank46_4s4h2d_true_GTO_strict_IP_ZERO=True,
         no_fake_hero_lock_from_original_GTO=True,
         no_model_texture_bucket_GTO=True,
         no_NL2_private_combo_conditional_rate_claims=True,
         PR2_draft_never_merge=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    lines=['# B159 | all 250 V30 APPROX verified source-blind GTO/hero-lock gaps','',
      '**142 CERT /250 APPROX /0 EST** unchanged. **554** genuine named boards, '
      '**646** authentic hero-lock source variants, **131** exact 50% pot research flags.','',
      'This audit checks exact board, actual preceding action line, actor, convergence '
      '<=0.5%, genuine full-street sequential combo, SPR within 5%, and paired actual '
      'actor-side NL2 partial source. Source-blind, no fabricated GTO or NL2 private-card statistics.','',
      f'Frozen original 255 APPROX rows: {counts["original_frozen_ALREADY_PROMOTED"]} previously promoted, '
      f'{counts["CURRENT_APPROX"]} remain APPROX. Source-ready source-verified nodes: {len(ready)}.','',
      '| frequency rank | model id | valid GTO flop count | correct hero-lock flop count | missing to 3 | missing locks on existing GTO |',
      '| ---: | --- | ---: | ---: | ---: | --- |']
    for x in rows[:35]:
        lines.append(f"| {x['rank']} | {x['model_id']} | {len(x['validated_GTO_and_sequential_combo_flops'])} | {x['actual_hero_lock_flops']} | {x['remaining_DISTINCT_flops_to_3']} | {', '.join(x['missing_hero_lock_on_existing_valid_GTO_flops']) or 'none'} |")
    lines.extend(['','Full **250-row** SHA-grounded status: '+str(OUT)+'.',
       'B154 source GTO true but rank46 4s4h2d/8s exact checked-turn IP strict combo is **0**. '
       'Its solver job is not a third authentic matched locked flop.',
       'Batch E VERIFIED, all existing CERT locks/nonpolar research flags verified. '
       'All 2475 HU river links must PASS independent Actions prior to commit.',
       'Draft PR #2, NEVER MERGE.',''])
    DOC.parent.mkdir(parents=True,exist_ok=True)
    DOC.write_text('\n'.join(lines))
    print(json.dumps(dict(PASS=True,cert=142,approx=250,rows=len(rows),
         promoted=counts['original_frozen_ALREADY_PROMOTED'],
         ready=len(ready),gap_counts=dict(counts),
         latest_negative='B154 rank46 4s4h2d/8s strict IP combos zero',
         output_sha256=sha(OUT)),ensure_ascii=False))
if __name__=='__main__':main()
