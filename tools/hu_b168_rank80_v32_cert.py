#!/usr/bin/env python3
"""B168: fail-closed source-blind rank80 V32 promotion, only after B167 PASS.

Exact 3-5 distinct GTO flop/hero-locked NL2 pairs; no generic texture GTO,
no measured private-hand conditional NL2 rates and no unvalidated b50 advice.
"""
import copy
import gzip
import hashlib
import json
import pathlib
from hu_multiboard_promote import build_source_index, candidates, choose_3_5, hero_seat
from hu_cert_lock_medium_coverage_matrix import create, write_md

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v31_b161_rank150.json'
B166=D/'nl2_hu_b166_v31_249_APPROX_true_sourceblind_gaps.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
PIN=D/'nl2_hu_b165_rank80_lmp_7s5h3d_gto_parent_pin.json'
OUT=D/'nl2_hu_multiboard_status_v32_b168_rank80.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v32_b168.json'
DOC=pathlib.Path('docs/NL2_HU_B168_V32_RANK80_THREE_AUTHENTIC_BOARD_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B168_V32_ALL_CERT_BOARD_LOCK_MEDIUM.md')
MID='ln-iso-lmp_r_model-17pklmg'
LINE='b33 c/x x/x'
FLOPS={'4s4h2d','KsQh4d','7s5h3d'}
GTO=D/'solver_evidence/NL2_MULTIBOARD_B165_R80_7S5H3D_GTO.json.gz'
EXP=D/'solver_evidence/NL2_MULTIBOARD_B167_R80_7S5H3D_EXP_IP.json.gz'
OLD_EXP=D/'solver_evidence/NL2_MULTIBOARD_B164_R80_B9_ORIGINAL_EXP_IP.json.gz'

