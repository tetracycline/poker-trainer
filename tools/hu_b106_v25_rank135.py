#!/usr/bin/env python3
"""B106 V25 strict source-only upgrade of preregistered rank135.

Source must be a genuine B105 pinned original B1 flop GTO with new authentic
turn/river IP NL2 partially locked Rust subgame for As9h2d; original GTO flop
unchanged. Fail-closed on any action/actor/source/SPR/combo mismatch.
All CERT claims apply only to individual exact named boards.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
R=pathlib.Path('data')
BASE=R/'nl2_hu_multiboard_status_v24_b103_rank43.json'
B70=R/'nl2_hu_b70_next20_sourceblind_gaps.json'
PIN=R/'nl2_hu_b104_btn_as9h2d_gto_parent_pin.json'
ARCH=R/'solver_evidence/NL2_MULTIBOARD_B105_BTN_XX_RIVER.json.gz'
INDEX=R/'solver_evidence/NL2_MULTIBOARD_B105_BTN_XX_RIVER.index.json'
OUT=R/'nl2_hu_multiboard_status_v25_b106_rank135.json'
MAT=R/'nl2_hu_cert_lock_medium_matrix_v25.json'
DOC=pathlib.Path('docs/NL2_HU_B106_V25_RANK135_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B106_V25_ALL_LOCKS_MEDIUM.md')
ID='ln-ipfr-r_model-3lq5u6'
FLOPS={'As9h2d','Jh9d6s','KsQh4d'}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    before=json.loads(BASE.read_text())
    prereg=json.loads(B70.read_text())
    pin=json.loads(PIN.read_text())
    idx=json.loads(INDEX.read_text())
    raw=gzip.decompress(ARCH.read_bytes())
    evidence=json.loads(raw)
    assert before['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V24_B103_RANK43'
    assert (before['CERT_MULTIBOARD'],before['APPROX'],before['TOTAL'])==(134,258,392)
    assert before['records'][ID]['label']=='APPROX'
    assert prereg['schema']=='NL2_HU_B70_SOURCE_BLIND_NEXT20_GAP_AUDIT_V1'
    assert prereg['source_blind_preselection_ranks']==list(range(116,136))
    assert prereg['fixed_rank_sha256']==digest(R/'nl2_hu_multiboard_prerank.json')
    row=next(x for x in prereg['rows'] if x['rank']==135)
    assert row['model_id']==ID and row['missing_to_three_flops']==1
    assert row['matched_hero_side_NL2_lock_flops']==['Jh9d6s','KsQh4d']
    assert row['matching_true_GTO_flops']==['As9h2d','Jh9d6s','KsQh4d']
    assert pin['schema']=='NL2_HU_B104_B1_BTN_AS9H2D_GTO_SHA_PARENT_V1'
    assert pin['result']=='PASS_FULL_ORIGINAL_GTO_PIN'
    assert pin['original_source_run_id']==44666285424
    assert pin['preselected_rank']==135 and pin['preselected_model_id']==ID
    assert pin['original_root_full_flop_size_menu'] is True
    assert pin['source_preflop_CFR_pinned_not_holecard_observed'] is True
    assert (pin['target_public_flop'],pin['target_turn'],pin['flop_line'],pin['turn_line'])==(
      'As9h2d','Kd','x b100 c','x x')
    assert pin['original_source_GTO_IP_hero_river_nodes']>0
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B105_BTN_XX_RIVER' and idx['run_id']>0
    assert idx['original_gto_parent_run']==44666285424
    assert idx['actual_spot_flop_version_jobs']==1
    assert idx['gto_cases']==0 and idx['locked_cases']>=1
    assert idx['original_parent_GTO_root_SHA256']==pin['original_GTO_flop_root_sha256']
    assert idx['original_B104_parent_manifest_SHA256']==pin['original_GTO_manifest_sha256']
    assert idx['original_pinned_GTO_flop_NOT_recomputed'] is True
    assert idx['source_sha256']==sha(raw) and idx['gzip_sha256']==digest(ARCH)
    assert evidence['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert evidence['source_run_id']==idx['run_id'] and evidence['errors']==[]
    assert len(evidence['artifacts'])==1 and evidence['new_authentic_board_cases']==idx['verified_cases']>=1
    a=evidence['artifacts'][0]
    assert (a['spot'],a['version'],a['flop'])==('BTN_BB','exp_ip','As9h2d')
    assert not a['errors'] and len(a['cases'])==1
    case=a['cases'][0]
    assert (case['flop_line'],case['turn'])==('x b100 c','Kd')
    hero=[n for n in case['nodes'] if n['acting_seat']==1 and
          n['exact_node_line']=='x b100 c/x x/x' and n['strictly_reachable_combos']>0]
    assert hero, 'No authentic IP hero river continuation on requested GTO reach'
    ranking=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((R/'nl2_hu_stage2_queue.json').read_text())
    r=next(dict(z) for z in ranking['nodes'] if z['model_id']==ID)
    m=next(z for z in queue['records'] if z['model_id']==ID)
    assert r['rank_by_empirically_grounded_frequency_proxy']==135
    assert (m['solver_profile'],m['family'],m['street'])==('BTN_BB','SRP',2)
    assert hero_seat(m['preflop_text'])==1
    r['preflop_text']=m['preflop_text'];r['abstract_action_history']=m['abstract_action_history']
    sources=[pathlib.Path(x) for x in before['source_evidence']['source_files']]
    assert len(sources)>=25 and all(x.is_file() for x in sources)
    sources=list(dict.fromkeys(sources+[ARCH]))
    gto,locks,metadata=build_source_index(R,sources)
    proof,why=candidates(r,gto,locks,None)
    if why:raise ValueError('Rank135 authentic GTO source mismatch: '+str(why))
    boards,gap=choose_3_5(proof)
    if gap or len(boards)!=3:raise ValueError('Rank135 lacks 3 truly paired boards: '+str(gap))
    assert {b['flop'] for b in boards}==FLOPS
    assert len({b['flop_texture'] for b in boards})>=2
    for b in boards:
        assert b['acting_seat']==1 and b['actual_exact_action_line']=='x b100 c/x x/x'
        assert b['strict_full_street_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=.5 and b['relative_spr_error_pct']<=5
        assert b['assumed_preflop_ranges'] is False and len(b['source_sha256'])==64
        assert b['nl2_locked_variants'] and all(v['version']=='exp_ip' for v in b['nl2_locked_variants'])
    named=next(b for b in boards if b['flop']=='As9h2d')
    assert named['source_run_id']==44666285424 and named['turn']=='Kd'
    assert any(v['run_id']==idx['run_id'] for v in named['nl2_locked_variants'])
    assert named['strict_full_street_combo_reachable']>0
    upgraded=copy.deepcopy(before)
    upgraded['records'][ID].update(
      label='CERT-MULTIBOARD',high_frequency_preregistered=True,
      original_top24_high_frequency_preregistered=False,
      source_blind_expansion_rank=135,prereg_cohort='B70_NEXT20',
      certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
      blocked_reason=None,
      source_credibility='B104_SHA_PINNED_B1_ORIGINAL_GTO_AND_B105_AUTHENTIC_TURN_RIVER_IP_POOL_LOCK')
    assert {k for k in upgraded['records'] if before['records'][k]!=upgraded['records'][k]}=={ID}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in upgraded['records'].values())==135
    assert sum(x['label']=='APPROX' for x in upgraded['records'].values())==257
    assert upgraded['records']['ln-ipfr-t_model-sxr0qa']['label']=='APPROX'
    upgraded.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135',
       CERT_MULTIBOARD=135,APPROX=257,original_v24_cert=134,original_v24_approx=258,
       original_top24_cutoff_unchanged=True,
       added_cert_rank=135,added_cert_model_id=ID,
       source_blind_expansion_ranks=[135],supplementary_cert_count=111,
       parent_v24_sha256=digest(BASE),B70_sourceblind_rank_sha256=digest(B70),
       B104_original_B1_GTO_pin_sha256=digest(PIN),source_evidence=metadata,
       original_B1_GTO_flop_not_resolved=True,
       B105_only_turn_river_NL2_IP_lock=True,
       no_generic_texture_GTO=True,no_empirically_observed_conditional_private_NL2_rates=True,
       PR2_remains_draft_never_merge=True)
    upgraded['independently_verified_completed_batches']['B105_BTN_XX_RIVER']=dict(
      status='VERIFIED',run_id=idx['run_id'],authentic_jobs=1,gto_cases=0,
      locked_cases=idx['locked_cases'],new_subgames=idx['verified_cases'],
      gzip_sha256=idx['gzip_sha256'],original_GTO_parent_run_id=44666285424,
      locked_game_scope='TURN_RIVER_ONLY_FROM_IMMUTABLE_GTO_FLOP')
    assert upgraded['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    matrix=create(upgraded)
    assert matrix['CERT_MULTIBOARD']==135 and matrix['APPROX']==257
    assert len(matrix['models'])==135 and len(matrix['boards'])==533
    assert matrix['strict_aggregate']['named_board_proofs']==533
    OUT.write_text(json.dumps(upgraded,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V25',
      parent_v25_status_sha256=digest(OUT),
      no_general_bet_size_advice=True,
      original_B1_flop_not_recomputed=True,
      no_observed_private_card_conditionals=True,never_merge=True)
    MAT.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    doc=['# B106 | V25 rank135 true three-board source-backed IP CERT','',
      '**135 CERT / 257 APPROX / EST 0**, all V1–V24 source registries immutable.',
      'B104 frozen full original 100bb B1 BTN_BB As9h2d GTO root; B105 solves only turn Kd x-x and river, partially locked NL2 pool marginal EXP_IP.',
      'Three different exact GTO boards with correct hero-IP locked source and positive sequential legal combo reach:',
      '| Flop | Turn | Original GTO run | Matching true NL2 hero lock runs | Strict combos |',
      '| --- | --- | ---: | --- | ---: |']
    for b in boards:
        doc.append('| '+b['flop']+' | '+b['turn']+' | '+str(b['source_run_id'])+
         ' | '+str([v['run_id'] for v in b['nl2_locked_variants']])+
         ' | '+str(b['strict_full_street_combo_reachable'])+' |')
    doc+=['','All 533 named certified boards and source provenance verified; 50% nonpolarized research only where independently supported.',
      'NL2 measured pooled bet-size/street marginal is NOT private-card conditional behavior.',
      'B64 rank41 negative proof remains APPROX, Batch E and 2475/2475 HU river navigation verified.',
      'Original B1 flop never re-solved. PR #2 Draft; NEVER merge.','']
    DOC.write_text('\n'.join(doc))
    MATDOC.write_text('# B106 | V25 all 135 CERT exact-board NL2 node locks and medium research\n\n'+write_md(matrix))
    agg=matrix['strict_aggregate']
    print(json.dumps(dict(PASS=True,CERT=135,APPROX=257,EST=0,
       new_rank=135,flops=[b['flop'] for b in boards],named_boards=533,
       hero_lock_variants=agg['hero_lock_variants'],
       b50_research_candidate_boards=agg['b50_research_candidate_boards']),ensure_ascii=False))

if __name__=='__main__':main()
