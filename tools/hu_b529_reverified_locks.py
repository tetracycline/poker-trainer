"""Refit previously reverified boards and replay completed B525 subgames at additional exact decisions."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import sha
from hu_b483_locked_medium import POOL
from hu_b504_root_only_locks import REGISTRY, register, solve_or_replay, write
from hu_b521_native_street_locks import SCOPES, assumed_turn, targets
from hu_b525_native_street_locks import original
from hu_board_reach_corrections import read_replays, source_key
from hu_sequential_cfr_reach import game_reach
from solve_hu_missing_branches import EXTRA_SPOTS

PINS = Path('data/nl2_hu_b529_originals.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--originals', type=Path, required=True)
    parser.add_argument('--key')
    parser.add_argument('--run', type=int)
    parser.add_argument('--out', type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--driver', type=Path)
    modes.add_argument('--replay', type=Path)
    args = parser.parse_args()

    solver = args.solver.resolve()
    assert subprocess.check_output(['git', '-C', solver, 'rev-parse', 'HEAD'], text=True).strip() == SOLVER
    if args.driver:
        assert args.key and args.driver.resolve() == solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git', '-C', solver/'postflop/postflop-solver', 'rev-parse', 'HEAD'], text=True).strip() == RUST
    sys.path.insert(0, str(solver/'postflop/py'))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pipeline.SPOTS.update(EXTRA_SPOTS)
    raw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)['NL2']
    pins = json.loads(PINS.read_bytes())
    scopes = json.loads(SCOPES.read_bytes())['sources']
    models = json.loads(REGISTRY.read_bytes())['records']
    _, previous_locked, gto, _ = read_replays()
    reports, observations = [], {}
    if args.driver or args.replay:
        assert args.run > 0 and args.out
        out = args.out/'data/solver_evidence'
        out.mkdir(parents=True, exist_ok=True)
    if args.key:
        pins = {args.key: pins[args.key]}

    for key, pin in pins.items():
        old = original(args.originals, pin, ranges)
        scope = scopes[f"{old['run']}/{old['source_sha256']}"]
        assert scope['scope'] == 'CONFIRMED' and scope['evidence'] and pin['source_sha256'].startswith(key)
        selected = targets(pin, old, models, previous_locked, gto)
        for model, board, _ in selected:
            descriptor = Path('data/solver_evidence/reverified')/f"rank{model['frequency_rank']}.json"
            group = json.loads(descriptor.read_bytes())
            assert group['model_id'] == model['model_id']
            assert any(b['public_board'] == board['public_board'] and b['source_sha256'] == board['source_sha256']
                       and b['source_run_id'] == board['source_run_id'] for b in group['boards'])
        if not args.driver and not args.replay:
            print(key, len(selected))
            continue

        source_batch = pin.get('reuse_batch', 'B529')
        code = f'{source_batch}_{key}'
        native_args = argparse.Namespace(**vars(args))
        if 'reuse_batch' in pin:
            assert source_batch == 'B525' and not args.driver
            native_args.run = pin['native_run']
        if args.replay:
            packed = args.replay/'data/solver_evidence'/f'NL2_{code}.json.gz'
            if not packed.is_file():
                reports.append(dict(parent_source=key, status='MISSING_COMPLETED_OUTPUT'))
                continue
        source, path, rates = solve_or_replay(native_args, old, pipeline, pool, out, archive_code=code)
        if args.driver:
            return
        source['manifest']['pot_family'] = pin['family']
        envelope = json.loads(gzip.decompress(path.read_bytes()))
        assumed = assumed_turn(old, source, envelope, rates)
        masks = game_reach(old['root'], source['subgame'])[0]
        for model, board, previous in selected:
            row = register(out, model, board, old, source, path, rates, observations, masks,
                           batch='B529', source_suffix='_' + key, river_only=assumed)
            row.update(parent_source=key, model_id=model['model_id'])
            reports.append(row)
            if row['status'] == 'REGISTERED':
                overlay_path = out/'lock_variants'/f"rank{model['frequency_rank']}_b529_{key}.json"
                overlay = json.loads(overlay_path.read_bytes())
                overlay['after_reverification'] = True
                write(overlay_path, overlay)
                observations[source_key(model['model_id'], previous)] = previous
    if args.replay:
        write(args.out/'data/nl2_hu_b529_native_street_locks.json', dict(run=args.run, pool_sha256=POOL, records=reports))
        write(args.out/'data/nl2_hu_b529_locked_medium.json', dict(schema='NL2_HU_B529_ORIGINAL_LOCKED_MEDIUM_V1', references=observations))


if __name__ == '__main__':
    main()