def read(p):
    return json.loads(p.read_text())
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def checked_source(path,version):
    idx=path.with_suffix('').with_suffix('.index.json')
    assert path.is_file() and idx.is_file(),str(path)
    i=read(idx)
    raw=gzip.decompress(path.read_bytes())
    v=json.loads(raw)
    assert i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert i['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert i['gzip_sha256']==sha(path)
    assert (i['gto_cases'],i['locked_cases'],i['verified_cases']) == ((1,0,1) if version=='gto' else (0,1,1))
    assert i['actual_spot_flop_version_jobs']==1
    assert v['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert v['source_run_id']==i['run_id'] and i['run_id']>0 and not v['errors']
    assert len(v['artifacts'])==1 and len(v['artifacts'][0]['cases'])==1
    a=v['artifacts'][0]
    assert not a['errors'] and (a['spot'],a['version'])==('LMP_CO_BB',version)
    assert a['flop']=='7s5h3d' if path in (GTO,EXP) else a['flop']=='4s4h2d'
    return i,v

def main():
    parent=read(PARENT)
    b166=read(B166)
    frozen=read(FROZEN)
    p=read(PIN)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['EST'],parent['TOTAL'])==(143,249,0,392)
    assert len(parent['records'])==392 and parent['records'][MID]['label']=='APPROX'
    assert b166['schema']=='NL2_HU_B166_V31_249_APPROX_SOURCE_BLIND_GTO_NL2_GAP_AUDIT_V1'
    assert b166['parent_V31_sha256']==sha(PARENT)
    assert b166['B112_frozen_sha256']==sha(FROZEN)
    assert b166['source_blind_real_certification_ready_rows']==[]
    row=next(x for x in b166['rows'] if x['rank']==80)
    assert (row['model_id'],row['hero_actor_seat'])==(MID,1)
    assert set(row['actually_paired_genuine_NL2_hero_locked_flops'])=={'4s4h2d','KsQh4d'}
    assert row['remaining_distinct_matched_flops_to_3']==1
    assert (p['schema'],p['source_run_id'],p['target_rank'])==(
        'NL2_HU_B165_RANK80_LMP_7S5H3D_GTO_PARENT_PIN_V1',44862108987,80)
    assert (p['flop'],p['turn'],p['flop_line'],p['turn_line'],p['model_id'])==(
        '7s5h3d','6c','b33 c','x x',MID)
    assert p['target_exact_actor_IP_river_nodes']>0 and p['target_exact_actor_IP_strict_combos']>0
    assert p['original_full_100bb_lmp_gto_not_recomputed'] is True
    assert p['assumed_limped_169class'] is True and p['observed_preflop_ranges'] is False
    g,gv=checked_source(GTO,'gto')
    e,ev=checked_source(EXP,'exp_ip')
    oi,ov=checked_source(OLD_EXP,'exp_ip')
    assert (g['batch'],g['run_id'])==('B165_R80_7S5H3D_GTO',44862108987)
    assert e['batch']=='B167_R80_7S5H3D_EXP_IP' and e['run_id']!=g['run_id']
    assert oi['batch']=='B164_R80_B9_ORIGINAL_EXP_IP' and oi['run_id']==44861858112
    assert (g['original_parent_GTO_root_SHA256'],g['original_parent_GTO_job_SHA256'],g['original_parent_GTO_manifest_SHA256'])==(
        p['original_gto_root_sha256'],p['original_gto_job_sha256'],p['original_gto_manifest_sha256'])
    assert (e['original_parent_GTO_root_SHA256'],e['original_parent_GTO_job_SHA256'],e['original_parent_GTO_manifest_SHA256'])==(
        p['original_gto_root_sha256'],p['original_gto_job_sha256'],p['original_gto_manifest_sha256'])
    assert e['exact_actor_IP_river_nodes']>0 and e['exact_actor_IP_strict_combos']>0
    assert e['strict_failure_reason'] is None
    assert e['exact_action_line']==LINE and e['flop']=='7s5h3d' and e['turn']=='6c'
    assert e['rank']==80 and e['generic_model_certification']==0 and e['immediate_CERT_upgrades']==0
    assert g['no_generic_model_certification'] is True
    case=ev['artifacts'][0]['cases'][0]
    hero=[n for n in case['nodes'] if n['exact_node_line']==LINE and
          n['acting_seat']==1 and n['strictly_reachable_combos']>0]
    assert hero and sum(n['strictly_reachable_combos'] for n in hero)==e['exact_actor_IP_strict_combos']
    assert case['flop_line']=='b33 c' and case['turn']=='6c'
    sources=[pathlib.Path(q) for q in parent['source_evidence']['source_files']]
    assert sources and len(sources)==len(set(sources)) and all(q.is_file() for q in sources)
    for q in (OLD_EXP,GTO,EXP):
        if q not in sources:sources.append(q)
    assert len(sources)==len(set(sources))
    exact,locks,meta=build_source_index(D,sources)
    rank=next(copy.deepcopy(x) for x in read(RANK)['nodes']
              if x['rank_by_empirically_grounded_frequency_proxy']==80)
    model=next(x for x in read(STAGE)['records'] if x['model_id']==MID)
    assert rank['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('LMP_CO_BB','LMP',2)
    assert hero_seat(model['preflop_text'])==1 and model['preflop_ranges_source'].startswith('ASSUMED:')
    rank['preflop_text']=model['preflop_text']
    rank['abstract_action_history']=model['abstract_action_history']
    possible,why=candidates(rank,exact,locks,None)
    assert why is None,why
    chosen,why2=choose_3_5(possible)
    assert why2 is None,why2
    assert len(chosen)==3 and {x['flop'] for x in chosen}==FLOPS
    assert len({x['flop_texture'] for x in chosen})>=2
    for x in chosen:
        assert x['acting_seat']==1 and x['actual_exact_action_line']==LINE
        assert x['strict_full_street_combo_reachable']>0 and x['exact_combo_reachable']>0
        assert x['relative_spr_error_pct']<=5 and x['genuine_gto_exploitability_pct']<=.5
        assert x['assumed_preflop_ranges'] is True
        assert x['nl2_locked_variants'] and all(v['version']=='exp_ip' for v in x['nl2_locked_variants'])
    third=next(x for x in chosen if x['flop']=='7s5h3d')
    assert (third['turn'],third['source_run_id'])==('6c',44862108987)
    assert any(v['run_id']==e['run_id'] and v['version']=='exp_ip' for v in third['nl2_locked_variants'])
    out=copy.deepcopy(parent)
    out['records'][MID].update(label='CERT-MULTIBOARD',
        high_frequency_preregistered=True,original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=80,prereg_cohort='B166_FROZEN_ONE_MISSING_DISTINCT_MATCHED_FLOP',
        certified_3_to_5_exact_flop_boards=chosen,proven_exact_board_count=3,
        blocked_reason=None,source_credibility='B166_SOURCE_BLIND_GAP_B165_ORIGINAL_SHA_PINNED_RUST_GTO_B167_TRUE_NL2_ACTOR_IP_CHILD_AND_B164_PREVIOUS_REAL_LOCK')
    changed={k for k in parent['records'] if parent['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(z['label']=='CERT-MULTIBOARD' for z in out['records'].values())==144
    assert sum(z['label']=='APPROX' for z in out['records'].values())==248
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V32_B168_RANK80',
        CERT_MULTIBOARD=144,APPROX=248,EST=0,TOTAL=392,
        original_v31_cert=143,original_v31_approx=249,
        parent_v31_sha256=sha(PARENT),B166_sourceblind_audit_sha256=sha(B166),
        B165_original_GTO_index_sha256=sha(GTO.with_suffix('').with_suffix('.index.json')),
        B167_exact_actor_IP_NL2_index_sha256=sha(EXP.with_suffix('').with_suffix('.index.json')),
        source_evidence=meta,
        source_blind_expansion_ranks=sorted(set(parent['source_blind_expansion_ranks'])|{80}),
        supplementary_cert_count=120,
        B168_rank80_true_third_flop=dict(rank=80,model_id=MID,flops=sorted(FLOPS),
            original_GTO_run=44862108987,true_NL2_actor_IP_run=e['run_id'],
            strict_actor_IP_combos=e['exact_actor_IP_strict_combos'],
            exact_action_line=LINE,preflop_169class_assumed=True),
        original_top24_cutoff_unchanged=True,
        no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(144,248)
    assert len(matrix['models'])==144 and len(matrix['boards'])==560
    assert matrix['strict_aggregate']['named_board_proofs']==560
    assert all(x['hero_lock_proofs'] and x['strictly_reachable_combo_count']>0 and
               x['no_general_bet_size_recommendation'] for x in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V32_B168',
        parent_v32_status_sha256=sha(OUT),no_general_bet_size_advice=True,
        no_observed_private_card_conditionals=True,PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B168 | Rank80 frozen 3 genuine board GTO + actor-IP NL2 evidence\n\n'
       '**144 CERT-MULTIBOARD /248 APPROX /0 EST** across all 392.\n\n'
       'Only exact named flops 4s4h2d, 7s5h3d and KsQh4d are certified. '
       'All named examples match CO IP b33-call / x-x / river check, full sequential combo reach, '
       'SPR within 5%, and GTO exploitability <=0.5%. B165 original source '
       'run 44862108987 plus B167 Rust partial actor-IP lock run '+str(e['run_id'])+
       '. B164 also supplies independently authenticated actor-IP evidence on the older 4s4h2d flop. '
       'All limped preflop 169-class distributions are assumed. NL2 locks are pooled '
       'measured marginals or explicit defaults, never observed private-card conditionals. '
       '50% nonpolarized action flags remain exact-board research only. '
       'River navigation 2475/2475, PR2 remains Draft, NEVER MERGE.\n')
    MATDOC.write_text('# B168 V32 full CERT exact-board lock and 50% medium evidence\n\n'+write_md(matrix))
    print(json.dumps(dict(PASS=True,CERT=144,APPROX=248,EST=0,
        rank=80,named_boards=560,nl2_actor_ip_run=e['run_id'],
        full_river_links=2475),ensure_ascii=False))

if __name__=='__main__':
    main()
