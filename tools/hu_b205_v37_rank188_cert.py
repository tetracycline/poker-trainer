#!/usr/bin/env python3
"""B205 V37: independent source-first exact rank188 3 genuine GTO+NL2 flops.

SB_BB BB-IP actor, exact x b50 c/x b100 c/x only. Original B1 8s8h3d,
original B4_MICRO 9s6h3d GTO parent SHA; fresh genuine B200 separate
NL2 Rust actor-IP children; old Ks7h2d original true GTO+NL2 pairing.
Never infer arbitrary similar-flop hand-class GTO, measured private-card
NL2 villain conditional frequencies or generic bet sizing.
"""
import copy, gzip, hashlib, json, pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v36_b201_rank159.json'
B175=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
LOCK=D/'solver_evidence/NL2_MULTIBOARD_B200_R188_SBBB_2FLOP_EXP_IP.json.gz'
PINS={flop:D/f'nl2_hu_b199_rank188_{flop}_original_SB_BB_gto_pin.json'
      for flop in ('8s8h3d','9s6h3d')}
OUT=D/'nl2_hu_multiboard_status_v37_b205_rank188.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v37_b205.json'
DOC=pathlib.Path('docs/NL2_HU_B205_V37_R188_THREE_GENUINE_SBBB_BBIP_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B205_V37_ALL_578_NAMED_BOARD_LOCK_MEDIUM.md')
MID='ln-ipc-r_model-1s0a4ds'
FLOPS={'8s8h3d','9s6h3d','Ks7h2d'}
LINE='x b50 c/x b100 c/x'

