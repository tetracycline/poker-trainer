#!/usr/bin/env python3
"""B150 frozen rank46 V31 certification gate; fail-closed on all genuine
original GTO SHA and exact full-street actor-IP EXP lock for 3 distinct flops.

Preflop LMP 169-class weights are assumed, NOT empirical NL2 private
card frequencies. None of the 3 boards implies generic texture GTO.
This is STAGED, it is not proof B147 or B149 has completed.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v30_b145_rank47.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
PARENT26=D/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
PIN=D/'nl2_hu_b148_rank46_as9h2d_gto_parent_pin.json'
CORRECTED=D/'solver_evidence/NL2_MULTIBOARD_B148_R46_AS9H2D_GTO_VERIFIED.index.json'
OUT=D/'nl2_hu_multiboard_status_v31_b150_rank46.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v31_b150.json'
DOC=pathlib.Path('docs/NL2_HU_B150_V31_RANK46_GENUINE_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B150_V31_PER_BOARD_NL2_LOCK_MEDIUM.md')
NEW={
  'B146_R46_LMP_9s6h3d':D/'solver_evidence/NL2_MULTIBOARD_B146_R46_LMP_9s6h3d.json.gz',
  'B147_R46_AS9H2D_GTO':D/'solver_evidence/NL2_MULTIBOARD_B147_R46_AS9H2D_GTO.json.gz',
  'B149_R46_AS9H2D_EXP_IP':D/'solver_evidence/NL2_MULTIBOARD_B149_R46_AS9H2D_EXP_IP.json.gz'}
MID='ln-iso-lmp_t_model-17z0wyl'
FLOPS={'8s8h3d','9s6h3d','As9h2d'}
OLD={'8s8h3d'}
LINE='x b50 c/x'; HERO=1; B3=44666294821; B147=44853428350

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def checked_source(key,path):
    assert path.is_file() and path.with_suffix('').with_suffix('.index.json').is_file()
    ix=read(path.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(path.read_bytes())
    proof=json.loads(raw)
    assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert ix['batch']==key and ix['generic_model_certification']==0
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert ix['gzip_sha256']==sha(path)
    assert proof['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert proof['source_run_id']==ix['run_id'] and not proof['errors']
    assert len(proof['artifacts'])==ix['actual_spot_flop_version_jobs']==1
    assert sum(len(a['cases']) for a in proof['artifacts'])==ix['verified_cases']==1
    assert sum(a['version']=='gto' for a in proof['artifacts'])==ix['gto_cases']
    assert sum(a['version']!='gto' for a in proof['artifacts'])==ix['locked_cases']
    return ix,proof

def legal(proof,flop,turn,version):
    return [n for a in proof['artifacts']
       if (a['spot'],a['version'],a['flop'])==('LMP_CO_BB',version,flop)
       for c in a['cases'] if (c['flop_line'],c['flop'],c['turn'])==('x b50 c',flop,turn)
       for n in c['nodes'] if n['acting_seat']==HERO and
       n['exact_node_line']==LINE and n['strictly_reachable_combos']>0]

def main():
    parent=read(PARENT);frozen=read(FROZEN);p26=read(PARENT26)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['EST'],parent['TOTAL'])==(142,250,0,392)
    assert (p26['CERT_MULTIBOARD'],p26['APPROX'])==(137,255)
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['parent_V26_sha256']==sha(PARENT26)
    assert frozen['frozen_rank_sha256']==sha(RANK)
    assert frozen['candidate_count']==255
    assert parent['records'][MID]['label']=='APPROX'
    assert parent['records']['ln-iso-lmp_t_model-1oaypnl']['label']=='CERT-MULTIBOARD'
    frozen46=next(x for x in frozen['rows'] if x['rank']==46)
    assert frozen46['model_id']==MID and frozen46['missing_real_hero_flops_to_3']==2
    assert set(frozen46['matched_real_gto_flops'])=={'8s8h3d','9s6h3d'}
    assert set(frozen46['hero_locked_flops'])==OLD
    assert PIN.is_file() and CORRECTED.is_file()
    p=read(PIN);ci=read(CORRECTED)
    assert p['schema']=='NL2_HU_B148_RANK46_LMP_AS9H2D_CORRECTED_GTO_PARENT_PIN_V1'
    assert ci['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert ci['batch']=='B148_R46_AS9H2D_GTO_VERIFIED'
    assert p['target_rank']==46 and p['model_id']==MID
    assert (p['spot'],p['flop'],p['flop_line'],p['turn_line'],p['acting_seat'])==(
       'LMP_CO_BB','As9h2d','x b50 c','x x',HERO)
    assert p['acting_position']=='CO_IP' and p['source_run_id']==B147
    assert p['target_exact_actor_IP_turn_nodes']>0 and p['target_exact_actor_IP_turn_strict_combos']>0
    assert p['assumed_limped_169class'] and p['observed_preflop_ranges'] is False
    assert p['original_full_100bb_lmp_gto_not_recomputed'] and p['no_generic_model_certification']
    assert ci['corrected_pin_sha256']==sha(PIN)
    assert ci['frozen_high_frequency_rank']==46 and ci['acting_seat']==1
    assert ci['exact_actor_IP_checked_turn_nodes']==p['target_exact_actor_IP_turn_nodes']
    ix={};proof={}
    for key,path in NEW.items():ix[key],proof[key]=checked_source(key,path)
    base=ix['B146_R46_LMP_9s6h3d']
    gt=ix['B147_R46_AS9H2D_GTO']
    exp=ix['B149_R46_AS9H2D_EXP_IP']
    assert (base['run_id'],base['gto_cases'],base['locked_cases'])==(44853239543,0,1)
    assert base['target_rank']==46 and base['exact_actor_IP_checked_turn_nodes']>0
    assert base['exact_actor_IP_strict_combos']>0 and base['strict_failure_reason'] is None
    assert (gt['run_id'],gt['gto_cases'],gt['locked_cases'])==(B147,1,0)
    assert (exp['gto_cases'],exp['locked_cases'])==(0,1)
    assert gt['source_sha256']==p['original_gto_evidence_sha256']
    assert gt['gzip_sha256']==p['original_gto_gzip_sha256']
    assert ci['source_sha256']==gt['source_sha256']
    assert ci['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256']
    assert ci['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256']
    assert ci['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256']
    assert exp['original_gto_parent_run']==B147
    assert exp['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256']
    assert exp['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256']
    assert exp['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256']
    assert exp['corrected_B148_rank46_pin_sha256']==sha(PIN)
    assert exp['true_actor_IP_checked_turn_nodes']>0 and exp['true_actor_IP_strict_combo_sum']>0
    assert exp['strict_failure_reason'] is None and exp['target_rank']==46
    assert exp['exact_action_line']==LINE and exp['target_flop']=='As9h2d'
    assert exp['turn']==p['turn']
    assert exp['original_B147_flop_NOT_recomputed']
    assert legal(proof['B147_R46_AS9H2D_GTO'],'As9h2d',p['turn'],'gto')
    assert legal(proof['B149_R46_AS9H2D_EXP_IP'],'As9h2d',p['turn'],'exp_ip')
    assert legal(proof['B146_R46_LMP_9s6h3d'],'9s6h3d','Ts','exp_ip')
    e=parent['independently_verified_completed_batches']['B4_MICRO']
    assert e['status']=='VERIFIED' and e['run_id']==44732810327
    source_files=[pathlib.Path(x) for x in parent['source_evidence']['source_files']]
    assert source_files and all(x.is_file() for x in source_files)
    source_files+=list(NEW.values())
    assert len(source_files)==len(set(source_files))
    gto,locked,meta=build_source_index(D,source_files)
    rank=next(copy.deepcopy(x) for x in read(RANK)['nodes']
              if x['rank_by_empirically_grounded_frequency_proxy']==46)
    model=next(x for x in read(STAGE)['records'] if x['model_id']==MID)
    assert rank['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('LMP_CO_BB','LMP',1)
    assert hero_seat(model['preflop_text'])==HERO
    assert model['preflop_ranges_source'].startswith('ASSUMED:')
    rank['preflop_text']=model['preflop_text']
    rank['abstract_action_history']=model['abstract_action_history']
    sources,reason=candidates(rank,gto,locked,None)
    assert reason is None,(46,reason)
    selected,why=choose_3_5(sources)
    assert why is None,(46,why)
    assert len(selected)==3 and {x['flop'] for x in selected}==FLOPS
    assert len({x['flop_texture'] for x in selected})>=2
    for x in selected:
        assert x['acting_seat']==HERO and x['actual_exact_action_line']==LINE
        assert x['strict_full_street_combo_reachable']>0 and x['exact_combo_reachable']>0
        assert x['genuine_gto_exploitability_pct'] is not None and x['genuine_gto_exploitability_pct']<=.5
        assert x['relative_spr_error_pct']<=5
        assert x['assumed_preflop_ranges'] is True
        assert x['nl2_locked_variants']
        assert all(v['version']=='exp_ip' for v in x['nl2_locked_variants'])
    x=next(x for x in selected if x['flop']=='9s6h3d')
    assert x['source_run_id']==B3
    assert any(z['run_id']==base['run_id'] for z in x['nl2_locked_variants'])
    x=next(x for x in selected if x['flop']=='As9h2d')
    assert x['source_run_id']==B147 and x['turn']==p['turn']
    assert any(z['run_id']==exp['run_id'] for z in x['nl2_locked_variants'])
    out=copy.deepcopy(parent)
    out['records'][MID].update(label='CERT-MULTIBOARD',
       high_frequency_preregistered=True,original_top24_high_frequency_preregistered=False,
       source_blind_expansion_rank=46,
       prereg_cohort='B112_FROZEN_TWO_MISSING_REAL_HERO_FLOPS',
       certified_3_to_5_exact_flop_boards=selected,proven_exact_board_count=3,
       blocked_reason=None,
       source_credibility='B3_ORIGINAL_GTO_B146_IP_AND_B147_ORIGINAL_GTO_B148_FIX_B149_TRUE_RUST_IP_LMP_PREFLOP_ASSUMED')
    changed={k for k in parent['records'] if parent['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(v['label']=='CERT-MULTIBOARD' for v in out['records'].values())==143
    assert sum(v['label']=='APPROX' for v in out['records'].values())==249
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B150_RANK46',
       CERT_MULTIBOARD=143,APPROX=249,EST=0,
       original_v30_cert=142,original_v30_approx=250,parent_v30_sha256=sha(PARENT),
       B112_frozen_gap_sha256=sha(FROZEN),
       B146_source_index_sha256=sha(NEW['B146_R46_LMP_9s6h3d'].with_suffix('').with_suffix('.index.json')),
       B148_corrected_pin_sha256=sha(PIN),
       B149_source_index_sha256=sha(NEW['B149_R46_AS9H2D_EXP_IP'].with_suffix('').with_suffix('.index.json')),
       source_evidence=meta,source_blind_expansion_ranks=[41,46,47,69,88,236],
       supplementary_cert_count=119,
       B150_rank46_two_true_missing_flops=dict(rank=46,model_id=MID,
          flops=sorted(FLOPS),original_B3_GTO_run=B3,original_B147_GTO_run=B147,
          authentic_actor_IP_lock_runs=dict(
             B146_9s6h3d=base['run_id'],B149_As9h2d=exp['run_id']),
          corrected_B148_actor_position='CO_IP',
          new_flop='As9h2d',new_turn=p['turn'],exact_action_line=LINE,
          limped_preflop_169class_assumed=True,no_generic_texture_certification=True),
       original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
       no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True)
    for key,index in ix.items():
        out['independently_verified_completed_batches'][key]=dict(
           status='VERIFIED',run_id=index['run_id'],
           authentic_jobs=index['actual_spot_flop_version_jobs'],
           gto_cases=index['gto_cases'],locked_cases=index['locked_cases'],
           new_subgames=index['verified_cases'],gzip_sha256=index['gzip_sha256'],
           no_generic_texture_GTO=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(143,249)
    assert len(matrix['models'])==143 and len(matrix['boards'])==557
    assert matrix['strict_aggregate']['named_board_proofs']==557
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0 and
        z['no_general_bet_size_recommendation'] for z in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V31_B150',
       parent_v31_status_sha256=sha(OUT),no_general_bet_size_advice=True,
       no_observed_private_card_conditionals=True,PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B150 V31 rank46 exact three-flop GTO+NL2 actor-IP CERT\n\n'
      '**143 CERT-MULTIBOARD / 249 APPROX / 0 EST** of 392.\n\n'
      'Original named flops 8s8h3d and 9s6h3d, new As9h2d. '
      'Original B3 GTO and a new true As9h2d B147 GTO, separately SHA verified; '
      'B146 and B149 true Rust actor-IP NL2 pooled-marginal/assumed-default '
      'turn-only lock, exact action x b50 c/x. '
      'Original B147 wrong rank/actor index independently corrected B148, original raw GTO unchanged.\n'
      'Preflop 169-class limped profile **assumed, not observed**. '
      'No observed per-hole-card conditional NL2 action policy, no texture-wide GTO. '
      '50% pot only source-specific research candidates.\n'
      'Batch E source VERIFIED, full HU river navigation 2475/2475, '
      'PR#2 Draft, NEVER MERGE.\n')
    MATDOC.write_text('# B150 V31 per-named-board NL2 lock and 50% size provenance\n\n'+write_md(matrix))
    print(json.dumps({'PASS':True,'CERT':143,'APPROX':249,'EST':0,
       'rank':46,'named_boards':len(matrix['boards']),
       'hero_lock_variants':matrix['strict_aggregate']['hero_lock_variants'],
       'b50_candidate_boards':matrix['strict_aggregate']['b50_research_candidate_boards'],
       'original_GTO_run':B147,'actual_actor_IP_lock_run':exp['run_id']}))
if __name__=='__main__':main()
