#!/usr/bin/env python3
"""B161 source-blind, frozen rank150 exact 3-board CERT from B3 GTO + B144
authentic NL2 actor-IP partial Rust turn/river lock.

Requires B159 independently audited ALL 250 APPROX gaps, pre-registered B112
rank150 original missing 2 genuine hero-lock flops, authentic pinned B3 GTO
and B144 independently source-SHA verified NL2. No texture GTO, no private
hand NL2 rate, no model-wide nonpolar 50% size recommendation.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat,texture
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v30_b145_rank47.json'
B159=D/'nl2_hu_b159_v30_250_APPROX_strict_source_gap.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
PARENT26=D/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
B154=D/'solver_evidence/NL2_MULTIBOARD_B154_R46_4S4H2D_GTO.json.gz'
NEW={
 '8s8h3d':D/'solver_evidence/NL2_MULTIBOARD_B144_R47_LMP_8s8h3d.json.gz',
 '9s6h3d':D/'solver_evidence/NL2_MULTIBOARD_B144_R47_LMP_9s6h3d.json.gz'}
OUT=D/'nl2_hu_multiboard_status_v31_b161_rank150.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v31_b161.json'
DOC=pathlib.Path('docs/NL2_HU_B161_V31_RANK150_GENUINE_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B161_V31_ALL_557_NAMED_BOARD_NL2_LOCK_MEDIUM.md')
MID='ln-iso-lmp_r_model-4ys53a'
FLOPS={'8s8h3d','9s6h3d','KsQh4d'}
OLD={'KsQh4d'}
ACTOR=1;LINE='x b33 c/x x/x';GTO_RUN=44666294821;LOCK_RUN=44852646580

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_b144_source(path,flop):
    idxpath=path.with_suffix('').with_suffix('.index.json')
    assert path.is_file() and idxpath.is_file()
    ix=read(idxpath)
    raw=gzip.decompress(path.read_bytes());data=json.loads(raw)
    assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert ix['batch']=='B144_R47_LMP_'+flop
    assert (ix['run_id'],ix['gto_cases'],ix['locked_cases'],ix['verified_cases'])==(LOCK_RUN,0,1,1)
    assert ix['actual_spot_flop_version_jobs']==1
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert ix['gzip_sha256']==sha(path)
    assert ix['original_gto_parent_run']==GTO_RUN and ix['original_B3_flop_NOT_recomputed']
    assert ix['target_rank']==47
    assert ix['original_gto_parent_run']==GTO_RUN
    assert ix['exact_actor_IP_checked_turn_nodes']>0 and ix['exact_actor_IP_strict_combos']>0
    assert ix['strict_failure_reason'] is None
    assert ix['actual_exact_action_line']=='x b33 c/x'
    assert ix['full_100bb_LMP_preflop_range_assumed']
    assert ix['source_NL2_pool_marginal_vs_assumed_size_rates_not_private_combo_conditional']
    assert ix['generic_model_certification']==0 and ix['immediate_CERT_upgrades']==0
    assert data['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert data['source_run_id']==LOCK_RUN and not data['errors']
    assert (data['exact_board_gto_sources'],data['imputed_pool_locked_sources'],
            data['new_authentic_board_cases'])==(0,1,1)
    assert len(data['artifacts'])==1
    a=data['artifacts'][0]
    assert (a['spot'],a['version'],a['flop'])==('LMP_CO_BB','exp_ip',flop)
    assert not a['errors'] and len(a['cases'])==1
    c=a['cases'][0]
    assert c['flop_line']=='x b33 c' and c['turn']==ix['turn']
    assert ix['flop']==flop
    hero=[n for n in c['nodes'] if n['exact_node_line']==LINE
          and n['acting_seat']==ACTOR and n['strictly_reachable_combos']>0]
    assert hero,('true B144 IP river should be real for rank150',flop)
    return ix,hero

def main():
    parent=read(PARENT);p26=read(PARENT26);frozen=read(FROZEN);recent=read(B159)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['EST'],parent['TOTAL'])==(142,250,0,392)
    assert (p26['CERT_MULTIBOARD'],p26['APPROX'])==(137,255)
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['parent_V26_sha256']==sha(PARENT26) and frozen['frozen_rank_sha256']==sha(RANK)
    assert frozen['candidate_count']==255 and frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    assert parent['records'][MID]['label']=='APPROX'
    frozen150=next(x for x in frozen['rows'] if x['rank']==150)
    assert frozen150['model_id']==MID and frozen150['missing_real_hero_flops_to_3']==2
    assert set(frozen150['matched_real_gto_flops'])==FLOPS
    assert set(frozen150['hero_locked_flops'])==OLD
    assert set(frozen150['missing_locked_existing_GTO_flops'])==FLOPS-OLD
    assert recent['schema']=='NL2_HU_B159_V30_FULL_250_APPROX_SOURCE_BLIND_STRICT_GAP_V1'
    assert recent['parent_V30_sha256']==sha(PARENT)
    assert recent['parent_B112_frozen_sha256']==sha(FROZEN)
    assert (recent['CERT_MULTIBOARD'],recent['APPROX'],recent['EST'],recent['count'])==(142,250,0,250)
    assert (recent['existing_real_named_board_proofs'],recent['existing_NL2_lock_source_variants'],
            recent['existing_b50_exact_board_research_candidates'])==(554,646,131)
    assert len(recent['ready_for_independent_3_5_full_cert_gate'])==1
    ready=recent['ready_for_independent_3_5_full_cert_gate'][0]
    assert (ready['rank'],ready['model_id'])==(150,MID)
    assert set(ready['selected_flops'])==FLOPS and set(ready['matched_flops'])==FLOPS
    row=next(x for x in recent['rows'] if x['rank']==150)
    assert row['model_id']==MID and row['certified_3_to_5_now']
    assert row['actual_hero_lock_flops']==3 and row['remaining_DISTINCT_flops_to_3']==0
    assert row['hero_actor_seat']==ACTOR and set(row['known_matched_textures'])=={'LOW','PAIRED','KQ_HIGH'}
    assert not row['missing_hero_lock_on_existing_valid_GTO_flops']
    assert row['measured_NL2_private_combo_conditional_rates'] is False
    # B154 extra GTO was independently true, but rank46 strict actor-IP 0;
    # it cannot count as rank150's 4th matched source.
    origidx=read(B154.with_suffix('').with_suffix('.index.json'))
    assert origidx['run_id']==44855330215
    assert origidx['exact_target_actor_IP_strict_combos']==0
    assert origidx['source_sha256']==hashlib.sha256(gzip.decompress(B154.read_bytes())).hexdigest()
    assert recent['parent_GTO_B154_source_index_sha256']==sha(B154.with_suffix('').with_suffix('.index.json'))
    ix={}
    for flop,p in NEW.items():
        ix[flop],hero=verify_b144_source(p,flop)
        assert len(hero)>0
        old=next(a for a in frozen150['missing_locked_known_source_samples'] if a['flop']==flop)
        assert (old['turn'],old['gto_run'],old['exact_line'],old['acting_seat'])==(
            ix[flop]['turn'],GTO_RUN,LINE,ACTOR)
        assert old['strict_legal_combos']>0 and old['actual_spr']>0
    src=[pathlib.Path(x) for x in parent['source_evidence']['source_files']]
    assert src and all(p.is_file() for p in src)
    assert all(p in src for p in NEW.values())
    assert B154 not in src
    src.append(B154)
    assert len(src)==len(set(src))
    gto,locked,meta=build_source_index(D,src)
    rank=next(copy.deepcopy(x) for x in read(RANK)['nodes']
              if x['rank_by_empirically_grounded_frequency_proxy']==150)
    model=next(x for x in read(STAGE)['records'] if x['model_id']==MID)
    assert rank['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('LMP_CO_BB','LMP',2)
    assert hero_seat(model['preflop_text'])==ACTOR
    assert model['preflop_ranges_source'].startswith('ASSUMED:')
    rank['preflop_text']=model['preflop_text']
    rank['abstract_action_history']=model['abstract_action_history']
    possible,reason=candidates(rank,gto,locked,None)
    assert reason is None,(150,reason)
    selected,why=choose_3_5(possible)
    assert why is None,(150,why)
    assert len(selected)==3 and {x['flop'] for x in selected}==FLOPS
    assert {x['flop_texture'] for x in selected}=={'PAIRED','LOW','KQ_HIGH'}
    for x in selected:
        assert x['acting_seat']==ACTOR and x['actual_exact_action_line']==LINE
        assert x['strict_full_street_combo_reachable']>0 and x['exact_combo_reachable']>0
        assert x['relative_spr_error_pct']<=5 and x['genuine_gto_exploitability_pct']<=0.5
        assert x['assumed_preflop_ranges'] is True
        assert x['source_run_id']==GTO_RUN
        assert x['nl2_locked_variants'] and all(v['version']=='exp_ip' for v in x['nl2_locked_variants'])
        assert x['source_sha256'] and len(x['source_sha256'])==64
    for flop in ('8s8h3d','9s6h3d'):
        x=next(x for x in selected if x['flop']==flop)
        assert x['turn']==ix[flop]['turn']
        assert any(v['run_id']==LOCK_RUN and v['version']=='exp_ip' for v in x['nl2_locked_variants'])
    out=copy.deepcopy(parent)
    out['records'][MID].update(label='CERT-MULTIBOARD',
        high_frequency_preregistered=True,original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=150,prereg_cohort='B112_FROZEN_TWO_MISSING_REAL_HERO_FLOPS',
        certified_3_to_5_exact_flop_boards=selected,
        proven_exact_board_count=3,blocked_reason=None,
        source_credibility='B3_PINNED_ORIGINAL_GTO_PLUS_B144_TWO_GENUINE_RUST_EXP_IP_PARTIALS_AND_ORIGINAL_KSQH4D_HERO_LOCK_LMP_ASSUMED_PREFLOP')
    changed={k for k in parent['records'] if parent['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in out['records'].values())==143
    assert sum(x['label']=='APPROX' for x in out['records'].values())==249
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150',
        CERT_MULTIBOARD=143,APPROX=249,EST=0,
        original_v30_cert=142,original_v30_approx=250,
        parent_v30_sha256=sha(PARENT),
        B112_frozen_gap_sha256=sha(FROZEN),B159_sourceblind_audit_sha256=sha(B159),
        B144_8s8h3d_index_sha256=sha(NEW['8s8h3d'].with_suffix('').with_suffix('.index.json')),
        B144_9s6h3d_index_sha256=sha(NEW['9s6h3d'].with_suffix('').with_suffix('.index.json')),
        source_evidence=meta,source_blind_expansion_ranks=[41,47,69,88,150,236],
        supplementary_cert_count=119,
        B161_rank150_original_two_gaps_now_true_locked=dict(
           rank=150,model_id=MID,flops=sorted(FLOPS),
           original_B3_full_GTO_run=GTO_RUN,new_actor_IP_NL2_Rust_run=LOCK_RUN,
           exact_action_line=LINE,actor='CO_IP',
           sourceblind_pre_registered_missing_two_flops=['8s8h3d','9s6h3d'],
           low_and_paired_and_KQ_textures=True,
           limped_preflop_169class_assumed=True,
           no_observed_NL2_private_combo_conditional_rates=True),
        original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
        no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(143,249)
    assert len(matrix['models'])==143 and len(matrix['boards'])==557
    assert matrix['strict_aggregate']['named_board_proofs']==557
    assert all(b['hero_lock_proofs'] and b['strictly_reachable_combo_count']>0
               and b['no_general_bet_size_recommendation'] for b in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V31_B161',
        parent_v31_status_sha256=sha(OUT),no_general_bet_size_advice=True,
        no_observed_private_card_conditionals=True,PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B161 | Frozen B112 high-frequency rank150 3 exact GTO+NL2 hero-IP boards\n\n'
       '**143 CERT-MULTIBOARD /249 APPROX /0 EST** of 392.\n\n'
       'B159 complete independent source-blind all 250 APPROX gap audit found this '
       'single directly source-ready rank150: 8s8h3d, 9s6h3d, KsQh4d. '
       'They have ORIGINAL full-size B3 GTO (run 44666294821), same true hero '
       'CO IP river x b33 c/x x/x, all 3 genuine legal combo/SPR/convergence proofs, '
       'and matching actor-IP NL2 lock source; first two B144 true fresh Rust '
       'turn/river children run 44852646580, final KsQh4d original true lock.\n'
       'LMP preflop 169 classes explicitly ASSUMED, NOT observed NL2 private-card action. '
       'Node-lock source pooled measured-vs-assumed marginals preserved. '
       '50% pot labels exact named-board research flags only, not universal bet advice.\n'
       'Batch E VERIFIED; full 2475/2475 reachability; PR #2 Draft, NEVER MERGE.\n')
    MATDOC.write_text('# B161 V31 all 557 genuine named CERT board lock/medium size provenance\n\n'+write_md(matrix))
    print(json.dumps(dict(PASS=True,CERT=143,APPROX=249,EST=0,
       rank=150,boards=len(matrix['boards']),
       hero_lock_variants=matrix['strict_aggregate']['hero_lock_variants'],
       b50_candidate_boards=matrix['strict_aggregate']['b50_research_candidate_boards'],
       original_gto_run=GTO_RUN,real_NL2_lock_run=LOCK_RUN),ensure_ascii=False))
if __name__=='__main__': main()
