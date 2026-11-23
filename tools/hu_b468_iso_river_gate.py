"""Replay the paired ISO CO-OOP source trees at the first public river of each exact line."""
import argparse
import gzip
import json
import subprocess

from hu_b463_rank45_gate import DATA, GATE, PRIOR, THIRD, archive_path, digest, exact_pair
from hu_b467_river_source_gate import NoLegalRiver, export_board, json_bytes, publish_bytes

PROOF = DATA / "nl2_hu_b468_iso_river_gate.json"
BASE = DATA / "nl2_hu_multiboard_status_v51_b453_rank32.json"
TARGETS = {
    140: ("ln-iso-iso_r_model-1gds1ky", "x x/b50 c/", 4.803),
    160: ("ln-iso-iso_r_model-17k9x0l", "x x/x x/", 10.105),
    161: ("ln-iso-iso_r_model-19fbxqk", "x x/x x/", 10.105),
}


def replay(frozen, verify=False):
    routes = json.loads(subprocess.check_output(["node", "tools/hu_b468_iso_trainer_routes.cjs"]))
    records = json.loads(BASE.read_bytes())["records"]
    groups = {}
    for rank, (model_id, line, spr) in TARGETS.items():
        record = records[model_id]
        route = routes[str(rank)]
        assert (record['label'], record['frequency_rank'], record['solver_profile'],
                record['street'], record['source_model_id'], record['assumed_model_node_spr']) == (
                    'APPROX', rank, 'ISO_BTN_CO', 2, route['source_model_id'], spr)
        groups[rank] = dict(model_id=model_id, rank=rank, spot="ISO_BTN_CO", actor="CO_OOP", line=line,
                            trainer_scope=route, boards=[], pins=[], source_exclusions=[])
    for code, flop, turn, run, expected_sha in frozen:
        archive = archive_path(code).read_bytes()
        assert digest(archive) == expected_sha
        pack = json.loads(gzip.decompress(archive))
        parent, pin = exact_pair(pack, code, flop, turn, run, expected_sha)
        # Both check-through models lead to the same exact public subgame.
        # The UI route test above checks the two different parent table IDs.
        for rank in (140, 160):
            _, line, spr = TARGETS[rank]
            group = groups[rank]
            if parent is None:
                group['source_exclusions'].append(dict(flop=flop, reason="NO_COMPATIBLE_PAIRED_PARENT"))
                continue
            try:
                board, evidence = export_board(pin, parent, pack["source_arrays"], rank, line, spr,
                                               verify=verify, archive_digest=expected_sha)
            except NoLegalRiver as why:
                group['source_exclusions'].append(dict(flop=flop, reason=str(why)))
                continue
            assert board["assumed_preflop_ranges"] and board["source_kind"] == "ASSUMED_EXPLICIT_169CLASS"
            group["boards"].append(board)
            group["pins"].append(evidence)
    assert TARGETS[160][1:] == TARGETS[161][1:]
    for field in ("boards", "pins", "source_exclusions"):
        groups[161][field] = list(groups[160][field])
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    frozen = list(PRIOR)
    source_gate_sha = None
    if GATE.is_file():
        upstream = json.loads(GATE.read_bytes())
        assert (upstream["model_id"], upstream["rank"]) == ('ln-iso-iso_t_model-1x553s3', 45)
        third, = (p for p in upstream["pins"] if p["archive_code"] == THIRD[0])
        assert third["flop"] == THIRD[1] and third["turn"] == THIRD[2]
        frozen.append((*THIRD, third["source_run_id"], third["archive_sha256"]))
        source_gate_sha = digest(GATE.read_bytes())
    assert len({row[1] for row in frozen}) == len({row[3] for row in frozen}) == len(frozen)
    groups = replay(frozen, verify=args.verify)
    extensions = DATA / "solver_evidence/extensions"
    extensions.mkdir(exist_ok=True)
    for group in groups.values():
        flops = [b['flop'] for b in group['boards']]
        assert len(set(flops)) == len(flops)
        group['trainer_scope'].update(
            generic_trainer_cells_certified=[],
            claim="NAMED_ACTION_LINE_EXAMPLES_ONLY",
            source_flop_textures={b['flop']:b['flop_texture'] for b in group['boards']})
        group['certifiable'] = len(flops) == 3
        destination = extensions / f"rank{group['rank']}.json"
        if group['certifiable']:
            publish_bytes(destination, json_bytes(group), args.verify)
        else:
            assert not destination.exists(), f"Stale unsupported certification: {destination}"
    result = dict(schema='NL2_HU_B468_ISO_OOP_RIVER_V1', source_gate_sha256=source_gate_sha,
                  river_selection='LEXICOGRAPHICALLY_FIRST_PUBLIC_RIVER_BEFORE_PRIVATE_MASK',
                  nl2_frequency_scope='POOL_STREET_AND_SIZE_MARGINAL',
                  original_flops_replayed_per_model=len(frozen), distinct_original_solve_pairs=len(frozen),
                  third_original_source_published=source_gate_sha is not None,
                  shared_line_models=[160,161], models=list(groups.values()))
    publish_bytes(PROOF, json_bytes(result), args.verify)
    print({rank:(len(group['boards']),group['certifiable']) for rank,group in groups.items()})


if __name__ == '__main__':
    main()
