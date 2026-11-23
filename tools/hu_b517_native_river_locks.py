"""Publish the measured river responses in the original B504 solve, preserving its turn assumption."""
import argparse
import base64
import gzip
import json
import re
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from hu_b504_root_only_locks import GROUPS, REGISTRY, original, register, solve_or_replay, targets, write
from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import sha
from hu_b483_locked_medium import POOL
from hu_board_reach_corrections import read_replays
from hu_sequential_cfr_reach import game_reach

SOURCE_RUN = 45109975829
SOURCE_FILE = 'data/solver_evidence/NL2_B504_14594206088.json.gz'
SOURCE_SHA = '12a26c634be7684bdfdf2464126f3d24a0f9b6742618337054429c3e1705e625'


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--originals', required=True, type=Path)
    cli.add_argument('--solver', required=True, type=Path)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip() == SOLVER
    pool_raw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    archived = Path(SOURCE_FILE).read_bytes()
    assert sha(archived) == SOURCE_SHA
    envelope = json.loads(gzip.decompress(archived))
    assert envelope['run'] == SOURCE_RUN and envelope['pool_sha256'] == POOL
    run, aid, line, turn, ranks = GROUPS[0]
    assert (aid,ranks) == (14594206088,(9,91,119))
    old = original(args.originals,run,aid,line,turn,pipeline,ranges)
    _, locked, gtos, _ = read_replays()
    models = {m['frequency_rank']:m for m in json.loads(REGISTRY.read_bytes())['records'].values()}
    selected = targets(old,ranks,models,locked,gtos)
    with TemporaryDirectory() as tmp:
        replay = SimpleNamespace(replay=Path.cwd(),run=SOURCE_RUN)
        source,path,rates = solve_or_replay(replay,old,pipeline,pool,Path(tmp))
        assert path.read_bytes() == archived
        sub = source['subgame']
        assert source['source_sha256'] == sha(base64.b64decode(envelope['source_file_b64'],validate=True))
        assert {r['street'] for r in rates} == {3} and {r['token'] for r in rates} == {'b50','b100'}
        assumption, = (r for r in envelope['locks'] if r['pat'] == '.*/x$')
        rule, = (r for r in envelope['job']['locks'] if r['pat'] == assumption['pat'])
        assert rule['bet'] == .45 and assumption['scope'] == 'ASSUMED_HISTORY_RATE_OR_SIZE' and assumption['n'] == 0
        actual = sub['info']['lock_stats'][assumption['pat']]
        assert abs(actual['agg'] - rule['bet']) < .001 and actual['nodes'] > 0
        checked_turn, = (n for n in sub['nodes'] if (n['board'],n['line'],n['player']) == ('2d7hKs9d',line+'/x',1))
        assert len(checked_turn['acts']) > 1 and any(w>1e-4 for w in checked_turn['w'][1])
        first_match = next(r for r in envelope['locks'] if re.search(r['pat'], checked_turn['line']))
        assert first_match == assumption
        disclosure = dict(pattern=rule['pat'],bet=rule['bet'],pool_decisions=assumption['n'],
                          applied_subgame_nodes=actual['nodes'],scope=assumption['scope'])
        out = Path('data/solver_evidence')
        observations = {}
        masks = game_reach(old['root'],sub)[0]
        for model, board in selected:
            status = register(out,model,board,old,source,path,rates,observations,masks,batch='B517',river_only=disclosure)
            assert status['status'] == 'REGISTERED'
            print(model['frequency_rank'],status['compatible_hole_card_pairs'])
        write(out.parent/'nl2_hu_b517_locked_medium.json',dict(schema='NL2_HU_B517_ORIGINAL_LOCKED_MEDIUM_V1',references=observations))


if __name__ == '__main__':
    main()
