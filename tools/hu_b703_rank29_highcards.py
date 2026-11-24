"""Solve three new high-card two-suit rank29 flops with exact two-seat and UI gates."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b582_rank29_reach import DECK, LINE, cards, rendered
from hu_b637_rank57 import solve
from hu_b659_rank29_monotone import eligible_by_river
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible

MODEL = 'ln-iso-lmp_r_model-gifggm'
CASES = {
    'Kd9d4c': ['2d', '3d', '6d', '7d'],
    'Qh8h3s': ['2h', '4h', '5h', '6h'],
    'As7s2d': ['3s', '4s', '5s', '9s'],
}
RANGE_WITNESSES = {
    'Kd9d4c': ('2d', '6s', 'KcQd', 'AdAh'),
    'Qh8h3s': ('2h', '6d', 'QcKh', 'AdAc'),
    'As7s2d': ('3s', '9c', 'AcQs', 'KhKd'),
}
TEMPLATE = 'data/solver_evidence/NL2_B580_R27_LMP.zip'
TEMPLATE_SHA = 'd4b98b4351012d78aa62f3cd31b75228d4f7a35725584d86f633552fbf28369a'
ALGORITHM_PINS = {
    'tools/hu_b659_rank29_monotone.py': '167c1a6de9c98882d8487e493368585b92adc833',
    'tools/hu_b582_rank29_reach.py': '191862b9aa1f869b78e40e621f6325f15be61c9e',
    'tools/hu_b582_rank29_route.cjs': '96eaa79cef526cbc68db6d4b1c9b2698c2cf972e',
    'tools/hu_b637_rank57.py': '86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9',
    'tools/hu_b481_rank27_limp_rivers.py': '1df87de10baee731af50c89c6297bf67e3543098',
}
APP_PINS = {
    'nl2_hu_model.js': 'a98cb80d7762b464064874de39dcff6f4bf5707d',
    'nl2.js': '15aee97e53a156fe073c96a120638a8a3679958f',
}


def git_blob(path):
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def range_class(hand):
    a, b = sorted([hand[:2], hand[2:]], key=lambda card: '23456789TJQKA'.index(card[0]), reverse=True)
    return a[0] + b[0] + ('' if a[0] == b[0] else 's' if a[1] == b[1] else 'o')


def static_witness(flop, manifest, route):
    turn, river, hero, villain = RANGE_WITNESSES[flop]
    assert len(cards(flop + turn + river + hero + villain)) == 9
    weights = [manifest['preflop_ranges'][key][range_class(hand)]
        for key, hand in (('oop_169', hero), ('ip_169', villain))]
    assert min(weights) > 0
    assert all(rendered(hero, board, stage, route)
        for board, stage in ((flop, 'flop'), (flop + turn, 'turn'), (flop + turn + river, 'river')))
    return dict(turn=turn, river=river, hero=hero, villain=villain, preflop_weights=weights,
        exact_ui_each_street=True, not_a_native_strategy_witness=True)


def root_gate(root, turn, route):
    lead, = [node for node in root['nodes'] if node['line'] == '']
    call, = [node for node in root['nodes'] if node['line'] == 'b50']
    parent, = [node for node in root['nodes'] if node['line'] == 'b50 c/' and node['board'].endswith(turn)]
    assert (lead['player'], lead['pot'], call['player'], call['pot']) == (0, 250, 1, 375)
    assert (parent['player'], parent['pot'], parent['bets']) == (0, 500, [125, 125])
    public = parent['board']
    assert len(public) == 8 and cards(public[:6]) == cards(root['flop']) and public[6:] == turn
    assert len(lead['board']) == len(call['board']) == 6
    assert cards(lead['board']) == cards(call['board']) == cards(root['flop'])
    dead = cards(public)
    first = accepted(lead, root['hands'], 'b50')
    called = accepted(call, root['hands'], 'c')
    weighted = [{cardkey(hand) for hand, weight in zip(root['hands'][seat], parent['wr'][seat], strict=True)
        if weight > 1e-4 and dead.isdisjoint(cardkey(hand))} for seat in (0, 1)]
    actors = first & weighted[0]
    villains = called & weighted[1]
    deals = {hand: sum(set(hand).isdisjoint(other) for other in villains) for hand in actors}
    joint = {hand for hand, count in deals.items() if count}
    heroes = [''.join(hand) for hand in joint if rendered(''.join(hand), public[:6], 'flop', route)]
    legal = eligible_by_river(parent, route, heroes, villains)
    diagnostic = dict(oop_b50_accepted=len(first), ip_call_accepted=len(called),
        turn_weighted_oop=len(weighted[0]), turn_weighted_ip=len(weighted[1]),
        strict_two_seat_hero_combos=len(joint), compatible_hole_card_pairs=sum(deals.values()),
        flop_ui_after_ancestry=len(heroes),
        turn_ui_after_ancestry=sum(rendered(hand, public, 'turn', route) for hand in heroes),
        legal_river_count=len(legal),
        legal_river_hands={river: sorted(hands) for river, hands in legal.items()})
    return parent, legal, diagnostic


def observations(root, sub, turn, legal, route):
    sub.update(line0='b50 c', turn=turn, rivers=list(legal))
    masks = game_reach(root, sub)[0]
    targets = [node for node in sub['nodes'] if (node['line'], node['player']) == (LINE, 0)]
    assert {node['board'][-2:] for node in targets} == set(legal)
    rows, positive = {}, {}
    for node in targets:
        public = node['board']
        assert len(public) == 10 and cards(public[:6]) == cards(root['flop']) and public[6:8] == turn
        assert (node['pot'], node['bets']) == (1250, [375, 375])
        assert 'b75' in node['acts']
        row = proof(root, sub, node, masks)
        bits = base64.b64decode(row['compatible_action_mask_b64'], validate=True)
        chosen = 1 << node['acts'].index('b75')
        hands = {''.join(cardkey(hand)) for hand, mask in zip(sub['hands'][0], bits, strict=True) if mask & chosen}
        common = sorted(hands & legal[public[-2:]])
        for hand in common:
            assert all(rendered(hand, board, stage, route) for board, stage in (
                (public[:6], 'flop'), (public[:8], 'turn'), (public, 'river')))
        rows[public] = dict(strict_legal_combos=row['strict_legal_combos'],
            compatible_hole_card_pairs=row['compatible_hole_card_pairs'],
            compatible_action_mask_b64=row['compatible_action_mask_b64'],
            b50=row['b50'], displayed_b75_hands=common)
        if common:
            assert row['strict_legal_combos'] > 0 and row['compatible_hole_card_pairs'] > 0
            positive[public] = common
    return rows, positive


def run(args):
    for path, digest in {**ALGORITHM_PINS, **APP_PINS}.items():
        assert git_blob(path) == digest, (path, 'unrecognized source revision')
    solver = args.solver.resolve()
    assert subprocess.check_output(['git', '-C', solver, 'rev-parse', 'HEAD'], text=True).strip() == SOLVER
    py = solver / 'postflop/py'
    assert sha((py / 'pipeline.py').read_bytes()) == PIPELINE
    assert sha((py / 'ranges.py').read_bytes()) == RANGES
    if args.driver:
        assert args.driver.resolve() == solver / 'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git', '-C', solver / 'postflop/postflop-solver', 'rev-parse', 'HEAD'], text=True).strip() == RUST
    sys.path.insert(0, str(py))
    import pipeline
    pool_raw = (solver / 'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)['NL2']
    template_raw = Path(TEMPLATE).read_bytes()
    assert sha(template_raw) == TEMPLATE_SHA
    with ZipFile(Path(TEMPLATE)) as archive:
        root_template, turn_template, manifest = [json.loads(archive.read(name)) for name in (
            'original-flop.job.json', 'original-turn.job.json', 'original-manifest.json')]
    route_raw = subprocess.check_output(['node', 'tools/hu_b703_rank29_routes.cjs'])
    route = json.loads(route_raw)
    assert (route['model_id'], route['actor'], route['line'], route['spr']) == (MODEL, 0, LINE, 7.52)
    assert (route['root_pot'], route['root_stack'], route['turn_pot'], route['turn_stack'],
        route['river_pot'], route['river_stack']) == (250, 9900, 500, 9775, 1250, 9400)
    assert route['turn'] == ['mono:0'] and route['river'] == {'mono:0': '下注 ¾'}
    check_limp_source(dict(manifest=manifest, root_job=root_template, subgame_job=None))
    witness = static_witness(args.flop, manifest, route)
    if args.preflight:
        print(json.dumps(dict(flop=args.flop, static_witness=witness, exact_prices_verified=True)))
        return
    contract = json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    if args.driver:
        assert not args.output.exists() or not any(args.output.iterdir()), 'Use a fresh native source directory'
    else:
        assert (args.output / 'proof.json').is_file(), 'Replay requires a completed original proof'
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'rendered-routes.json').write_bytes(route_raw)
    (args.output / 'original-manifest.json').write_bytes(json_bytes(manifest))
    root_job = dict(root_template, flop=args.flop, out='result.json',
        extract=[dict(prefix=[], street=True)] + [dict(prefix=['b50', 'c', turn], street=False, raw=True) for turn in CASES[args.flop]])
    assert (root_job['pot'], root_job['stack'], root_job['flop_oop'], root_job['flop_ip']) == (250, 9900, '50%', '50%')
    check_limp_source(dict(manifest=manifest, root_job=root_job, subgame_job=None))
    root = solve(args.output / 'flop', root_job, args.driver)
    assert len(root['flop']) == 6 and cards(root['flop']) == cards(args.flop)
    assert (root['pot'], root['stack']) == (250, 9900)
    assert 0 <= root['info']['gto_expl_pct'] <= .5 and not root['info'].get('lock_stats')
    tested = []
    for turn in CASES[args.flop]:
        parent, legal, diagnostic = root_gate(root, turn, route)
        record = dict(turn=turn, root_gate=diagnostic, gto_solved=False, actor_locked=False, checks=[],
            negative_stage='ROOT_TWO_SEAT_UI_INTERSECTION_ZERO' if not legal else None)
        tested.append(record)
        if not legal:
            continue
        job = dict(turn_template, flop=args.flop, turn=turn, out='result.json',
            turn_oop='75%', turn_ip='50%,100%', river_oop='50%,75%,100%,a', river_ip='50%,75%,100%,a',
            target_pct=.45, iters=2000, extract=[dict(prefix=[], street=True)] +
            [dict(prefix=['b75', 'c', river], street=False) for river in legal])
        for seat, key in enumerate(('oop_w', 'ip_w')):
            job[key] = [[hand, weight] for hand, weight in zip(root['hands'][seat], parent['wr'][seat], strict=True) if weight > 1e-4]
        check_limp_source(dict(manifest=manifest, root_job=root_job, subgame_job=None))
        assert (job['pot'], job['stack'], job['rake_rate'], job['rake_cap']) == (500, 9775, .05, 1000)
        assert job['oop_w'] and job['ip_w']
        assert job['river_oop'] == job['river_ip'] == '50%,75%,100%,a'
        gto = solve(args.output / (turn + '-gto'), job, args.driver)
        assert cards(gto['flop']) == cards(args.flop) and (gto['pot'], gto['stack']) == (500, 9775)
        assert 0 <= gto['info']['gto_expl_pct'] <= .5 and not gto['info'].get('lock_stats')
        grows, original = observations(root, gto, turn, legal, route)
        record.update(gto_solved=True, gto_rivers=grows, gto_gap_pct=gto['info']['gto_expl_pct'])
        if not original:
            record['negative_stage'] = 'GTO_RIVER_DISPLAYED_B75_INTERSECTION_ZERO'
            continue
        locked_job, rules = prepare_job(dict(source=dict(version='gto', root=root, manifest=manifest), job=job), 'exp_oop', pool, pipeline)
        locked_job['out'] = 'result.json'
        assert locked_job['hero'] == 0 and locked_job['locks']
        locked = solve(args.output / (turn + '-exp_oop'), locked_job, args.driver)
        assert cards(locked['flop']) == cards(args.flop) and (locked['pot'], locked['stack']) == (500, 9775)
        assert 0 <= locked['info']['gto_expl_pct'] <= .5 and 0 <= locked['info']['hero_gap_pct'] <= .5
        applied = audit_patterns(locked, locked_job, dict(manifest, locks=rules), pool, 0)
        erows, paired = observations(root, locked, turn, legal, route)
        record.update(actor_locked=True, nl2_rivers=erows, measured_lock_application=applied,
            locked_hero_gap_pct=locked['info']['hero_gap_pct'], lock_rules=rules)
        for public in sorted(original.keys() & paired.keys()):
            common = sorted(set(original[public]) & set(paired[public]))
            if not common:
                continue
            assert compatible(contract, dict(public_board=public, actual_exact_action_line=LINE, acting_seat=0))
            record['checks'].append(dict(public_board=public, shared_hands=common,
                gto_b50=grows[public]['b50'], nl2_b50=erows[public]['b50']))
        record['negative_stage'] = None if record['checks'] else 'GTO_NL2_RENDERED_HAND_INTERSECTION_ZERO'
        if record['checks']:
            break
    native_paths = [path for path in args.output.rglob('*') if path.is_file() and path.name != 'proof.json']
    report = dict(schema='NL2_B703_R29_ORIGINAL_WORKER_V1', rank=29, model_id=MODEL,
        flop=args.flop, line=LINE, actor=0, solver=SOLVER, rust=RUST,
        pipeline_sha256=PIPELINE, ranges_sha256=RANGES, pool_sha256=POOL,
        source_algorithm_blobs=ALGORITHM_PINS, source_app_blobs=APP_PINS,
        source_worker_blob=git_blob('tools/hu_b703_rank29_highcards.py'),
        source_route_blob=git_blob('tools/hu_b703_rank29_routes.cjs'),
        template_archive_sha256=TEMPLATE_SHA, rendered_routes_sha256=sha(route_raw),
        root_sha256=sha((args.output / 'flop/result.json').read_bytes()),
        root_job_sha256=sha(compact(root_job)), root_gap_pct=root['info']['gto_expl_pct'],
        root_pot=250, root_stack=9900, turn_pot=500, turn_stack=9775, river_pot=1250, river_stack=9400, river_spr=7.52,
        preregistered_flops=list(CASES), preregistered_turns=CASES[args.flop],
        static_range_witness=witness, assumed_preflop_ranges=True,
        range_scope='PINNED_B580_EXPLICIT_LMP_169_CLASS_ASSUMPTION',
        lock_scope='GTO_FLOP_WITH_ACTOR_OOP_LOCKED_TURN_RIVER_NL2_STREET_MARGINALS',
        no_observed_per_hole_card_NL2_frequencies=True,
        restricted_source_menus=dict(flop_oop='50%', flop_ip='50%', turn_oop='75%', turn_ip='50%,100%',
            river_oop='50%,75%,100%,a', river_ip='50%,75%,100%,a'),
        root_gate_threshold='MAX_FREQUENCY_OR_GE40PCT_AND_GE70PCT_OF_MAX_UNCHANGED',
        native_file_sha256={str(path.relative_to(args.output)): sha(path.read_bytes()) for path in sorted(native_paths)},
        not_a_certification=True, turns=tested,
        positive_distinct_flops=int(any(record['checks'] for record in tested)),
        gto_turn_subgames=sum(record['gto_solved'] for record in tested),
        actor_locked_turn_subgames=sum(record['actor_locked'] for record in tested),
        gto_half_pot_river_nodes=sum(len(record.get('gto_rivers', {})) for record in tested),
        nl2_half_pot_river_nodes=sum(len(record.get('nl2_rivers', {})) for record in tested))
    (args.output / 'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({key: report[key] for key in ('flop', 'positive_distinct_flops', 'gto_turn_subgames',
        'actor_locked_turn_subgames', 'gto_half_pot_river_nodes', 'nl2_half_pot_river_nodes')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--flop', choices=CASES, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--driver', type=Path)
    parser.add_argument('--preflight', action='store_true')
    run(parser.parse_args())
