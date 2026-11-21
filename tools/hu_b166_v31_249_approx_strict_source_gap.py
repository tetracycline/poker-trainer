#!/usr/bin/env python3
"""B166: independently recompute all CURRENT V31 249 APPROX missing source
gaps from ORIGINAL frozen B112 ranks plus only genuine SHA-audited B156/
B158 new full GTO and B164 new NL2 actor-IP partial sources.

Never automatically CERT. Correct actor, full action history and strict
sequential legal private-card combo reach matter; the mere existence of an
unweighted Rust action node is not GTO evidence. Distinguish observed NL2
POOLED marginal rates, assumed defaults, historically unknown sources.
"""
import collections,copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat,texture
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data')
PARENT=D/'nl2_hu_multiboard_status_v31_b161_rank150.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v31_b161.json'
FROZEN=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
PARENT26=D/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
QUEUE=D/'nl2_hu_stage2_queue.json'
B154=D/'solver_evidence/NL2_MULTIBOARD_B154_R46_4S4H2D_GTO.json.gz'
NEW={
 'B156_R71_KS7H2D_GTO':D/'solver_evidence/NL2_MULTIBOARD_B156_R71_KS7H2D_GTO.json.gz',
 'B158_R313_KS7H2D_GTO':D/'solver_evidence/NL2_MULTIBOARD_B158_R313_KS7H2D_GTO.json.gz',
 'B164_R80_B9_ORIGINAL_EXP_IP':D/'solver_evidence/NL2_MULTIBOARD_B164_R80_B9_ORIGINAL_EXP_IP.json.gz'}
