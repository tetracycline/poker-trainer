#!/usr/bin/env python3
"""B299: failclosed original Rust source identity checks for rank71 B290/B293/B296
only if GTO full 100bb LMP SHA, exact BB-OOP RIVER b50 c/x b50 c/,
strict 40/70 combo path>0 and model-SPR9.916. Test synthetic adversarial
metadata, don't imply a new original GTO, real NL2 partial child or CERT.
"""
import hashlib,json,pathlib,sys,inspect
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from verify_hu_multiboard_100bb import authorized_b294_rank71_new_exact_GTO_OOP_child
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v42_b289_rank46.json'
SOLVER=pathlib.Path('tools/solve_hu_b294_rank71_new_original_gto_nl2_oop.py')
VERIFIER=pathlib.Path('tools/verify_hu_multiboard_100bb.py')
OUT=D/'nl2_hu_b299_v42_rank71_B294_four_GTO_SHA_negative_gate.json'
MD=DOC/'NL2_HU_B299_R71_FOUR_GTO_SHA_OOP_FAILCLOSED.md'
SPECS={'As7h3d':('B290',44948738190),'QsJh4d':('B293',44951459377),'Js8h3d':('B296',44951459385),'5s5h3d':('B298',44950943882)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    verifier=inspect.getsource(authorized_b294_rank71_new_exact_GTO_OOP_child)
    solve=SOLVER.read_text()
    registry=VERIFIER.read_text()
    assert registry.count('def authorized_b294_rank71_new_exact_GTO_OOP_child(m):')==1
    assert 'authorized_b294_rank71_new_exact_GTO_OOP_child(m)\n                        or' in registry
    for flop,(batch,run) in SPECS.items():
        assert f"'{flop}':('{batch}',{run})" in verifier
        assert f"'{flop}':('{batch}',{run})" in solve
    assert "idx['source_sha256']==hashlib.sha256(raw).hexdigest()" in verifier
    assert "m.get('original_B294_parent_pin_sha256')==sha(pinpath)" in verifier
    assert "p['target_exact_actor_OOP_strict_combos']>0" in verifier
    assert "n['acting_seat']==0 and len(n['public_board'])==10" in verifier
    assert "abs(n['node_spr']-9.916)/9.916<=.05" in verifier
    assert "m.get('gto_parent_source_run_id')==run" in verifier
    assert "m.get('turn_line_policy')=='xb50only'" in verifier
    assert "pipeline.solve_sub(SPOT,'exp_oop',FLOP,fr,LINE,TURN)" in solve
    assert "ix['exact_target_actor_OOP_strict_combos']==pin['target_exact_actor_OOP_strict_combos']" in solve
    negatives={}
    for flop,(batch,run) in SPECS.items():
        root=dict(spot='LMP_CO_BB',version='exp_oop',flop=flop,
            selected_lines=['b50 c'],selected_turn_lines=['x b50 c'],
            flop_line_policy='oop-b50only',turn_line_policy='xb50only',
            flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
            NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_SHA_PINNED_B294_RANK71_GTO',
            gto_parent_source_run_id=run,
            original_full_GTO_flop_byte_identical_not_recomputed=True,
            preflop_ranges={'source':'ASSUMED_EXPLICIT_169CLASS'},
            restricted_tree_assumption=False,flop_size_profile='full',
            turns=['SOURCE_NOT_PINNED'],
            original_B294_parent_pin_sha256='0'*64,
            gto_parent_source_sha256='1'*64,
            flop_root_jobfile_sha256='2'*64,
            gto_parent_source_manifest_sha256='3'*64)
        mutations={
            'forged_original_pin_sha':{},
            'wrong_spot':{'spot':'CO_BB'},
            'wrong_hero_actor_seat':{'version':'exp_ip'},
            'imposter_original_GTO':{'version':'gto'},
            'wrong_prior_flop_line':{'selected_lines':['x b50 c']},
            'wrong_bet_fraction':{'selected_lines':['b33 c']},
            'missing_turn_b50_call':{'selected_turn_lines':['x x']},
            'incorrect_turn_size':{'selected_turn_lines':['x b100 c']},
            'reordered_actor_history':{'selected_turn_lines':['b50 c x']},
            'wrong_original_run':{'gto_parent_source_run_id':44947726457},
            'unapproved_full_tree_source':{'flop_parent_mode':'UNKNOWN_PARENT'},
            'fake_measured_private_card_ranges':{'preflop_ranges':{'source':'MEASURED_NL2_PRIVATE_HAND'}},
            'fake_whole_flop_lock':{'NL2_hero_lock_scope':'WHOLE_FLOP_NL2_LOCKED'},
            'reoptimized_original_GTO_flop':{'original_full_GTO_flop_byte_identical_not_recomputed':False},
            'wrong_50pct_flop_policy':{'flop_line_policy':'checked-b50only'},
            'wrong_turn_line_policy':{'turn_line_policy':'xxonly'},
            'restricted_original_flop_tree':{'flop_size_profile':'lmp-50-only'},
            'fake_limited_tree_flag':{'restricted_tree_assumption':True},
            'wrong_other_flop':{'flop':'7s7h2d'},
        }
        for name,mods in mutations.items():
            args={**root,**mods}
            assert authorized_b294_rank71_new_exact_GTO_OOP_child(args) is False,(batch,name)
            negatives[f'{batch}_{flop}_{name}']='REJECTED'
    assert len(negatives)==76 and all(x=='REJECTED' for x in negatives.values())
    s=json.loads(STATUS.read_text())
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(155,237,0,392)
    assert s['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    a=audit(s)
    assert (a['cert_multiboard'],a['approx'],a['EST'])==(155,237,0)
    assert (a['aggregate']['named_board_proofs'],a['aggregate']['paired_hero_locked_source_variants'],
       a['aggregate']['board_examples_with_b50_candidate'])==(593,685,134)
    assert a['not_generalized_handclass_GTO'] and a['not_actual_NL2_earnings']
    # A pending/zero-combo GTO job is never an NL2 lock or a CERT.
    # When actual SHA-pinned archives have been committed, independently check
    # whether the original turn/river actor-OOP source is eligible to be locked.
    readiness={}
    for flop,(batch,run) in SPECS.items():
        pinpath=D/f'nl2_hu_{batch.lower()}_rank71_lmp_{flop}_gto_parent_pin.json'
        if not pinpath.exists():
            readiness[flop]='PENDING_NO_COMMITTED_GTO_SOURCE'
            continue
        pin=json.loads(pinpath.read_text())
        if pin.get('target_exact_actor_OOP_strict_combos',0)<=0:
            readiness[flop]='GTO_EXISTS_ZERO_STRICT_ACTOR_COMBOS_NO_LOCK'
            continue
        legit=dict(spot='LMP_CO_BB',version='exp_oop',flop=flop,
            selected_lines=['b50 c'],selected_turn_lines=['x b50 c'],
            flop_line_policy='oop-b50only',turn_line_policy='xb50only',
            flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
            NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_SHA_PINNED_B294_RANK71_GTO',
            gto_parent_source_run_id=run,
            original_full_GTO_flop_byte_identical_not_recomputed=True,
            preflop_ranges={'source':'ASSUMED_EXPLICIT_169CLASS'},
            restricted_tree_assumption=False,flop_size_profile='full',
            turns=[pin['turn']],
            original_B294_parent_pin_sha256=sha(pinpath),
            gto_parent_source_sha256=pin['original_gto_root_sha256'],
            flop_root_jobfile_sha256=pin['original_gto_job_sha256'],
            gto_parent_source_manifest_sha256=pin['original_gto_manifest_sha256'])
        readiness[flop]=('AUTHENTIC_POSITIVE_GTO_PARENT_READY_FOR_SEPARATE_REAL_NL2_OOP_LOCK'
            if authorized_b294_rank71_new_exact_GTO_OOP_child(legit)
            else 'NOT_AUTHORIZED_SHA_ACTOR_LINE_OR_SPR_MISMATCH')
    result=dict(schema='NL2_HU_B299_RANK71_B290_B293_B296_B298_GTO_OOP_SHA_RIVER_ACTOR_76_NEGATIVES_V1',
        V42_status_sha256=sha(STATUS),
        source_authorizer_sha256=sha(VERIFIER),
        downstream_NL2_source_solver_sha256=sha(SOLVER),
        exact_future_source_flops_and_runs={k:list(v) for k,v in SPECS.items()},
        source_readiness_not_certification=readiness,
        adversarial_original_GTO_metadata_cases=len(negatives),
        all_adversarial_source_cases_failclosed=True,
        negative_test_results=negatives,
        positive_source_not_assumed_or_generated_from_negative_tests=True,
        no_new_authenticated_NL2_OOP_partial_source_claimed=True,
        no_private_hand_conditional_NL2_frequencies_observed=True,
        no_automatic_generic_CERT=True,
        CERT_MULTIBOARD=155,APPROX=237,EST=0,TOTAL=392,
        existing_named_board_proofs=593,existing_real_NL2_actor_lock_variants=685,
        exact_board_50pct_nonpolarized_research_only=134,
        PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    MD.write_text('# B299 rank71 original GTO SHA + BB-OOP river actor failclosed source gate\n\n'
        'B290 As7h3d, B293 QsJh4d, B296 Js8h3d and B298 5s5h3d are independently preregistered '
        'future original GTO sources. A real Rust NL2 OOP downstream partial '
        'lock may run only AFTER original 100bb GTO positive exact BB-OOP '
        'b50 c/x b50 c/ 40%/70% strict legal combos, SPR9.916±5%, '
        'correct actor and pinned original root/job/manifest/case SHA.\n\n'
        '76/76 deliberately forged source metadata cases rejected. '
        'This is a **negative security audit**, not a claim of successful '
        'new Rust original GTO or NL2 conditional private-hand action frequencies. '
        'V42 unchanged 155 CERT/237 APPROX, 593 original GTO+NL2 exact actor '
        'boards, 685 real lock variants, 134 exact-board b50 research cases. '
        'Full 2475/2475 HU audit required before commit. '
        'PR #2 stays Draft, NEVER FORCE PUSH or MERGE.\n')
    print('PASS B299 76/76 source forgeries rejected',json.dumps(dict(cert=155,approx=237,cases=76)),flush=True)
if __name__=='__main__':main()
