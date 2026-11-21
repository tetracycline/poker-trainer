#!/usr/bin/env python3
"""V43 rank60 one-cell promotion: 3 DISTINCT SHA-verified genuine GTO public flops,
separate exact actor-IP NL2 Rust partial locks, >=2 flop texture classes,
100bb CO_BB x b50 c/x, 40/70 sequential hands and SPR8.614 +-5%.

Requires immutable B311 historical B2 GTO+NL2 actor evidence, B261 original GTO
plus B304 true Rust NL2, and a successful B314/B315 original GTO plus separately
verified genuine downstream NL2 partial Rust child. Never claim observed NL2
private-hand conditional action frequencies, full tree locked policy, or any
generic betting recommendation.
"""
import argparse,copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import texture
from hu_cert_lock_medium_coverage_matrix import create,write_md
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data');DOC=pathlib.Path('docs')
MID='ln-ipfr-t_model-hxdit'
SPOT='CO_BB';LINE='x b50 c/x';SPR=8.614
PARENT=D/'nl2_hu_multiboard_status_v42_b289_rank46.json'
STATUS=D/'nl2_hu_multiboard_status_v43_b319_rank60.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v43_b319.json'
PROOF=D/'nl2_hu_b319_rank60_three_true_GTO_NL2_source_gate.json'
THIRDS={
 'B314':dict(flop='8s7h4d',run=44959459086),
 'B315':dict(flop='KsJh4d',run=44959462500),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ld(p):return json.loads(p.read_text())
def raw_source(p,idx):
    b=p.read_bytes()
    assert sha(p)==idx['gzip_sha256']
    raw=gzip.decompress(b)
    assert hashlib.sha256(raw).hexdigest()==idx['source_sha256']
    return json.loads(raw)
def source_case(data,flop,turn,version,expected_sha=None):
    matches=[]
    for art in data['artifacts']:
        if (art['spot'],art['flop'],art['version'])!=(SPOT,flop,version):continue
        assert not art.get('errors')
        for c in art['cases']:
            if (c['flop_line'],c['turn'])!=('x b50 c',turn):continue
            if expected_sha and c['source_sha256']!=expected_sha:continue
            matches.append(c)
    assert len(matches)==1,('source evidence missing or ambiguous',flop,turn,version,len(matches))
    c=matches[0]
    assert c['flop_root_pot_bb']==5.5 and c['flop_root_stack_bb']==97.5
    assert c['source_sha256'] and len(c['source_sha256'])==64
    return c
def actor_nodes(case):
    return [n for n in case['nodes'] if
       n['exact_node_line']==LINE and n['acting_seat']==1 and len(n['public_board'])==8
       and n['strictly_reachable_combos']>0
       and abs(n['node_spr']-SPR)/SPR<=.05]
def sample(c,flop,turn,run,lock_run,lock_sha,scope):
    assert c['run_id']==run
    assert c['gto_exploitability_pct'] is not None and 0<=c['gto_exploitability_pct']<=.5
    assert c['flop_line']=='x b50 c' and c['turn']==turn
    nodes=actor_nodes(c)
    assert len(nodes)==1,('not exactly one legal original GTO turn hero node',flop,len(nodes))
    n=nodes[0]
    assert len(n['public_board'])==8 and n['public_board'].endswith(turn)
    assert n['source_reachable_combos']>=n['strictly_reachable_combos']>0
    assert n['source_actions']
    assert run>0 and lock_run>0 and len(lock_sha)==64
    medium=int(n.get('medium_50pct_eligible_combos') or 0)
    research=bool(n.get('b50_nonpolarized_relative_equity_research_candidate',False))
    if research:assert medium>0
    # Pool measured marginals are not observed private-hand NL2 action conditionals.
    # UNKNOWN historical / partial downstream node source denominators stay null.
    lock=dict(version='exp_ip',run_id=lock_run,sha256=lock_sha,
      source_scope=scope,
      villain_observed_pattern_node_share_pct=None,
      source_not_real_per_combo_observation=True,
      unknown_history_frequency_filled_with_default=True,
      observed_marginal_source_nodes=None,assumed_default_source_nodes=None,
      unlocked_source_nodes=None,hero_model_gain_bb=None)
    return dict(flop=flop,turn=turn,public_board=n['public_board'],
      actual_exact_action_line=LINE,acting_seat=1,exact_flop_action='x b50 c',
      actual_pot_bb=n['pot_bb'],actual_effective_stack_bb=n['remaining_bb'],
      actual_spr=n['node_spr'],model_assumed_spr=SPR,
      relative_spr_error_pct=round(100*abs(n['node_spr']-SPR)/SPR,5),
      genuine_gto_exploitability_pct=c['gto_exploitability_pct'],
      source_run_id=run,source_sha256=c['source_sha256'],
      source_kind=c['empirical_scope'],assumed_preflop_ranges=False,
      exact_combo_reachable=n['source_reachable_combos'],
      strict_full_street_combo_reachable=n['strictly_reachable_combos'],
      exact_node_actions=n['source_actions'],
      medium_50pct_eligible_combos=medium,
      b50_nonpolarized_relative_equity_research_candidate=research,
      flop_texture=texture(flop),nl2_locked_variants=[lock])
def historic_first():
    ixp=D/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.index.json'
    gz=D/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.json.gz'
    ix=ld(ixp)
    assert (ix['run_id'],ix['gto_cases'],ix['locked_cases'],ix['verified_cases'])==(44666290556,65,166,231)
    src=raw_source(gz,ix)
    assert src['source_run_id']==44666290556 and not src['errors']
    auditfile=D/'nl2_hu_b311_rank60_historic_B2_real_coip_actor_source.json'
    h=ld(auditfile)
    assert h['schema']=='NL2_HU_B311_RANK60_HISTORIC_B2_TRUE_GTO_PLUS_ACTOR_NL2_V1'
    assert h['paired_original_exact_flop_actor_SPR_source']
    assert h['V42_593_and_HU2475_Independent_audit_PASS']
    assert (h['flop'],h['turn'],h['rank'],h['original_run'])==('Js9h4d','Ts',60,44666290556)
    assert h['original_B2_partial_archive_sha256']==sha(gz)
    g=source_case(src,'Js9h4d','Ts','gto',h['original_gto_case_sha256'])
    e=source_case(src,'Js9h4d','Ts','exp_ip',h['actual_original_NL2_partial_actor_case_sha256'])
    assert g['gto_exploitability_pct']<=.5
    assert sum(n['strictly_reachable_combos'] for n in actor_nodes(g))==20
    assert sum(n['strictly_reachable_combos'] for n in actor_nodes(e))==h['actual_NL2_actor_matched_SPR_40_70_combos']>0
    return sample(g,'Js9h4d','Ts',44666290556,44666290556,e['source_sha256'],
      'HISTORICAL_B2_AUTHENTIC_ACTOR_IP_POOL_PARTIAL_NL2_LOCK_UNKNOWN_NODE_SOURCE_DENOMINATORS'),dict(
        proof_run=44666290556,historic_proof_sha256=sha(auditfile),
        GTO_source_sha256=g['source_sha256'],NL2_source_sha256=e['source_sha256'],
        GTO_strict=20,NL2_strict=h['actual_NL2_actor_matched_SPR_40_70_combos'])
def newer_pair(batch,flop,run):
    pinfile=D/f'nl2_hu_{batch.lower()}_rank60_cobb_{flop}_gto_parent_pin.json'
    gip=D/f'solver_evidence/NL2_MULTIBOARD_{batch}_R60_{flop.upper()}_GTO.index.json'
    ggz=D/f'solver_evidence/NL2_MULTIBOARD_{batch}_R60_{flop.upper()}_GTO.json.gz'
    pin,gidx=ld(pinfile),ld(gip)
    assert (pin['source_run_id'],gidx['run_id'],gidx['verified_cases'],gidx['gto_cases'],gidx['locked_cases'])==(run,run,1,1,0)
    assert (pin['target_rank'],pin['model_id'],pin['spot'],pin['flop'])==(60,MID,SPOT,flop)
    assert (pin['flop_line'],pin['turn_line'])==('x b50 c','x')
    assert pin['preflop_CFR_pinned_not_observed_NL2_private_card']
    assert pin['original_full_100bb_cobb_gto_source_pinned'] and not pin['direct_nl2_lock_source_present']
    assert pin['target_exact_actor_IP_turn_nodes']>0 and pin['target_exact_actor_IP_turn_strict_combos']>0
    assert gidx['exact_target_actor_IP_turn_strict_combos']==pin['target_exact_actor_IP_turn_strict_combos']
    assert (gidx['original_parent_GTO_root_SHA256'],gidx['original_parent_GTO_job_SHA256'],
        gidx['original_parent_GTO_manifest_SHA256'])==(
        pin['original_gto_root_sha256'],pin['original_gto_job_sha256'],pin['original_gto_manifest_sha256'])
    gsrc=raw_source(ggz,gidx)
    gc=source_case(gsrc,flop,pin['turn'],'gto')
    assert gc['run_id']==run and gc['gto_exploitability_pct']<=.5
    assert sum(n['strictly_reachable_combos'] for n in actor_nodes(gc))==pin['target_exact_actor_IP_turn_strict_combos']
    ipath=D/f'solver_evidence/NL2_MULTIBOARD_B255_R60_{flop.upper()}_EXP_IP.index.json'
    rgz=D/f'solver_evidence/NL2_MULTIBOARD_B255_R60_{flop.upper()}_EXP_IP.json.gz'
    i=ld(ipath)
    assert i['schema']=='NL2_HU_B257_CO_BB_EXACT_ORIGINAL_GTO_PLUS_REAL_NL2_IP_PARTIAL_LOCK_V1'
    assert (i['rank'],i['model_id'],i['spot'],i['flop'],i['turn'])==(60,MID,SPOT,flop,pin['turn'])
    assert (i['actor'],i['acting_seat'],i['exact_line'],i['model_SPR'])==('CO_IP',1,LINE,SPR)
    assert i['original_GTO_source_run']==run
    assert i['gto_pin_sha256']==sha(pinfile)
    assert i['gto_index_sha256']==sha(gip)
    assert i['gto_archive_sha256']==sha(ggz)
    assert i['original_GTO_actor_strict_combos']==pin['target_exact_actor_IP_turn_strict_combos']
    assert i['authentic_NL2_Rust_gzip_sha256']==sha(rgz)
    assert i['authentic_NL2_Rust_source_sha256']==hashlib.sha256(gzip.decompress(rgz.read_bytes())).hexdigest()
    assert i['source_run_id']>0 and i['source_run_id']!=run
    assert i['NL2_actor_strict_combos']>0 and i['NL2_actor_model_SPR_eligible_combos']>0
    assert i['genuine_actor_matched_GTO_NL2_board']
    assert i['no_observed_per_private_hand_NL2_conditionals'] and i['partial_downstream_only_not_whole_flop_lock']
    assert i['no_generic_CERT_upgrade'] and i['PR2_Draft_NEVER_MERGE']
    return sample(gc,flop,pin['turn'],run,i['source_run_id'],i['authentic_NL2_Rust_source_sha256'],
        'TURN_RIVER_ONLY_SHA_GTO_PARENT_PLUS_GENUINE_RUST_NL2_ACTOR_IP_PARTIAL_LOCK_UNKNOWN_RATE_DENOMINATORS'),dict(
        original_GTO_run=run,original_GTO_source_sha256=gc['source_sha256'],
        original_GTO_pin_sha256=sha(pinfile),original_GTO_index_sha256=sha(gip),
        true_NL2_Rust_run=i['source_run_id'],
        true_NL2_index_sha256=sha(ipath),true_NL2_raw_sha256=i['authentic_NL2_Rust_source_sha256'],
        GTO_actor_strict=i['original_GTO_actor_strict_combos'],
        NL2_actor_strict=i['NL2_actor_strict_combos'],
        NL2_actor_model_SPR_strict=i['NL2_actor_model_SPR_eligible_combos'])
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--third',choices=tuple(THIRDS),required=True)
    a=ap.parse_args()
    third=THIRDS[a.third]
    old=ld(PARENT)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(155,237,0,392)
    assert old['records'][MID]['label']=='APPROX'
    assert old['records']['ln-iso-lmp_t_model-17z0wyl']['label']=='CERT-MULTIBOARD'
    assert old['records']['ln-ipfr-t_model-qpx6tn']['label']=='CERT-MULTIBOARD'
    assert old['PR2_remains_draft_never_merge'] and old['no_generic_texture_GTO'] and old['no_observed_private_card_NL2_rates']
    first,pfirst=historic_first()
    second,psecond=newer_pair('B261','Js9h5d',44902827510)
    thirdproof,pthird=newer_pair(a.third,third['flop'],third['run'])
    boards=[first,second,thirdproof]
    assert len({z['flop'] for z in boards})==3
    # Legacy project requires >=2 genuinely different textures: all-J9 JT-high alone is insufficient.
    assert len({z['flop_texture'] for z in boards})>=2
    assert {z['flop'] for z in boards}=={'Js9h4d','Js9h5d',third['flop']}
    assert all(z['acting_seat']==1 and z['actual_exact_action_line']==LINE and
       z['relative_spr_error_pct']<=5 and z['strict_full_street_combo_reachable']>0 and
       z['genuine_gto_exploitability_pct']<=.5 and
       z['nl2_locked_variants'] and z['nl2_locked_variants'][0]['version']=='exp_ip' and
       len(z['source_sha256'])==len(z['nl2_locked_variants'][0]['sha256'])==64 and
       not z['assumed_preflop_ranges'] for z in boards)
    result=copy.deepcopy(old)
    result['records'][MID].update(label='CERT-MULTIBOARD',high_frequency_preregistered=True,
       original_top24_high_frequency_preregistered=False,
       source_blind_expansion_rank=60,
       prereg_cohort='B2_JS9H4D_GTO_NL2_PLUS_B261_B304_JS9H5D_GTO_NL2_PLUS_'+a.third+'_GENUINE_GTO_NL2',
       certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
       blocked_reason=None,source_credibility='3_DISTINCT_REAL_100BB_PRE_FLOP_CFR_GTO_SHA_AND_HERO_CO_IP_NL2_RUST_PARTIAL_LOCK_AT_LEAST_2_TEXTURES')
    assert {k for k in old['records'] if old['records'][k]!=result['records'][k]}=={MID}
    result.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V43_B319_RANK60',
      CERT_MULTIBOARD=156,APPROX=236,EST=0,TOTAL=392,
      parent_v42_sha256=sha(PARENT),
      source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{60}),
      supplementary_cert_count=old['supplementary_cert_count']+1,
      B319_rank60_three_true_GTO_NL2_CO_IP_flops=dict(
       rank=60,model_id=MID,flops=sorted(z['flop'] for z in boards),
       textures=sorted({z['flop_texture'] for z in boards}),
       exact_line=LINE,actor='CO_IP',model_SPR=SPR,
       prereg_third_batch=a.third,third_flop=third['flop'],
       original_preflop_CFR_not_measured_NL2_private_hands=True,
       GTO_and_NL2_source_shas=[dict(flop=z['flop'],turn=z['turn'],
          GTO_run=z['source_run_id'],GTO_case_sha=z['source_sha256'],
          NL2_run=z['nl2_locked_variants'][0]['run_id'],
          NL2_raw_case_sha=z['nl2_locked_variants'][0]['sha256'],
          strict_GTO_actor_combos=z['strict_full_street_combo_reachable'])
         for z in boards]),
       B2_historic_source=pfirst,B261_B304_source=psecond,third_new_source=pthird,
       new_CERT_count=1,no_generic_texture_CERT=True,
       all_other_391_models_unchanged=True))
    assert sum(z['label']=='CERT-MULTIBOARD' for z in result['records'].values())==156
    assert sum(z['label']=='APPROX' for z in result['records'].values())==236
    assert result['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    boardproof=create(result)
    assert (len(boardproof['boards']),len(boardproof['models']))==(596,156)
    assert boardproof['strict_aggregate']['named_board_proofs']==596
    assert boardproof['strict_aggregate']['hero_lock_variants']==688
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0 and
       z['no_general_bet_size_recommendation'] for z in boardproof['boards'])
    audited=audit(result)
    assert (audited['cert_multiboard'],audited['approx'],audited['EST'])==(156,236,0)
    assert (audited['aggregate']['named_board_proofs'],audited['aggregate']['paired_hero_locked_source_variants'])==(596,688)
    assert audited['not_generalized_handclass_GTO'] and audited['not_actual_NL2_earnings']
    # Write only after all 3 authentic exact GTO sources, new real Rust NL2, old V42 SHA, SPR,
    # actor, 40/70 and 2-texture audits passed independently.
    STATUS.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    boardproof.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V43_B319',
       parent_v43_status_sha256=sha(STATUS),
       partial_NL2_locks_are_not_whole_flop_GTO=True,
       NL2_private_combo_conditional_rates_not_observed=True,
       only_exact_board_b50_nonpolarized_research=True,
       unknown_source_denominators_are_not_zero_or_empirical=True,
       PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(boardproof,ensure_ascii=False,indent=2)+'\n')
    PROOF.write_text(json.dumps(dict(schema='NL2_HU_B319_RANK60_SOURCE_GATED_V43_PROMOTION_V1',
       old_status_SHA256=sha(PARENT),new_status_SHA256=sha(STATUS),
       new_matrix_SHA256=sha(MATRIX),third_batch=a.third,
       third_flop=third['flop'],evidence=dict(B2=pfirst,B304=psecond,third=pthird),
       CERT=156,APPROX=236,EST=0,TOTAL=392,exact_named_boards=596,
       authentic_NL2_actor_lock_variants=688,
       research_only_medium_bet_boards=boardproof['strict_aggregate']['b50_research_candidate_boards'],
       multiple_true_textures=sorted({x['flop_texture'] for x in boards}),
       exact_public_card_only=True,no_private_card_conditional_NL2_data=True,
       full_HU2475_audit_still_required=True,PR2_Draft_NEVER_MERGE=True),
       ensure_ascii=False,indent=2)+'\n')
    DOC.mkdir(parents=True,exist_ok=True)
    (DOC/'NL2_HU_B319_V43_RANK60_THREE_REAL_GTO_NL2_CERT.md').write_text(
      '# B319 V43 Rank60 three true GTO + actual NL2 CO-IP partial locks\n\n'
      'V43 156 CERT /236 APPROX /0 EST (392). Precisely rank60 upgraded from V42 after 3 genuinely independent exact public flop/turn/action examples: '
      +', '.join(f"{z['flop']}/{z['turn']}" for z in boards)+'.\n'
      'Original 100bb genuine GTO source actions CO_BB x b50 c/x, actor CO-IP, SPR8.614 +/-5%, 40/70 sequential legal per-combo, GTO exploitability <=0.5%, and at least two genuine textures. '
      'Original separate real NL2 Rust downstream actor locks retain original full flop GTO byte-identical; not fully NL2-locked flop. Preflop pinned poker-solver CFR, not observed NL2 private-hand data. '
      'Pooled opponent marginal frequencies are NOT observed conditional per-card decisions; unknown node counts stay unknown.\n'
      'All other 391 status records unchanged. 596 named authentic GTO+actor NL2 public boards, 688 partial lock source variants. 50%-pot nonpolarized flags apply only to individual named boards for research; never generalized optimal-size advice. '
      'Source SHA, SPR and HU2475 independent audit must PASS before any UI update/commit. PR#2 stays DRAFT, NEVER MERGE.\n')
    (DOC/'NL2_HU_B319_V43_ALL_596_NAMED_ACTOR_LOCK_MEDIUM.md').write_text(write_md(boardproof))
    print('PASS B319 V43',json.dumps(dict(CERT=156,APPROX=236,boards=596,
       actor_locks=688,flops=sorted(z['flop'] for z in boards),
       textures=sorted({z['flop_texture'] for z in boards}),
       b50_research_only=boardproof['strict_aggregate']['b50_research_candidate_boards']),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
