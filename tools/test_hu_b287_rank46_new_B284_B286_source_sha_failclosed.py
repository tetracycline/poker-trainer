#!/usr/bin/env python3
"""B287 failclosed original GTO SHA/actor source gate when extending B282 to
predeclared rank46 B284 low-connect and B286 paired middle candidates.
26 synthetic attack configurations must all fail: no original GTO SHA
positive actor source or genuine CO-IP NL2 Rust child is presumed.
"""
import copy,hashlib,json,pathlib,sys,inspect
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from verify_hu_multiboard_100bb import authorized_b282_rank46_new_GTO_IP_turn
from hu_cert_lock_medium_audit import audit
ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/'data';DOC=ROOT/'docs'
STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
SOLVER=ROOT/'tools/solve_hu_b282_rank46_new_original_gto_partial_nl2_ip.py'
VERIFIER=ROOT/'tools/verify_hu_multiboard_100bb.py'
OUT=D/'nl2_hu_b287_rank46_B284_B286_GTO_COIP_SHA_auth_negative_tests.json'
MD=DOC/'NL2_HU_B287_R46_B284_B286_SHA_COIP_SOURCE_FAILCLOSED.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
SPECS={'7s5h3d':('B284',44938881037),'7s7h2d':('B286',44939456600)}
def main():
    src=inspect.getsource(authorized_b282_rank46_new_GTO_IP_turn)
    text=SOLVER.read_text()
    for flop,(batch,run) in SPECS.items():
        assert f"'{flop}':('{batch}',{run})" in src
        assert f"'{flop}':('{batch}',{run})" in text
    assert "p['target_exact_actor_IP_turn_nodes']>0" in src
    assert "ix['exact_target_actor_IP_strict_combos']==p['target_exact_actor_IP_strict_combos']" in src
    assert "ix['source_sha256']==hashlib.sha256(gzip.decompress(gz.read_bytes())).hexdigest()" in src
    assert "m.get('original_B282_parent_pin_sha256')==sha(pinpath)" in src
    assert "abs(n['node_spr']-19.55)/19.55<=.05" in src
    assert "m.get('gto_parent_source_run_id')==run" in src
    assert "m.get('selected_turn_lines')==['x x']" in src
    assert "m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B282_RANK46_GTO'" in src
    assert "pin['target_exact_actor_IP_strict_combos']>0" in text
    assert "pipeline.solve_sub(SPOT,'exp_ip',FLOP,fr,LINE,TURN)" in text
    cases={}
    for flop,(batch,run) in SPECS.items():
        base=dict(spot='LMP_CO_BB',version='exp_ip',flop=flop,
          selected_lines=['x b50 c'],selected_turn_lines=['x x'],
          flop_line_policy='checked-b50only',turn_line_policy='xxonly',
          flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
          NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_SHA_PINNED_B282_RANK46_GTO',
          gto_parent_source_run_id=run,
          original_full_GTO_flop_byte_identical_not_recomputed=True,
          preflop_ranges={'source':'ASSUMED_EXPLICIT_169CLASS'},
          restricted_tree_assumption=False,flop_size_profile='full',
          turns=['NOT_VERIFIED_REAL_TURN'],
          original_B282_parent_pin_sha256='0'*64,
          gto_parent_source_sha256='1'*64,flop_root_jobfile_sha256='2'*64,
          gto_parent_source_manifest_sha256='3'*64)
        changes={
          'forged_sha':{},
          'wrong_spot':{'spot':'CO_BB'},
          'fake_hero_IP':{'version':'exp_oop'},
          'fake_unlocked_GTO':{'version':'gto'},
          'wrong_original_run':{'gto_parent_source_run_id':44937484979},
          'wrong_root_kind':{'flop_parent_mode':'UNKNOWN_SOURCE'},
          'wrong_line':{'selected_lines':['b50 c']},
          'wrong_size':{'selected_lines':['x b100 c']},
          'wrong_turn_line':{'selected_turn_lines':['x b100 c']},
          'wrong_villain_data_origin':{'preflop_ranges':{'source':'MEASURED_NL2_PRIVATE_CARDS'}},
          'wrong_bet_tree':{'flop_size_profile':'lmp-50-only'},
          'wrong_actor_scope':{'NL2_hero_lock_scope':'WHOLE_FLOP_LOCKED'},
          'forged_gto_reoptimized':{'original_full_GTO_flop_byte_identical_not_recomputed':False},
        }
        for label,mods in changes.items():
            candidate={**base,**mods}
            assert authorized_b282_rank46_new_GTO_IP_turn(candidate) is False,flop+' '+label
            cases[f'{batch}_{flop}_{label}']='REJECTED'
    assert len(cases)==26 and all(x=='REJECTED' for x in cases.values())
    s=json.loads(STATUS.read_text())
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(154,238,0,392)
    assert s['records']['ln-iso-lmp_t_model-17z0wyl']['label']=='APPROX'
    a=audit(s)
    assert (a['cert_multiboard'],a['approx'],a['EST'])==(154,238,0)
    assert (a['aggregate']['named_board_proofs'],
      a['aggregate']['paired_hero_locked_source_variants'],
      a['aggregate']['board_examples_with_b50_candidate'])==(590,682,134)
    assert a['not_generalized_handclass_GTO'] and a['not_actual_NL2_earnings']
    out=dict(schema='NL2_HU_B287_RANK46_B284_B286_26_NEGATIVE_ORIGINAL_GTO_NL2_SOURCE_GATE_V1',
      V41_status_sha256=sha(STATUS),B282_solver_sha256=sha(SOLVER),
      core_verifier_sha256=sha(VERIFIER),
      prereg_allowed_exact_flops_and_run_ids=SPECS,
      negative_forgery_case_count=len(cases),all_26_synthetic_attacks_rejected=True,
      negative_test_results=cases,
      no_unverified_B284_B286_GTO_case_claimed=True,
      no_new_authentic_NL2_partial_Rust_solve_claimed=True,
      no_B279_or_B280_false_source_rehabilitated=True,
      no_generic_textures_or_unobserved_NL2_private_cards_certified=True,
      CERT_MULTIBOARD=154,APPROX=238,EST=0,TOTAL=392,
      exact_named_boards=590,genuine_actor_lock_variants=682,
      exact_board_b50_nonpolar_research_only=134,PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    MD.write_text('# B287 rank46 B284/B286 original-GTO-to-real-NL2 source SHA fail-closed\n\n'
      'Pre-registered exact boards 7s5h3d/B284 and 7s7h2d/B286 must first '
      'prove original complete Rust 100bb LMP SHA and strictly positive '
      'correct CO-IP turn x b50 c/x combos with model SPR19.55/40%+70% '
      'sequential action ancestry. Only then may B282 true Rust downstream '
      'NL2 pool-marginal/explicit-default partial lock run.\n\n'
      '26/26 synthetic forged source, actor, flop action, turn line, preflop '
      'scope and SHA configurations were rejected. This is a *negative gate*, '
      'NOT a claim that a positive original GTO or NL2 private-hand '
      'conditional dataset exists. Prior B279 actor0 and B280 cancellation '
      'remain rejected. V41 154 CERT/238 APPROX 590 named boards/682 locks '
      'and 134 exact board b50 research-only cases unchanged. '
      'Full 2475/2475 HU audit required before commit; PR #2 Draft NEVER MERGE.\n')
    print('PASS B287 26/26 forged new GTO-to-NL2 rank46 sources failclosed',flush=True)
if __name__=='__main__':main()
