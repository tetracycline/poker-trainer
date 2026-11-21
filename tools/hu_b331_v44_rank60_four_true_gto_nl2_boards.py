#!/usr/bin/env python3
"""B331 V44 expand already-certified rank60 from 3 to 4 truly different
SHA-verified original GTO + genuinely separate actor-matched NL2 Rust
partial turn-only source boards. Never upgrade generic hand class/texture.
CERT model count remains 156 / 236 APPROX; exact named board proof +1.
"""
import copy,hashlib,json,pathlib
from hu_b319_v43_rank60_three_real_gto_nl2_cert import newer_pair,texture
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data'); DOC=pathlib.Path('docs')
MID='ln-ipfr-t_model-hxdit'
OLD=D/'nl2_hu_multiboard_status_v43_b319_rank60.json'
OUT=D/'nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v44_b331.json'
PROOF=D/'nl2_hu_b331_rank60_four_true_GTO_NL2_actor_lock_source_gate.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
    old=load(OLD)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V43_B319_RANK60'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(156,236,0,392)
    assert old['records'][MID]['label']=='CERT-MULTIBOARD'
    assert old['records'][MID]['proven_exact_board_count']==3
    oldboards=old['records'][MID]['certified_3_to_5_exact_flop_boards']
    assert {x['flop'] for x in oldboards}=={'Js9h4d','Js9h5d','Js9s4s'}
    assert old['B319_rank60_three_true_GTO_NL2_CO_IP_flops']['prereg_third_batch']=='B322'
    assert old['PR2_remains_draft_never_merge'] and old['no_generic_texture_GTO'] and old['no_observed_private_card_NL2_rates']
    fourth,src=newer_pair('B323','9s7h4d',44960100932)
    assert (fourth['flop'],fourth['turn'],fourth['actual_exact_action_line'],fourth['acting_seat'])==(
       '9s7h4d','Ad','x b50 c/x',1)
    assert fourth['strict_full_street_combo_reachable']==6
    assert fourth['relative_spr_error_pct']<=5 and fourth['genuine_gto_exploitability_pct']<=.5
    assert fourth['flop_texture']=='LOW'
    assert fourth['nl2_locked_variants'][0]['version']=='exp_ip'
    assert fourth['nl2_locked_variants'][0]['run_id']==44960924477
    assert src['original_GTO_run']==44960100932 and src['true_NL2_Rust_run']==44960924477
    assert src['GTO_actor_strict']==src['NL2_actor_strict']==src['NL2_actor_model_SPR_strict']==6
    allboards=list(oldboards)+[fourth]
    assert len(allboards)==4 and len({x['flop'] for x in allboards})==4
    textures={x['flop_texture'] for x in allboards}
    assert {'LOW','JT_HIGH','MONOTONE'}.issubset(textures)
    result=copy.deepcopy(old)
    rm=result['records'][MID]
    rm['certified_3_to_5_exact_flop_boards']=allboards
    rm['proven_exact_board_count']=4
    rm['source_credibility']='FOUR_DISTINCT_REAL_100BB_GTO_SHA_AND_PARTIAL_NL2_RUST_CO_IP_LOCKS_THREE_TEXTURES'
    rm['sourceblind_extra_exact_board_scope']='B323_ORIGINAL_GTO_PLUS_B325_TRUE_NL2_LOWTEXTURE'
    assert {k for k in old['records'] if old['records'][k]!=result['records'][k]}=={MID}
    result.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V44_B331_RANK60_FOUR',
      parent_v43_sha256=sha(OLD),CERT_MULTIBOARD=156,APPROX=236,EST=0,TOTAL=392,
      B331_rank60_four_true_GTO_NL2_actor_lock_boards=dict(
        model_id=MID,rank=60,actor='CO_IP',exact_line='x b50 c/x',model_SPR=8.614,
        flops=sorted(x['flop'] for x in allboards),
        textures=sorted(textures),board_count=4,
        original_V43_B319_three_GTO_NL2_sources_preserved_unchanged=True,
        fourth_original_GTO_and_NL2_source=dict(
          flop='9s7h4d',turn='Ad',original_GTO_run=44960100932,
          original_GTO_case_sha256=fourth['source_sha256'],
          true_partial_Rust_NL2_run=44960924477,
          authentic_real_NL2_source_sha256=fourth['nl2_locked_variants'][0]['sha256'],
          strict_GTO_actor_combos=fourth['strict_full_street_combo_reachable'],
          strict_real_NL2_actor_combos=src['NL2_actor_strict'],
          NL2_actor_matching_SPR_combos=src['NL2_actor_model_SPR_strict'],
          original_GTO_pin_sha256=src['original_GTO_pin_sha256'],
          NL2_source_index_sha256=src['true_NL2_index_sha256']),
        other_391_models_completely_unchanged=True,
        no_generic_or_private_hand_derived_GTO=True,
        source_provenance_truly_partial_NL2_rust_downstream_only=True,
        CERT_count_delta=0,named_board_count_delta=1,
        PR2_Draft_NEVER_MERGE=True))
    assert sum(v['label']=='CERT-MULTIBOARD' for v in result['records'].values())==156
    assert sum(v['label']=='APPROX' for v in result['records'].values())==236
    assert result['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    proof=create(result)
    audit_report=audit(result)
    assert (len(proof['boards']),len(proof['models']))==(597,156)
    assert (proof['strict_aggregate']['named_board_proofs'],proof['strict_aggregate']['hero_lock_variants'])==(597,689)
    assert (audit_report['cert_multiboard'],audit_report['approx'],audit_report['EST'])==(156,236,0)
    assert (audit_report['aggregate']['named_board_proofs'],audit_report['aggregate']['paired_hero_locked_source_variants'])==(597,689)
    assert audit_report['not_generalized_handclass_GTO'] and audit_report['not_actual_NL2_earnings']
    assert all(x['hero_lock_proofs'] and x['strictly_reachable_combo_count']>0 and
       x['no_general_bet_size_recommendation'] for x in proof['boards'])
    # All source/actor/SHA/SPR/40-70 validation complete before writing any output.
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    proof.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V44_B331',
      parent_V44_status_sha256=sha(OUT),
      only_named_public_boards_no_generic_texture_CERT=True,
      partial_NL2_locks_are_not_whole_flop_GTO=True,
      NL2_private_combo_conditional_rates_not_observed=True,
      unknown_source_denominators_are_not_zero_or_empirical=True,
      PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    PROOF.write_text(json.dumps(dict(
      schema='NL2_HU_B331_V44_RANK60_FOUR_REAL_GTO_AND_NL2_ACTOR_BOARD_V1',
      parent_V43_SHA256=sha(OLD),result_V44_SHA256=sha(OUT),matrix_SHA256=sha(MATRIX),
      rank=60,model_id=MID,flops=sorted(z['flop'] for z in allboards),
      textures=sorted(textures),fourth_source=src,
      original_3_V43_genuine_GTO_plus_NL2_flops_unchanged=True,
      CERT=156,APPROX=236,EST=0,TOTAL=392,
      exact_named_boards=597,true_actor_NL2_source_lock_variants=689,
      b50_nonpolarized_exact_board_research_only=proof['strict_aggregate']['b50_research_candidate_boards'],
      only_exact_named_board_evidence=True,no_invented_private_card_NL2_conditional_data=True,
      hu_2475_independent_audit_required_before_commit=True,PR2_Draft_NEVER_MERGE=True),
      ensure_ascii=False,indent=2)+'\n')
    DOC.mkdir(parents=True,exist_ok=True)
    (DOC/'NL2_HU_B331_V44_RANK60_FOUR_REAL_GTO_NL2_BOARD_CERT.md').write_text(
      '# B331 V44 fourth authentic rank60 actor COIP board\n\n'
      'Existing V43 three distinct exact GTO+true NL2 actor partially locked boards stay SHA intact. '
      'New original B323 GTO low 9s7h4d/Ad (6 strict actor/IP combos) plus independent '
      'B325 genuine Rust NL2 CO-IP partial lock (6 SPR-matched combos) individually pinned SHA. '
      'Four distinct named flops: '+', '.join(sorted(z['flop'] for z in allboards))+
      '. Distinct textures '+', '.join(sorted(textures))+'. '
      'Source-only exact x b50 c/x, SPR8.614 +/-5%, original preflop CFR is not measured private-hand NL2 behavior. '
      'Model totals **156 CERT /236 APPROX /0 EST unchanged**, 597 authenticated named boards, '
      '689 actual NL2 actor locked source variants, 50% depolarized only individual named-board research, not general advice. '
      'Unseen board and all generic textures remain approximate. All 2475 HU routes must independently PASS before release. '
      'PR #2 remains Draft/Open, never merge.\n')
    (DOC/'NL2_HU_B331_V44_ALL_597_NAMED_ACTOR_LOCK_MEDIUM.md').write_text(write_md(proof))
    print('PASS B331 V44',json.dumps(dict(CERT=156,APPROX=236,authentic_named_boards=597,
       NL2_actor_variants=689,b50_research_only=proof['strict_aggregate']['b50_research_candidate_boards'],
       textures=sorted(textures)),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
