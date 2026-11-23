"""Fit street-specific opponent marginals on original, positive-reach SRP boundaries."""

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
from hu_b521_native_street_locks import SCOPES, assumed_turn, original, targets
from hu_board_reach_corrections import read_replays, source_key
from hu_sequential_cfr_reach import game_reach


PINS = Path('data/nl2_hu_b526_originals.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals', required=True, type=Path)
    parser.add_argument('--solver', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--run', type=int)
    parser.add_argument('--key')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--driver', type=Path)
    mode.add_argument('--replay', type=Path)
    args = parser.parse_args()

    solver = args.solver.resolve()
    assert subprocess.check_output(['git', '-C', solver, 'rev-parse', 'HEAD'], text=True).strip() == SOLVER
    if args.driver:
        assert args.key and args.driver.resolve() == solver / 'postflop/pfdriver/target/release/pfdriver'
        engine = solver / 'postflop/postflop-solver'
        assert subprocess.check_output(['git', '-C', engine, 'rev-parse', 'HEAD'], text=True).strip() == RUST
    pool_raw = (solver / 'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)['NL2']
    sys.path.insert(0, str(solver / 'postflop/py'))
    import pipeline
    import ranges

    pins = json.loads(PINS.read_bytes())
    if args.key:
        pins = {args.key: pins[args.key]}
    registry = json.loads(REGISTRY.read_bytes())['records']
    scopes = json.loads(SCOPES.read_bytes())['sources']
    _, refs, gtos, _ = read_replays()
    if args.replay or args.driver:
        assert args.run and args.run > 0 and args.out
        out = args.out / 'data/solver_evidence'
        out.mkdir(exist_ok=True, parents=True)

    outcomes, observations = [], {}
    for key, pin in pins.items():
        old = original(args.originals, pin, ranges)
        assert pin['source_sha256'].startswith(key)
        scope = scopes[f"{old['run']}/{old['source_sha256']}"]
        assert scope['scope'] == 'CONFIRMED' and scope['evidence']
        selected = targets(pin, old, registry, refs, gtos)
        assert len(selected) == len(pin['targets']) > 0
        if not args.replay and not args.driver:
            print(key, [model['frequency_rank'] for model, _, _ in selected])
            continue
        source, path, rates = solve_or_replay(args, old, pipeline, pool, out, archive_code=f'B526_{key}')
        if args.driver:
            continue
        native = json.loads(gzip.decompress(path.read_bytes()))
        turn_assumption = assumed_turn(old, source, native, rates)
        masks, _ = game_reach(old['root'], source['subgame'])
        for model, board, prior in selected:
            row = register(out, model, board, old, source, path, rates, observations, masks,
                           batch='B526', source_suffix='_' + key, river_only=turn_assumption)
            row.update(parent_source=key, model_id=model['model_id'])
            outcomes.append(row)
            if row['status'] == 'REGISTERED':
                observations[source_key(model['model_id'], prior)] = prior

    if args.replay:
        write(out.parent / 'nl2_hu_b526_native_street_locks.json',
              dict(run=args.run, pool_sha256=POOL, records=outcomes))
        write(out.parent / 'nl2_hu_b526_locked_medium.json',
              dict(schema='NL2_HU_B526_ORIGINAL_LOCKED_MEDIUM_V1', references=observations))


if __name__ == '__main__':
    main()
