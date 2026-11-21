#!/usr/bin/env python3
"""B67: promote rank40 only after B66 recovered an ORIGINAL, SHA-verified
SB_BB EXP_IP hero node and independently matched three genuine GTO flops.
Immutable V1-V8 ledgers and B64 rank41 negative conclusion remain untouched.
CERT only names exact public boards, acting seat and legal SPR/action lines.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

ROOT=pathlib.Path('data')
BASE=ROOT/'nl2_hu_multiboard_status_v8_batch61.json'
B48=ROOT/'nl2_hu_b48_next9_sourceblind_gaps.json'
B66=ROOT/'nl2_hu_b66_rank40_source_reverification.json'
IDX=ROOT/'solver_evidence/NL2_MULTIBOARD_B66_SB_B100_IP.index.json'
ARCH=ROOT/'solver_evidence/NL2_MULTIBOARD_B66_SB_B100_IP.json.gz'
NEGATIVE_B64=ROOT/'nl2_hu_b64_rank41_unmatched_hero_node.json'
OUT=ROOT/'nl2_hu_multiboard_status_v9_rank40_b67.json'
MATRIX=ROOT/'nl2_hu_cert_lock_medium_matrix_v9_rank40_b67.json'
DOC=pathlib.Path('docs/NL2_HU_B67_V9_RANK40_CERT.md')
LOCK_DOC=pathlib.Path('docs/NL2_HU_B67_V9_ALL_LOCKS_MEDIUM.md')
ID='ln-ipc-t_model-188b2d5'
EXPECTED={'As9h2d','Js9h4d','9s6h3d'}
def sha(buf): return hashlib.sha256(buf).hexdigest()
def fsha(p): return sha(p.read_bytes())

def main():
    old=json.loads(BASE.read_text())
    prereg=json.loads(B48.read_text())
    b66=json.loads(B66.read_text())
    b64=json.loads(NEGATIVE_B64.read_text())
    idx=json.loads(IDX.read_text())
    raw=gzip.decompress(ARCH.read_bytes())
    proof=json.loads(raw)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V8_BATCH61'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['TOTAL'])==(56,336,392)
    assert prereg['schema']=='NL2_HU_B48_SOURCE_BLIND_NEXT9_GAP_AUDIT_V1'
    assert prereg['source_blind_preselection_ranks']==list(range(33,42))
    frozen=next(x for x in prereg['rows'] if x['rank']==40)
    assert frozen['model_id']==ID and frozen['missing_to_three_flops']==1
    assert old['records'][ID]['label']=='APPROX'
    assert b64['status']=='PASS_EXCLUSION' and b64['rank']==41
    assert b64['no_CERT_promotion'] and b64['new_EXP_IP_source_hero_nodes']==0
    assert old['records'][b64['model_id']]['label']=='APPROX'
    assert b66['schema']=='NL2_HU_B66_B52_SB_B100_IP_REVERIFICATION_V1'
    assert b66['preselected_rank']==40 and b66['model_id']==ID
    assert b66['original_github_run_id']==44809135555
    assert b66['status']=='ELIGIBLE_FOR_NEW_VERSION'
    assert b66['authentic_source_verifier_pass'] is True
    assert b66['eligible_for_separate_cert_version'] is True
    assert b66['remaining_gate_issues']==[] and b66['source_verification_errors']==[]
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B66_SB_B100_IP' and idx['run_id']==44809135555
    assert idx['actual_spot_flop_version_jobs']==1
    assert idx['gto_cases']==0 and idx['locked_cases']>=1
    assert idx['source_sha256']==sha(raw) and idx['gzip_sha256']==fsha(ARCH)
    assert b66['verified_archive_index_sha256']==fsha(IDX)
    assert idx['corrected_prefix_required']==['x','b100','c']
    assert idx['original_B52_artifact_unmodified'] is True
    assert proof['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert proof['source_run_id']==44809135555 and proof['errors']==[]
    assert len(proof['artifacts'])==1
    art=proof['artifacts'][0]
    assert (art['spot'],art['version'],art['flop'])==('SB_BB','exp_ip','9s6h3d')
    assert art['cases'] and not art['errors']
    assert all(x['flop_line']=='x b100 c' for x in art['cases'])
    queue=json.loads((ROOT/'nl2_hu_stage2_queue.json').read_text())
    rank=json.loads((ROOT/'nl2_hu_multiboard_prerank.json').read_text())
    model=next(x for x in queue['records'] if x['model_id']==ID)
    r=next(dict(x) for x in rank['nodes'] if x['model_id']==ID)
    assert r['rank_by_empirically_grounded_frequency_proxy']==40
    assert model['family']=='SRP' and model['solver_profile']=='SB_BB'
    r['preflop_text']=model['preflop_text']
    r['abstract_action_history']=model['abstract_action_history']
    hero=hero_seat(model['preflop_text'])
    assert hero==1
    source_files=[pathlib.Path(x) for x in old['source_evidence']['source_files']]
    source_files=list(dict.fromkeys(source_files+[ARCH]))
    assert len(source_files)>=25 and all(x.is_file() for x in source_files)
    gto,locked,source_summary=build_source_index(ROOT,source_files)
    refs,why=candidates(r,gto,locked,None)
    if why: raise ValueError('Rank40 GTO pair not found: '+str(why))
    boards,gap=choose_3_5(refs)
    if gap or len(boards)!=3:
        raise ValueError('Rank40 cannot qualify without three full GTO plus hero locks: '+str(gap))
    assert {b['flop'] for b in boards}==EXPECTED
    assert len({b['flop_texture'] for b in boards})>=2
    independently_verified={x['flop']:x for x in b66['matching_real_GTO_and_hero_lock_flops']}
    assert set(independently_verified)==EXPECTED
    for b in boards:
        assert b['acting_seat']==1
        assert b['actual_exact_action_line']=='x b100 c/x'
        assert b['strict_full_street_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=.5
        assert b['relative_spr_error_pct']<=5
        assert b['public_board'] and len(b['source_sha256'])==64
        assert b['nl2_locked_variants']
        assert all(v['version']=='exp_ip' for v in b['nl2_locked_variants'])
        pair=independently_verified[b['flop']]
        assert (pair['turn'],pair['line'],pair['actor'],pair['gto_run'])==(
            b['turn'],b['actual_exact_action_line'],b['acting_seat'],b['source_run_id'])
        assert pair['legal_combo_count']==b['strict_full_street_combo_reachable']
        assert set(pair['hero_lock_run_ids'])=={x['run_id'] for x in b['nl2_locked_variants']}
    fresh=next(b for b in boards if b['flop']=='9s6h3d')
    assert fresh['source_run_id']==44732810327  # Original independent Batch E GTO
    assert any(x['run_id']==44809135555 for x in fresh['nl2_locked_variants'])
    assert fresh['strict_full_street_combo_reachable']==6
    new=copy.deepcopy(old)
    new['records'][ID].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=40,prereg_cohort='B48_NEXT9',
        certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility='GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH')
    assert {key for key in old['records'] if old['records'][key]!=new['records'][key]}=={ID}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in new['records'].values())==57
    assert sum(x['label']=='APPROX' for x in new['records'].values())==335
    assert new['records'][b64['model_id']]==old['records'][b64['model_id']]
    new.update(
        schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V9_RANK40_B67',
        CERT_MULTIBOARD=57,APPROX=335,
        original_v8_cert=56,original_v8_approx=336,
        original_top24_cutoff_unchanged=True,
        added_cert_rank=40,added_cert_model_id=ID,
        source_blind_expansion_ranks=[40],supplementary_cert_count=33,
        parent_v8_sha256=fsha(BASE),
        source_blind_b48_sha256=fsha(B48),
        authenticated_b66_verification_sha256=fsha(B66),
        B64_rank41_exclusion_sha256=fsha(NEGATIVE_B64),
        B52_source_recovered_only_for_SB_BB_rank40=True,
        rank41_CO_BB_still_APPROX=True,
        source_evidence=source_summary,
        no_generic_texture_GTO=True,no_observed_private_combo_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    new['independently_verified_completed_batches']['B66_SB_B100_IP']=dict(
        status='VERIFIED',run_id=idx['run_id'],authentic_jobs=1,gto_cases=0,
        locked_cases=idx['locked_cases'],new_subgames=idx['verified_cases'],
        gzip_sha256=idx['gzip_sha256'],original_B52_group_failed=True,
        corrected_full_3_token_source_gate=True)
    assert new['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    assert new['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    matrix=create(new)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(57,335)
    assert len(matrix['models'])==57 and len(matrix['boards'])==222
    assert matrix['strict_aggregate']['named_board_proofs']==222
    assert matrix['strict_aggregate']['hero_lock_variants']>=268
    OUT.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V9_RANK40_B67',
        parent_v9_sha256=fsha(OUT),
        no_general_bet_size_advice=True,no_conditional_private_combo_pool_rate_claim=True,
        B64_rank41_remains_approx=True,never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    rows=['# B67 | V9 rank40 exact board certificate','',
        '**V9: 57 CERT / 335 APPROX.** V1-V8 are immutable.',
        'B48 source-blind rank40 now has 3 real unique flops; hero IP true 100%-pot flop action line.',
        'The original B52 source failed due to a two-token verifier bug, not the original Rust CFR.',
        'B66 independently recovered exactly SB_BB 9s6h3d EXP_IP with full three-token verification.',
        'Batch E 44732810327 supplies the independent exact 9s6h3d GTO parent.',
        '| Named flop | Turn | Real GTO run | NL2 hero lock runs | Strict reachable combos |',
        '| --- | --- | ---: | --- | ---: |']
    for b in boards:
        rows.append('| '+b['flop']+' | '+b['turn']+' | '+str(b['source_run_id'])+' | '+
            str([x['run_id'] for x in b['nl2_locked_variants']])+' | '+
            str(b['strict_full_street_combo_reachable'])+' |')
    rows+=['','Rank40 9s6h3d has only **6 strict combos**, a thin source; no generic texture GTO or conditional per-private-hand NL2 frequencies.',
        'B64 rank41 negative CO_BB proof remains binding and APPROX.',
        '50% pot nonpolarized is only a named-board research flag, not an all-board recommendation.',
        'Original V1-V8 source ledgers remain byte-for-byte unchanged; PR #2 Draft, NEVER merge.','']
    DOC.write_text('\n'.join(rows))
    LOCK_DOC.write_text('# B67 | V9 all 57 CERT true board lock and medium-bet provenance\n\n'+
        'Observed NL2 player-pool marginals, assumed/default and historical unknown remain separate.\n\n'+
        write_md(matrix))
    a=matrix['strict_aggregate']
    print(json.dumps(dict(PASS=True,CERT=57,APPROX=335,rank40_flops=[b['flop'] for b in boards],
        strict_combo_count={b['flop']:b['strict_full_street_combo_reachable'] for b in boards},
        named_board_proofs=len(matrix['boards']),
        hero_lock_variants=a['hero_lock_variants'],
        b50_research_candidate_boards=a['b50_research_candidate_boards'],
        B64_rank41_protection=True),ensure_ascii=False))
if __name__=='__main__':main()
