"""Add three new rank89 native flops using the B705 canonical-card gate repair."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import hu_b696_turn_call_rivers as native
from hu_b467_river_source_gate import json_bytes, sha

RANK = 89
CASES = {
    'Td8c3h': ['Ts', '8h', '3s'],
    'Jh7d4c': ['Js', '7s', '4h'],
    'Qc9s5d': ['Qh', '9d', '5h'],
}
WITNESSES = {
    'Td8c3h': ('6c6h', '8d8s', 'Ac'),
    'Jh7d4c': ('6c6h', '8c8s', 'Ac'),
    'Qc9s5d': ('7c7h', '8c8s', 'Ac'),
}
PINS = {
    'tools/hu_b696_turn_call_rivers.py': 'ca9d29bbe212262dd5f834714779a339e8204c3c',
    'tools/hu_b705_resume_turn_call.py': '65da6780b509e42873a6fce2aaeda37f3dcba4dc',
    'tools/hu_b696_turn_call_routes.cjs': 'c3e61df26eba23f6b15be5f5e9d181c1a4fa7e5b',
    'tools/hu_b637_rank57.py': '86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9',
    'tools/hu_b568_caller_rivers.py': 'e69bda7fe46c3dd18a48dee1bb97f965ab2813f7',
    'tools/staged/hu_b696_nl2_hu_model.js': 'b4a308a0f65b707f43f41f0b354cec87c08d5af6',
    'tools/staged/hu_b696_trainer_route_contract.cjs': '3b10524228c357552bb3f1eac88e17f9b2459b32',
    'nl2.js': '15aee97e53a156fe073c96a120638a8a3679958f',
}
PRIOR_POSITIVES = [
    dict(run=45320372683, head='610d867a828115e80285e5aebe49fc0059c788c3', flop='Qs7h3d', turn='Qh',
        river='Ac', artifact=14886954846, archive_sha256='852d07b176da3f191521489ef1381eae4f84c25260f9fffbcbb5f3949195006d',
        shared_hand_class='66', shared_hands=6),
    dict(run=45320372683, head='610d867a828115e80285e5aebe49fc0059c788c3', flop='Jc6d2s', turn='Jh',
        river='Ac', artifact=14886929899, archive_sha256='3dd4257e7d3767eb6a4735d6a5a9ff1d4d314f080d5f57841f25dd895ee3e7b1',
        shared_hand_class='55', shared_hands=6),
]
ORIGINAL_PARENT = native.parent_candidates


def blob(path):
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def canonical_parent_candidates(root, turn, route):
    """The B705 repair changes only a temporary metadata view, never native bytes."""
    first, = (node for node in root['nodes'] if (node['line'], node['player']) == ('', 0))
    response, = (node for node in root['nodes'] if (node['line'], node['player']) == ('x', 1))
    cards = native.public_cards(root['flop'])
    assert len(root['flop']) == 6 and len(cards) == 3
    for node in (first, response):
        assert len(node['board']) == 6 and native.public_cards(node['board']) == cards
        assert (node['pot'], node['bets']) == (route['pot'], [0, 0])
    boundary, = (node for node in root['nodes'] if node['line'] == 'x x/' and node['board'].endswith(turn))
    assert len(boundary['board']) == 8 and native.public_cards(boundary['board'][:6]) == cards
    assert boundary['board'][6:] == turn and turn not in cards
    view = dict(root, flop=first['board'])
    return ORIGINAL_PARENT(view, turn, route)


def range_class(hand):
    ranks = sorted((hand[0], hand[2]), key='23456789TJQKA'.index, reverse=True)
    return ''.join(ranks) + ('' if ranks[0] == ranks[1] else 's' if hand[1] == hand[3] else 'o')


def configure():
    assert all(blob(path) == digest for path, digest in PINS.items())
    native.CASES = {RANK: CASES}
    native.parent_candidates = canonical_parent_candidates


def static(args):
    solver = args.solver.resolve()
    assert subprocess.check_output(['git', '-C', solver, 'rev-parse', 'HEAD'], text=True).strip() == native.SOLVER
    assert sha((solver / 'postflop/py/pipeline.py').read_bytes()) == native.PIPELINE
    assert sha((solver / 'postflop/py/ranges.py').read_bytes()) == native.RANGES
    sys.path.insert(0, str(solver / 'postflop/py'))
    import ranges
    import pipeline
    assert ranges.SPOTS['BTN_BB'] == native.SPOTS[RANK]
    rendered = subprocess.check_output(['node', 'tools/hu_b696_turn_call_routes.cjs',
        '--model-file', 'tools/staged/hu_b696_nl2_hu_model.js'])
    assert args.routes.read_bytes() == rendered, 'Use the exact staged model routes, independent of the live evidence loader'
    route = json.loads(rendered)[str(RANK)]
    assert (route['id'], route['spot'], route['actor'], route['pot'], route['stack'],
        route['river_pot'], route['river_stack'], route['line'], route['turn_call_pct']) == (
        native.MODELS[RANK], 'BTN_BB', 1, 550, 9750, 1100, 9475, 'x x/b50 c/x', 50)
    assert route['spr'] == 8.614
    job = native.make_root(RANK, args.flop, route, pipeline)
    assert (job['pot'], job['stack'], job['rake_rate'], job['rake_cap'], job['flop_oop'], job['flop_ip']) == (
        550, 9750, .05, 1000, '33%,50%,75%', '33%,50%,75%')
    weights = [dict(zip(ranges.NAMES, row, strict=True)) for row in ranges.ranges('BTN_BB', 'gto')]
    hero, villain, river = WITNESSES[args.flop]
    ip_weight, oop_weight = weights[1][range_class(hero)], weights[0][range_class(villain)]
    assert min(ip_weight, oop_weight) >= .005
    paths = []
    for turn in CASES[args.flop]:
        public = args.flop + turn + river
        assert len(native.public_cards(public + hero + villain)) == 9
        cells = [native.hand_cell(hero, public[:length]) for length in (6, 8, 10)]
        assert all(cell[0] in route['routes'][street] for cell, street in zip(cells, ('flop', 'turn', 'river'), strict=True))
        assert route['routes']['river'][cells[-1][0]] == '過'
        paths.append(dict(turn=turn, river=river, cells=cells))
    return dict(hero=hero, villain=villain, ip_weight=ip_weight, oop_weight=oop_weight,
        paths=paths, exact_ui_each_street=True, not_a_native_strategy_witness=True)


def run(args):
    assert args.rank == RANK and args.flop in CASES
    configure()
    witness = static(args)
    if args.preflight:
        print(json.dumps(dict(rank=RANK, flop=args.flop, static_range_witness=witness,
            exact_prices=[550, 9750, 1100, 9475], no_certification=True)))
        return
    if args.driver:
        assert not args.output.exists() or not any(args.output.iterdir()), 'Use a fresh native source directory'
    else:
        assert (args.output / 'proof.json').is_file(), 'Replay requires the complete original source'
    try:
        native.run(args)
    finally:
        native.parent_candidates = ORIGINAL_PARENT
    path = args.output / 'proof.json'
    report = json.loads(path.read_bytes())
    assert report['schema'] == 'NL2_B696_TURN_CALL_ORIGINAL_WORKER_V1'
    report.update(schema='NL2_B709_R89_NEW_TURN_CALL_WORKER_V1',
        original_algorithm_schema=report['schema'], source_algorithm_blobs=PINS,
        source_worker_blob=blob('tools/hu_b709_rank89_extra.py'),
        canonical_card_order_fix='B705_CARD_SET_CHECK_AND_TEMPORARY_NATIVE_ORDER_VIEW',
        preregistered_new_flops=list(CASES), preregistered_turns=CASES[args.flop],
        selection_mechanism='NEW_HIGH_FLOP_MID_CHECK_HIGHEST_CARD_PAIRED_TURN_CALL_FIRST',
        prior_positive_references=PRIOR_POSITIVES, prior_native_solves_repeated=0,
        static_range_witness=witness,
        native_file_sha256={str(p.relative_to(args.output)): sha(p.read_bytes())
            for p in sorted(args.output.rglob('*')) if p.is_file() and p != path})
    path.write_bytes(json_bytes(report))
    turns = report['turns']
    reachable_gto = [b for t in turns for b in t['gto_boards'] if b['reach']['strict_legal_combos'] > 0 and b['reach']['b50'] is not None]
    reachable_nl2 = [b for t in turns for b in t['nl2_boards'] if b['reach']['strict_legal_combos'] > 0 and b['reach']['b50'] is not None]
    print(json.dumps(dict(rank=RANK, flop=args.flop, positive=report['positive_distinct_flops'],
        gto_turn_subgames=sum('gto_source_sha256' in t for t in turns),
        actor_locked_turn_subgames=sum(t['paired_policies'] for t in turns),
        gto_reachable_half_pot_boards=len(reachable_gto), nl2_reachable_half_pot_boards=len(reachable_nl2),
        nl2_nonpolarized_candidates=sum(b['reach']['b50']['candidate'] for b in reachable_nl2))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('solver', 'routes', 'output'):
        parser.add_argument('--' + field, type=Path, required=True)
    parser.add_argument('--rank', type=int, choices=[RANK], default=RANK)
    parser.add_argument('--flop', choices=CASES, required=True)
    parser.add_argument('--driver', type=Path)
    parser.add_argument('--preflight', action='store_true')
    run(parser.parse_args())
