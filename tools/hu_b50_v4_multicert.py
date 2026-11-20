#!/usr/bin/env python3
"""B50: versioned V4 CERT for prereg rank31 plus ranks34,36-39.

Never revise V1 24/368, V2 26/366, V3 27/365, the NL2 frequency ranking,
or the exact observed/assumed/unknown source provenance. True multi-board
CERT applies ONLY to named boards/acting seat/SPR, never generic textures.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create as lock_matrix,write_md

ROOT=pathlib.Path('data')
V3=ROOT/'nl2_hu_multiboard_status_v3_rank28.json'
B42=ROOT/'nl2_hu_b42_next6_sourceblind_gaps.json'
B48=ROOT/'nl2_hu_b48_next9_sourceblind_gaps.json'
B49=ROOT/'nl2_hu_b49_rank31_third_flop_proof.json'
NEW=ROOT/'solver_evidence/NL2_MULTIBOARD_B43_UTG_B75.json.gz'
IDX=ROOT/'solver_evidence/NL2_MULTIBOARD_B43_UTG_B75.index.json'
OUT=ROOT/'nl2_hu_multiboard_status_v4_batch50.json'
MATRIX=ROOT/'nl2_hu_cert_lock_medium_matrix_v4.json'
DOC=pathlib.Path('docs/NL2_HU_B50_V4_CERT.md')
MATRIX_MD=pathlib.Path('docs/NL2_HU_CERT_LOCK_MEDIUM_MATRIX_V4.md')
RANKS=[31,34,36,37,38,39]
def sha(v):return hashlib.sha256(v).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def main():
    src=json.loads(V3.read_text())
    b42=json.loads(B42.read_text())
    b48=json.loads(B48.read_text())
    b49=json.loads(B49.read_text())
    rank=json.loads((ROOT/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((ROOT/'nl2_hu_stage2_queue.json').read_text())
    idx=json.loads(IDX.read_text())
    raw=gzip.decompress(NEW.read_bytes())
    prior=json.loads(raw)
    assert src['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28'
    assert src['CERT_MULTIBOARD']==27 and src['APPROX']==365 and src['TOTAL']==392
    assert b42['source_blind_preselection_ranks']==list(range(27,33))
    assert b48['source_blind_preselection_ranks']==list(range(33,42))
    assert b49['qualifies_for_next_separate_versioned_CERT'] and b49['source_blind_B42_rank']==31
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B43_UTG_B75' and idx['run_id']==44806967313
    assert idx['actual_spot_flop_version_jobs']==2 and idx['gto_cases']>=1 and idx['locked_cases']>=1
    assert idx['source_sha256']==sha(raw) and idx['gzip_sha256']==file_sha(NEW)
    assert prior['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1' and not prior['errors']
    assert len(prior['artifacts'])==2 and prior['source_run_id']==idx['run_id']
    assert prior['new_authentic_board_cases']==idx['verified_cases']
    assert set(RANKS)=={31}|{x['rank'] for x in b48['rows'] if x['meets_named_board_certification_evidence']}
    assert b49['model_id']==next(x['model_id'] for x in b42['rows'] if x['rank']==31)
    byrank={x['rank_by_empirically_grounded_frequency_proxy']:dict(x) for x in rank['nodes']}
    bymodel={x['model_id']:x for x in queue['records']}
    proofs=[pathlib.Path(x) for x in src['source_evidence']['source_files']]
    assert NEW not in proofs and all(p.is_file() for p in proofs)
    exact,locked,source_summary=build_source_index(ROOT,proofs+[NEW])
    v4=copy.deepcopy(src)
    upgraded=[]
    for i in RANKS:
        r=byrank[i]
        model=bymodel[r['model_id']]
        assert src['records'][r['model_id']]['label']=='APPROX'
        assert model['solver_profile']==r['spot'] and model['family']==r['family']
        r['preflop_text']=model['preflop_text']
        r['abstract_action_history']=model['abstract_action_history']
        rows,why=candidates(r,exact,locked,None)
        if why:raise ValueError('No exact authentic source for rank '+str(i)+' '+str(why))
        boards,gap=choose_3_5(rows)
        if gap or not 3<=len(boards)<=5:
            raise ValueError('Not certified with real matched boards rank '+str(i)+' '+str(gap))
        assert len({x['flop'] for x in boards})==len(boards)
        assert len({x['flop_texture'] for x in boards})>=2
        actor=hero_seat(model['preflop_text'])
        assert actor in (0,1)
        for b in boards:
            assert b['acting_seat']==actor
            assert b['strict_full_street_combo_reachable']>0
            assert b['genuine_gto_exploitability_pct']<=0.5 and b['relative_spr_error_pct']<=5
            assert b['nl2_locked_variants'] and len(b['source_sha256'])==64
            assert b['actual_exact_action_line'] and b['actual_spr']>0
            assert all(x['version']==('exp_ip' if actor==1 else 'exp_oop') for x in b['nl2_locked_variants'])
        if i==31:
            expected={x['flop'] for x in b49['real_GTO_and_hero_lock_flops']}
            assert {x['flop'] for x in boards}==expected=={'AsKh3d','Ks7h2d','9s6h3d'}
            recent=next(x for x in boards if x['flop']=='9s6h3d')
            assert recent['source_run_id']==idx['run_id'] and recent['source_kind']=='PINNED_PREFLOP_CFR'
            assert any(x['run_id']==idx['run_id'] for x in recent['nl2_locked_variants'])
        else:
            b48row=next(x for x in b48['rows'] if x['rank']==i)
            assert b48row['meets_named_board_certification_evidence']
            assert {x['flop'] for x in boards}==set(b48row['candidate_3_5_flops'])
        if i==34:
            assert all(b['assumed_preflop_ranges'] and b['source_kind']=='ASSUMED_PREFLOP_RANGES' for b in boards)
        record=v4['records'][r['model_id']]
        record.update(label='CERT-MULTIBOARD',
            high_frequency_preregistered=True,
            original_top24_high_frequency_preregistered=False,
            source_blind_expansion_rank=i,
            prereg_cohort='B42_NEXT6' if i==31 else 'B48_NEXT9',
            certified_3_to_5_exact_flop_boards=boards,
            proven_exact_board_count=len(boards),
            blocked_reason=None,
            source_credibility='GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH')
        upgraded.append(dict(rank=i,model_id=r['model_id'],
            certified_flops=[x['flop'] for x in boards],
            source_GTO_run_ids=sorted({x['source_run_id'] for x in boards}),
            paired_lock_run_ids=sorted({v['run_id'] for b in boards for v in b['nl2_locked_variants']}),
            strict_combo_under10=[dict(flop=b['flop'],n=b['strict_full_street_combo_reachable'])
                for b in boards if b['strict_full_street_combo_reachable']<10]))
    changed={mid for mid in src['records'] if v4['records'][mid]!=src['records'][mid]}
    assert changed=={x['model_id'] for x in upgraded}
    assert len(changed)==6
    assert sum(x['label']=='CERT-MULTIBOARD' for x in v4['records'].values())==33
    assert sum(x['label']=='APPROX' for x in v4['records'].values())==359
    v4.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V4_BATCH50',
      CERT_MULTIBOARD=33,APPROX=359,
      original_v3_cert=27,original_v3_approx=365,
      original_v2_cert=26,original_v2_approx=366,
      original_top24_cert=24,original_top24_approx=368,
      original_top24_cutoff_unchanged=True,
      source_blind_expansion_ranks=RANKS,
      b50_certificates=upgraded,supplementary_cert_count=9,
      parent_v3_sha256=file_sha(V3),
      source_blind_b42_sha256=file_sha(B42),
      source_blind_b48_sha256=file_sha(B48),
      verified_rank31_b49_sha256=file_sha(B49),
      source_evidence=source_summary,
      no_generic_texture_GTO=True,
      no_per_private_combo_observed_pool_rates=True)
    batches=v4['independently_verified_completed_batches']
    batches['B43_UTG_B75']=dict(status='VERIFIED',
       run_id=idx['run_id'],authentic_jobs=idx['actual_spot_flop_version_jobs'],
       gto_cases=idx['gto_cases'],locked_cases=idx['locked_cases'],
       new_subgames=idx['verified_cases'],gzip_sha256=idx['gzip_sha256'])
    assert batches['B4_MICRO']['status']=='VERIFIED' and batches['B4_MICRO']['run_id']==44732810327
    matrix=lock_matrix(v4)
    assert matrix['CERT_MULTIBOARD']==33 and matrix['APPROX']==359
    assert matrix['strict_aggregate']['named_board_proofs']==125
    assert len(matrix['boards'])==125 and len(matrix['models'])==33
    assert matrix['strict_aggregate']['hero_lock_variants']>=124
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V4',
        parent_v4_status_sha256=None,
        missing_b50_is_NOT_a_recommendation=True,
        no_private_combo_NL2_pool_policy=True,
        original_LMP_50pct_restricted_tree_disclosed=True,
        PR_2_stays_draft_never_merge=True)
    OUT.write_text(json.dumps(v4,ensure_ascii=False,indent=2)+'\n')
    matrix['parent_v4_status_sha256']=file_sha(OUT)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    docs=['# B50 | 33 exact named-board CERT / 359 APPROX (versioned V4)','',
      'Draft PR #2 only; do not merge. Original V1 24/368, V2 26/366 and V3 27/365 remain immutable.',
      'Six rank-preselected models 31,34,36,37,38,39 have 3–5 distinct real GTO/hero-lock flop proofs:',
      '| Rank | Model | Flops | source GTO run IDs | lock runs | Thin strict-reach warnings |',
      '| ---: | --- | --- | --- | --- | --- |']
    for q in upgraded:
        docs.append('| '+str(q['rank'])+' | '+q['model_id']+' | '+', '.join(q['certified_flops'])+
          ' | '+str(q['source_GTO_run_ids'])+' | '+str(q['paired_lock_run_ids'])+
          ' | '+str(q['strict_combo_under10'])+' |')
    docs+=['','101 existing +24 new =125 named board certificates. Each has correct acting seat, actual SPR, source SHA, legal combos and hero-side lock.',
      'LMP rank34 uses assumed 169-class preflop ranges and a RESTRICTED 50% single-size flop tree, NOT unrestricted GTO.',
      'Any 1–2 strictly reachable combos are thin evidence and cannot justify generic six-texture strategies.',
      '50% pot depolarization is research-only on explicitly supported named boards. Unsupported examples are NOT recommendations.',
      'NL2 observed aggregate marginals do not measure particular private-hand action frequencies.',
      'Batch E 44732810327 remained VERIFIED, river links previously 2475/2475. PR stays Draft/Open.','']
    DOC.write_text('\n'.join(docs))
    MATRIX_MD.write_text('# B50 | Exact V4 node-lock and medium bet provenance (all 33 CERT)\n\n'+
      'Pool-marginal observed frequencies, assumed rates, unmatched villain nodes and historical unknown counts remain separated.\n'+
      'Every row is a named exact public board with actual SHA and actor/SPR match, not a universal GTO strategy.\n'+
      'LMP restricted single 50%-size solve and assumed preflop ranges are NOT unrestricted full-game GTO.\n\n'+write_md(matrix))
    print(json.dumps({'status':'PASS','V4_CERT':33,'V4_APPROX':359,
      'new_rank_CERT':RANKS,'named_boards':len(matrix['boards']),
      'hero_lock_variants':matrix['strict_aggregate']['hero_lock_variants'],
      'b50_research_candidates':matrix['strict_aggregate']['b50_research_candidate_boards'],
      'unsupported_b50':len(matrix['boards'])-matrix['strict_aggregate']['b50_research_candidate_boards']},ensure_ascii=False))
if __name__=='__main__':main()