OUT=D/'nl2_hu_b166_v31_249_APPROX_true_sourceblind_gaps.json'
DOC=pathlib.Path('docs/NL2_HU_B166_ALL_249_APPROX_V31_STRICT_SOURCE_GAPS.md')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked_source(key,p):
    assert p.is_file() and p.with_suffix('').with_suffix('.index.json').is_file()
    ix=read(p.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(p.read_bytes());e=json.loads(raw)
    assert ix['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert ix['batch']==key
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert ix['gzip_sha256']==sha(p)
    assert (ix.get('generic_model_certification')==0 or
            ix.get('no_generic_model_certification') is True),('no generic GTO',key)
    assert ix['immediate_CERT_upgrades']==0
    assert e['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert e['source_run_id']==ix['run_id'] and not e['errors']
    assert len(e['artifacts'])==ix['actual_spot_flop_version_jobs']==1
    assert ix['verified_cases']==sum(len(a['cases']) for a in e['artifacts'])==1
    assert ix['gto_cases']==sum(a['version']=='gto' for a in e['artifacts'])
    assert ix['locked_cases']==sum(a['version']!='gto' for a in e['artifacts'])
    return ix,e
def main():
    parent=read(PARENT);matrix=read(MATRIX);frozen=read(FROZEN)
    rank=read(RANK);queue=read(QUEUE)
    assert parent['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150'
    assert (parent['CERT_MULTIBOARD'],parent['APPROX'],parent['EST'],parent['TOTAL'])==(143,249,0,392)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'],matrix['EST'])==(143,249,0)
    assert matrix['parent_v31_status_sha256']==sha(PARENT)
    assert len(matrix['boards'])==557 and len(matrix['models'])==143
    assert matrix['strict_aggregate']['named_board_proofs']==557
    assert matrix['strict_aggregate']['hero_lock_variants']==649
    assert matrix['strict_aggregate']['b50_research_candidate_boards']==131
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['candidate_count']==len(frozen['rows'])==255
    assert frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    p26=read(PARENT26)
    assert frozen['parent_V26_sha256']==sha(PARENT26)
    assert frozen['frozen_rank_sha256']==sha(RANK)
    assert (p26['CERT_MULTIBOARD'],p26['APPROX'])==(137,255)
    assert parent['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    assert parent['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    assert parent['records']['ln-iso-lmp_r_model-4ys53a']['label']=='CERT-MULTIBOARD'
    assert parent['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert parent['records']['ln-iso-lmp_r_model-wpg493']['label']=='APPROX'
    assert parent['records']['ln-iso-lmp_r_model-17pklmg']['label']=='APPROX'
    b154idx=read(B154.with_suffix('').with_suffix('.index.json'))
    assert b154idx['batch']=='B154_R46_4S4H2D_GTO'
    assert b154idx['exact_target_actor_IP_strict_combos']==0
    assert b154idx['source_sha256']==hashlib.sha256(gzip.decompress(B154.read_bytes())).hexdigest()
    idx={};proofs={}
    for key,p in NEW.items():idx[key],proofs[key]=checked_source(key,p)
    assert (idx['B156_R71_KS7H2D_GTO']['run_id'],
            idx['B156_R71_KS7H2D_GTO']['gto_cases'],
            idx['B156_R71_KS7H2D_GTO']['locked_cases'])==(44860317844,1,0)
    assert idx['B156_R71_KS7H2D_GTO']['exact_target_actor_OOP_river_nodes']==0
    assert idx['B156_R71_KS7H2D_GTO']['exact_target_actor_OOP_strict_combos']==0
    assert (idx['B158_R313_KS7H2D_GTO']['run_id'],
            idx['B158_R313_KS7H2D_GTO']['gto_cases'],
            idx['B158_R313_KS7H2D_GTO']['locked_cases'])==(44860436462,1,0)
    assert (idx['B164_R80_B9_ORIGINAL_EXP_IP']['run_id'],
            idx['B164_R80_B9_ORIGINAL_EXP_IP']['gto_cases'],
            idx['B164_R80_B9_ORIGINAL_EXP_IP']['locked_cases'])==(44861858112,0,1)
    assert idx['B164_R80_B9_ORIGINAL_EXP_IP']['frozen_rank']==80
    assert idx['B164_R80_B9_ORIGINAL_EXP_IP']['exact_actor_IP_river_nodes']>0
    assert idx['B164_R80_B9_ORIGINAL_EXP_IP']['exact_actor_IP_strict_combos']>0
    assert idx['B164_R80_B9_ORIGINAL_EXP_IP']['strict_failure_reason'] is None
    source_files=[pathlib.Path(p) for p in parent['source_evidence']['source_files']]
    assert source_files and len(set(source_files))==len(source_files)
    assert B154 in source_files
    assert all(p.is_file() for p in source_files)
    for p in NEW.values():
        assert p not in source_files
        source_files.append(p)
    assert len(set(source_files))==len(source_files)
    gto,locked,meta=build_source_index(D,source_files)
    rank_by_number={x['rank_by_empirically_grounded_frequency_proxy']:x for x in rank['nodes']}
    stage_by_model={x['model_id']:x for x in queue['records']}
    counts=collections.Counter();rows=[];ready=[]
    for old in sorted(frozen['rows'],key=lambda z:z['rank']):
        r=old['rank'];mid=old['model_id']
        assert mid==rank_by_number[r]['model_id']
        current=parent['records'][mid]
        if current['label']=='CERT-MULTIBOARD':
            counts['original_B112_APPROX_ALREADY_PROMOTED']+=1
            continue
        assert current['label']=='APPROX'
        m=stage_by_model[mid]
        assert (m['solver_profile'],m['family'],m['street'])==(old['spot'],old['family'],old['street'])
        node=copy.deepcopy(rank_by_number[r])
        node['preflop_text']=m['preflop_text']
        node['abstract_action_history']=m['abstract_action_history']
        possibilities,reason=candidates(node,gto,locked,None)
        GTOflops=sorted({x['flop'] for x in possibilities})
        paired=sorted({x['flop'] for x in possibilities if x['nl2_locked_variants']})
        missing=max(0,3-len(paired))
        selected,why=choose_3_5(possibilities)
        gate_pass=bool(selected and not reason and not why)
        if gate_pass:
            ready.append(dict(rank=r,model_id=mid,matched=paired,
                              selected_flops=sorted(z['flop'] for z in selected)))
        counts['current_APPROX']+=1
        counts['zero_GTO_candidates']+=int(not possibilities)
        counts['one_true_hero_locked_flop_short']+=int(missing==1)
        counts['two_true_hero_locked_flops_short']+=int(missing==2)
        counts['three_or_more_true_hero_locked_flops_short']+=int(missing>=3)
        counts['missing_actor_correct_NL2_locks_on_valid_GTO_flops']+=len(set(GTOflops)-set(paired))
        rows.append(dict(rank=r,model_id=mid,family=old['family'],spot=old['spot'],
          street=old['street'],estimated_model_SPR=old['model_spr'],
          frozen_frequency_proxy=old['frozen_frequency_proxy'],
          hero_actor_seat=hero_seat(node['preflop_text']),
          abstract_action_history=old['abstract_history'],
          authentic_GTO_STRICT_legal_flops=GTOflops,
          actually_paired_genuine_NL2_hero_locked_flops=paired,
          remaining_distinct_matched_flops_to_3=missing,
          missing_actor_correct_NL2_locks_on_existing_GTO=sorted(set(GTOflops)-set(paired)),
          matched_real_textures=sorted({texture(z) for z in paired}),
          current_blocker=None if gate_pass else why or reason or 'INSUFFICIENT_REAL_MATCHED_SOURCE',
          certified_3_to_5_now=gate_pass,
          GTO_exploitability_max_pct=0.5,SPR_relative_error_max_pct=5,
          no_empirical_NL2_private_card_conditional_action_rates=True,
          no_generic_texture_or_bucket_CERT=True))
    assert counts['current_APPROX']==len(rows)==249
    assert counts['original_B112_APPROX_ALREADY_PROMOTED']==6
    assert len({x['model_id'] for x in rows})==249
    assert sum(x['certified_3_to_5_now'] for x in rows)==len(ready)
    assert all(x['model_id']!='ln-iso-lmp_r_model-vlgh2t' or
             x['remaining_distinct_matched_flops_to_3']>=1 for x in rows)
    assert all(x['model_id']!='ln-iso-lmp_r_model-17pklmg' or
             '4s4h2d' in x['actually_paired_genuine_NL2_hero_locked_flops']
             for x in rows)
    independent=audit(parent);agg=independent['aggregate']
    assert agg['named_board_proofs']==557 and agg['paired_hero_locked_source_variants']==649
    assert agg['board_examples_with_b50_candidate']==131
    assert independent['not_generalized_handclass_GTO'] and independent['not_actual_NL2_earnings']
    out=dict(schema='NL2_HU_B166_V31_249_APPROX_SOURCE_BLIND_GTO_NL2_GAP_AUDIT_V1',
      parent_V31_sha256=sha(PARENT),B112_frozen_sha256=sha(FROZEN),
      added_original_source_indexes_sha256={
        key:sha(path.with_suffix('').with_suffix('.index.json')) for key,path in NEW.items()},
      source_file_count=len(source_files),source_index_summary=meta,
      CERT_MULTIBOARD=143,APPROX=249,EST=0,TOTAL=392,
      existing_named_exact_boards=557,existing_hero_lock_source_variants=649,
      exactly_supported_b50_nonpolar_candidate_boards=131,
      source_blind_real_certification_ready_rows=ready,
      rows=rows,row_count=len(rows),frequency_gap_counts=dict(counts),
      original_B156_rank71_strict_OOP_GTO_RIVER_ZERO=True,
      original_B154_rank46_strict_IP_GTO_TURN_ZERO=True,
      no_automatic_MODEL_CERT_upgrade=True,no_generic_TEXTURE_GTO=True,
      no_false_observed_private_card_NL2_conditional_rate=True,
      PR2_remains_draft_never_merge=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    lines=['# B166 | refreshed complete V31 249 high-frequency APPROX strict source gaps','',
      '**143 CERT-MULTIBOARD /249 APPROX /0 EST** of 392. '
      '**557** exact named verified GTO/NL2 boards, **649** genuinely actor-locked NL2 source variants, '
      '**131** exact-board 50% pot nonpolar research flags.','',
      'This source-blind check adds only independently authenticated B156, B158 original GTO '
      'and B164 true actor-IP NL2 partial sources. Original B154 genuine GTO strict-zero '
      'source is already in V31; no original source is overwritten. '
      'All candidates require 3–5 different flops, >=2 genuine textures, '
      'correct actor, exact action lineage, full sequential combo reach, '
      'GTO <=0.5%, SPR within 5%, and matched NL2 actor-locked source.','',
      'B156 rank71 Ks7h2d/9d original GTO had **zero legal actor-OOP river combo** '
      'despite syntactically existing action nodes, not used to certify.','',
      f"Rechecked {counts['current_APPROX']} current APPROX; B112 promoted rows: {counts['original_B112_APPROX_ALREADY_PROMOTED']}. "
      f"Independently 3-board source-ready rows: {len(ready)}.",'',
      '| frequency rank | model | strict genuine GTO boards | genuine matched NL2 hero-locked boards | remaining to 3 |',
      '| ---: | --- | --- | --- | ---: |']
    for x in rows[:40]:
        lines.append('| '+str(x['rank'])+' | '+x['model_id']+' | '+
          (', '.join(x['authentic_GTO_STRICT_legal_flops']) or 'none')+
          ' | '+(', '.join(x['actually_paired_genuine_NL2_hero_locked_flops']) or 'none')+
          ' | '+str(x['remaining_distinct_matched_flops_to_3'])+' |')
    lines.extend(['','Complete 249-row current sourceblind file: '+str(OUT)+'.',
      'Original LMP limped 169-class starting preflop distribution explicitly ASSUMED. '
      'No NL2 private-card conditional measured rates are claimed. '
      'All 557 original CERT source scopes and 2475/2475 river links must be re-audited before PR2 commit.',
      'Draft PR2, NEVER MERGE.',''])
    DOC.parent.mkdir(parents=True,exist_ok=True)
    DOC.write_text('\n'.join(lines))
    print(json.dumps(dict(PASS=True,CERT=143,APPROX=249,EST=0,
        sources=len(source_files),ready=len(ready),gaps=dict(counts),
        B158_strict_IP_GTO_nodes=idx['B158_R313_KS7H2D_GTO']['exact_target_actor_IP_river_nodes'],
        B158_strict_IP_GTO_combos=idx['B158_R313_KS7H2D_GTO']['exact_target_actor_IP_strict_combos'],
        B164_rank80_real_NL2_strict_IP_combos=idx['B164_R80_B9_ORIGINAL_EXP_IP']['exact_actor_IP_strict_combos'],
        output_sha256=sha(OUT)),ensure_ascii=False))
if __name__=='__main__':main()
