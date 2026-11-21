#!/usr/bin/env python3
"""B145 V30 gated frozen rank47 LMP 3 named-board true GTO + actor-IP NL2
CFR. NO generic texture policy and NO observed hole-card conditional rates.
This script fails closed and writes no status without 2 positive SHA-indexed
fresh B144 authentic partial NL2 sources and the original B3 GTO root pins.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v29_b142_rank88.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
PARENT26=D/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
PIN=D/'nl2_hu_b144_rank47_lmp_b3_two_gto_parent_pin.json'
OUT=D/'nl2_hu_multiboard_status_v30_b145_rank47.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v30_b145.json'
DOC=pathlib.Path('docs/NL2_HU_B145_V30_RANK47_GENUINE_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B145_V30_PER_BOARD_NL2_LOCK_MEDIUM.md')
NEW={
 'B144_R47_LMP_8s8h3d':D/'solver_evidence/NL2_MULTIBOARD_B144_R47_LMP_8s8h3d.json.gz',
 'B144_R47_LMP_9s6h3d':D/'solver_evidence/NL2_MULTIBOARD_B144_R47_LMP_9s6h3d.json.gz'}
MID='ln-iso-lmp_t_model-1oaypnl'
FLOPS={'8s8h3d','9s6h3d','KsQh4d'}
OLD_FLOPS={'KsQh4d'}
LINE='x b33 c/x'
HERO=1
GTO_RUN=44666294821

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def checked_source(key,p):
    ix=read(p.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(p.read_bytes())
    evidence=json.loads(raw)
    assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert ix['batch']==key and ix['generic_model_certification']==0
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert ix['gzip_sha256']==sha(p)
    assert evidence['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert not evidence['errors'] and evidence['source_run_id']==ix['run_id']
    assert len(evidence['artifacts'])==ix['actual_spot_flop_version_jobs']==1
    assert sum(len(a['cases']) for a in evidence['artifacts'])==ix['verified_cases']==1
    assert ix['gto_cases']==0 and ix['locked_cases']==1
    return ix,evidence

def strict_turn(proof,flop,turn):
    return [n for a in proof['artifacts'] if (a['spot'],a['flop'],a['version'])==
            ('LMP_CO_BB',flop,'exp_ip') for c in a['cases']
            if (c['flop'],c['turn'],c['flop_line'])==(flop,turn,'x b33 c')
            for n in c['nodes']
            if n['exact_node_line']==LINE and n['acting_seat']==HERO
            and n['strictly_reachable_combos']>0]

def main():
    parent=read(PARENT);frozen=read(FROZEN);p26=read(PARENT26);pin=read(PIN)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V29_B142_RANK88'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['EST'],parent['TOTAL'])==(141,251,0,392)
    assert (p26['CERT_MULTIBOARD'],p26['APPROX'])==(137,255)
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['parent_V26_sha256']==sha(PARENT26)
    assert frozen['frozen_rank_sha256']==sha(RANK)
    assert frozen['candidate_count']==255
    assert frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    assert parent['records'][MID]['label']=='APPROX'
    assert parent['records']['ln-3bp-3b_r_model-8uwbze']['label']=='CERT-MULTIBOARD'
    frozen47=next(x for x in frozen['rows'] if x['rank']==47)
    assert frozen47['model_id']==MID and frozen47['missing_real_hero_flops_to_3']==2
    assert set(frozen47['matched_real_gto_flops'])==FLOPS
    assert set(frozen47['hero_locked_flops'])==OLD_FLOPS
    assert pin['schema']=='NL2_HU_B144_RANK47_LMP_B3_TWO_PINNED_GTO_FLOP_PARENTS_V1'
    assert pin['source_run_id']==GTO_RUN and pin['target_rank']==47 and pin['target_model_id']==MID
    assert (pin['flop_action_line'],pin['turn_action_line'],pin['hero_actor_seat'])==('x b33 c','x x',HERO)
    assert pin['root_pot_bb']==2.5 and pin['root_remaining_bb']==99.0
    assert pin['preflop_ranges_source']=='ASSUMED_EXPLICIT_169CLASS'
    assert pin['full_original_B3_parent_NOT_recomputed']
    assert {x['flop'] for x in pin['two_sources']}=={'8s8h3d','9s6h3d'}
    indexes={};proofs={}
    for key,path in NEW.items():
        assert path.is_file() and path.with_suffix('').with_suffix('.index.json').is_file()
        indexes[key],proofs[key]=checked_source(key,path)
    for p in pin['two_sources']:
        flop=p['flop'];key='B144_R47_LMP_'+flop
        i=indexes[key]
        assert i['original_gto_parent_run']==GTO_RUN
        assert i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256']
        assert i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256']
        assert i['original_parent_GTO_manifest_SHA256']==p['original_manifest_sha256']
        assert i['original_B3_flop_NOT_recomputed'] is True
        assert i['exact_actor_IP_checked_turn_nodes']>0
        assert i['exact_actor_IP_strict_combos']>0
        assert i['strict_failure_reason'] is None
        assert i['flop']==flop and i['turn']==p['turn']
        assert i['actual_exact_action_line']==LINE
        assert strict_turn(proofs[key],flop,p['turn'])
        assert i['source_NL2_pool_marginal_vs_assumed_size_rates_not_private_combo_conditional']
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
              if x['rank_by_empirically_grounded_frequency_proxy']==47)
    model=next(x for x in read(STAGE)['records'] if x['model_id']==MID)
    assert rank['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('LMP_CO_BB','LMP',1)
    assert hero_seat(model['preflop_text'])==HERO
    assert model['preflop_ranges_source'].startswith('ASSUMED:')
    rank['preflop_text']=model['preflop_text']
    rank['abstract_action_history']=model['abstract_action_history']
    sources,reason=candidates(rank,gto,locked,None)
    assert reason is None,(47,reason)
    selected,why=choose_3_5(sources)
    assert why is None,(47,why)
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
    for flop in ('8s8h3d','9s6h3d'):
        x=next(x for x in selected if x['flop']==flop)
        assert x['source_run_id']==GTO_RUN
        assert any(q['run_id']==indexes['B144_R47_LMP_'+flop]['run_id'] and
                   q['version']=='exp_ip' for q in x['nl2_locked_variants'])
    out=copy.deepcopy(parent)
    out['records'][MID].update(label='CERT-MULTIBOARD',
        high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=47,
        prereg_cohort='B112_FROZEN_TWO_MISSING_REAL_HERO_FLOPS',
        certified_3_to_5_exact_flop_boards=selected,
        proven_exact_board_count=3,blocked_reason=None,
        source_credibility='B3_ORIGINAL_FULL_GTO_AND_TWO_B144_TRUE_ACTOR_IP_TURN_ONLY_NL2_SHA_AUDITED_LMP_PREFLOP_ASSUMED')
    changed={k for k in parent['records'] if parent['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(v['label']=='CERT-MULTIBOARD' for v in out['records'].values())==142
    assert sum(v['label']=='APPROX' for v in out['records'].values())==250
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47',
        CERT_MULTIBOARD=142,APPROX=250,EST=0,
        original_v29_cert=141,original_v29_approx=251,
        parent_v29_sha256=sha(PARENT),
        B112_frozen_gap_sha256=sha(FROZEN),
        B144_8s8h3d_index_sha256=sha(NEW['B144_R47_LMP_8s8h3d'].with_suffix('').with_suffix('.index.json')),
        B144_9s6h3d_index_sha256=sha(NEW['B144_R47_LMP_9s6h3d'].with_suffix('').with_suffix('.index.json')),
        source_evidence=meta,
        source_blind_expansion_ranks=[41,47,69,88,236],
        supplementary_cert_count=118,
        B145_rank47_true_two_missing_flops=dict(rank=47,model_id=MID,
             flops=sorted(FLOPS),original_GTO_run=GTO_RUN,
             new_NL2_actor_IP_lock_runs={flop:indexes['B144_R47_LMP_'+flop]['run_id'] for flop in ('8s8h3d','9s6h3d')},
             exact_action_line=LINE,
             limped_preflop_169class_assumed=True,
             original_GTO_turn_size_profile_66pct=True,
             child_NL2_current_size_tree_disclosed=True,
             no_generic_texture_certification=True),
        original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
        no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True)
    for key,index in indexes.items():
        out['independently_verified_completed_batches'][key]=dict(
            status='VERIFIED',run_id=index['run_id'],
            authentic_jobs=index['actual_spot_flop_version_jobs'],
            gto_cases=index['gto_cases'],locked_cases=index['locked_cases'],
            new_subgames=index['verified_cases'],
            gzip_sha256=index['gzip_sha256'],
            no_generic_texture_GTO=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(142,250)
    assert len(matrix['models'])==142 and len(matrix['boards'])==554
    assert matrix['strict_aggregate']['named_board_proofs']==554
    assert all(x['hero_lock_proofs'] and x['strictly_reachable_combo_count']>0
               and x['no_general_bet_size_recommendation'] for x in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V30_B145',
       parent_v30_status_sha256=sha(OUT),no_general_bet_size_advice=True,
       no_observed_private_card_conditionals=True,PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B145 V30 frozen rank47 true three-flop GTO plus actor-IP NL2 source\n\n'
       '**142 CERT-MULTIBOARD / 250 APPROX / 0 EST** of 392.\n\n'
       'Three real named flops 8s8h3d, 9s6h3d and KsQh4d. '
       'Frozen actor CO(IP) turn after flop BB x / CO b33 / BB c and BB turn x. '
       'Original B3 GTO root 44666294821 SHA-pinned for first two flops; '
       'B144 new genuine Rust NL2 partial turn locks only, no fabricated re-solved GTO flop.\n'
       'CO limp 169-class preflop profile **assumed, not measured**. '
       'NL2 pooled marginal villain rates observed where available; defaults and no private-card conditional claims '
       'remain explicit. Original B3 GTO turn sizing (66% only) and new NL2 turn subtree sizing '
       '(50/100%) are disclosed, not described as identical trees.\n'
       'Per-board 50% pot flag is research, not blanket sizing. '
       'Batch E VERIFIED, 2475/2475 river audit, PR #2 Draft, NEVER MERGE.\n')
    MATDOC.write_text('# B145 V30 every named board hero lock/50% pot provenance\n\n'+write_md(matrix))
    print(json.dumps({'PASS':True,'CERT':142,'APPROX':250,'EST':0,'rank':47,
        'named_boards':len(matrix['boards']),
        'hero_lock_variants':matrix['strict_aggregate']['hero_lock_variants'],
        'b50_candidate_boards':matrix['strict_aggregate']['b50_research_candidate_boards'],
        'original_GTO_run':GTO_RUN,'B144_source_runs':{k:v['run_id'] for k,v in indexes.items()}}))
if __name__=='__main__':main()
