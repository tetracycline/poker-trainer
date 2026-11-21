#!/usr/bin/env python3
"""TASK-HYBRID B133. Promote only B112-frozen rank69 after three different
named-flop full-street exact hero-IP GTO AND genuine NL2 source matches.
Preflop is pinned BTN_BB CFR, not inferred pool hole-card action rates.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
D=pathlib.Path('data')
BASE=D/'nl2_hu_multiboard_status_v27_b123_r41_236.json'
BASE26=D/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
OUT=D/'nl2_hu_multiboard_status_v28_b133_rank69.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v28_b133.json'
DOC=pathlib.Path('docs/NL2_HU_B133_V28_RANK69_THIRD_FLOP_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B133_V28_NAMED_BOARD_NODE_LOCK_MEDIUM.md')
SOURCES={
 'B129_R69_BTN_B33XX': D/'solver_evidence/NL2_MULTIBOARD_B129_R69_BTN_B33XX.json.gz',
 'B132_R69_GTO_B124': D/'solver_evidence/NL2_MULTIBOARD_B132_R69_GTO_B124.json.gz'
}
MID='ln-ipfr-r_model-159a6z6'
TARGET={'rank':69,'model_id':MID,'spot':'BTN_BB','family':'SRP',
        'street':2,'seat':1,'line':'b33 c/x x/x','new_flop':'As7h3d',
        'old_flops':{'Jh9d6s','KsQh4d'},
        'all_flops':{'As7h3d','Jh9d6s','KsQh4d'}}
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_source(batch,p):
    idx=read(p.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(p.read_bytes())
    d=json.loads(raw)
    assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert idx['batch']==batch and idx.get('generic_model_certification',0)==0
    assert idx['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert idx['gzip_sha256']==digest(p)
    assert d['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert d['source_run_id']==idx['run_id'] and not d['errors']
    assert len(d['artifacts'])==idx['actual_spot_flop_version_jobs']
    assert sum(len(a['cases']) for a in d['artifacts'])==idx['verified_cases']
    assert sum(a['version']=='gto' for a in d['artifacts'])==idx['gto_cases']
    assert sum(a['version']!='gto' for a in d['artifacts'])==idx['locked_cases']
    return idx,d
def legal_nodes(source,version):
    return [n for a in source['artifacts'] if a['version']==version
        for c in a['cases'] if c['flop']==TARGET['new_flop']
        and c['flop_line']=='b33 c' and c['turn']=='Kd'
        for n in c['nodes'] if n['exact_node_line']==TARGET['line']
        and n['acting_seat']==TARGET['seat']
        and n['strictly_reachable_combos']>0]
def main():
    base=read(BASE);old26=read(BASE26);frozen=read(FROZEN)
    assert base['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V27_B123_R41_236'
    assert (base['CERT_MULTIBOARD'],base['APPROX'],base.get('EST',0),base['TOTAL'])==(139,253,0,392)
    assert (old26['CERT_MULTIBOARD'],old26['APPROX'])==(137,255)
    assert base['records'][MID]['label']=='APPROX'
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['parent_V26_sha256']==digest(BASE26)
    assert frozen['frozen_rank_sha256']==digest(RANK)
    assert frozen['candidate_count']==255 and frozen['one_board_short_count']==6
    assert frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    fr=next(x for x in frozen['rows'] if x['rank']==69)
    assert fr['model_id']==MID and fr['missing_real_hero_flops_to_3']==1
    assert set(fr['hero_locked_flops'])==TARGET['old_flops']
    assert TARGET['new_flop'] not in TARGET['old_flops']
    idx={};proof={}
    for batch,p in SOURCES.items():
        assert p.is_file() and p.with_suffix('').with_suffix('.index.json').is_file()
        idx[batch],proof[batch]=load_source(batch,p)
    g=idx['B132_R69_GTO_B124'];l=idx['B129_R69_BTN_B33XX']
    assert (g['run_id'],g['gto_cases'],g['locked_cases'])==(44839543260,1,0)
    assert (l['run_id'],l['gto_cases'],l['locked_cases'])==(44840873316,0,1)
    assert g['strict_dual_policy_hero_IP_river_confirmed'] is True
    assert g['exact_GTO_hero_IP_river_nodes']>0
    assert l['exact_actor_IP_river_nodes']>0 and l['strict_failure_reason'] is None
    assert l['original_gto_parent_run']==g['run_id']
    assert g['original_GTO_root_SHA256']==l['original_parent_GTO_root_SHA256']
    assert legal_nodes(proof['B132_R69_GTO_B124'],'gto')
    assert legal_nodes(proof['B129_R69_BTN_B33XX'],'exp_ip')
    assert base['records']['ln-ipfr-t_model-sxr0qa']['label']=='CERT-MULTIBOARD'
    assert base['records']['ln-ipc-r_model-1nz4lt1']['label']=='CERT-MULTIBOARD'
    assert base['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    assert base['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    srcfiles=[pathlib.Path(q) for q in base['source_evidence']['source_files']]
    assert srcfiles and all(p.is_file() for p in srcfiles)
    srcfiles+=list(SOURCES.values())
    assert len(srcfiles)==len(set(srcfiles)), 'Duplicated exact source files'
    gto,locked,meta=build_source_index(D,srcfiles)
    node=next(copy.deepcopy(x) for x in read(RANK)['nodes']
              if x['rank_by_empirically_grounded_frequency_proxy']==69)
    model=next(x for x in read(STAGE)['records'] if x['model_id']==MID)
    assert node['model_id']==MID
    assert (model['solver_profile'],model['family'],model['street'])==('BTN_BB','SRP',2)
    assert hero_seat(model['preflop_text'])==1
    assert model['preflop_ranges_source'].startswith('PRE_FLOP_CFR:')
    node['preflop_text']=model['preflop_text']
    node['abstract_action_history']=model['abstract_action_history']
    choices,reason=candidates(node,gto,locked,None)
    assert reason is None,(69,reason)
    chosen,reason=choose_3_5(choices)
    assert reason is None,(69,reason)
    assert len(chosen)==3 and {x['flop'] for x in chosen}==TARGET['all_flops']
    assert len({x['flop_texture'] for x in chosen})>=2
    for b in chosen:
        assert b['acting_seat']==1 and b['actual_exact_action_line']==TARGET['line']
        assert b['strict_full_street_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct'] is not None
        assert b['genuine_gto_exploitability_pct']<=0.5
        assert b['relative_spr_error_pct']<=5
        assert not b['assumed_preflop_ranges'], 'BTN 100bb pinned CFR cannot borrow assumed LMP range'
        assert b['nl2_locked_variants']
        assert any(q['version']=='exp_ip' for q in b['nl2_locked_variants'])
        assert b['exact_combo_reachable']>0
    third=next(x for x in chosen if x['flop']==TARGET['new_flop'])
    assert third['source_run_id']==g['run_id']
    assert any(x['run_id']==l['run_id'] and x['version']=='exp_ip'
               for x in third['nl2_locked_variants'])
    assert third['actual_spr']>0
    out=copy.deepcopy(base)
    out['records'][MID].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=69,
        prereg_cohort='B112_FROZEN_SIX_ONE_BOARD_SHORT',
        certified_3_to_5_exact_flop_boards=chosen,proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility='B124_TRUE_GTO_RUST_PLUS_B129_TRUE_HERO_IP_NL2_CHILD_SHA_INDEPENDENT')
    changed={k for k in base['records'] if base['records'][k]!=out['records'][k]}
    assert changed=={MID}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in out['records'].values())==140
    assert sum(x['label']=='APPROX' for x in out['records'].values())==252
    assert all(x['label'] in ('CERT-MULTIBOARD','APPROX') for x in out['records'].values())
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V28_B133_RANK69',
       CERT_MULTIBOARD=140,APPROX=252,EST=0,
       original_v27_cert=139,original_v27_approx=253,
       parent_v27_sha256=digest(BASE),parent_v26_sha256=digest(BASE26),
       B112_frozen_gap_sha256=digest(FROZEN),
       B129_source_index_sha256=digest(SOURCES['B129_R69_BTN_B33XX'].with_suffix('').with_suffix('.index.json')),
       B132_source_index_sha256=digest(SOURCES['B132_R69_GTO_B124'].with_suffix('').with_suffix('.index.json')),
       source_evidence=meta,source_blind_expansion_ranks=[41,69,236],
       supplementary_cert_count=116,
       B133_rank69_true_third_flop=dict(
         model_id=MID,rank=69,flops=sorted(TARGET['all_flops']),
         original_GTO_run=g['run_id'],actual_hero_IP_NL2_run=l['run_id'],
         source_policy='ORIGINAL_GTO_ON_SAME_EXACT_ACTION_NODE_AND_NL2_HERO_IP_TRUE_CHILD',
         certified_generic_textures=False),
       original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
       no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True)
    for k,ix in idx.items():
        out['independently_verified_completed_batches'][k]=dict(
            status='VERIFIED',run_id=ix['run_id'],
            authentic_jobs=ix['actual_spot_flop_version_jobs'],
            gto_cases=ix['gto_cases'],locked_cases=ix['locked_cases'],
            new_subgames=ix['verified_cases'],gzip_sha256=ix['gzip_sha256'],
            no_generic_texture_GTO=True)
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(140,252)
    assert len(matrix['models'])==140
    assert len(matrix['boards'])==548 and matrix['strict_aggregate']['named_board_proofs']==548
    assert all(q['hero_lock_proofs'] and q['strictly_reachable_combo_count']>0
               and q['no_general_bet_size_recommendation'] for q in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V28_B133',
       parent_v28_status_sha256=digest(OUT),
       no_general_bet_size_advice=True,no_observed_private_card_conditionals=True,
       PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B133 V28: frozen rank69 authentic three-flop certificate\n\n'
       '**140 CERT-MULTIBOARD / 252 APPROX / 0 EST** of 392.\n\n'
       'BTN_BB SRP rank69 exact actor-IP river action b33 c/x x/x. '
       'Exact flop proofs: As7h3d, Jh9d6s, KsQh4d. '
       'As7h3d original GTO B124 run 44839543260, authentic NL2 actor-IP '
       'turn/river Rust B129 run 44840873316, same SHA-pinned flop parent.\n\n'
       'No texture-wide generalized GTO, no measured per-private-card NL2 action '
       'conditional. 50% pot markers indicate per-board research evidence, not '
       'an unconditional size recommendation. Other incomplete ranks 71,88,313 '
       'stay APPROX. Batch E VERIFIED and 2475/2475 river path contract unchanged.\n'
       'Draft PR #2, NEVER MERGE.\n')
    MATDOC.write_text('# B133 V28 per-board node-lock and nonpolar 50% pot evidence\n\n'+write_md(matrix))
    print(json.dumps({'PASS':True,'CERT':140,'APPROX':252,'EST':0,
       'new_rank':69,'new_named_boards':3,'total_named_boards':len(matrix['boards']),
       'hero_lock_variants':matrix['strict_aggregate']['hero_lock_variants'],
       'b50_research_candidate_boards':matrix['strict_aggregate']['b50_research_candidate_boards'],
       'gto_source_run':g['run_id'],'hero_IP_source_run':l['run_id']}))
if __name__=='__main__':
    main()
