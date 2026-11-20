#!/usr/bin/env python3
"""B109 source-blind V26 two real 3-flop CERT only after B108 authentic Rust.

The original B2 overall GitHub run FAILED, but its independently verified
CO_BB Js9h4d GTO was recovered in B2_PARTIAL. Verify source/run/SHA and
exact actor IP before rank215/220 upgrades. No general texture GTO, no
empirically observed private-card conditional opponent behavior.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
R=pathlib.Path('data')
OLD=R/'nl2_hu_multiboard_status_v25_b106_rank135.json'
B79=R/'nl2_hu_b79_next20_sourceblind_gaps.json'
B81=R/'nl2_hu_b81_next20_sourceblind_gaps.json'
PIN=R/'nl2_hu_b107_co_js9h4d_b2_gto_parent_pin.json'
ARCH=R/'solver_evidence/NL2_MULTIBOARD_B108_CO_XB33_XB100.json.gz'
IDX=R/'solver_evidence/NL2_MULTIBOARD_B108_CO_XB33_XB100.index.json'
OUT=R/'nl2_hu_multiboard_status_v26_b109_co_pair.json'
MATRIX=R/'nl2_hu_cert_lock_medium_matrix_v26.json'
DOC=pathlib.Path('docs/NL2_HU_B109_V26_RANK215_220_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B109_V26_ALL_LOCKS_MEDIUM.md')
TARGETS={215:'ln-ipfr-r_model-2h1iyv',220:'ln-ipfr-r_model-nzfk3y'}
FLOPS={'8s8h3d','As9h2d','Js9h4d'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()

def main():
    before=json.loads(OLD.read_text())
    first=json.loads(B79.read_text());second=json.loads(B81.read_text())
    pin=json.loads(PIN.read_text())
    idx=json.loads(IDX.read_text())
    raw=gzip.decompress(ARCH.read_bytes())
    source=json.loads(raw)
    assert before['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135'
    assert (before['CERT_MULTIBOARD'],before['APPROX'],before['TOTAL'])==(135,257,392)
    assert first['source_blind_preselection_ranks']==list(range(196,216))
    assert second['source_blind_preselection_ranks']==list(range(216,236))
    rankSHA=sha(R/'nl2_hu_multiboard_prerank.json')
    assert first['fixed_rank_sha256']==second['fixed_rank_sha256']==rankSHA
    assert pin['schema']=='NL2_HU_B107_CO_B2_JS9H4D_GTO_PARENT_V1'
    assert pin['result']=='PASS_INDIVIDUALLY_VERIFIED_B2_GTO_ARTIFACT'
    assert pin['full_B2_workflow_failed_unrelated_job'] is True
    assert pin['B2_failed_SB3_BTN_GTO_job_explicitly_excluded'] is True
    assert pin['frozen_targets']==[215,220]
    assert pin['original_source_run_id']==44666290556
    assert (pin['public_flop'],pin['turn'],pin['flop_line'],pin['turn_line'])==(
       'Js9h4d','Ts','x b33 c','x b100 c')
    assert pin['original_GTO_positive_strict_IP_actor_node_count']>0
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B108_CO_XB33_XB100' and idx['run_id']>0
    assert idx['actual_spot_flop_version_jobs']==1 and idx['gto_cases']==0 and idx['locked_cases']>=1
    assert idx['original_gto_parent_run']==44666290556
    assert idx['original_parent_GTO_root_SHA256']==pin['original_GTO_flop_SHA256']
    assert idx['original_B107_parent_manifest_SHA256']==pin['original_manifest_SHA256']
    assert idx['B2_whole_workflow_failed_unrelated_source'] is True
    assert idx['B2_PARTIAL_individual_GTO_was_independently_verified'] is True
    assert idx['original_GTO_flop_NOT_recomputed'] is True
    assert idx['source_sha256']==digest(raw) and idx['gzip_sha256']==sha(ARCH)
    assert source['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert source['source_run_id']==idx['run_id'] and source['errors']==[]
    assert len(source['artifacts'])==1 and source['new_authentic_board_cases']==idx['verified_cases']>=1
    artifact=source['artifacts'][0]
    assert (artifact['spot'],artifact['flop'],artifact['version'])==('CO_BB','Js9h4d','exp_ip')
    assert not artifact['errors'] and len(artifact['cases'])==1
    case=artifact['cases'][0]
    assert (case['flop_line'],case['turn'])==('x b33 c','Ts')
    exact_hero=[n for n in case['nodes'] if n['acting_seat']==1 and
        n['exact_node_line']=='x b33 c/x b100 c/x' and n['strictly_reachable_combos']>0]
    assert exact_hero, 'No authentic hero-IP reach from new B108 genuine solver source'
    ranking=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((R/'nl2_hu_stage2_queue.json').read_text())
    ranks={x['rank_by_empirically_grounded_frequency_proxy']:dict(x) for x in ranking['nodes']}
    models={x['model_id']:x for x in queue['records']}
    old_sources=[pathlib.Path(s) for s in before['source_evidence']['source_files']]
    assert len(old_sources)>=25 and all(p.is_file() for p in old_sources)
    paths=list(dict.fromkeys(old_sources+[ARCH]))
    gto,locked,source_meta=build_source_index(R,paths)
    after=copy.deepcopy(before)
    certifications=[]
    for rank,mid in TARGETS.items():
        history=first if rank==215 else second
        r=ranks[rank];m=models[mid]
        prereg=next(x for x in history['rows'] if x['rank']==rank)
        assert r['model_id']==prereg['model_id']==mid
        assert prereg['missing_to_three_flops']==1
        assert prereg['matched_hero_side_NL2_lock_flops']==['8s8h3d','As9h2d']
        assert prereg['matching_true_GTO_flops']==['8s8h3d','As9h2d','Js9h4d']
        assert before['records'][mid]['label']=='APPROX'
        assert (m['solver_profile'],m['family'],m['street'])==('CO_BB','SRP',2)
        assert hero_seat(m['preflop_text'])==1
        r['preflop_text']=m['preflop_text']
        r['abstract_action_history']=m['abstract_action_history']
        rows,err=candidates(r,gto,locked,None)
        if err:raise ValueError('Rank'+str(rank)+' missing authentic source '+str(err))
        boards,reason=choose_3_5(rows)
        if reason or len(boards)!=3:raise ValueError('Rank'+str(rank)+' requires 3 real boards: '+str(reason))
        assert {b['flop'] for b in boards}==FLOPS
        assert len({b['flop_texture'] for b in boards})>=2
        for b in boards:
            assert b['acting_seat']==1 and b['actual_exact_action_line']=='x b33 c/x b100 c/x'
            assert b['strict_full_street_combo_reachable']>0
            assert b['genuine_gto_exploitability_pct']<=.5
            assert b['relative_spr_error_pct']<=5
            assert b['assumed_preflop_ranges'] is False
            assert b['nl2_locked_variants'] and len(b['source_sha256'])==64
            assert all(x['version']=='exp_ip' for x in b['nl2_locked_variants'])
        added=next(b for b in boards if b['flop']=='Js9h4d')
        assert added['turn']=='Ts' and added['source_run_id']==44666290556
        assert any(x['run_id']==idx['run_id'] for x in added['nl2_locked_variants'])
        after['records'][mid].update(
            label='CERT-MULTIBOARD',high_frequency_preregistered=True,
            original_top24_high_frequency_preregistered=False,
            source_blind_expansion_rank=rank,
            prereg_cohort='B79_NEXT20' if rank==215 else 'B81_NEXT20',
            certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
            blocked_reason=None,
            source_credibility='B107_INDIVIDUALLY_VERIFIED_B2_GTO_AND_AUTHENTIC_B108_IP_RIVER_NL2_LOCK')
        certifications.append(dict(rank=rank,model_id=mid,
          flops=[b['flop'] for b in boards],
          real_GTO_runs=sorted({b['source_run_id'] for b in boards}),
          real_hero_lock_runs=sorted({v['run_id'] for b in boards for v in b['nl2_locked_variants']}),
          thin_combo_warnings=[dict(flop=b['flop'],strict=b['strict_full_street_combo_reachable'])
              for b in boards if b['strict_full_street_combo_reachable']<10]))
    changed={x for x in after['records'] if after['records'][x]!=before['records'][x]}
    assert changed==set(TARGETS.values()) and len(changed)==2
    assert sum(v['label']=='CERT-MULTIBOARD' for v in after['records'].values())==137
    assert sum(v['label']=='APPROX' for v in after['records'].values())==255
    assert after['records']['ln-ipfr-t_model-sxr0qa']['label']=='APPROX'
    after.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B109_CO_PAIR',
       CERT_MULTIBOARD=137,APPROX=255,
       original_v25_cert=135,original_v25_approx=257,
       original_top24_cutoff_unchanged=True,
       source_blind_expansion_ranks=[215,220],
       b109_certificates=certifications,supplementary_cert_count=113,
       parent_v25_sha256=sha(OLD),B79_sourceblind_sha256=sha(B79),B81_sourceblind_sha256=sha(B81),
       B107_individually_verified_GTO_pin_sha256=sha(PIN),
       source_evidence=source_meta,
       B2_whole_workflow_failed_original_unrelated_job=True,
       only_verified_B2_PARTIAL_original_GTO_claimed=True,
       B108_only_turn_river_IP_NL2_marginal_lock=True,
       no_generic_texture_GTO=True,
       no_observed_private_card_conditional_opponent_action_rates=True,
       PR2_remains_draft_never_merge=True)
    after['independently_verified_completed_batches']['B108_CO_XB33_XB100']=dict(
       status='VERIFIED',run_id=idx['run_id'],authentic_jobs=1,gto_cases=0,
       locked_cases=idx['locked_cases'],new_subgames=idx['verified_cases'],
       gzip_sha256=idx['gzip_sha256'],original_GTO_parent_run_id=44666290556,
       locked_game_scope='TURN_RIVER_ONLY_FROM_INDIVIDUALLY_VERIFIED_ORIGINAL_B2_GTO')
    assert after['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    matrix=create(after)
    assert matrix['CERT_MULTIBOARD']==137 and matrix['APPROX']==255
    assert len(matrix['models'])==137 and len(matrix['boards'])==539
    assert matrix['strict_aggregate']['named_board_proofs']==539
    OUT.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V26',
       parent_v26_status_sha256=sha(OUT),
       B2_failed_job_not_used_in_CERT=True,
       no_general_50pct_bet_size_advice=True,
       no_observed_private_combo_pool_frequencies=True,
       historical_unknown_counts_not_fabricated=True,never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    doc=['# B109 | V26 two authentic CO_BB source-blind certifications','',
      '**137 CERT / 255 APPROX / EST 0**. Original V1–V25 immutable.',
      'Ranks215 and220 each have 3 different true public flop GTO/hero-IP lock sources.',
      'Original failed B2 GitHub run did NOT pass as a whole; only the independently audited CO_BB Js9h4d GTO from B2_PARTIAL is used.',
      'B107 pinned that exact full GTO root and B108 solved only Ts turn x-b100-call and river.',
      '| Model rank | Exact flops | Genuine GTO runs | Actor-IP lock runs | Thin combo warnings |',
      '| ---: | --- | --- | --- | --- |']
    for x in certifications:
        doc.append('| '+str(x['rank'])+' | '+', '.join(x['flops'])+
          ' | '+str(x['real_GTO_runs'])+' | '+str(x['real_hero_lock_runs'])+
          ' | '+str(x['thin_combo_warnings'])+' |')
    doc+=['','539 named exact source boards. NL2 pooled observed marginal frequencies are not exact conditional private-card actions.',
      '50% pot nonpolarization only shown for exact boards with separately grounded evidence.',
      'Excluded failed B2 other job, rank41 APPROX negative proof, Batch E 44732810327, 2475/2475 river links remain unchanged.',
      'PR #2 Draft/Open; NEVER merge.','']
    DOC.write_text('\n'.join(doc))
    MATDOC.write_text('# B109 | V26 all 137 CERT named-board NL2 actor locks and b50 research provenance\n\n'+write_md(matrix))
    agg=matrix['strict_aggregate']
    print(json.dumps(dict(PASS=True,CERT=137,APPROX=255,EST=0,
       ranks=[215,220],flops=sorted(FLOPS),original_GTO_run=44666290556,
       new_partial_NL2_lock_run=idx['run_id'],
       named_boards=539,hero_lock_variants=agg['hero_lock_variants'],
       b50_research_candidates=agg['b50_research_candidate_boards']),ensure_ascii=False))

if __name__=='__main__':main()
