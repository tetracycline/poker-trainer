#!/usr/bin/env python3
"""B111: two B79/B81 preregistered 3-board CERT from ORIGINAL B2 GTO
plus B108 genuinely solved actor-IP turn+river NL2 partial lock.
Never count failed SB3 job in original B2 run, invent empirical hand rates,
relabel generic texture as GTO, or change immutable V1–V25 status files.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
R=pathlib.Path('data')
OLD=R/'nl2_hu_multiboard_status_v25_b106_rank135.json'
A=R/'nl2_hu_b79_next20_sourceblind_gaps.json'
B=R/'nl2_hu_b81_next20_sourceblind_gaps.json'
PIN=R/'nl2_hu_b107_co_js9h4d_b2_gto_parent_pin.json'
IDX=R/'solver_evidence/NL2_MULTIBOARD_B108_CO_XB33_XB100.index.json'
ARCH=R/'solver_evidence/NL2_MULTIBOARD_B108_CO_XB33_XB100.json.gz'
OUT=R/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
MAT=R/'nl2_hu_cert_lock_medium_matrix_v26.json'
DOC=pathlib.Path('docs/NL2_HU_B111_V26_TWO_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B111_V26_ALL_LOCKS_MEDIUM.md')
TARGETS={215:'ln-ipfr-r_model-2h1iyv',220:'ln-ipfr-r_model-nzfk3y'}
FLOPS={'8s8h3d','As9h2d','Js9h4d'}
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
def digest(buf):return hashlib.sha256(buf).hexdigest()
def main():
    parent=json.loads(OLD.read_text())
    a=json.loads(A.read_text());b=json.loads(B.read_text())
    pin=json.loads(PIN.read_text())
    idx=json.loads(IDX.read_text())
    raw=gzip.decompress(ARCH.read_bytes());evidence=json.loads(raw)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['TOTAL'])==(135,257,392)
    assert a['schema']=='NL2_HU_B79_SOURCE_BLIND_NEXT20_GAP_AUDIT_V1'
    assert b['schema']=='NL2_HU_B81_SOURCE_BLIND_NEXT20_GAP_AUDIT_V1'
    assert a['source_blind_preselection_ranks']==list(range(196,216))
    assert b['source_blind_preselection_ranks']==list(range(216,236))
    rank_hash=sha(R/'nl2_hu_multiboard_prerank.json')
    assert a['fixed_rank_sha256']==b['fixed_rank_sha256']==rank_hash
    assert pin['schema']=='NL2_HU_B107_CO_B2_JS9H4D_GTO_PARENT_V1'
    assert pin['result']=='PASS_INDIVIDUALLY_VERIFIED_B2_GTO_ARTIFACT'
    assert pin['full_B2_workflow_failed_unrelated_job'] is True
    assert pin['B2_failed_SB3_BTN_GTO_job_explicitly_excluded'] is True
    assert pin['frozen_targets']==[215,220]
    assert pin['original_source_run_id']==44666290556
    assert (pin['public_flop'],pin['turn'],pin['flop_line'],pin['turn_line'])==(
        'Js9h4d','Ts','x b33 c','x b100 c')
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B108_CO_XB33_XB100'
    assert idx['run_id']==44832882376 and idx['original_gto_parent_run']==44666290556
    assert idx['actual_spot_flop_version_jobs']==1
    assert idx['gto_cases']==0 and idx['locked_cases']>=1
    assert idx['original_parent_GTO_root_SHA256']==pin['original_GTO_flop_SHA256']
    assert idx['original_B107_parent_manifest_SHA256']==pin['original_manifest_SHA256']
    assert idx['B2_whole_workflow_failed_unrelated_source'] is True
    assert idx['B2_PARTIAL_individual_GTO_was_independently_verified'] is True
    assert idx['original_GTO_flop_NOT_recomputed'] is True
    assert idx['source_sha256']==digest(raw) and idx['gzip_sha256']==sha(ARCH)
    assert evidence['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert evidence['source_run_id']==idx['run_id'] and evidence['errors']==[]
    assert len(evidence['artifacts'])==1 and evidence['new_authentic_board_cases']>=1
    source=evidence['artifacts'][0]
    assert (source['spot'],source['version'],source['flop'])==('CO_BB','exp_ip','Js9h4d')
    assert not source['errors'] and len(source['cases'])==1
    case=source['cases'][0]
    assert (case['flop_line'],case['turn'])==('x b33 c','Ts')
    valid_hero=[n for n in case['nodes'] if n['acting_seat']==1 and
           n['exact_node_line']=='x b33 c/x b100 c/x' and n['strictly_reachable_combos']>0]
    assert valid_hero and len(valid_hero)==idx['exact_ip_hero_river_actor_nodes']
    ranking=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((R/'nl2_hu_stage2_queue.json').read_text())
    rmap={x['rank_by_empirically_grounded_frequency_proxy']:dict(x) for x in ranking['nodes']}
    qm={x['model_id']:x for x in queue['records']}
    source_paths=list(dict.fromkeys(pathlib.Path(x) for x in parent['source_evidence']['source_files']))
    assert ARCH not in source_paths and len(source_paths)>=25
    source_paths.append(ARCH)
    assert all(x.is_file() for x in source_paths)
    gto,locks,meta=build_source_index(R,source_paths)
    output=copy.deepcopy(parent);proofs=[]
    for rank,mid in TARGETS.items():
        base=a if rank==215 else b
        frozen=next(x for x in base['rows'] if x['rank']==rank)
        assert frozen['model_id']==mid and frozen['missing_to_three_flops']==1
        assert frozen['matched_hero_side_NL2_lock_flops']==['8s8h3d','As9h2d']
        assert frozen['matching_true_GTO_flops']==['8s8h3d','As9h2d','Js9h4d']
        assert frozen['source_samples'][2]['GTO_run']==44666290556
        assert frozen['source_samples'][2]['line']=='x b33 c/x b100 c/x'
        assert parent['records'][mid]['label']=='APPROX'
        model=qm[mid];r=rmap[rank]
        assert (model['solver_profile'],model['family'],model['street'])==('CO_BB','SRP',2)
        assert r['model_id']==mid and hero_seat(model['preflop_text'])==1
        r['preflop_text']=model['preflop_text']
        r['abstract_action_history']=model['abstract_action_history']
        choices,why=candidates(r,gto,locks,None)
        if why:raise ValueError(f'rank{rank} source mismatch: {why}')
        boards,gap=choose_3_5(choices)
        if gap or len(boards)!=3:raise ValueError(f'rank{rank} no 3 distinct real boards: {gap}')
        assert {x['flop'] for x in boards}==FLOPS
        assert len({x['flop_texture'] for x in boards})>=2
        for z in boards:
            assert z['acting_seat']==1 and z['actual_exact_action_line']=='x b33 c/x b100 c/x'
            assert z['strict_full_street_combo_reachable']>0
            assert z['genuine_gto_exploitability_pct']<=.5 and z['relative_spr_error_pct']<=5
            assert not z['assumed_preflop_ranges']
            assert len(z['source_sha256'])==64 and z['nl2_locked_variants']
            assert all(q['version']=='exp_ip' for q in z['nl2_locked_variants'])
        fresh=next(x for x in boards if x['flop']=='Js9h4d')
        assert fresh['turn']=='Ts' and fresh['source_run_id']==44666290556
        assert any(q['run_id']==idx['run_id'] for q in fresh['nl2_locked_variants'])
        assert fresh['strict_full_street_combo_reachable']>0
        output['records'][mid].update(
           label='CERT-MULTIBOARD',high_frequency_preregistered=True,
           original_top24_high_frequency_preregistered=False,
           source_blind_expansion_rank=rank,prereg_cohort='B79_NEXT20' if rank==215 else 'B81_NEXT20',
           certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
           blocked_reason=None,
           source_credibility='B107_INDIVIDUALLY_VERIFIED_ORIGINAL_B2_GTO_AND_B108_REAL_RUST_PARTIAL_IP_LOCK')
        proofs.append(dict(rank=rank,model_id=mid,
           named_flops=[q['flop'] for q in boards],
           gto_run_ids=sorted({q['source_run_id'] for q in boards}),
           locked_source_run_ids=sorted({v['run_id'] for q in boards for v in q['nl2_locked_variants']}),
           thin_combo_proofs=[dict(flop=q['flop'],strict=q['strict_full_street_combo_reachable'])
               for q in boards if q['strict_full_street_combo_reachable']<10]))
    changed={k for k in output['records'] if parent['records'][k]!=output['records'][k]}
    assert changed==set(TARGETS.values())
    assert sum(x['label']=='CERT-MULTIBOARD' for x in output['records'].values())==137
    assert sum(x['label']=='APPROX' for x in output['records'].values())==255
    assert output['records']['ln-ipfr-t_model-sxr0qa']['label']=='APPROX' # B64 negative gate
    output.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220',
        CERT_MULTIBOARD=137,APPROX=255,EST=0,
        original_v25_cert=135,original_v25_approx=257,
        original_top24_cutoff_unchanged=True,
        source_blind_expansion_ranks=[215,220],
        b111_certificates=proofs,supplementary_cert_count=113,
        parent_v25_sha256=sha(OLD),
        B79_sourceblind_SHA256=sha(A),B81_sourceblind_SHA256=sha(B),
        B107_original_B2_GTO_pin_SHA256=sha(PIN),
        source_evidence=meta,
        B2_whole_workflow_failed_unrelated_job=True,
        B2_failed_SB3_source_excluded=True,
        B108_reused_original_B2_GTO_flop_not_recomputed=True,
        no_generic_texture_GTO=True,
        no_observed_private_combo_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    output['independently_verified_completed_batches']['B108_CO_XB33_XB100']=dict(
        status='VERIFIED',run_id=idx['run_id'],authentic_jobs=1,gto_cases=0,
        locked_cases=idx['locked_cases'],new_subgames=idx['verified_cases'],
        gzip_sha256=idx['gzip_sha256'],original_GTO_parent_run_id=44666290556,
        locked_game_scope='TURN_RIVER_ONLY_FROM_IMMUTABLE_ORIGINAL_B2_GTO_FLOP',
        excluded_failed_SB3_BTN_source=True)
    E=output['independently_verified_completed_batches']['B4_MICRO']
    assert E['status']=='VERIFIED' and E['run_id']==44732810327
    assert E['gto_cases']==E['locked_cases']==30
    matrix=create(output)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(137,255)
    assert len(matrix['models'])==137 and len(matrix['boards'])==539
    assert matrix['strict_aggregate']['named_board_proofs']==539
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V26',
        parent_v26_status_sha256=sha(OUT),
        no_general_bet_size_advice=True,
        original_B2_full_GTO_flop_not_recomputed=True,
        no_observed_private_card_conditionals=True,
        PR2_remains_draft_never_merge=True)
    MAT.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    doc=['# B111 | V26 two source-blind genuine 3-board CO_BB river CERT','',
      '**137 CERT / 255 APPROX / EST 0**; V1–V25 remain unchanged.',
      'B107 independently verifies only original B2 CO_BB Js9h4d GTO, not the failed B2 SB3_BTN job.',
      'B108 authentic Rust turn Ts x-b100-call and river hero-IP partial pooled NL2 marginal lock.',
      'Both preregistered ranks 215 and 220 use the same strictly source-matched third flop but distinct model proofs.',
      '| Rank | Flop | Turn | Original GTO run | True matching hero NL2 lock runs | Strict legal combos |',
      '| ---: | --- | --- | ---: | --- | ---: |']
    for rank,mid in TARGETS.items():
        for q in output['records'][mid]['certified_3_to_5_exact_flop_boards']:
            doc.append('| '+str(rank)+' | '+q['flop']+' | '+q['turn']+' | '+
              str(q['source_run_id'])+' | '+
              str([v['run_id'] for v in q['nl2_locked_variants']])+' | '+
              str(q['strict_full_street_combo_reachable'])+' |')
    doc+=['','539 named board proofs with matching hero partial NL2 locks and separate 50% pot research flags.',
      'No generic texture class becomes GTO. Historical unknown observations and assumed NL2 marginals stay separate.',
      'Source parent run failed overall due only the excluded SB3_BTN artifact; CO_BB parent individually verified.',
      'Batch E 44732810327 VERIFIED, HU river 2475/2475 separately audited. PR #2 Draft; NEVER MERGE.','']
    DOC.write_text('\n'.join(doc))
    MATDOC.write_text('# B111 | V26 all 137 CERT exact-board NL2 locks and 50% pot research flags\n\n'+write_md(matrix))
    a=matrix['strict_aggregate']
    print(json.dumps(dict(PASS=True,CERT=137,APPROX=255,EST=0,new_ranks=[215,220],
      named_board_proofs=539,hero_lock_variants=a['hero_lock_variants'],
      b50_research_candidate_boards=a['b50_research_candidate_boards'],
      original_B2_failed_unrelated_SB3_excluded=True,
      original_B2_GTO_flop_not_recomputed=True),ensure_ascii=False))

if __name__=='__main__':main()
