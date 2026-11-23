"""Solve BB's original river after calling a 33% BTN flop c-bet and checking the turn through."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b508_rank134_native import mark_conditional
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board

MODEL = 'ln-bb-r_model-myhu0j'
FLOP_LINE = 'x b33 c'
LINE = 'x b33 c/x x/'
CASES = {
    'AsQh8d': (14528675947, '3c', '9s'),
    'KsQh4d': (14591903053, 'Tc', '3h'),
    'Js9h4d': (14591863023, 'Ts', 'Ah'),
    '8s8h3d': (14592317474, '5s', '4s'),
}
PINS = Path('data/nl2_hu_b512_rank86_artifacts.json')
STATUS = Path('data/nl2_hu_multiboard_status_current.json')


def observe(source, public, root_sha):
    observation = audit_decision(source, public, LINE, 0, root_sha)
    if observation is None:
        return None
    assert observation['source_actions'] == ['x','b50','b100','a']
    child, = (n for n in source['subgame']['nodes'] if (n['board'],n['line'],n['player']) == (public,LINE+'b50',1))
    assert child['pot'] == 1371 and child['bets'] == [457,0]
    return observation


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--originals', type=Path, required=True)
    cli.add_argument('--solver', type=Path, required=True)
    cli.add_argument('--flop', choices=CASES)
    cli.add_argument('--driver', type=Path)
    cli.add_argument('--results', type=Path)
    cli.add_argument('--run', type=int)
    args = cli.parse_args()
    solver = args.solver.resolve()
    def head(folder):
        return subprocess.check_output(['git','-C',str(folder),'rev-parse','HEAD'], text=True).strip()
    assert head(solver) == SOLVER
    if args.driver:
        assert args.driver.resolve() == solver/'postflop/pfdriver/target/release/pfdriver'
        assert head(solver/'postflop/postflop-solver') == RUST
    raw_pool = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw_pool) == POOL
    pool = json.loads(raw_pool)['NL2']
    sys.path.insert(0, str(solver/'postflop/py'))
    import pipeline
    import ranges
    pins = json.loads(PINS.read_bytes())
    model = json.loads(STATUS.read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['street'],model['assumed_model_node_spr']) == (86,'BTN_BB','SRP',2,10.436)
    assert model['abstract_action_history'] == '你過、對手下注、你跟|你過、對手過|'
    group = dict(rank=86,model_id=MODEL,boards=[],pins=[])
    report = dict(schema='NL2_HU_B512_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    attempts = []
    for flop,(aid,turn,river) in CASES.items():
        if args.flop and flop != args.flop:
            continue
        original = load_original(args.originals,aid,pins[str(aid)],'BTN_BB',flop,turn,'gto',
                                 flop_line=FLOP_LINE,pot=550,stack=9750,pipeline=pipeline,ranges=ranges)
        g,identity = original['source'],original['identity']
        assert identity['flop_oop_menu'] == '' and identity['flop_ip_menu'] == (
            '33%,75%' if flop == 'AsQh8d' else '33%,50%,75%')
        public = original['public']+river
        gr = observe(g,public,identity['root_sha256'])
        assert gr and gr['status'] == 'POSITIVE_JOINT_REACH'
        code = f'B512_R86_{flop.upper()}_{turn.upper()}_EXP_OOP'
        filename = f'NL2_{code}.json.gz'
        if args.driver:
            assert args.flop and args.results and args.run > 0
            result = solve_native(original,'exp_oop',pool,pipeline,args.results,args.driver,args.run,code)
            replay_native(original,'exp_oop',pool,pipeline,result,args.run,code)
            return
        if not args.results:
            print(flop, public, gr['strict_legal_combos'], gr['compatible_hole_card_pairs'])
            continue
        assert args.run > 0 and not args.flop
        matches = list(args.results.rglob(filename))
        assert len(matches) <= 1
        row = dict(flop=flop,public_board=public,original_gto=identity,gto=gr)
        attempts.append(row)
        if not matches:
            row['status'] = 'MISSING_COMPLETED_NATIVE_OUTPUT'
            continue
        shutil.copyfile(matches[0],EVIDENCE/filename)
        e = replay_native(original,'exp_oop',pool,pipeline,matches[0],args.run,code)
        er = observe(e,public,identity['root_sha256'])
        row.update(exp_oop=er,frozen_gto_flop=True,verified_street_locks=e['measured_lock_application'])
        if er is None:
            row['status'] = 'EXACT_NODE_UNAVAILABLE'
            continue
        if not (0 <= er['gto_gap_pct'] <= .5 and 0 <= er['locked_hero_gap_pct'] <= .5):
            row['status'] = 'CONVERGENCE_OUTSIDE_GATE'
            continue
        if not (er['lock_scope']['observed_marginal_source_nodes'] and er['subgame_applied_rust_lock_nodes']):
            row['status'] = 'NO_APPLIED_MEASURED_LOCK'
            continue
        row['status'] = er['status']
        if er['status'] != 'POSITIVE_JOINT_REACH':
            continue
        board,pin = emit_board(model,g,e,public,LINE,texture(flop))
        assert (board['actual_pot_bb'],board['actual_effective_stack_bb']) == (9.14,95.68)
        assert gr['compatible_hole_card_pairs'] == pin['GTO_compatible_hole_card_pairs'] > 0
        assert er['compatible_hole_card_pairs'] == pin['NL2_compatible_hole_card_pairs'] > 0
        pin['original_gto_archive'] = identity
        mark_conditional(board,pin,e,identity)
        group['boards'].append(board)
        group['pins'].append(pin)
        report['references'][source_key(MODEL,er)] = er
        report['gto_references'][source_key(MODEL,gr)] = gr
    if args.results:
        Path('data/nl2_hu_b512_rank86_attempts.json').write_bytes(json_bytes(dict(rank=86,model_id=MODEL,run_id=args.run,attempts=attempts)))
        if len(group['boards']) >= 3:
            assert len({b['flop'] for b in group['boards']}) == len(group['boards']) <= 5
            (EVIDENCE/'reverified/rank86.json').write_bytes(json_bytes(group))
            Path('data/nl2_hu_b512_locked_medium.json').write_bytes(json_bytes(report))


if __name__ == '__main__':
    main()
