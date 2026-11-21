#!/usr/bin/env python3
"""B142 | frozen rank88 source-blind V29 promotion. Only EXACT 3 named
SB3_BTN flops with genuine GTO <=0.5%, real actor-OOP partial NL2
Rust lock, legal full-sequence combos and matching true SPR qualify.
Do not generalize textures or infer private-combo NL2 actions.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v28_b133_rank69.json'
PARENT26=D/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
OUT=D/'nl2_hu_multiboard_status_v29_b142_rank88.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v29_b142.json'
DOC=pathlib.Path('docs/NL2_HU_B142_V29_RANK88_GENUINE_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B142_V29_PER_BOARD_NL2_LOCK_MEDIUM.md')
NEW={
 'B140_R88_SB3_B33B50':D/'solver_evidence/NL2_MULTIBOARD_B140_R88_SB3_B33B50.json.gz',
 'B141_R88_GTO_B117':D/'solver_evidence/NL2_MULTIBOARD_B141_R88_GTO_B117.json.gz'
}
MID='ln-3bp-3b_r_model-8uwbze'
FLOPS={'As7h3d','Ks7h2d','Jh9d6s'}
OLD_FLOPS={'As7h3d','Ks7h2d'}
SPOT='SB3_BTN';LINE='b33 c/b50 c/';HERO=0
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked_source(key,p):
    i=read(p.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(p.read_bytes())
    v=json.loads(raw)
    assert i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert i['batch']==key and i['generic_model_certification']==0
    assert i['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert i['gzip_sha256']==sha(p)
    assert v['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert not v['errors'] and v['source_run_id']==i['run_id']
    assert len(v['artifacts'])==i['actual_spot_flop_version_jobs']
    assert sum(len(a['cases']) for a in v['artifacts'])==i['verified_cases']
    assert sum(a['version']=='gto' for a in v['artifacts'])==i['gto_cases']
    assert sum(a['version']!='gto' for a in v['artifacts'])==i['locked_cases']
    return i,v
def legal(proof,version):
    return [n for a in proof['artifacts'] if a['version']==version
        for c in a['cases'] if c['flop']=='Jh9d6s' and c['turn']=='3c'
        and c['flop_line']=='b33 c'
        for n in c['nodes'] if n['exact_node_line']==LINE
        and n['acting_seat']==HERO and n['strictly_reachable_combos']>0]
def main():
    parent=read(PARENT);p26=read(PARENT26);frozen=read(FROZEN)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V28_B133_RANK69'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['EST'],parent['TOTAL'])==(140,252,0,392)
    assert (p26['CERT_MULTIBOARD'],p26['APPROX'])==(137,255)
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['parent_V26_sha256']==sha(PARENT26)
    assert frozen['frozen_rank_sha256']==sha(RANK)
    assert frozen['candidate_count']==255
    assert frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    assert parent['records'][MID]['label']=='APPROX'
    frozen88=next(x for x in frozen['rows'] if x['rank']==88)
    assert frozen88['model_id']==MID and frozen88['missing_real_hero_flops_to_3']==1
    assert set(frozen88['hero_locked_flops'])==OLD_FLOPS
    ix={};proof={}
    for k,p in NEW.items():
        assert p.is_file() and p.with_suffix('').with_suffix('.index.json').is_file()
        ix[k],proof[k]=checked_source(k,p)
    ip=ix['B140_R88_SB3_B33B50'];gt=ix['B141_R88_GTO_B117']
    assert (ip['run_id'],ip['gto_cases'],ip['locked_cases'])==(44850121199,0,1)
    assert (gt['run_id'],gt['gto_cases'],gt['locked_cases'])==(44837416843,1,0)
    assert ip['exact_actor_OOP_river_nodes']>0 and ip['strict_failure_reason'] is None
    assert gt['exact_target_actor_OOP_gto_river_nodes']>0 and gt['exact_target_actor_OOP_gto_strict_combo_sum']>0
    assert ip['original_gto_parent_run']==gt['run_id']
    assert ip['original_parent_GTO_root_SHA256']==gt['original_parent_GTO_root_SHA256']
    assert ip['original_parent_GTO_job_SHA256']==gt['original_parent_GTO_job_SHA256']
    assert ip['original_parent_GTO_manifest_SHA256']==gt['original_parent_GTO_manifest_SHA256']
    assert ip['original_GTO_flop_NOT_recomputed'] and gt['B117_GTO_flop_not_recomputed']
    assert ip['source_GTO_preflop_CFR_pinned'] and gt['pinned_100bb_SB3_preflop_CFR']
    assert legal(proof['B140_R88_SB3_B33B50'],'exp_oop')
    assert legal(proof['B141_R88_GTO_B117'],'gto')
    assert parent['records']['ln-ipfr-t_model-sxr0qa']['label']=='CERT-MULTIBOARD'
    assert parent['records']['ln-ipfr-r_model-159a6z6']['label']=='CERT-MULTIBOARD'
    assert parent['records']['ln-ipc-r_model-1nz4lt1']['label']=='CERT-MULTIBOARD'
    e=parent['independently_verified_completed_batches']['B4_MICRO']
    assert e['status']=='VERIFIED' and e['run_id']==44732810327
    source_files=[pathlib.Path(x) for x in parent['source_evidence']['source_files']]
    assert source_files and all(x.is_file() for x in source_files)
    source_files+=list(NEW.values())
    assert len(source_files)==len(set(source_files))
    gto,locked,meta=build_source_index(D,source_files)
    rank=next(copy.deepcopy(x) for x in read(RANK)['nodes']
         if x['rank_by_empirically_grounded_frequency_proxy']==88)
    model=next(x for x in read(STAGE)['records'] if x['model_id']==MID)
    assert rank['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('SB3_BTN','3BP',2)
    assert hero_seat(model['preflop_text'])==HERO
    assert model['preflop_ranges_source'].startswith('PRE_FLOP_CFR:')
    rank['preflop_text']=model['preflop_text']
    rank['abstract_action_history']=model['abstract_action_history']
    sources,reason=candidates(rank,gto,locked,None)
    assert reason is None,(88,reason)
    selected,why=choose_3_5(sources)
    assert why is None,(88,why)
    assert len(selected)==3 and {x['flop'] for x in selected}==FLOPS
    assert len({x['flop_texture'] for x in selected})>=2
    for x in selected:
        assert x['acting_seat']==HERO and x['actual_exact_action_line']==LINE
        assert x['strict_full_street_combo_reachable']>0 and x['exact_combo_reachable']>0
        assert x['genuine_gto_exploitability_pct'] is not None and x['genuine_gto_exploitability_pct']<=.5
        assert x['relative_spr_error_pct']<=5 and not x['assumed_preflop_ranges']
        assert x['nl2_locked_variants']
        assert all(v['version']=='exp_oop' for v in x['nl2_locked_variants'])
    third=next(x for x in selected if x['flop']=='Jh9d6s')
    assert third['turn']=='3c' and third['source_run_id']==gt['run_id']
    assert any(q['run_id']==ip['run_id'] and q['version']=='exp_oop' for q in third['nl2_locked_variants'])
    out=copy.deepcopy(parent)
    out['records'][MID].update(label='CERT-MULTIBOARD',
        high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=88,prereg_cohort='B112_FROZEN_SIX_ONE_BOARD_SHORT',
        certified_3_to_5_exact_flop_boards=selected,proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility='B117_ORIGINAL_GTO_AND_B140_TRUE_RUST_ACTOR_OOP_NL2_SHA_AUDITED')
    changed={k for k in parent['records'] if parent['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(v['label']=='CERT-MULTIBOARD' for v in out['records'].values())==141
    assert sum(v['label']=='APPROX' for v in out['records'].values())==251
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V29_B142_RANK88',
        CERT_MULTIBOARD=141,APPROX=251,EST=0,
        original_v28_cert=140,original_v28_approx=252,
        parent_v28_sha256=sha(PARENT),B112_frozen_gap_sha256=sha(FROZEN),
        B140_source_index_sha256=sha(NEW['B140_R88_SB3_B33B50'].with_suffix('').with_suffix('.index.json')),
        B141_source_index_sha256=sha(NEW['B141_R88_GTO_B117'].with_suffix('').with_suffix('.index.json')),
        source_evidence=meta,source_blind_expansion_ranks=[41,69,88,236],
        supplementary_cert_count=117,
        B142_rank88_true_third_flop=dict(rank=88,model_id=MID,flops=sorted(FLOPS),
            original_GTO_run=gt['run_id'],authentic_actor_OOP_lock_run=ip['run_id'],
            strict_GTO_actor_combo_sum=gt['exact_target_actor_OOP_gto_strict_combo_sum'],
            new_flop='Jh9d6s',new_turn='3c',exact_action_line=LINE,
            no_generic_texture_certification=True),
        original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
        no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True)
    for k,index in ix.items():
        out['independently_verified_completed_batches'][k]=dict(
            status='VERIFIED',run_id=index['run_id'],
            authentic_jobs=index['actual_spot_flop_version_jobs'],
            gto_cases=index['gto_cases'],locked_cases=index['locked_cases'],
            new_subgames=index['verified_cases'],
            gzip_sha256=index['gzip_sha256'],
            no_generic_texture_GTO=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(141,251)
    assert len(matrix['models'])==141 and len(matrix['boards'])==551
    assert matrix['strict_aggregate']['named_board_proofs']==551
    assert all(x['hero_lock_proofs'] and x['strictly_reachable_combo_count']>0
            and x['no_general_bet_size_recommendation'] for x in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V29_B142',
        parent_v29_status_sha256=sha(OUT),
        no_general_bet_size_advice=True,no_observed_private_card_conditionals=True,
        PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B142 V29 frozen rank88 exact three-flop CERT\n\n'
        '**141 CERT-MULTIBOARD / 251 APPROX / 0 EST** of 392 nodes.\n\n'
        'SB3_BTN 3bet pot, acting OOP SB, exact river action b33 c/b50 c/. '
        'Three genuine named flops As7h3d, Ks7h2d, Jh9d6s. '
        'Third flop uses original B117 GTO run 44837416843 and independent B140 '
        'true Rust actor-OOP NL2 partial lock run 44850121199.\n\n'
        'No category-wide or texture-wide GTO, no real observed private-card NL2 '
        'conditional rate. Measured pool marginals and assumed/default rates remain '
        'separately labeled. Medium 50% pot bets are per-board research only.\n'
        'Batch E source verified, navigation 2475/2475, PR#2 remains Draft and NEVER MERGE.\n')
    MATDOC.write_text('# B142 V29 every named board hero-lock and 50% bet provenance\n\n'+write_md(matrix))
    print(json.dumps({'PASS':True,'CERT':141,'APPROX':251,'EST':0,'rank':88,
       'named_boards':len(matrix['boards']),
       'hero_lock_variants':matrix['strict_aggregate']['hero_lock_variants'],
       'b50_candidate_boards':matrix['strict_aggregate']['b50_research_candidate_boards'],
       'GTO_run':gt['run_id'],'hero_NL2_run':ip['run_id']}))
if __name__=='__main__':main()