def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def source_gate():
    old=load(PARENT); prov=load(B175)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B201_RANK159'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(149,243,0,392)
    assert len(old['records'])==392 and old['records'][MID]['label']=='APPROX'
    assert old['records']['ln-ipc-r_model-vvxn9n']['label']=='CERT-MULTIBOARD'
    for mid in ('ln-iso-lmp_r_model-vlgh2t','ln-iso-lmp_r_model-wpg493'):
        assert old['records'][mid]['label']=='APPROX'
    assert prov['schema']=='NL2_HU_B175_V32_ALL_248_GENUINE_GTO_RUN_ACTOR_TURN_SHA_PROVENANCE_V1'
    assert old['B175_sourceblind_sha256']==sha(B175)
    row=next(r for r in prov['rows'] if r['rank']==188)
    assert row['model_id']==MID and row['hero_seat']==1
    assert row['distinct_GTO_plus_NL2_hero_flops']==['Ks7h2d']
    assert FLOPS<=set(row['distinct_real_GTO_flops'])
    for flop,pfile in PINS.items():
        p=load(pfile)
        assert p['schema']=='NL2_HU_B199_RANK188_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1'
        assert (p['target_rank'],p['model_id'],p['spot'],p['flop'])==(188,MID,'SB_BB',flop)
        assert p['acting_seat']==1 and p['acting_position']=='BB_IP'
        assert p['exact_river_line']==LINE
        assert p['flop_line']=='x b50 c' and p['turn_line']=='x b100 c'
        assert p['minimum_strict_original_actor_IP_combos']>0
        assert p['original_parent_GTO_not_recomputed'] is True
        assert p['preflop_source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
        assert p['observed_NL2_private_hand_conditional_rates'] is False
        idx=D/f"solver_evidence/NL2_MULTIBOARD_{p['source_batch']}.index.json"
        arc=D/f"solver_evidence/NL2_MULTIBOARD_{p['source_batch']}.json.gz"
        ix=load(idx)
        assert (ix['batch'],ix['run_id'])==(p['source_batch'],p['source_run_id'])
        assert p['original_archive_sha256']==ix['gzip_sha256']==sha(arc)
        assert p['original_index_sha256']==sha(idx)
        assert ix['source_sha256']==hashlib.sha256(gzip.decompress(arc.read_bytes())).hexdigest()
        exact=[z for z in row['exact_authentic_gto_source_proofs'] if
          z['flop']==flop and z['turn']==p['turn'] and z['source_run']==p['source_run_id'] and
          z['source_sha']==p['original_case_sha256'] and z['exact_line']==LINE and z['actor']==1 and
          z['strict_legal_combos']>0 and z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5 and
          not z['true_NL2_actor_locked']]
        assert exact
    assert LOCK.is_file()
    ix=load(LOCK.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(LOCK.read_bytes())
    auth=json.loads(raw)
    assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert (ix['batch'],ix['rank'],ix['model_id'])==('B200_R188_SBBB_2FLOP_EXP_IP',188,MID)
    assert (ix['actual_spot_flop_version_jobs'],ix['verified_cases'],ix['gto_cases'],ix['locked_cases'])==(2,2,0,2)
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert ix['gzip_sha256']==sha(LOCK)
    assert ix['exact_SB_BB_BB_IP_line']==LINE and ix['exact_action_line']==LINE and ix['actor_seat']==1
    assert ix['both_new_flops_positive_strict_BB_IP_combos'] is True
    assert ix['strict_failure_reason'] is None
    assert (ix['generic_model_certification'],ix['immediate_CERT_upgrades'])==(0,0)
    assert auth['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert auth['source_run_id']==ix['run_id'] and not auth['errors'] and len(auth['artifacts'])==2
    original=ix['real_B1_B4_GTO_pinned_flop_sources']
    assert set(original)=={'8s8h3d','9s6h3d'}
    for flop,z in original.items():
        p=load(PINS[flop])
        assert z['nodes']>0 and z['strict_combos']>0
        assert z['original_GTO_run']==p['source_run_id']
        assert (z['original_GTO_root_sha256'],z['original_GTO_job_sha256'],z['original_GTO_manifest_sha256'])==(
            p['original_gto_root_sha256'],p['original_gto_job_sha256'],p['original_gto_manifest_sha256'])
        assert z['original_SBBB_preflop_CFR_pinned_not_observed_NL2_private_hand'] is True
    for a in auth['artifacts']:
        assert a['spot']=='SB_BB' and a['version']=='exp_ip' and a['flop'] in original and not a['errors']
        assert len(a['cases'])==1
        c=a['cases'][0]
        assert (c['flop_line'],c['turn'])==('x b50 c',load(PINS[a['flop']])['turn'])
        true=[n for n in c['nodes'] if n['exact_node_line']==LINE and
              n['acting_seat']==1 and n['strictly_reachable_combos']>0]
        assert true and sum(n['strictly_reachable_combos'] for n in true)==original[a['flop']]['strict_combos']
    return old,ix

def main():
    old,ix=source_gate()
    sources=[pathlib.Path(x) for x in old['source_evidence']['source_files']]
    assert len(sources)==len(set(sources)) and all(p.is_file() for p in sources)
    assert LOCK not in sources
    sources.append(LOCK)
    gto,locked,summary=build_source_index(D,sources)
    item=next(copy.deepcopy(x) for x in load(RANK)['nodes'] if x['rank_by_empirically_grounded_frequency_proxy']==188)
    m=next(z for z in load(STAGE)['records'] if z['model_id']==MID)
    assert item['model_id']==MID and (m['solver_profile'],m['family'],m['street'])==('SB_BB','SRP',2)
    assert hero_seat(m['preflop_text'])==1
    item['preflop_text']=m['preflop_text'];item['abstract_action_history']=m['abstract_action_history']
    candidates_all,why=candidates(item,gto,locked,None)
    assert why is None,why
    boards,reason=choose_3_5(candidates_all)
    assert reason is None,reason
    assert len(boards)==3 and {z['flop'] for z in boards}==FLOPS
    assert len({z['flop_texture'] for z in boards})>=2
    for z in boards:
        assert z['acting_seat']==1 and z['actual_exact_action_line']==LINE
        assert z['strict_full_street_combo_reachable']>0 and z['exact_combo_reachable']>0
        assert z['genuine_gto_exploitability_pct']<=.5 and z['relative_spr_error_pct']<=5
        assert z['assumed_preflop_ranges'] is False
        assert z['nl2_locked_variants'] and all(v['version']=='exp_ip' for v in z['nl2_locked_variants'])
        assert len(z['source_sha256'])==64
    for flop in PINS:
        z=next(z for z in boards if z['flop']==flop)
        pin=load(PINS[flop])
        assert (z['source_run_id'],z['source_sha256'],z['turn'])==(
           pin['source_run_id'],pin['original_case_sha256'],pin['turn'])
        assert any(q['run_id']==ix['run_id'] for q in z['nl2_locked_variants'])
    third=next(z for z in boards if z['flop']=='Ks7h2d')
    assert third['source_run_id']==44654973894
    assert any(z['run_id']!=ix['run_id'] for z in third['nl2_locked_variants'])
    out=copy.deepcopy(old)
    out['records'][MID].update(
       label='CERT-MULTIBOARD',high_frequency_preregistered=True,
       original_top24_high_frequency_preregistered=False,source_blind_expansion_rank=188,
       prereg_cohort='B175_V32_FROZEN_RANK188_TWO_MISSING_TRUE_GTO_NL2_BBIP_FLOPS',
       certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
       blocked_reason=None,
       source_credibility='B199_ORIGINAL_B1_8S8H3D_B4_9S6H3D_GTO_SHA_PLUS_B200_TRUE_BBIP_NL2_RUST_AND_OFFICIAL_KS7H2D')
    assert {mid for mid in old['records'] if old['records'][mid]!=out['records'][mid]}=={MID}
    assert sum(z['label']=='CERT-MULTIBOARD' for z in out['records'].values())==150
    assert sum(z['label']=='APPROX' for z in out['records'].values())==242
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V37_B205_RANK188',
        CERT_MULTIBOARD=150,APPROX=242,EST=0,TOTAL=392,
        parent_v36_sha256=sha(PARENT),source_evidence=summary,
        B175_sourceblind_sha256=sha(B175),
        B199_original_B1_B4_GTO_pin_sha256s={k:sha(v) for k,v in PINS.items()},
        B200_real_BB_IP_NL2_source_index_sha256=sha(LOCK.with_suffix('').with_suffix('.index.json')),
        source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{188}),
        supplementary_cert_count=old['supplementary_cert_count']+1,
        B205_rank188_three_genuine_GTO_NL2_BB_IP_flops=dict(
            rank=188,model_id=MID,flops=sorted(FLOPS),exact_line=LINE,actor='BB_IP',
            original_GTO_runs={'8s8h3d':44666285424,'9s6h3d':44732810327,'Ks7h2d':44654973894},
            genuine_B200_real_NL2_child_run=ix['run_id'],
            preflop_CFR_pinned_not_observed_NL2_private_hand=True),
        original_top24_cutoff_unchanged=True,
        no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(150,242)
    assert len(matrix['models'])==150 and len(matrix['boards'])==578
    assert matrix['strict_aggregate']['named_board_proofs']==578
    assert matrix['strict_aggregate']['hero_lock_variants']>=664
    assert matrix['strict_aggregate']['b50_research_candidate_boards']>=132
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0 and
       z['no_general_bet_size_recommendation'] for z in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V37_B205',
       parent_v37_status_sha256=sha(OUT),
       no_general_bet_size_advice=True,
       no_observed_private_card_conditionals=True,
       PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B205 V37 | rank188 genuine 3-board SB-BB BB-IP GTO + NL2 CERT\n\n'
       '**150 CERT-MULTIBOARD /242 APPROX /0 EST** across 392 original nodes. '
       'Only rank188 changes; original genuine exact 8s8h3d/5s (B1), '
       '9s6h3d/Ts (B4_MICRO), Ks7h2d/9d (already paired) flops. '
       'Exact BB-IP x b50 c/x b100 c/x river only; true Rust B200 actor-IP '
       'node-lock has 194 strict BB-IP river combos on 8s8h3d and 68 on 9s6h3d. '
       'Full original GTO SHA and 100bb preflop solver CFR pinned, NOT '
       'observed NL2 private-hand conditional response rates. '
       'Only exact named board/turn/action and pooled NL2 street/size marginal '
       'source lock evidence, explicit defaults kept distinct; GTO gap <=0.5%, '
       'SPR error <=5%. Do NOT generalize to all textures/hand classes or '
       'recommend 50% pot unless that exact-board source is separately proven. '
       'Require full 578 named source/lock proof and 2475/2475 HU link reach '
       'independent GitHub Actions PASS, PR2 Draft, NEVER MERGE.\n')
    MATDOC.write_text('# B205 V37 all 578 genuine named GTO/NL2 board lock and medium evidence\n\n'+write_md(matrix))
    print(json.dumps(dict(PASS=True,CERT=150,APPROX=242,EST=0,
      promoted_rank=188,boards=len(matrix['boards']),
      actor_locked_source_variants=matrix['strict_aggregate']['hero_lock_variants'],
      exact_b50_research=matrix['strict_aggregate']['b50_research_candidate_boards'],
      new_true_BB_IP_Rust_run=ix['run_id'],HU_links_required=2475),ensure_ascii=False))
if __name__=='__main__':main()
