#!/usr/bin/env python3
"""B118: independently promote frozen B112 rank41 only on third exact CO_BB
GTO+hero-IP 8s8h3d proof, never on inferred texture or missing combo."""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

ROOT=pathlib.Path('data')
BASE=ROOT/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
FROZEN=ROOT/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
ARCH=ROOT/'solver_evidence/NL2_MULTIBOARD_B114_R41_CO_XX.json.gz'
INDEX=ROOT/'solver_evidence/NL2_MULTIBOARD_B114_R41_CO_XX.index.json'
OUT=ROOT/'nl2_hu_multiboard_status_v27_b118_rank41.json'
MATRIX=ROOT/'nl2_hu_cert_lock_medium_matrix_v27.json'
DOC=pathlib.Path('docs/NL2_HU_B118_V27_RANK41_AUTHENTIC_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B118_V27_ALL_CERT_LOCKS_MEDIUM.md')
MID='ln-ipfr-t_model-sxr0qa'
FLOPS={'8s8h3d','As9h2d','Js9h4d'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def jread(path):return json.loads(path.read_text())

def main():
    base=jread(BASE); frozen=jread(FROZEN); idx=jread(INDEX)
    assert base['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220'
    assert (base['CERT_MULTIBOARD'],base['APPROX'],base['TOTAL'])==(137,255,392)
    assert base.get('EST',0)==0 and base['records'][MID]['label']=='APPROX'
    assert frozen['candidate_count']==255 and frozen['one_board_short_count']==6
    assert frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    assert frozen['parent_V26_sha256']==sha(BASE)
    assert frozen['frozen_rank_sha256']==sha(ROOT/'nl2_hu_multiboard_prerank.json')
    fr=next(x for x in frozen['rows'] if x['rank']==41)
    assert fr['model_id']==MID and fr['missing_real_hero_flops_to_3']==1
    assert set(fr['hero_locked_flops'])=={'As9h2d','Js9h4d'}
    assert set(fr['missing_locked_existing_GTO_flops'])=={'8s8h3d'}
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']=='B114_R41_CO_XX'
    assert idx['generic_model_certification']==0
    assert idx['actual_spot_flop_version_jobs']==2
    assert idx['gto_cases']>=1 and idx['locked_cases']>=1
    assert idx['source_sha256']==hashlib.sha256(gzip.decompress(ARCH.read_bytes())).hexdigest()
    assert idx['gzip_sha256']==sha(ARCH)
    proof=json.loads(gzip.decompress(ARCH.read_bytes()))
    assert proof['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert proof['errors']==[] and proof['source_run_id']==idx['run_id']
    assert len(proof['artifacts'])==2
    art={x['version']:x for x in proof['artifacts']}
    assert set(art)=={'gto','exp_ip'}
    for a in art.values():
        assert not a['errors'] and (a['spot'],a['flop'])==('CO_BB','8s8h3d')
        assert a['cases']
        for case in a['cases']:
            assert (case['flop_line'],case['turn'])==('x x','5s')
    for version in ('gto','exp_ip'):
        assert any(n['exact_node_line']=='x x/x'
            and n['acting_seat']==1 and n['strictly_reachable_combos']>0
            for case in art[version]['cases'] for n in case['nodes'])
    rank=jread(ROOT/'nl2_hu_multiboard_prerank.json')
    queue=jread(ROOT/'nl2_hu_stage2_queue.json')
    r=next(copy.deepcopy(x) for x in rank['nodes']
        if x['rank_by_empirically_grounded_frequency_proxy']==41)
    model=next(x for x in queue['records'] if x['model_id']==MID)
    assert r['model_id']==MID
    assert (model['family'],model['solver_profile'],model['street'])==('SRP','CO_BB',1)
    assert hero_seat(model['preflop_text'])==1
    r['preflop_text']=model['preflop_text']
    r['abstract_action_history']=model['abstract_action_history']
    sources=[pathlib.Path(s) for s in base['source_evidence']['source_files']]
    if (ROOT/'solver_evidence/NL2_MULTIBOARD_B113_UTG_B75_XB50.json.gz').is_file():
        prev=ROOT/'solver_evidence/NL2_MULTIBOARD_B113_UTG_B75_XB50.json.gz'
        six=jread(prev.with_suffix('').with_suffix('.index.json'))
        assert six['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
        assert six['gzip_sha256']==sha(prev) and six['immediate_CERT_upgrades']==0
        sources.append(prev)
    assert ARCH not in sources
    sources.append(ARCH)
    assert all(x.is_file() for x in sources)
    gto,locked,meta=build_source_index(ROOT,sources)
    eligible,reason=candidates(r,gto,locked,None)
    assert reason is None,reason
    boards,reason=choose_3_5(eligible)
    assert reason is None,reason
    assert len(boards)==3 and {x['flop'] for x in boards}==FLOPS
    for b in boards:
        assert (b['acting_seat'],b['actual_exact_action_line'])==(1,'x x/x')
        assert b['strict_full_street_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=.5
        assert b['relative_spr_error_pct']<=5
        assert not b['assumed_preflop_ranges']
        assert any(v['version']=='exp_ip' for v in b['nl2_locked_variants'])
    third=next(b for b in boards if b['flop']=='8s8h3d')
    assert any(v['run_id']==idx['run_id'] for v in third['nl2_locked_variants'])
    out=copy.deepcopy(base)
    out['records'][MID].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=41,prereg_cohort='B112_FROZEN_SIX_ONE_BOARD_SHORT',
        certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility='ORIGINAL_VERIFIED_GTO_PLUS_B114_AUTHENTIC_IP_RUST_LOCK')
    changed={k for k in base['records'] if base['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in out['records'].values())==138
    assert sum(x['label']=='APPROX' for x in out['records'].values())==254
    assert base['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V27_B118_RANK41',
        CERT_MULTIBOARD=138,APPROX=254,EST=0,
        source_evidence=meta,
        parent_v26_sha256=sha(BASE),
        B112_frozen_gap_sha256=sha(FROZEN),
        B114_source_index_sha256=sha(INDEX),
        original_top24_cutoff_unchanged=True,
        source_blind_expansion_ranks=[41],
        supplementary_cert_count=114,
        b118_rank41_certificate={'model_id':MID,'named_flops':sorted(FLOPS),
            'exact_GTO_runs':sorted({x['source_run_id'] for x in boards}),
            'actor_IP_locked_runs':sorted({q['run_id'] for x in boards
                for q in x['nl2_locked_variants']}),
            'B114_run':idx['run_id']},
        no_generic_texture_GTO=True,no_observed_private_combo_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    out['independently_verified_completed_batches']['B114_R41_CO_XX']={
        'status':'VERIFIED','run_id':idx['run_id'],
        'authentic_jobs':idx['actual_spot_flop_version_jobs'],
        'gto_cases':idx['gto_cases'],'locked_cases':idx['locked_cases'],
        'new_subgames':idx['verified_cases'],'gzip_sha256':idx['gzip_sha256'],
        'no_generic_texture_GTO':True}
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(138,254)
    assert len(matrix['models'])==138
    assert matrix['strict_aggregate']['named_board_proofs']==542
    assert len(matrix['boards'])==542
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0
        and z['no_general_bet_size_recommendation'] for z in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V27',
        parent_v27_status_sha256=sha(OUT),
        no_general_bet_size_advice=True,
        no_observed_private_card_conditionals=True,
        PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B118 V27: rank41 third authentic CO_BB flop\n\n'
        '**138 CERT-MULTIBOARD / 254 APPROX / EST 0** (392 total).\n\n'
        'rank41 CO_BB, exact x x/x actor-IP; only named flops '
        + ', '.join(sorted(FLOPS)) + '; generic textures remain APPROX.\n\n'
        'B114 real GTO and actor-IP partially locked NL2 pool-marginal CFR, '
        'source run '+str(idx['run_id'])+'; index SHA '+sha(INDEX)+'.\n'
        'No observed private-hole-card NL2 action conditional.\n'
        'Original Batch E VERIFIED and 2,475/2,475 river navigation unchanged.\n'
        'Draft PR #2: NEVER MERGE.\n')
    MATDOC.write_text('# B118 V27 per-board lock and 50% pot evidence\n\n'+write_md(matrix))
    print(json.dumps({'PASS':True,'CERT':138,'APPROX':254,'EST':0,
        'new_ranks':[41],'named_board_proofs':len(matrix['boards']),
        'hero_lock_variants':matrix['strict_aggregate']['hero_lock_variants'],
        'b50_research_candidate_boards':matrix['strict_aggregate']['b50_research_candidate_boards'],
        'B114_run':idx['run_id']}))

if __name__=='__main__':
    main()
