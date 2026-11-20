#!/usr/bin/env python3
"""B63: V9 genuine CO_BB rank41 third-flop EXP_IP source from B62 strict salvage.

Original B52 group failed; ONLY independently reverified CO_BB 8s8h3d is
admitted. SB_BB 9s6h3d rejected history is explicitly forbidden.
No generic texture-level GTO or exact private-hand opponent behavior.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
R=pathlib.Path('data')
P=R/'nl2_hu_multiboard_status_v8_batch61.json'
B48=R/'nl2_hu_b48_next9_sourceblind_gaps.json'
IDX=R/'solver_evidence/NL2_MULTIBOARD_B52_TWO_IP_LOCKS.index.json'
ARCH=R/'solver_evidence/NL2_MULTIBOARD_B52_TWO_IP_LOCKS.json.gz'
B62=R/'nl2_hu_b62_B52_one_valid_one_rejected.json'
OUT=R/'nl2_hu_multiboard_status_v9_rank41.json'
MAT=R/'nl2_hu_cert_lock_medium_matrix_v9.json'
DOC=pathlib.Path('docs/NL2_HU_B63_V9_RANK41_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B63_V9_LOCK_MEDIUM.md')
ID='ln-ipfr-t_model-sxr0qa'
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def main():
    before=json.loads(P.read_text())
    frozen=json.loads(B48.read_text())
    b62=json.loads(B62.read_text())
    ix=json.loads(IDX.read_text())
    raw=gzip.decompress(ARCH.read_bytes())
    source=json.loads(raw)
    assert before['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V8_BATCH61'
    assert (before['CERT_MULTIBOARD'],before['APPROX'],before['TOTAL'])==(56,336,392)
    assert frozen['schema']=='NL2_HU_B48_SOURCE_BLIND_NEXT9_GAP_AUDIT_V1'
    assert frozen['source_blind_preselection_ranks']==list(range(33,42))
    pre=next(r for r in frozen['rows'] if r['rank']==41)
    assert pre['model_id']==ID and pre['missing_to_three_flops']==1
    assert before['records'][ID]['label']=='APPROX'
    assert b62['schema']=='NL2_B62_B52_ONE_VALID_CO_BB_HERO_LOCK_SALVAGE_V1'
    assert b62['valid_jobs']==1 and b62['rejected_jobs']==1
    assert b62['valid_exact_boards']==[dict(spot='CO_BB',flop='8s8h3d',actor='IP',line='x x')]
    assert len(b62['excluded_invalid_source'])==1
    assert b62['excluded_invalid_source'][0]['permissible_for_CERT'] is False
    assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert ix['batch']=='B52_TWO_IP_LOCKS' and ix['run_id']==44809135555
    assert ix['actual_spot_flop_version_jobs']==1 and ix['gto_cases']==0 and ix['locked_cases']>=1
    assert ix['source_sha256']==sha(raw) and ix['gzip_sha256']==file_sha(ARCH)
    assert source['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert source['source_run_id']==ix['run_id'] and not source['errors']
    assert len(source['artifacts'])==1 and (
      source['artifacts'][0]['spot'],source['artifacts'][0]['flop'],
      source['artifacts'][0]['version'])==('CO_BB','8s8h3d','exp_ip')
    assert all(c['flop_line']=='x x' for c in source['artifacts'][0]['cases'])
    ranking=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((R/'nl2_hu_stage2_queue.json').read_text())
    m=next(x for x in queue['records'] if x['model_id']==ID)
    r=next(dict(x) for x in ranking['nodes'] if x['model_id']==ID)
    assert r['rank_by_empirically_grounded_frequency_proxy']==41
    assert m['solver_profile']=='CO_BB' and m['family']=='SRP'
    r['preflop_text']=m['preflop_text'];r['abstract_action_history']=m['abstract_action_history']
    old=[pathlib.Path(x) for x in before['source_evidence']['source_files']]
    assert ARCH not in old and len(old)>=25 and all(x.is_file() for x in old)
    exact,lock,meta=build_source_index(R,old+[ARCH])
    candidates_,why=candidates(r,exact,lock,None)
    if why:raise ValueError(str(why))
    boards,gap=choose_3_5(candidates_)
    if gap or len(boards)!=3:raise ValueError('Rank41 cannot be certified: '+str(gap))
    assert {b['flop'] for b in boards}=={'8s8h3d','As9h2d','Js9h4d'}
    assert len({b['flop_texture'] for b in boards})>=2
    hero=hero_seat(m['preflop_text']);assert hero==1
    for b in boards:
        assert b['acting_seat']==hero and b['actual_exact_action_line']=='x x/x'
        assert b['nl2_locked_variants'] and all(v['version']=='exp_ip' for v in b['nl2_locked_variants'])
        assert b['strict_full_street_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=.5 and b['relative_spr_error_pct']<=5
        assert len(b['source_sha256'])==64
    new=next(b for b in boards if b['flop']=='8s8h3d')
    assert any(v['run_id']==ix['run_id'] for v in new['nl2_locked_variants'])
    assert new['source_run_id']!=ix['run_id'] and new['acting_seat']==1
    after=copy.deepcopy(before)
    after['records'][ID].update(label='CERT-MULTIBOARD',
        high_frequency_preregistered=True,original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=41,prereg_cohort='B48_NEXT9',
        certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility='GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH')
    assert {k for k in after['records'] if after['records'][k]!=before['records'][k]}=={ID}
    assert sum(z['label']=='CERT-MULTIBOARD' for z in after['records'].values())==57
    assert sum(z['label']=='APPROX' for z in after['records'].values())==335
    after.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V9_RANK41',
        CERT_MULTIBOARD=57,APPROX=335,
        original_v8_cert=56,original_v8_approx=336,
        original_top24_cutoff_unchanged=True,
        added_cert_rank=41,added_cert_model_id=ID,
        source_blind_expansion_ranks=[41],supplementary_cert_count=33,
        parent_v8_sha256=file_sha(P),source_blind_b48_sha256=file_sha(B48),
        strict_B62_salvage_exclusion_sha256=file_sha(B62),
        source_evidence=meta,no_generic_texture_GTO=True,
        original_rejected_SB_BB_is_not_CERT_source=True,
        no_observed_conditional_private_card_NL2_rates=True,never_merge=True)
    after['independently_verified_completed_batches']['B52_TWO_IP_LOCKS']=dict(
       status='VERIFIED',salvaged_one_valid_job_only=True,original_group_failed=True,run_id=ix['run_id'],
       authentic_jobs=1,gto_cases=0,locked_cases=ix['locked_cases'],
       new_subgames=ix['verified_cases'],gzip_sha256=ix['gzip_sha256'],
       excluded_invalid_sources=ix['excluded_invalid_source'])
    assert after['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    matrix=create(after)
    assert matrix['CERT_MULTIBOARD']==57 and matrix['APPROX']==335
    assert len(matrix['models'])==57 and len(matrix['boards'])==222
    assert matrix['strict_aggregate']['named_board_proofs']==222
    OUT.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V9',
      parent_v9_status_sha256=file_sha(OUT),no_general_bet_size_advice=True,
      original_SB_BB_B52_artifact_EXCLUDED=True,never_merge=True)
    MAT.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B63 | Rank41 CO_BB independently verified 3-board CERT; V9 57/335\n\n'+
       'Source-blind B48 rank41 had two matched boards. B62 rescued ONLY CO_BB 8s8h3d actor-IP true NL2 lock; original B52 whole group failed and SB_BB invalid artifact is excluded.\n'+
       'True exact GTO flop boards: '+', '.join(x['flop'] for x in boards)+'. All actor/SPR/full-street reach/source SHA are verified.\n'+
       'V1–V8 status files remain unchanged. 50% pot evidence is for the exact board only; no per-private-card NL2 observation is claimed.\n'+
       'PR #2 Draft, never merge.\n')
    MATDOC.write_text('# B63 | V9 all 57 CERT exact NL2 locks and nonpolarized research markers\n\n'+write_md(matrix))
    a=matrix['strict_aggregate']
    print(json.dumps({'PASS':True,'CERT':57,'APPROX':335,'flops':[b['flop'] for b in boards],
      'boards':len(matrix['boards']),'hero_lock_variants':a['hero_lock_variants'],
      'b50_candidates':a['b50_research_candidate_boards'],'SB_BB_source_rejected':True},ensure_ascii=False))
if __name__=='__main__':main()
