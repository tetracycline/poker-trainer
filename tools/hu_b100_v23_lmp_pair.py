#!/usr/bin/env python3
"""B100 frozen rank77+78: upgrade ONLY if B99 true anchored Rust hero-OOP
x-x river nodes match three different authentic GTO flops per model.

V22 remains immutable; LMP preflop assumptions and marginal NL2 locks are
NOT measured conditional private-card behavior. All CERT are named-board only.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

R=pathlib.Path('data')
OLD=R/'nl2_hu_multiboard_status_v22_batch94.json'
B60=R/'nl2_hu_b60_next20_sourceblind_gaps.json'
B98=R/'nl2_hu_b98_lmp_8s8h3d_gto_parent_pin.json'
NEW=R/'solver_evidence/NL2_MULTIBOARD_B99_LMP_XX_RIVER.json.gz'
IDX=R/'solver_evidence/NL2_MULTIBOARD_B99_LMP_XX_RIVER.index.json'
OUT=R/'nl2_hu_multiboard_status_v23_b100_lmp_pair.json'
MAT=R/'nl2_hu_cert_lock_medium_matrix_v23.json'
DOC=pathlib.Path('docs/NL2_HU_B100_V23_RANK77_78_CERT.md')
LOCKDOC=pathlib.Path('docs/NL2_HU_B100_V23_ALL_LOCKS_MEDIUM.md')
TARGETS={77:'ln-iso-lmp_r_model-inztdd',78:'ln-iso-lmp_r_model-m4z78r'}
EXPECTED_FLOPS={'8s8h3d','9s6h3d','KsQh4d'}
def sha(buf):return hashlib.sha256(buf).hexdigest()
def fsha(p):return sha(p.read_bytes())

def main():
    before=json.loads(OLD.read_text())
    pre=json.loads(B60.read_text())
    frozen=json.loads(B98.read_text())
    idx=json.loads(IDX.read_text())
    raw=gzip.decompress(NEW.read_bytes())
    proof=json.loads(raw)
    assert before['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V22_BATCH94'
    assert (before['CERT_MULTIBOARD'],before['APPROX'],before['TOTAL'])==(131,261,392)
    assert pre['schema']=='NL2_HU_B60_SOURCE_BLIND_NEXT20_GAP_AUDIT_V1'
    assert pre['source_blind_preselection_ranks']==list(range(76,96))
    assert pre['fixed_rank_sha256']==fsha(R/'nl2_hu_multiboard_prerank.json')
    assert frozen['result']=='PASS_GTO_ROOT_PIN'
    assert frozen['source_run_id']==44666294821 and frozen['frozen_rank_targets']==[77,78]
    assert frozen['original_GTO_preflop_assumed_169class'] is True
    assert frozen['original_GTO_full_size_tree'] is True
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B99_LMP_XX_RIVER' and idx['run_id']>0
    assert idx['actual_spot_flop_version_jobs']==1 and idx['gto_cases']==0 and idx['locked_cases']>=1
    assert idx['original_gto_parent_run']==44666294821
    assert idx['certified_pinned_GTO_parent_not_recomputed'] is True
    assert idx['original_parent_GTO_root_SHA256']==frozen['original_GTO_flop_sha256']
    assert idx['original_B98_parent_manifest_SHA256']==frozen['original_manifest_sha256']
    assert idx['source_sha256']==sha(raw) and idx['gzip_sha256']==fsha(NEW)
    assert proof['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert proof['source_run_id']==idx['run_id'] and not proof['errors']
    assert len(proof['artifacts'])==1 and proof['new_authentic_board_cases']==idx['verified_cases']>=1
    one=proof['artifacts'][0]
    assert (one['spot'],one['version'],one['flop'])==('LMP_CO_BB','exp_oop','8s8h3d')
    assert one['cases'] and not one['errors']
    g=one['cases'][0]
    assert (g['flop_line'],g['turn'])==('x x','5s')
    hero=[n for n in g['nodes'] if n['acting_seat']==0 and
         n['exact_node_line']=='x x/x x/' and n['strictly_reachable_combos']>0]
    assert hero, 'No genuine OOP hero river lock: cannot upgrade'
    rank=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((R/'nl2_hu_stage2_queue.json').read_text())
    byrank={x['rank_by_empirically_grounded_frequency_proxy']:dict(x) for x in rank['nodes']}
    models={x['model_id']:x for x in queue['records']}
    prior=[pathlib.Path(x) for x in before['source_evidence']['source_files']]
    assert len(prior)>=25 and all(x.is_file() for x in prior)
    paths=list(dict.fromkeys(prior+[NEW]))
    gto,locks,meta=build_source_index(R,paths)
    out=copy.deepcopy(before)
    upgrades=[]
    for i,mid in TARGETS.items():
        r=byrank[i];m=models[mid]
        sourceblind=next(x for x in pre['rows'] if x['rank']==i)
        assert r['model_id']==sourceblind['model_id']==mid
        assert sourceblind['missing_to_three_flops']==1
        assert sourceblind['matched_hero_side_NL2_lock_flops']==['9s6h3d','KsQh4d']
        assert before['records'][mid]['label']=='APPROX'
        assert m['solver_profile']=='LMP_CO_BB' and m['family']=='LMP' and m['street']==2
        assert hero_seat(m['preflop_text'])==0
        r['preflop_text']=m['preflop_text']
        r['abstract_action_history']=m['abstract_action_history']
        rows,err=candidates(r,gto,locks,None)
        if err:raise ValueError('Rank'+str(i)+' source mismatch: '+str(err))
        boards,reason=choose_3_5(rows)
        if reason or len(boards)!=3:raise ValueError('Rank'+str(i)+' exact boards still incomplete: '+str(reason))
        assert {b['flop'] for b in boards}==EXPECTED_FLOPS
        assert len({b['flop_texture'] for b in boards})>=2
        for b in boards:
            assert b['acting_seat']==0 and b['actual_exact_action_line']=='x x/x x/'
            assert b['strict_full_street_combo_reachable']>0
            assert b['genuine_gto_exploitability_pct']<=.5
            assert b['relative_spr_error_pct']<=5
            assert b['assumed_preflop_ranges'] is True
            assert len(b['source_sha256'])==64
            assert b['nl2_locked_variants']
            assert all(v['version']=='exp_oop' for v in b['nl2_locked_variants'])
        n=next(b for b in boards if b['flop']=='8s8h3d')
        assert n['turn']=='5s' and n['source_run_id']==44666294821
        assert any(v['run_id']==idx['run_id'] for v in n['nl2_locked_variants'])
        out['records'][mid].update(
           label='CERT-MULTIBOARD',high_frequency_preregistered=True,
           original_top24_high_frequency_preregistered=False,
           source_blind_expansion_rank=i,prereg_cohort='B60_NEXT20',
           certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
           blocked_reason=None,
           source_credibility='GITHUB_ACTIONS_SHA_PINNED_GTO_AND_AUTHENTIC_TURN_ONLY_RUST_NL2_PARTIAL_LOCK')
        upgrades.append(dict(rank=i,model_id=mid,
            flops=[b['flop'] for b in boards],
            GTO_runs=sorted({b['source_run_id'] for b in boards}),
            hero_lock_runs=sorted({z['run_id'] for b in boards for z in b['nl2_locked_variants']}),
            thin_combo_warnings=[dict(flop=b['flop'],combos=b['strict_full_street_combo_reachable'])
                                 for b in boards if b['strict_full_street_combo_reachable']<10]))
    changed={mid for mid in before['records'] if out['records'][mid]!=before['records'][mid]}
    assert changed==set(TARGETS.values()) and len(changed)==2
    assert sum(x['label']=='CERT-MULTIBOARD' for x in out['records'].values())==133
    assert sum(x['label']=='APPROX' for x in out['records'].values())==259
    assert out['records']['ln-ipfr-t_model-sxr0qa']['label']=='APPROX', 'B64 rank41 still blocked'
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V23_B100_LMP_PAIR',
      CERT_MULTIBOARD=133,APPROX=259,
      original_v22_cert=131,original_v22_approx=261,
      original_top24_cutoff_unchanged=True,source_blind_expansion_ranks=[77,78],
      supplementary_cert_count=109,
      b100_certificates=upgrades,parent_v22_sha256=fsha(OLD),
      source_blind_b60_sha256=fsha(B60),B98_original_GTO_pin_sha256=fsha(B98),
      source_evidence=meta,original_LMP_169class_preflop_is_assumed=True,
      B99_only_turn_river_pool_lock_not_locked_flop=True,
      Batch_E_run_44732810327_still_VERIFIED=True,
      no_generic_texture_GTO=True,no_private_combo_NL2_empirical_rates=True,
      PR2_remains_draft_never_merge=True)
    out['independently_verified_completed_batches']['B99_LMP_XX_RIVER']=dict(
        status='VERIFIED',run_id=idx['run_id'],authentic_jobs=1,gto_cases=0,
        locked_cases=idx['locked_cases'],new_subgames=idx['verified_cases'],
        gzip_sha256=idx['gzip_sha256'],original_GTO_run_id=44666294821,
        locked_game_scope='TURN_RIVER_ONLY_FROM_PINNED_ORIGINAL_GTO_FLOP')
    assert out['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(133,259)
    assert len(matrix['models'])==133 and len(matrix['boards'])==527
    assert matrix['strict_aggregate']['named_board_proofs']==527
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V23',
        parent_v23_status_sha256=fsha(OUT),
        no_general_bet_size_advice=True,
        no_exact_private_combo_pool_counts=True,
        historical_unknown_counts_remain_null=True,
        LMP_full_flop_original_GTO_and_turn_only_NL2_actor_locked=True,
        PR2_remains_draft_never_merge=True)
    MAT.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    lines=['# B100 | V23 two genuine source-blind LMP ranks77,78','',
      '**133 CERT / 259 APPROX / EST 0**. Original V1–V22 frozen.',
      'Both ranks77,78 had one missing 8s8h3d x-x / 5s x-x OOP hero locked board.',
      'B98 pinned B3 true full-tree GTO flop, B99 genuinely solved only downstream turn+river',
      'with NL2 pool-size/street marginals where observed; remaining assumptions clearly labeled.',
      '| Rank | 3 exact GTO + OOP hero-locked flops | Real GTO runs | NL2 actor lock runs | Thin proof |',
      '| ---: | --- | --- | --- | --- |']
    for q in upgrades:
        lines.append('| '+str(q['rank'])+' | '+', '.join(q['flops'])+
            ' | '+str(q['GTO_runs'])+' | '+str(q['hero_lock_runs'])+
            ' | '+str(q['thin_combo_warnings'])+' |')
    lines+=['','527 named exact-board GTO proofs with matching hero-side NL2 local lock provenance.',
      'LMP preflop 169-class range is **assumed**, not observed from the NL2 pool.',
      'Pool marginal is **not** conditional observed private-card strategy.',
      'B100 B99 did not re-solve or relabel the GTO flop: only turn/river partially locked.',
      '50% pot nonpolarized is named-board research only; unsupported boards remain flagged.',
      'B64 rank41 cannot certify; B4 MICRO Batch E and all 2475 links remain pinned.',
      'Draft PR #2, never merge.','']
    DOC.write_text('\n'.join(lines))
    LOCKDOC.write_text('# B100 | V23 133 CERT exact named-board lock and 50% pot provenance\n\n'+write_md(matrix))
    agg=matrix['strict_aggregate']
    print(json.dumps(dict(PASS=True,CERT=133,APPROX=259,EST=0,
        ranks=[77,78],gto_flops=list(EXPECTED_FLOPS),gto_ancestor=44666294821,
        B99_lock_run=idx['run_id'],real_boards=527,
        hero_lock_variants=agg['hero_lock_variants'],
        b50_candidates=agg['b50_research_candidate_boards']),ensure_ascii=False))

if __name__=='__main__':main()
