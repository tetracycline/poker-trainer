#!/usr/bin/env python3
"""B201 V36 fail-closed exact rank159 genuine SB_BB BB-IP GTO/NL2 CERT.

Source-blind frozen original B175, V35 392 registry, ORIGINAL B1 Js9h4d
and B5 KsQh4d, authentic true actor BB-IP B195 + B198 Rust children.
Only STRICTLY POSITIVE actor-IP NL2 named 9s6h3d,Js9h4d,KsQh4d.
Exclude As7h3d and As9h2d whose genuine NL2 child has zero river combos.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v35_b193_rank201.json'
FROZEN=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
PINS={'Js9h4d':D/'nl2_hu_b194_rank159_Js9h4d_original_SB_BB_gto_pin.json',
      'KsQh4d':D/'nl2_hu_b197_rank159_KsQh4d_original_SB_BB_gto_pin.json'}
LOCKS={
    'Js9h4d':(D/'solver_evidence/NL2_MULTIBOARD_B195_R159_SBBB_2FLOP_EXP_IP.json.gz','B195_R159_SBBB_2FLOP_EXP_IP'),
    'KsQh4d':(D/'solver_evidence/NL2_MULTIBOARD_B198_R159_SBBB_2FLOP_EXP_IP.json.gz','B198_R159_SBBB_2FLOP_EXP_IP')
}
OUT=D/'nl2_hu_multiboard_status_v36_b201_rank159.json'
MAT=D/'nl2_hu_cert_lock_medium_matrix_v36_b201.json'
DOC=pathlib.Path('docs/NL2_HU_B201_V36_R159_THREE_TRUE_BBIP_GTO_NL2_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B201_V36_ALL_575_NAMED_BOARD_LOCK_MEDIUM.md')
MID='ln-ipc-r_model-vvxn9n'
THREE={'9s6h3d','Js9h4d','KsQh4d'}
LINE='x b100 c/x x/x'

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def freeze():
    v=load(PARENT)
    assert v['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V35_B193_RANK201'
    assert (v['CERT_MULTIBOARD'],v['APPROX'],v['EST'],v['TOTAL'])==(148,244,0,392)
    assert len(v['records'])==392 and v['records'][MID]['label']=='APPROX'
    for target in ['ln-iso-lmp_r_model-qsgdjf','ln-iso-lmp_r_model-10l8t7i','ln-iso-lmp_r_model-yh8124']:
        assert v['records'][target]['label']=='CERT-MULTIBOARD'
    assert v['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert v['records']['ln-iso-lmp_r_model-wpg493']['label']=='APPROX'
    f=load(FROZEN)
    assert f['schema']=='NL2_HU_B175_V32_ALL_248_GENUINE_GTO_RUN_ACTOR_TURN_SHA_PROVENANCE_V1'
    assert v['B175_sourceblind_sha256']==sha(FROZEN)
    row=next(z for z in f['rows'] if z['rank']==159)
    assert row['model_id']==MID and row['hero_seat']==1
    assert row['distinct_GTO_plus_NL2_hero_flops']==['9s6h3d']
    assert THREE<=set(row['distinct_real_GTO_flops'])
    runids={}
    for flop,(gz,batch) in LOCKS.items():
        pin=load(PINS[flop])
        assert pin['schema'] in (
         'NL2_HU_B194_RANK159_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1',
         'NL2_HU_B197_RANK159_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1')
        assert (pin['target_rank'],pin['model_id'],pin['spot'],pin['flop'],pin['acting_seat'])==(159,MID,'SB_BB',flop,1)
        assert pin['exact_river_line']==LINE and pin['minimum_strict_original_actor_IP_combos']>0
        assert pin['preflop_source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
        assert pin['original_parent_GTO_not_recomputed'] is True
        assert pin['observed_NL2_private_hand_conditional_rates'] is False
        assert gz.is_file()
        ix=load(gz.with_suffix('').with_suffix('.index.json'))
        raw=gzip.decompress(gz.read_bytes())
        evidence=json.loads(raw)
        assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
        assert (ix['batch'],ix['actual_spot_flop_version_jobs'],ix['verified_cases'],ix['gto_cases'],ix['locked_cases'])==(batch,2,2,0,2)
        assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
        assert ix['gzip_sha256']==sha(gz)
        assert ix['exact_SB_BB_BB_IP_line']==LINE and ix['actor_seat']==1
        assert ix['both_new_flops_positive_strict_BB_IP_combos'] is False
        assert ix['strict_failure_reason']=='ONE_OR_MORE_NEW_TRUE_SBBB_BBIP_CHILD_ZERO_KEEP_R159_APPROX'
        assert ix['generic_model_certification']==0 and ix['immediate_CERT_upgrades']==0
        assert evidence['source_run_id']==ix['run_id'] and not evidence['errors'] and len(evidence['artifacts'])==2
        original=ix['real_B1_B5_GTO_pinned_flop_sources'][flop]
        assert original['strict_combos']>0 and original['nodes']>0
        assert original['original_GTO_run']==pin['source_run_id']
        assert (original['original_GTO_root_sha256'],original['original_GTO_job_sha256'],original['original_GTO_manifest_sha256'])==(
            pin['original_gto_root_sha256'],pin['original_gto_job_sha256'],pin['original_gto_manifest_sha256'])
        assert original['original_SBBB_preflop_CFR_pinned_not_observed_NL2_private_hand'] is True
        if flop=='Js9h4d':
            assert ix['real_B1_B5_GTO_pinned_flop_sources']['As7h3d']['strict_combos']==0
        else:
            assert ix['real_B1_B5_GTO_pinned_flop_sources']['As9h2d']['strict_combos']==0
        cases=[a for a in evidence['artifacts'] if a['flop']==flop]
        assert len(cases)==1 and cases[0]['version']=='exp_ip' and cases[0]['spot']=='SB_BB'
        assert len(cases[0]['cases'])==1
        c=cases[0]['cases'][0]
        assert (c['flop_line'],c['turn'])==('x b100 c',pin['turn'])
        hero=[n for n in c['nodes'] if n['exact_node_line']==LINE and n['acting_seat']==1 and n['strictly_reachable_combos']>0]
        assert hero and sum(n['strictly_reachable_combos'] for n in hero)==original['strict_combos']
        legal=[x for x in row['exact_authentic_gto_source_proofs'] if
            x['flop']==flop and x['turn']==pin['turn'] and x['source_run']==pin['source_run_id'] and
            x['source_sha']==pin['original_case_sha256'] and x['actor']==1 and
            x['exact_line']==LINE and x['strict_legal_combos']>0 and x['GTO_gap_pct']<=.5 and x['SPR_error_pct']<=5]
        assert legal and all(not z['true_NL2_actor_locked'] for z in legal)
        runids[flop]=ix['run_id']
    assert set(runids)=={'Js9h4d','KsQh4d'}
    return v,runids

def main():
    old,new_runs=freeze()
    files=[pathlib.Path(q) for q in old['source_evidence']['source_files']]
    assert files and len(set(files))==len(files) and all(q.is_file() for q in files)
    for name,(path,batch) in LOCKS.items():
        assert path not in files
        files.append(path)
    exact,locked,meta=build_source_index(D,files)
    item=next(copy.deepcopy(z) for z in load(RANK)['nodes']
              if z['rank_by_empirically_grounded_frequency_proxy']==159)
    model=next(z for z in load(STAGE)['records'] if z['model_id']==MID)
    assert item['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('SB_BB','SRP',2)
    assert hero_seat(model['preflop_text'])==1
    item['preflop_text']=model['preflop_text']
    item['abstract_action_history']=model['abstract_action_history']
    cases,why=candidates(item,exact,locked,None)
    assert why is None,why
    boards,why=choose_3_5(cases)
    assert why is None,why
    assert len(boards)==3 and {q['flop'] for q in boards}==THREE
    assert len({q['flop_texture'] for q in boards})>=2
    for b in boards:
        assert b['acting_seat']==1 and b['actual_exact_action_line']==LINE
        assert b['strict_full_street_combo_reachable']>0 and b['exact_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=.5 and b['relative_spr_error_pct']<=5
        assert b['assumed_preflop_ranges'] is False
        assert b['nl2_locked_variants'] and all(q['version']=='exp_ip' for q in b['nl2_locked_variants'])
        assert len(b['source_sha256'])==64
    for flop,run in new_runs.items():
        sample=next(q for q in boards if q['flop']==flop)
        pin=load(PINS[flop])
        assert (sample['source_run_id'],sample['source_sha256'],sample['turn'])==(
            pin['source_run_id'],pin['original_case_sha256'],pin['turn'])
        assert any(q['run_id']==run for q in sample['nl2_locked_variants'])
    original=next(q for q in boards if q['flop']=='9s6h3d')
    assert original['source_run_id']==44732810327
    assert any(q['run_id'] not in new_runs.values() for q in original['nl2_locked_variants'])
    out=copy.deepcopy(old)
    out['records'][MID].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=159,
        prereg_cohort='B175_V32_FROZEN_3_ACTUAL_NL2_BBIP_FLOPS_POSITIVE_B195_JS9H4D_B198_KSQH4D',
        certified_3_to_5_exact_flop_boards=boards,
        proven_exact_board_count=3,blocked_reason=None,
        source_credibility='B194_B1_JS9H4D_GTO_B195_TRUE_IP_PLUS_B197_B5_KSQH4D_GTO_B198_TRUE_IP_PLUS_9S6H3D_OFFICIAL')
    assert {k for k in old['records'] if old['records'][k]!=out['records'][k]}=={MID}
    assert sum(z['label']=='CERT-MULTIBOARD' for z in out['records'].values())==149
    assert sum(z['label']=='APPROX' for z in out['records'].values())==243
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B201_RANK159',
        CERT_MULTIBOARD=149,APPROX=243,EST=0,TOTAL=392,
        parent_v35_sha256=sha(PARENT),source_evidence=meta,
        B175_sourceblind_sha256=sha(FROZEN),
        B194_B197_original_parent_GTO_SHA_pin_files={k:sha(v) for k,v in PINS.items()},
        B195_B198_true_BB_IP_child_index_SHA256={name:sha(path.with_suffix('').with_suffix('.index.json')) for name,(path,batch) in LOCKS.items()},
        source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{159}),
        supplementary_cert_count=old['supplementary_cert_count']+1,
        B201_rank159_three_genuine_GTO_NL2_BB_IP_flops=dict(
            rank=159,model_id=MID,flops=sorted(THREE),actor='BB_IP',exact_line=LINE,
            original_GTO_B1_B5_B4_runs={'Js9h4d':44666285424,'KsQh4d':44736420272,'9s6h3d':44732810327},
            fresh_true_BB_IP_NL2_child_runs=new_runs,
            excluded_zero_combo_flops=['As7h3d','As9h2d'],
            preflop_solver_CFR_pinned_not_NL2_private_hand_observed=True),
        original_top24_cutoff_unchanged=True,
        no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    m=create(out)
    assert (m['CERT_MULTIBOARD'],m['APPROX'])==(149,243)
    assert len(m['models'])==149 and len(m['boards'])==575
    assert m['strict_aggregate']['named_board_proofs']==575
    assert m['strict_aggregate']['hero_lock_variants']>=664
    assert m['strict_aggregate']['b50_research_candidate_boards']>=132
    assert all(q['hero_lock_proofs'] and q['strictly_reachable_combo_count']>0 and
        q['no_general_bet_size_recommendation'] for q in m['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    m.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V36_B201',
        parent_v36_status_sha256=sha(OUT),no_general_bet_size_advice=True,
        no_observed_private_card_conditionals=True,PR2_remains_draft_never_merge=True)
    MAT.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B201 V36 rank159 genuine SB_BB BB-IP three named-board CERT\n\n'
      '**149 CERT / 243 APPROX /0 EST** out of 392 original models, only rank159 label changed. '
      'True original positive 100bb GTO and correct BB-IP genuine NL2 turn-river paired '
      '9s6h3d/Ts, Js9h4d/Ts, KsQh4d/Tc on exact x b100 c/x x/x. '
      'Js9h4d original B1 GTO source and B195 true NL2 BB-IP 10 strict combos; '
      'KsQh4d original B5 GTO and B198 true NL2 BB-IP 16 strict combos; '
      'third 9s6h3d official exact original GTO+NL2 actor. '
      'As7h3d and As9h2d authentic GTO but ZERO locked BB-IP combo and excluded. '
      'Every displayed board has strict full-street reach >0, GTO <=0.5% and SPR error <=5%. '
      'Opponent observed NL2 data limited to pooled street/size marginals with explicit defaults '
      'and UNKNOWN; never claim private-card conditional observed rates. '
      '50%-pot nonpolarized flags research only on exact named boards, not generic strategy. '
      'Independently audit all 575 named boards and HU 2475/2475, PR2 DRAFT NEVER MERGE.\n')
    MATDOC.write_text('# B201 V36 all 575 genuine named board GTO/NL2 lock and medium evidence\n\n'+write_md(m))
    print(json.dumps(dict(PASS=True,CERT=149,APPROX=243,EST=0,
       promoted_rank=159,boards=len(m['boards']),lock_variants=m['strict_aggregate']['hero_lock_variants'],
       medium50=m['strict_aggregate']['b50_research_candidate_boards'],
       true_positive_lock_flops=sorted(THREE),excluded_zero_flops=['As7h3d','As9h2d'],
       river_links_required=2475),ensure_ascii=False))
if __name__=='__main__':main()
