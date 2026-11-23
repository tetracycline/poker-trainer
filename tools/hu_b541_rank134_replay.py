"""Replay both B528 river runouts per flop and resolve the opponent rules in driver order."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b528_rank134_monotone import CASES, LINE, MODEL, VERSIONS, authenticate, decide
from hu_checked_gto_boundary import lock_metadata
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from solve_hu_multiboard_100bb import make_fallbacks

RUN = 45118400160
HEAD = '959bbdef4b02e4f9be24429ba6d3a4412ecdcc19'
PINS = Path('data/nl2_hu_b541_originals.json')
REPORT = Path('data/nl2_hu_b541_rank134_original_reach.json')


def source(archives, directory, pin, flop, turn, rivers, version):
    aid = pin['id']
    metadata = json.loads((archives / f'{aid}.json').read_bytes())
    run = metadata['workflow_run']
    assert (run['id'], run['head_sha'], run['repository_id'], run['head_repository_id']) == (
        RUN, HEAD, 1438346845, 1438346845)
    name = f'NL2-B528-{flop}-{version}'
    assert (metadata['id'], metadata['name'], metadata['digest']) == (aid, name, 'sha256:'+pin['sha256'])
    archive = archives / f'{aid}.zip'
    assert sha(archive.read_bytes()) == pin['sha256']
    with ZipFile(archive) as z:
        z.extractall(directory/name)
    s = authenticate(directory, flop, turn, rivers, version)
    assert s['subgame'] and not s['manifest']['skipped']
    assert all(0 <= s[stage]['info']['gto_expl_pct'] <= .5 for stage in ('root','subgame'))
    if version == 'exp_ip':
        assert all(0 <= s[stage]['info']['hero_gap_pct'] <= .5 for stage in ('root','subgame'))
    s.update(run=RUN, archive_code=name, archive_sha256=pin['sha256'])
    return s


def opponent_decisions(s, pool, pipeline):
    root, sub = s['root'], s['subgame']
    configs, rules = make_fallbacks('BTN_BB','exp_ip',pool,pipeline.lock_list,root['flop'],by_street=True)
    records = lock_metadata(rules)
    assert records == s['manifest']['locks']
    assert all(s[k]['hero'] == 1 and s[k]['locks'] == configs for k in ('root_job','subgame_job'))
    masks = game_reach(root,sub)[0]
    turn_start = 'x b50 c/'
    turn_node, = (n for n in sub['nodes'] if n['line'] == turn_start)

    def deals(n):
        key = '|'.join((n['board'], n['line'], str(n['player'])))
        return compatible_node_reach(root, sub, n, masks[key])['compatible_hole_card_pairs']

    target = {
        1: ('', 'x b50'),
        2: (turn_start, turn_start+'x b50', turn_start+'x b100'),
        3: (LINE[:-1], LINE+' b50', LINE+' b100', LINE+' a'),
    }
    result = []
    for street, lines in target.items():
        game = root if street == 1 else sub
        for n in game['nodes']:
            if len(n['board']) != 4+2*street or n['line'] not in lines:
                continue
            assert n['player'] == 0
            row = dict(street=street, board=n['board'], line=n['line'], seat=n['player'], actions=n['acts'])
            if street == 1:
                # Every compatible deal reaching this particular turn also reached both flop ancestors.
                row['compatible_deal_lower_bound_from_named_turn'] = deals(turn_node)
            else:
                row['compatible_deals'] = deals(n)
            result.append(row)
            if len(n['acts']) == 1:
                row['scope'] = 'FORCED_ACTION_NO_OPPONENT_LOCK'
                continue
            first = next((i for i,rule in enumerate(records) if re.search(rule['pat'],n['line'])), None)
            if first is None:
                row['scope'] = 'NO_MATCHING_LOCK'
                continue
            config, record = configs[first], records[first]
            stats = game['info']['lock_stats'][record['pat']]
            assert stats['nodes'] > 0
            row.update(first_rule_index=first, pattern=record['pat'], scope=record['scope'],
                       source=record['source'], pool_decisions=record['n'], target={
                           k:v for k,v in config.items() if k!='pat'}, driver_pattern_aggregate=stats)
            if record['scope'] == 'PINNED_MEASURED_NL2_SOURCE':
                assert street == 2
                bucket = {'b50':'34-55%', 'b100':'81-110%'}[n['line'].split()[-1]]
                assert record['source'] == f'SRP_PFR_IP.vs_turn_barrel_by_size[{bucket}]'
                measured = pool['postflop_HU']['SRP_PFR_IP']['vs_turn_barrel_by_size'][bucket]
                assert (record['n'],config['fold'],config['raise']) == (
                    measured['n'],measured['fold']/100,measured['raise']/100)
            elif record['scope'] == 'IMPUTED_HISTORY_FROM_TRUE_STREET_BY_SIZE_MARGINAL':
                assert record['street'] == street and record['n'] >= 500
            elif record['scope'] == 'ASSUMED_HISTORY_RATE_OR_SIZE':
                assert record['n'] == 0 and config['bet'] == .45 and street == 3
            else:
                assert record['scope'] == 'NL2_PFR_CB_AGGREGATE_PROXY_NOT_EXACT_SPOT' and n['line'] == ''
    assert len(result) == 2 + 3 + 4*len(sub['rivers'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals', type=Path, required=True)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(['node','tools/hu_b528_rank134_routes.cjs'],check=True)
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip() == SOLVER
    raw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    model = json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr']) == (134,'BTN_BB',8.614)
    pins = {p['name']:p for p in json.loads(PINS.read_bytes())}
    assert len(pins) == len(CASES)*len(VERSIONS)
    attempts = []
    with TemporaryDirectory() as temp:
        for flop,(turn,rivers) in CASES.items():
            sources = [source(args.originals,Path(temp),pins[f'NL2-B528-{flop}-{v}'],flop,turn,rivers,v) for v in VERSIONS]
            assert sources[0]['manifest']['preflop_ranges'] == sources[1]['manifest']['preflop_ranges']
            locks = opponent_decisions(sources[1],pool,pipeline)
            measured_streets = sorted({r['street'] for r in locks
                if r['scope'] in ('PINNED_MEASURED_NL2_SOURCE','IMPUTED_HISTORY_FROM_TRUE_STREET_BY_SIZE_MARGINAL')
                and r.get('compatible_deals',r.get('compatible_deal_lower_bound_from_named_turn',0)) > 0})
            assert measured_streets == [1,2,3]
            results = [decide(model,sources,flop,r)[1] for r in rivers]
            # These immutable sources produce no paired rendered hero holding on either river.
            assert all(r['status'] in ('NO_PAIRED_JOINT_REACH','NO_RENDERED_HAND_IN_BOTH_SOURCES') for r in results)
            assert all(r.get('common_legal_hands',0) == 0 for r in results)
            identities = {s['version']:dict(archive_sha256=s['archive_sha256'],root_sha256=s['root_sha256'],
                                              subgame_sha256=s['source_sha256']) for s in sources}
            attempts.append(dict(flop=flop,turn=turn,sources=identities,river_decisions=results,
                                 streets_with_reachable_measured_response=measured_streets,opponent_locks=locks))
    args.out.write_bytes(json_bytes(dict(source_run_id=RUN,source_head=HEAD,model_id=MODEL,line=LINE,
                                         pool_sha256=POOL,qualified_distinct_flops=0,attempts=attempts)))


if __name__ == '__main__':
    main()
