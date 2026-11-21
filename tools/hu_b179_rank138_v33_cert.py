#!/usr/bin/env python3
"""B179 source-blind exact rank138 third-board V33 CERT, fail closed.

Only authentic SHA-proven original B04 legacy 8s8h3d, B2 Js9h4d,
official As9h2d GTO plus truly matched CO-IP NL2 turn-river locks.
GTO is bound to precisely named exact board/action/SPR; original B04 has
restricted historical flop action menu, not a modern full-tree solve.
No observed private-hole-card villain response, no universal b50 advice.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v32_b168_rank80.json'
B175=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
PIN_B04=D/'nl2_hu_b177_rank138_co_bb_8s8h3d_b04_gto_parent_pin.json'
PIN_B2=D/'nl2_hu_b176_rank138_js9h4d_b2_gto_parent_pin.json'
B176=D/'solver_evidence/NL2_MULTIBOARD_B176_R138_CO_JS9H4D_EXP_IP.json.gz'
B178=D/'solver_evidence/NL2_MULTIBOARD_B178_R138_B04_8S8H3D_EXP_IP.json.gz'
MID='ln-ipfr-r_model-hqu5je'
FLOPS={'8s8h3d','As9h2d','Js9h4d'}
LINE='x x/x x/x'
OUT=D/'nl2_hu_multiboard_status_v33_b179_rank138.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v33_b179.json'
DOC=pathlib.Path('docs/NL2_HU_B179_V33_R138_EXACT_3_GTO_NL2_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B179_V33_ALL_563_NAMED_BOARD_LOCK_MEDIUM.md')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def authenticated_new(path,batch):
    idx=path.with_suffix('').with_suffix('.index.json')
    assert path.is_file() and idx.is_file()
    i=read(idx); raw=gzip.decompress(path.read_bytes());e=json.loads(raw)
    assert i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert i['batch']==batch and (i['gto_cases'],i['locked_cases'],i['verified_cases'])==(0,1,1)
    assert i['actual_spot_flop_version_jobs']==1 and i['run_id']>0
    assert i['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert i['gzip_sha256']==sha(path)
    assert e['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert e['source_run_id']==i['run_id'] and not e['errors'] and len(e['artifacts'])==1
    a=e['artifacts'][0]
    assert (a['spot'],a['version'])==('CO_BB','exp_ip') and not a['errors']
    assert len(a['cases'])==1
    assert i['generic_model_certification']==0 and i['immediate_CERT_upgrades']==0
    assert i['strict_failure_reason'] is None
    assert i['exact_actor_IP_river_nodes']>0 and i['exact_actor_IP_strict_combos']>0
    assert i['exact_action_line']==LINE and i['rank']==138
    assert i['flop']==a['flop'] and i['turn']==a['cases'][0]['turn']
    hero=[n for n in a['cases'][0]['nodes'] if n['exact_node_line']==LINE
      and n['acting_seat']==1 and n['strictly_reachable_combos']>0]
    assert hero and sum(n['strictly_reachable_combos'] for n in hero)==i['exact_actor_IP_strict_combos']
    return i,e

def main():
    old=read(PARENT);proof=read(B175);frozen=read(FROZEN)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V32_B168_RANK80'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(144,248,0,392)
    assert len(old['records'])==392 and old['records'][MID]['label']=='APPROX'
    assert proof['schema']=='NL2_HU_B175_V32_ALL_248_GENUINE_GTO_RUN_ACTOR_TURN_SHA_PROVENANCE_V1'
    assert proof['v32_sha256']==sha(PARENT) and (proof['CERT_MULTIBOARD'],proof['APPROX'])==(144,248)
    assert not proof['source_ready_now']
    row=next(x for x in proof['rows'] if x['rank']==138)
    assert row['model_id']==MID and row['hero_seat']==1
    assert set(row['distinct_real_GTO_flops'])==FLOPS
    assert row['distinct_GTO_plus_NL2_hero_flops']==['As9h2d']
    b04=read(PIN_B04);b2=read(PIN_B2)
    assert (b04['schema'],b04['original_run_id'],b04['strict_original_GTO_combo_min'])==(
      'NL2_HU_B177_RANK138_B04_CO_BB_8S8H3D_GTO_PARENT_PIN_V1',44653774402,7)
    assert b04['historical_restricted_tree_not_full_modern_GTO'] is True
    assert b04['original_restricted_flop_menu']==dict(oop='',ip='33%,50%,75%',raises='3x,a')
    assert b2['schema']=='NL2_HU_B176_RANK138_CO_BB_JS9H4D_B2_GTO_PARENT_PIN_V1'
    assert (b2['original_source_run_id'],b2['strict_hero_IP_river_combos'])==(44666290556,20)
    ex2,raw2=authenticated_new(B176,'B176_R138_CO_JS9H4D_EXP_IP')
    ex4,raw4=authenticated_new(B178,'B178_R138_B04_8S8H3D_EXP_IP')
    assert (ex2['flop'],ex2['turn'])==('Js9h4d','Ts')
    assert (ex4['flop'],ex4['turn'])==('8s8h3d','5s')
    assert (ex2['original_parent_GTO_root_SHA256'],ex2['original_parent_GTO_job_SHA256'],ex2['original_parent_GTO_manifest_SHA256'])==(
      b2['original_GTO_flop_SHA256'],b2['original_GTO_job_SHA256'],b2['original_manifest_SHA256'])
    assert (ex4['original_parent_GTO_root_SHA256'],ex4['original_parent_GTO_job_SHA256'],ex4['original_parent_GTO_manifest_SHA256'])==(
      b04['original_flop_root_sha256'],b04['original_job_sha256'],b04['original_manifest_sha256'])
    assert ex4['historical_restricted_flop_game_tree_NOT_MODERN_FULL_GTO'] is True
    assert ex4['historical_original_action_menu']==b04['original_restricted_flop_menu']
    original_files=[pathlib.Path(f) for f in old['source_evidence']['source_files']]
    assert original_files and len(original_files)==len(set(original_files))
    assert all(f.is_file() for f in original_files)
    for x in (B176,B178):
        assert x not in original_files
        original_files.append(x)
    exact,locked,summary=build_source_index(D,original_files)
    rank=next(copy.deepcopy(x) for x in read(RANK)['nodes']
         if x['rank_by_empirically_grounded_frequency_proxy']==138)
    model=next(x for x in read(STAGE)['records'] if x['model_id']==MID)
    assert rank['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('CO_BB','SRP',2)
    assert hero_seat(model['preflop_text'])==1
    rank['preflop_text']=model['preflop_text'];rank['abstract_action_history']=model['abstract_action_history']
    candidates_exact,reason=candidates(rank,exact,locked,None)
    assert reason is None,reason
    selected,why=choose_3_5(candidates_exact)
    assert why is None,why
    assert len(selected)==3 and {x['flop'] for x in selected}==FLOPS
    assert len({x['flop_texture'] for x in selected})>=2
    for x in selected:
        assert x['acting_seat']==1 and x['actual_exact_action_line']==LINE
        assert x['strict_full_street_combo_reachable']>0 and x['exact_combo_reachable']>0
        assert x['genuine_gto_exploitability_pct']<=.5 and x['relative_spr_error_pct']<=5
        assert x['nl2_locked_variants'] and all(y['version']=='exp_ip' for y in x['nl2_locked_variants'])
        assert x['source_sha256'] and len(x['source_sha256'])==64
    newb04=next(x for x in selected if x['flop']=='8s8h3d')
    assert (newb04['turn'],newb04['source_run_id'],newb04['source_sha256'])==(
      '5s',44653774402,b04['source_original_GTO_case_SHA256'])
    assert newb04['assumed_preflop_ranges'] is False
    assert any(y['run_id']==ex4['run_id'] for y in newb04['nl2_locked_variants'])
    newb2=next(x for x in selected if x['flop']=='Js9h4d')
    assert (newb2['turn'],newb2['source_run_id'],newb2['source_sha256'])==(
      'Ts',44666290556,b2['original_GTO_sample_sha256'])
    assert any(y['run_id']==ex2['run_id'] for y in newb2['nl2_locked_variants'])
    out=copy.deepcopy(old)
    out['records'][MID].update(
      label='CERT-MULTIBOARD',high_frequency_preregistered=True,
      original_top24_high_frequency_preregistered=False,source_blind_expansion_rank=138,
      prereg_cohort='B175_V32_FROZEN_TWO_MISSING_GENUINE_NL2_ACTOR_IP_GTO_FLOPS',
      certified_3_to_5_exact_flop_boards=selected,proven_exact_board_count=3,
      blocked_reason=None,
      original_B04_flop_8s8h3d_tree_limited_to_historical_menu=True,
      source_credibility='ORIGINAL_LEGACY_B04_8S8H3D_GTO_SHA_AND_B178_TRUE_NL2_IP_PLUS_ORIGINAL_B2_JS9H4D_SHA_AND_B176_TRUE_NL2_IP_PLUS_OFFICIAL_AS9H2D_PAIR')
    changed={k for k in old['records'] if old['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(y['label']=='CERT-MULTIBOARD' for y in out['records'].values())==145
    assert sum(y['label']=='APPROX' for y in out['records'].values())==247
    out.update(
      schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V33_B179_RANK138',
      CERT_MULTIBOARD=145,APPROX=247,EST=0,TOTAL=392,
      original_v32_cert=144,original_v32_approx=248,
      parent_v32_sha256=sha(PARENT),B175_sourceblind_sha256=sha(B175),
      B176_real_NL2_actor_IP_index_sha256=sha(B176.with_suffix('').with_suffix('.index.json')),
      B178_real_NL2_actor_IP_index_sha256=sha(B178.with_suffix('').with_suffix('.index.json')),
      original_B177_GTO_sha_pin_sha256=sha(PIN_B04),
      source_evidence=summary,
      source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{138}),
      supplementary_cert_count=121,
      B179_rank138_three_genuine_flops=dict(
        rank=138,model_id=MID,flops=sorted(FLOPS),
        exact_action_line=LINE,actor='CO_IP',
        original_GTO_source_runs={'8s8h3d':44653774402,'Js9h4d':44666290556},
        genuine_new_NL2_hero_lock_runs={'8s8h3d':ex4['run_id'],'Js9h4d':ex2['run_id']},
        original_B04_historical_restricted_GTO_tree_explicit=True,
        no_observed_private_card_NL2_conditional_rates=True),
      original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
      no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(145,247)
    assert len(matrix['models'])==145 and len(matrix['boards'])==563
    assert matrix['strict_aggregate']['named_board_proofs']==563
    assert all(x['hero_lock_proofs'] and x['strictly_reachable_combo_count']>0
        and x['no_general_bet_size_recommendation'] for x in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(
      schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V33_B179',
      parent_v33_status_sha256=sha(OUT),no_general_bet_size_advice=True,
      no_observed_private_card_conditionals=True,PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B179 | Exact 3-board rank138 independently verified GTO plus CO-IP partial NL2 CERT\n\n'
      '**145 CERT-MULTIBOARD /247 APPROX /0 EST** across 392 models. '
      'Rank138 only EXACT public flops 8s8h3d, As9h2d and Js9h4d, same pot '
      'family CO_BB, same river x x/x x/x, all strict sequential combo reach >0, '
      'GTO gap <=0.5%, SPR error <=5%, genuine paired actor-IP NL2 source. '
      'Original B04 GTO on 8s8h3d used an HISTORICALLY RESTRICTED FLOP '
      'SIZE MENU OOP none, IP 33/50/75, raises 3x/all-in; it does NOT certify '
      'modern full-tree GTO and cannot transfer to arbitrary similar flop textures. '
      'B176 original B2 and B178 original B04 genuine NL2 Rust children are '
      'SHA pinned and independent. NL2 action observations pooled aggregates or '
      'assumed defaults are not conditional private-hand data. '
      '50% pot nonpolarized flags are specific-board research, not general advice. '
      'River 2475/2475, PR2 remains Draft and NEVER MERGE.\n')
    MATDOC.write_text('# B179 V33 complete 563 named GTO/NL2 source-lock and medium evidence\n\n'+write_md(matrix))
    print(json.dumps(dict(PASS=True,CERT=145,APPROX=247,EST=0,
        rank=138,boards=563,original_B04_restricted=True,
        paired_NL2_new_runs=[ex2['run_id'],ex4['run_id']],river_links=2475),ensure_ascii=False))
if __name__=='__main__':
    main()
