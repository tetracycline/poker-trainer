"""Verify BTN river decisions after a half-pot flop bet and checked turn on five new monotone flops."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import POOL
from hu_b508_rank134_native import LINE, MODEL, observe
from hu_b518_rank220_native import measured_rates
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lines_pipeline'))
from run10_common import classes, hcls

VERSIONS = ('gto', 'exp_ip')
CASES = {
    'Kh8h3h': ('5d', ['5h', '8s']),
    'Qc7c2c': ('3d', ['5s', '8c']),
    'Jd9d5d': ('3c', ['Qh', 'Kh']),
    'Ks9s5s': ('6c', ['4h', '2h']),
    '9d7d4d': ('8s', ['2d', 'Ah']),
}
RANGE_SHA = {'gto': '7aea0d354feb6095209205e35f2b013fe433fb818b39fdd3dcd1c10490183702',
             'exp_ip': 'c67b58b3644738888521b3c1e88257f088cffbdf83283c493b2707565a0b8cfa'}
DATA = Path('data')


def authenticate(directory, flop, turn, rivers, version):
    s = original(directory, flop, turn, version, batch='B528', spot='BTN_BB', flop_line='x b50 c',
                 flop_policy='checked-b50only', turn_policy='checkcheck', turn_extract='x x')
    root, job, sub = s['root'], s['root_job'], s['subgame']
    assert sha(compact([job['oop'], job['ip']])) == RANGE_SHA[version]
    assert s['manifest']['solver_pin'] == 'f0a173b3d9331c4ff8697359a838094f76babb35f16133e37bbd0bfb203b5253'
    assert s['manifest']['solver_ranges_sha256'] == 'f2a302b483c79995ed90031b62e65a202ae7a1fdc8695f8940fe3e8291fb2bba'
    if sub is not None:
        job = s['subgame_job']
        parent, = (n for n in root['nodes'] if n['line'] == 'x b50 c/' and n['board'].endswith(turn))
        assert parent['bets'] == [275,275] and parent['pot'] == sub['pot'] == job['pot'] == 1100
        assert root['stack'] - 275 == sub['stack'] == job['stack'] == 9475
        assert sub['rivers'] == rivers and job['root_no_bet']
        assert job['line0'] == ['x','b50','c','/'] and job['river_ip'] == job['river_oop'] == '50%,100%,a'
        for seat, key in enumerate(('oop_w','ip_w')):
            assert job[key] == [[h,w] for h,w in zip(root['hands'][seat], parent['wr'][seat], strict=True) if w > 1e-4]
    return s


def route_hands(hands, public):
    eligible = []
    for cards in sorted(hands):
        hand = ''.join(cards)
        flop_bucket = hcls(hand, public[:6])
        turn_bucket = hcls(hand, public[:8])
        river_bucket, = classes(hand, public)
        if (flop_bucket in ('TPW','MID','DRAW','WDRAW') and turn_bucket in ('TPW','MID','WDRAW')
                and river_bucket in ('TPW','MID','WDRAW')):
            eligible.append(dict(hand=hand, flop_bucket=flop_bucket, turn_bucket=turn_bucket, river_bucket=river_bucket))
    return eligible


def decide(model, sources, flop, river):
    boards = []
    for s in sources:
        matches = [n['board'] for n in s['subgame']['nodes'] if (n['line'], n['player']) == (LINE,1) and n['board'].endswith(river)]
        if not matches:
            return None, dict(status='NATIVE_TARGET_ABSENT')
        public, = matches
        boards.append(public)
    public, = set(boards)
    assert {public[i:i+2] for i in (0,2,4)} == {flop[i:i+2] for i in (0,2,4)} and len(set(flop[1::2])) == 1
    rows = [observe(s, public, s['root_sha256']) for s in sources]
    counts = {s['version']: r['compatible_hole_card_pairs'] for s,r in zip(sources, rows, strict=True)}
    if not min(counts.values()):
        return None, dict(status='NO_PAIRED_JOINT_REACH', public_board=public, compatible_deals=counts)
    pools = [source_case(model,s,public,LINE,1)[1] for s in sources]
    shared = pools[0] & pools[1]
    witness = route_hands(shared, public)
    info = dict(public_board=public, compatible_deals=counts, common_legal_hands=len(shared),
                route_witnesses=witness, status='PAIRED_RENDERED_RIVER' if witness else 'NO_RENDERED_HAND_IN_BOTH_SOURCES')
    return (rows if witness else None), info


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--downloads', type=Path, required=True)
    cli.add_argument('--run', type=int, required=True)
    args = cli.parse_args()
    assert args.run > 0
    subprocess.run(['node', 'tools/hu_b528_rank134_routes.cjs'], check=True)
    model = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr']) == (134,'BTN_BB',8.614)
    batch = dict(rank=134, model_id=MODEL, boards=[], pins=[])
    medium = dict(schema='NL2_HU_B528_ORIGINAL_LOCKED_MEDIUM_V1', references={}, gto_references={})
    attempts = []
    for flop,(turn,rivers) in CASES.items():
        audit = dict(flop=flop,turn=turn,rivers={},versions={},selected=None)
        attempts.append(audit)
        sources = []
        for v in VERSIONS:
            manifest = args.downloads / f'NL2-B528-{flop}-{v}/trainer/evidence/{flop}-{v}.json'
            if not manifest.is_file() or json.loads(manifest.read_bytes())['failures']:
                audit['versions'][v] = dict(status='NO_COMPLETED_ORIGINAL')
                continue
            s = authenticate(args.downloads,flop,turn,rivers,v)
            audit['versions'][v] = dict(root=s['root_sha256'], subgame=s['source_sha256'], skips=s['manifest']['skipped'])
            if s['subgame'] is not None:
                sources.append(s)
        if len(sources) != 2:
            audit['status'] = 'NO_PAIRED_SUBGAME'
            continue
        g,e = sources
        assert g['manifest']['preflop_ranges'] == e['manifest']['preflop_ranges']
        if not all(0 <= s[k]['info']['gto_expl_pct'] <= .5 for s in sources for k in ('root','subgame')) or not all(
                0 <= e[k]['info']['hero_gap_pct'] <= .5 for k in ('root','subgame')):
            audit['status'] = 'CONVERGENCE_OUTSIDE_GATE'
            continue
        rates = measured_rates(e)
        if not {1,2,3} <= {r['street'] for r in rates}:
            audit['status'] = 'INCOMPLETE_STREET_LOCKS'
            continue
        blob = gzip.compress(compact(dict(run_id=args.run, flop=flop, turn=turn, source_arrays=sources)), mtime=0)
        code = f'B528_R134_{flop.upper()}_{args.run}'
        for s in sources:
            s.update(run=args.run,archive_code=code,archive_sha256=sha(blob))
        for river in rivers:
            rows, info = decide(model,sources,flop,river)
            audit['rivers'][river] = info
            if not rows or audit['selected']:
                continue
            public = info['public_board']
            b, pin = emit_board(model,g,e,public,LINE,texture(flop))
            assert (b['actual_pot_bb'],b['actual_effective_stack_bb']) == (11,94.75)
            assert pin['common_legal_hero_combos'] == info['common_legal_hands']
            pin['shared_rendered_route_hands'] = info['route_witnesses']
            b['nl2_locked_variants'][0].update(variant_label='翻牌至河牌分街 NL2 鎖頻',measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
                pool_sha256=POOL,applied_street_rates=rates,viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
            batch['boards'].append(b)
            batch['pins'].append(pin)
            gr,er = rows
            medium['gto_references'][source_key(MODEL,gr)] = gr
            medium['references'][source_key(MODEL,er)] = er
            audit['selected'] = public
            (EVIDENCE / f'NL2_{code}.json.gz').write_bytes(blob)
        audit['status'] = 'PAIRED_RENDERED_RIVER' if audit['selected'] else 'NO_PAIRED_RENDERED_HAND'
    count = len(batch['boards'])
    assert len({b['flop'] for b in batch['boards']}) == count <= 5
    if count >= 3:
        (EVIDENCE/'reverified/rank134.json').write_bytes(json_bytes(batch))
        (DATA/'nl2_hu_b528_locked_medium.json').write_bytes(json_bytes(medium))
    (DATA/'nl2_hu_b528_rank134_monotone.json').write_bytes(json_bytes(dict(run=args.run, model_id=MODEL,
        qualified_distinct_flops=count, attempts=attempts, verified_pairs=batch, locked_medium=medium)))


if __name__ == '__main__':
    main()
