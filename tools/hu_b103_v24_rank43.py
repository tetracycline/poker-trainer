#!/usr/bin/env python3
"""B103 V24 strict rank43 named-board certificate gate.

Requires a separately SHA-verified B102 genuine Rust SB_BB EXP_OOP
As7h3d b50-call/turn-x-x river actor node, originating from unchanged
B101 pinned original B5 full-size 100bb GTO root.
Without that file or a valid actor/source/SPR proof: FAIL CLOSED and
do NOT change immutable V1-V23 ledgers, pool-conditional claims or UI.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

ROOT=pathlib.Path('data')
BASE=ROOT/'nl2_hu_multiboard_status_v23_b100_lmp_pair.json'
B54=ROOT/'nl2_hu_b54_next14_sourceblind_gaps.json'
PIN=ROOT/'nl2_hu_b101_sb_as7h3d_b5_gto_parent_pin.json'
ARCH=ROOT/'solver_evidence/NL2_MULTIBOARD_B102_SB_XX_RIVER.json.gz'
INDEX=ROOT/'solver_evidence/NL2_MULTIBOARD_B102_SB_XX_RIVER.index.json'
OUT=ROOT/'nl2_hu_multiboard_status_v24_b103_rank43.json'
MATRIX=ROOT/'nl2_hu_cert_lock_medium_matrix_v24.json'
DOC=pathlib.Path('docs/NL2_HU_B103_V24_RANK43_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B103_V24_LOCK_MEDIUM.md')
MODEL='ln-opfr-r_model-1e6gydx'
FLOPS={'As7h3d','As9h2d','Ks7h2d'}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    old=json.loads(BASE.read_text())
    prereg=json.loads(B54.read_text())
    pin=json.loads(PIN.read_text())
    index=json.loads(INDEX.read_text())
    raw=gzip.decompress(ARCH.read_bytes())
    proof=json.loads(raw)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V23_B100_LMP_PAIR'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['TOTAL'])==(133,259,392)
    assert old['records'][MODEL]['label']=='APPROX'
    assert prereg['schema']=='NL2_HU_B54_SOURCE_BLIND_NEXT14_GAP_AUDIT_V1'
    assert prereg['source_blind_preselection_ranks']==list(range(42,56))
    assert prereg['fixed_rank_sha256']==digest(ROOT/'nl2_hu_multiboard_prerank.json')
    pre=next(x for x in prereg['rows'] if x['rank']==43)
    assert pre['model_id']==MODEL and pre['missing_to_three_flops']==1
    assert pre['matched_hero_side_NL2_lock_flops']==['As9h2d','Ks7h2d']
    assert pre['matching_true_GTO_flops']==['As7h3d','As9h2d','Ks7h2d']
    assert pin['schema']=='NL2_HU_B101_SB_B5_AS7H3D_PINNED_PARENT_V1'
    assert pin['status']=='PASS_SHA_PINNED_GTO_PARENT'
    assert pin['original_B5_verified_run_id']==44736420272
    assert pin['original_B5_EXP_OOP_cancelled_and_not_accepted'] is True
    assert (pin['immutable_flop'],pin['immutable_turn'],pin['flop_line'],pin['turn_line'])==(
        'As7h3d','Kd','b50 c','x x')
    assert pin['GTO_positive_reach_OOP_river_nodes']>0
    assert index['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert index['batch']=='B102_SB_XX_RIVER' and int(index['run_id'])>0
    assert index['actual_spot_flop_version_jobs']==1
    assert index['gto_cases']==0 and index['locked_cases']>=1
    assert index['original_gto_parent_run']==44736420272
    assert index['original_parent_GTO_root_SHA256']==pin['original_GTO_flop_sha256']
    assert index['original_B101_parent_manifest_SHA256']==pin['original_GTO_manifest_sha256']
    assert index['original_B5_cancelled_exp_oop_excluded'] is True
    assert index['original_pinned_GTO_flop_NOT_recomputed'] is True
    assert index['source_sha256']==sha(raw) and index['gzip_sha256']==digest(ARCH)
    assert proof['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert not proof['errors'] and int(proof['source_run_id'])==index['run_id']
    assert len(proof['artifacts'])==1 and proof['new_authentic_board_cases']==index['verified_cases']>=1
    art=proof['artifacts'][0]
    assert (art['spot'],art['version'],art['flop'])==('SB_BB','exp_oop','As7h3d')
    assert not art['errors'] and len(art['cases'])==1
    sample=art['cases'][0]
    assert (sample['flop_line'],sample['turn'])==('b50 c','Kd')
    src_nodes=[x for x in sample['nodes'] if x['acting_seat']==0 and
         x['exact_node_line']=='b50 c/x x/' and x['strictly_reachable_combos']>0]
    assert src_nodes, 'B102 original solver has no strictly reachable OOP hero decision'
    rank=json.loads((ROOT/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((ROOT/'nl2_hu_stage2_queue.json').read_text())
    r=next(dict(x) for x in rank['nodes'] if x['model_id']==MODEL)
    m=next(x for x in queue['records'] if x['model_id']==MODEL)
    assert r['rank_by_empirically_grounded_frequency_proxy']==43
    assert m['solver_profile']=='SB_BB' and m['family']=='SRP' and m['street']==2
    assert hero_seat(m['preflop_text'])==0
    r['preflop_text']=m['preflop_text']
    r['abstract_action_history']=m['abstract_action_history']
    sources=[pathlib.Path(x) for x in old['source_evidence']['source_files']]
    assert len(sources)>=25 and all(x.is_file() for x in sources)
    sources=list(dict.fromkeys(sources+[ARCH]))
    gto,locked,meta=build_source_index(ROOT,sources)
    rows,why=candidates(r,gto,locked,None)
    if why:raise ValueError('B103 rank43 exact source mismatch '+str(why))
    boards,gap=choose_3_5(rows)
    if gap or len(boards)!=3:raise ValueError('B103 no three real matched boards: '+str(gap))
    assert {b['flop'] for b in boards}==FLOPS
    assert len({b['flop_texture'] for b in boards})>=2
    for b in boards:
        assert b['acting_seat']==0
        assert b['actual_exact_action_line']=='b50 c/x x/'
        assert b['strict_full_street_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=.5
        assert b['relative_spr_error_pct']<=5
        assert b['assumed_preflop_ranges'] is False
        assert len(b['source_sha256'])==64
        assert b['nl2_locked_variants'] and all(
            variant['version']=='exp_oop' for variant in b['nl2_locked_variants'])
    fresh=next(b for b in boards if b['flop']=='As7h3d')
    assert fresh['turn']=='Kd' and fresh['source_run_id']==44736420272
    assert fresh['source_sha256']==pre['source_samples'][0]['GTO_sha256']
    assert any(v['run_id']==index['run_id'] for v in fresh['nl2_locked_variants'])
    after=copy.deepcopy(old)
    after['records'][MODEL].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=43,prereg_cohort='B54_NEXT14',
        certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility='B101_SHA_PINNED_ORIGINAL_B5_GTO_AND_AUTHENTIC_B102_TURN_RIVER_NL2_PARTIAL_OOP_LOCK')
    assert {k for k in old['records'] if old['records'][k]!=after['records'][k]}=={MODEL}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in after['records'].values())==134
    assert sum(x['label']=='APPROX' for x in after['records'].values())==258
    assert after['records']['ln-ipfr-t_model-sxr0qa']['label']=='APPROX', 'B64 rank41 negative proof persists'
    after.update(
       schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V24_B103_RANK43',
       CERT_MULTIBOARD=134,APPROX=258,
       original_v23_cert=133,original_v23_approx=259,
       original_top24_cutoff_unchanged=True,
       added_cert_rank=43,added_cert_model_id=MODEL,
       source_blind_expansion_ranks=[43],supplementary_cert_count=110,
       parent_v23_sha256=digest(BASE),source_blind_b54_sha256=digest(B54),
       B101_original_GTO_root_pin_sha256=digest(PIN),
       source_evidence=meta,
       original_B5_cancelled_exp_oop_is_not_cert_source=True,
       B102_only_turn_river_NL2_lock_from_original_full_flop_GTO=True,
       rank41_source_negative_proof_remains_approx=True,
       no_generic_texture_GTO=True,no_per_private_combo_observed_pool_rates=True,
       PR2_remains_draft_never_merge=True)
    after['independently_verified_completed_batches']['B102_SB_XX_RIVER']=dict(
        status='VERIFIED',run_id=index['run_id'],authentic_jobs=1,
        gto_cases=0,locked_cases=index['locked_cases'],
        new_subgames=index['verified_cases'],gzip_sha256=index['gzip_sha256'],
        frozen_original_GTO_parent_run_id=44736420272,
        locked_game_scope='TURN_RIVER_ONLY_FROM_BYTE_PINNED_ORIGINAL_B5_GTO')
    assert after['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    matrix=create(after)
    assert matrix['CERT_MULTIBOARD']==134 and matrix['APPROX']==258
    assert len(matrix['models'])==134 and len(matrix['boards'])==530
    assert matrix['strict_aggregate']['named_board_proofs']==530
    OUT.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V24',
        parent_v24_status_sha256=digest(OUT),
        original_B5_GTO_flop_not_resolved=True,
        no_general_b50_advice=True,no_exact_private_combo_pool_counts=True,
        historical_unknown_counts_remain_null=True,never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    report=['# B103 | V24 rank43 genuine 3-flop CERT','',
      '**134 CERT / 258 APPROX / 0 EST**. Original V1–V23 intact.',
      'Original B5 independently authenticated full GTO flop root from run 44736420272',
      'with SHA pinned at B101. B102 Rust solved ONLY downstream turn Kd x-x and river',
      'with actor-OOP partial NL2 pooled marginal locks, not hole-card measurements.',
      '| Flop | Turn | Original GTO source run | NL2 hero actor lock sources | Strict combos |',
      '| --- | --- | ---: | --- | ---: |']
    for b in boards:
        report.append('| '+b['flop']+' | '+b['turn']+' | '+str(b['source_run_id'])+
         ' | '+str([v['run_id'] for v in b['nl2_locked_variants']])+
         ' | '+str(b['strict_full_street_combo_reachable'])+' |')
    report+=['','All 530 named source boards and corresponding hero locks independently catalogued.',
      'B5 old EXP-OOP cancellation remains excluded, and GTO flop never re-solved.',
      'NL2 pooled aggregate frequencies may be measured, exact opponent private-card policies are not.',
      '50% pot nonpolarized flags are research-only and named-board-specific.',
      'Batch E 44732810327 and 2475/2475 HU river links retained.',
      'PR #2 remains Draft/Open; NEVER merge.','']
    DOC.write_text('\n'.join(report))
    MATDOC.write_text('# B103 | V24 all 134 CERT named-board NL2 locks and 50% research gates\n\n'+write_md(matrix))
    a=matrix['strict_aggregate']
    print(json.dumps(dict(PASS=True,CERT=134,APPROX=258,EST=0,upgraded_rank=43,
       flops=[b['flop'] for b in boards],real_boards=len(matrix['boards']),
       hero_lock_variants=a['hero_lock_variants'],b50_candidates=a['b50_research_candidate_boards'],
       original_B5_exp_cancelled_excluded=True),ensure_ascii=False))

if __name__=='__main__':main()
