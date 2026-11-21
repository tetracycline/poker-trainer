#!/usr/bin/env python3
"""B283: independent negative synthetic checks of newly added B282
rank46 B279/B280 exact 100bb original GTO SHA authorization. Every
actor/line/parent/size/locked-version forgery must fail. No successful
N+1 CERT until a future positive source actually exists and verified.
"""
import copy,hashlib,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from verify_hu_multiboard_100bb import authorized_b282_rank46_new_GTO_IP_turn
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data');DOC=pathlib.Path('docs')
V41=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
SOLVER=pathlib.Path('tools/solve_hu_b282_rank46_new_original_gto_partial_nl2_ip.py')
VERIFIER=pathlib.Path('tools/verify_hu_multiboard_100bb.py')
OUT=D/'nl2_hu_b283_v41_rank46_B282_strict_original_GTO_parent_authorization_negative.json'
DOCOUT=DOC/'NL2_HU_B283_V41_RANK46_B279_B280_SOURCE_SHA_FAILCLOSED_GATE.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=VERIFIER.read_text()
    assert source.count('def authorized_b282_rank46_new_GTO_IP_turn(m):')==1
    assert source.count('authorized_b282_rank46_new_GTO_IP_turn(m)')==2
    assert 'authorized_b210_rank46_original_B3_LMP_CO_IP_xb50_x(m)' in source
    assert 'authorized_b282_rank46_new_GTO_IP_turn(m)\n                        or' in source
    assert "ix['exact_target_actor_IP_strict_combos']==p['target_exact_actor_IP_strict_combos']" in source
    assert "m.get('original_B282_parent_pin_sha256')==sha(pinpath)" in source
    assert "ix['source_sha256']==hashlib.sha256(gzip.decompress(gz.read_bytes())).hexdigest()" in source
    assert "m.get('gto_parent_source_run_id')==run" in source
    assert "m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B282_RANK46_GTO'" in source
    s=SOLVER.read_text()
    assert 'PINS={' in s and "'KsJh4d':('B279',44937413659)" in s
    assert "'QsJh4d':('B280',44937484979)" in s
    assert "index['exact_target_actor_IP_strict_combos']==pin['target_exact_actor_IP_strict_combos']" in s
    assert "pin['target_exact_actor_IP_strict_combos']>0" in s
    assert "m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'" in s
    assert "NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_SHA_PINNED_B282_RANK46_GTO'" in s
    original=dict(
        spot='LMP_CO_BB',version='exp_ip',flop='KsJh4d',
        selected_lines=['x b50 c'],selected_turn_lines=['x x'],
        flop_line_policy='checked-b50only',turn_line_policy='xxonly',
        flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
        NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_SHA_PINNED_B282_RANK46_GTO',
        gto_parent_source_run_id=44937413659,
        original_full_GTO_flop_byte_identical_not_recomputed=True,
        preflop_ranges=dict(source='ASSUMED_EXPLICIT_169CLASS'),
        restricted_tree_assumption=False,flop_size_profile='full',
        turns=['2h'],original_B282_parent_pin_sha256='forged-'+'0'*58,
        gto_parent_source_sha256='forged-'+'1'*58,
        flop_root_jobfile_sha256='forged-'+'2'*58,
        gto_parent_source_manifest_sha256='forged-'+'3'*58)
    negative=dict(
        forged_original_SHA=original,
        wrong_spot={**original,'spot':'CO_BB'},
        wrong_actor_lock_side={**original,'version':'exp_oop'},
        pretended_GTO={**original,'version':'gto'},
        novel_flop_not_authorized={**original,'flop':'Qs7h3d'},
        wrong_original_source_run={**original,'gto_parent_source_run_id':44902973337},
        actor_history_reordered={**original,'selected_lines':['b50 c']},
        wrong_flop_action_size={**original,'selected_lines':['x b100 c']},
        falsified_turn_actor_history={**original,'selected_turn_lines':['x b50 c']},
        wrong_flop_line_policy={**original,'flop_line_policy':'oop-b50only'},
        wrong_turn_line_policy={**original,'turn_line_policy':'xb50only'},
        no_original_pin_mode={**original,'flop_parent_mode':'ASSUMED_PARENT'},
        wrong_node_lock_scope={**original,'NL2_hero_lock_scope':'GTO_FULL_FLOP'},
        original_gto_reoptimized={**original,'original_full_GTO_flop_byte_identical_not_recomputed':False},
        fabricated_preflop_observed={**original,'preflop_ranges':dict(source='OBSERVED_NL2_PRIVATE_HAND')},
        made_up_restricted_tree={**original,'restricted_tree_assumption':True},
        wrong_full_sizing={**original,'flop_size_profile':'lmp-50-only'},
        missing_original_SHA_pin={**original,'original_B282_parent_pin_sha256':None},
        wrong_alternate_run_for_other_flop={**original,'flop':'QsJh4d'},
    )
    for name,case in negative.items():
        assert authorized_b282_rank46_new_GTO_IP_turn(case) is False,name
    status=json.loads(V41.read_text())
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(154,238,0,392)
    assert status['records']['ln-iso-lmp_t_model-17z0wyl']['label']=='APPROX'
    a=audit(status)
    assert (a['cert_multiboard'],a['approx'],a['EST'])==(154,238,0)
    assert (a['aggregate']['named_board_proofs'],
            a['aggregate']['paired_hero_locked_source_variants'],
            a['aggregate']['board_examples_with_b50_candidate'])==(590,682,134)
    assert a['not_generalized_handclass_GTO'] and a['not_actual_NL2_earnings']
    out=dict(schema='NL2_HU_B283_V41_R46_B282_GTO_SHA_POSITIVE_ONLY_NEGATIVE_GATE_V1',
        V41_status_sha256=sha(V41),verifier_sha256=sha(VERIFIER),
        original_GTO_to_NL2_solver_sha256=sha(SOLVER),
        synthetic_forgery_cases=len(negative),all_forged_cases_rejected=True,
        synthetic_forgery_types=sorted(negative),positive_CFR_source_not_claimed=True,
        accepted_future_flops=['KsJh4d','QsJh4d'],
        immutable_expected_original_GTO_run_ids=[44937413659,44937484979],
        missing_or_zero_original_legal_40_70_actor_combos_failclosed=True,
        no_false_hero_actor_NL2_private_card_rates=True,
        CERT_MULTIBOARD=154,APPROX=238,EST=0,TOTAL=392,
        existing_named_boards=590,existing_NL2_source_lock_variants=682,
        exact_board_50pct_nonpolarized_research_only=134,
        no_generic_model_CERT_upgrade=True,
        PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    lines=['# B283 failclosed original GTO -> actual Rust NL2 source authorization',
        '',
        'B282 can accept only originally SHA-pinned complete 100bb LMP rank46 '
        'original B279 KsJh4d or B280 QsJh4d GTO with strictly positive '
        'actor CO-IP x b50 c/x source combos and SPR 19.55, '
        'before any genuine Rust partially locked NL2 child is allowed.',
        'All '+str(len(negative))+' adversarial synthetic metadata tests were rejected.',
        'These are **negative** source gates, not a claim of a new genuine source, '
        'new CERT, measured NL2 private-card rates or a successful Rust GTO solve.',
        'All existing V41 590 authenticated source board locks / 134 exact b50 research '
        'and 2475/2475 HU route checks must PASS before commit.',
        'V41 unchanged 154 CERT / 238 APPROX; PR2 Draft NEVER MERGE.']
    DOCOUT.write_text('\n\n'.join(lines)+'\n')
    print('PASS B283',json.dumps(dict(adversarial_cases=len(negative),all_failclosed=True,
        cert=154,approx=238)),flush=True)
if __name__=='__main__':main()
