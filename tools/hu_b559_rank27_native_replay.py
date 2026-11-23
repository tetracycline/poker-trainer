"""Verify a locked continuation from a completed third-pot turn barrel in a limped pot."""
import argparse
import base64
import gzip
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import sha
from hu_b483_locked_medium import POOL, proof
from hu_b532_limp_barrels import authenticate
from hu_b536_sb_barrels import tx
from hu_checked_gto_boundary import replay_native
from hu_sequential_cfr_reach import cardkey, game_reach

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lines_pipeline'))
from run10_common import classes, hcls

FLOP, TURN = '7h6d4s', '8c'
LINE = 'b50 c/b33 c/'
RUN = 45119248711
ARTIFACT = 14793354999
ARCHIVE_SHA = '624c4a7bcc4e8d90d347473c6927076a1e5e6a9d2c0c20b7709ec67684af57b8'
CODE = 'B559_R27_7H6D4S_8C_EXP_OOP'


def witnesses(source, public, route, masks):
    sub = source['subgame']
    node, = (n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (public, LINE, 0))
    row = proof(source['root'], sub, node, masks)
    bets = base64.b64decode(row['compatible_action_mask_b64'], validate=True)
    seen = {}
    for h, bits in zip(sub['hands'][0], bets, strict=True):
        if not bits:
            continue
        hand = ''.join(cardkey(h))
        types = (hcls(hand, public[:6]), hcls(hand, public[:8]), classes(hand, public)[0])
        for street, group in enumerate(types):
            category = tx(public[:6+2*street])
            if category not in route or group not in route[category][street]:
                break
        else:
            seen[hand] = [a for i,a in enumerate(node['acts']) if bits & (1 << i)]
    return dict(compatible_pairs=row['compatible_hole_card_pairs'], named_hands=seen,
                half_pot_eligible_combos=(row['b50'] or {}).get('eligible', 0))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--original', required=True, type=Path)
    cli.add_argument('--solver', required=True, type=Path)
    cli.add_argument('--out', required=True, type=Path)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip() == SOLVER
    assert sha((solver/'inputs/pool_stats.json').read_bytes()) == POOL
    sys.path.insert(0, str(solver/'postflop/py'))
    import pipeline
    pool = json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    raw = (args.original/f'{ARTIFACT}.zip').read_bytes()
    assert sha(raw) == ARCHIVE_SHA
    runouts = json.loads(Path('data/nl2_hu_b532_flops.json').read_bytes())['27'][FLOP]
    with TemporaryDirectory() as directory, ZipFile(BytesIO(raw)) as archive:
        for item in archive.namelist():
            assert not Path(item).is_absolute() and '..' not in Path(item).parts
        archive.extractall(Path(directory) / f'NL2-B532-{FLOP}-gto')
        g = authenticate(Path(directory),FLOP,TURN,runouts,'gto')
    g.update(run=RUN, archive_code=f'GHA_{ARTIFACT}', archive_sha256=ARCHIVE_SHA)
    public = g['subgame']['nodes'][0]['board'][:8]
    ident = dict(artifact_id=ARTIFACT, artifact_run=RUN, artifact_sha256=ARCHIVE_SHA,
                 root_sha256=g['root_sha256'], source_sha256=g['source_sha256'])
    boundary = dict(source=g, identity=ident, job=g['subgame_job'], public=public)
    path = Path('data/solver_evidence') / f'NL2_{CODE}.json.gz'
    native = json.loads(gzip.decompress(path.read_bytes()))
    assert (native['execution'], native['batch'], native['run'], native['rust']) == ('LOCAL_PINNED_RUST', 559, None, RUST)
    e = replay_native(boundary, 'exp_oop', pool, pipeline, path, None, CODE)
    assert all(0 <= e['subgame']['info'][f] <= .5 for f in ('gto_expl_pct','hero_gap_pct'))
    route = json.loads(subprocess.check_output(['node','tools/hu_b532_limp_routes.cjs']))['27']
    masks = [game_reach(s['root'],s['subgame'])[0] for s in (g,e)]
    results = {}
    for river in runouts[TURN]:
        board = public+river
        gr, er = [witnesses(s, board, route, mask) for s,mask in zip((g,e),masks,strict=True)]
        shared = sorted(gr['named_hands'].keys() & er['named_hands'].keys())
        results[board] = dict(gto=gr, locked=er, common_reached_hands=shared)
    assert all(not r['common_reached_hands'] for r in results.values())
    report = dict(rank=27, original=ident, native_archive_sha256=sha(path.read_bytes()),
                  native_output_sha256=e['source_sha256'], native_execution=native['execution'],
                  applied_lock_patterns=len(e['applied_rust_rates']), public_boards=results)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+'\n')


if __name__=='__main__':
    main()
