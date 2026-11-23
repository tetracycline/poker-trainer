"""Replay four completed sources and test whether the trainer offers their predecessor check."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b508_rank134_native import CASES, LINE, MODEL, PINS, observe
from hu_checked_gto_boundary import load_original, replay_native
from hu_reverified_board_pair import source_case

RECOVERED = Path('data/nl2_hu_b523_recovered_archives.json')
OUT = Path('data/nl2_hu_b523_rank134_attempts.json')


def verified_native(directory, flop, filename):
    name = f'B508-native-{flop}'
    pin = json.loads(RECOVERED.read_bytes())[name]
    aid = pin['id']
    meta = json.loads((directory / f'{aid}.json').read_bytes())
    wf = meta['workflow_run']
    assert (meta['id'], meta['name'], meta['digest'], wf['id'], wf['head_sha'], wf['repository_id']) == (
        aid, name, 'sha256:' + pin['sha256'], pin['run'], pin['head'], 1438346845)
    archive = directory / f'{aid}.zip'
    assert sha(archive.read_bytes()) == pin['sha256']
    with ZipFile(archive) as z:
        assert z.namelist() == [filename]
        (EVIDENCE / filename).write_bytes(z.read(filename))
    return pin


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--solver', type=Path, required=True)
    cli.add_argument('--originals', type=Path, required=True)
    cli.add_argument('--completed', type=Path, required=True)
    args = cli.parse_args()
    subprocess.run(['node', 'tools/hu_b523_rank134_route.cjs'], check=True)
    solver = args.solver.resolve()
    assert subprocess.check_output(['git', '-C', str(solver), 'rev-parse', 'HEAD'], text=True).strip() == SOLVER
    pool_raw = (solver / 'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)['NL2']
    sys.path.insert(0, str(solver / 'postflop/py'))
    import pipeline
    import ranges

    origins = json.loads(PINS.read_bytes())
    model = json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'], model['solver_profile'], model['family']) == (134, 'BTN_BB', 'SRP')
    attempts = []
    for flop, (turn, river, gid, eid) in CASES.items():
        def original(aid, version):
            return load_original(args.originals, aid, origins[str(aid)], 'BTN_BB', flop, turn, version,
                                 pot=550, stack=9750, pipeline=pipeline, ranges=ranges, flop_line='x b50 c')
        g = original(gid, 'gto')
        public = g['public'] + river
        if eid:
            e = original(eid, 'exp_ip')
            locked, identity, root_sha = e['source'], e['identity'], e['identity']['root_sha256']
        else:
            code = f'B508_R134_{flop.upper()}_{turn.upper()}_EXP_IP'
            filename = 'NL2_' + code + '.json.gz'
            identity = verified_native(args.completed, flop, filename)
            locked = replay_native(g, 'exp_ip', pool, pipeline, EVIDENCE / filename, identity['run'], code)
            root_sha = g['identity']['root_sha256']
        hands = []
        rows = {}
        for version, source, root in [('gto', g['source'], g['identity']['root_sha256']), ('exp_ip', locked, root_sha)]:
            observation = observe(source, public, root)
            _, local, pairs = source_case(model, source, public, LINE, 1)
            assert len(local) == observation['strict_legal_combos'] and pairs == observation['compatible_hole_card_pairs']
            hands.append(local)
            rows[version] = observation
        suits = Counter(public[1:8:2])
        assert sum(suits.values()) == 4
        assert max(suits.values()) < 3, 'Recheck this candidate against the rendered hand columns'
        attempts.append(dict(flop=flop, public_board=public, line=LINE, original_gto=g['identity'], original_lock=identity,
            common_legal_btn_hands=sorted(''.join(h) for h in hands[0] & hands[1]), sources=rows,
            turn_suit_counts=dict(suits), status='OUTSIDE_RENDERED_MONOTONE_TURN_CHECK'))
    OUT.write_bytes(json_bytes(dict(rank=134, model_id=MODEL, eligible_distinct_flops=0, attempts=attempts)))


if __name__ == '__main__':
    main()
