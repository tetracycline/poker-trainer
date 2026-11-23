"""Reconstruct two reachable SB barrel decisions from frozen original GTO flops."""

import argparse
import base64
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, sha, json_bytes
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b519_sb_barrels import MODELS, observations
from hu_b536_sb_barrels import tx, COLUMNS
from hu_checked_gto_boundary import load_original, prepare_job
from hu_multiboard_promote import texture
from hu_native_turn_result import replay, run_native
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey

sys.path.insert(0, str(Path(__file__).resolve().parent / "lines_pipeline"))
from run10_common import hcls, classes

PINS = Path("data/nl2_hu_b552_sb_parents.json")
CASES = {15: ("AcTc3d", "4s", "Js"), 16: ("KsQh4d", "Tc", "2c")}


def priced_job(boundary, version, pool, pipeline):
    flop = boundary["source"]["subgame"]["flop"]
    (river,) = [
        r for f, t, r in CASES.values() if f == flop and t == boundary["job"]["turn"]
    ]
    if version == "gto":
        job, meta = deepcopy(boundary["job"]), []
    else:
        job, meta = prepare_job(boundary, version, pool, pipeline)
    assert (
        job["river_oop"] == "50%,100%,a"
        and job["turn_oop"] == job["turn_ip"] == "50%,100%"
    )
    job.update(
        river_oop="50%",
        out="turn.json",
        extract=[
            dict(prefix=[], street=True),
            dict(prefix=["b50", "c", river], street=True),
        ],
    )
    return job, meta


def native_source(boundary, version, rank, args, pool, pipeline):
    flop, turn, river = CASES[rank]
    code = f"B552_R{rank}_{flop}_{turn}_{river}_{version}".upper()
    name = "NL2_" + code + ".zip"
    folder = args.results / code
    if args.driver:
        job, meta = priced_job(boundary, version, pool, pipeline)
        run_native(folder, args.driver, boundary, job, meta, args.run, version, name)
    path = folder / name
    source = replay(boundary, version, pool, pipeline, path, args.run, code, priced_job)
    source["subgame"]["rivers"] = [river]
    assert all(
        0 <= source["subgame"]["info"][k] <= 0.5
        for k in (
            ["gto_expl_pct"] if version == "gto" else ["gto_expl_pct", "hero_gap_pct"]
        )
    )
    return source, path


def route_hands(source, row, ancestry, actions):
    board = row["public_board"]
    mask = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
    hits = {}
    for h, bits in zip(source["subgame"]["hands"][0], mask, strict=True):
        if not bits:
            continue
        cells = [
            tx(board[:n]) + ":" + str(COLUMNS.get(cls, -1))
            for n, cls in (
                (6, hcls(h, board[:6])),
                (8, hcls(h, board[:8])),
                (10, classes(h, board)[0]),
            )
        ]
        label = actions.get(cells[2])
        action = {"下注 ½": "b50", "過": "x"}.get(label)
        if (
            cells[0] in ancestry[0]
            and cells[1] in ancestry[1]
            and action in row["source_actions"]
            and bits & (1 << row["source_actions"].index(action))
        ):
            hits["".join(cardkey(h))] = dict(cells=cells, river_action=action)
    return hits


def first_match_rates(source, native, pool, line):
    with ZipFile(native) as z:
        metadata = json.loads(z.read("locks.json"))
        rules = json.loads(z.read("job.json"))["locks"]
    audited = {}
    for state in (line + "/b50", line + "/b50 c/b50"):
        i = next(i for i, r in enumerate(rules) if re.search(r["pat"], state))
        m = metadata[i]
        r = rules[i]
        obs = source["applied_rust_rates"][r["pat"]]
        assert m["pat"] == r["pat"] and m["n"] >= 500 and obs["nodes"] > 0
        if m["source"].startswith("NL2.HU_facing_bet"):
            street = 2 if state == line + "/b50" else 3
            sample = pool["HU_facing_bet"][str(street)]["by_size"]["34-55%"]
        else:
            street = "turn" if state == line + "/b50" else "river"
            sample = pool["postflop_HU"]["SRP_PFR_OOP"][
                "vs_" + street + "_barrel_by_size"
            ]["34-55%"]
        assert (m["n"], r["fold"], r["raise"]) == (
            sample["n"],
            sample["fold"] / 100,
            sample["raise"] / 100,
        )
        audited[state] = dict(
            pattern=r["pat"],
            source=m["source"],
            observations=m["n"],
            fold=r["fold"],
            raise_frequency=r["raise"],
            driver_pattern_aggregate=obs,
        )
    return audited


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("solver", "originals", "results"):
        p.add_argument("--" + n, type=Path, required=True)
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--driver", type=Path)
    args = p.parse_args()
    solver = args.solver.resolve()
    assert args.run > 0
    assert (
        subprocess.check_output(
            ["git", "-C", solver, "rev-parse", "HEAD"], text=True
        ).strip()
        == SOLVER
    )
    if args.driver:
        assert (
            args.driver.resolve()
            == solver / "postflop/pfdriver/target/release/pfdriver"
        )
        assert (
            subprocess.check_output(
                ["git", "-C", solver / "postflop/postflop-solver", "rev-parse", "HEAD"],
                text=True,
            ).strip()
            == RUST
        )
    raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline, ranges

    ancestry = json.loads(
        subprocess.check_output(["node", "tools/hu_b536_sb_route_cells.cjs"])
    )
    actions = json.loads(
        subprocess.check_output(["node", "tools/hu_b552_river_action_cells.cjs"])
    )
    models = json.loads(
        Path("data/nl2_hu_multiboard_status_current.json").read_bytes()
    )["records"]
    specs = json.loads(PINS.read_bytes())
    groups = {}
    for rank, (flop, turn, river) in CASES.items():
        mid, line, pot, stack = MODELS[rank]
        model = models[mid]
        spec = specs[str(rank)]
        aid = spec["id"]
        root = load_original(
            args.originals,
            aid,
            spec,
            "SB_BB",
            flop,
            turn,
            "gto",
            pot=600,
            stack=9700,
            pipeline=pipeline,
            ranges=ranges,
            flop_line=line,
        )
        assert (
            root["identity"]["flop_oop_menu"]
            == root["identity"]["flop_ip_menu"]
            == "33%,50%,75%,100%"
        )
        original = root["source"]
        g = original
        public = root["public"] + river
        files = []
        if rank == 16:
            g, path = native_source(root, "gto", rank, args, pool, pipeline)
            files.append(path)
        else:
            assert river in g["subgame"]["rivers"]
        e, epath = native_source(root, "exp_oop", rank, args, pool, pipeline)
        files.append(epath)
        if args.driver:
            continue
        rows = [
            observations(s, line, pot, stack, root["identity"]["root_sha256"])[public]
            for s in (g, e)
        ]
        same = [
            route_hands(s, r, ancestry[str(rank)], actions[str(rank)])
            for s, r in zip((g, e), rows, strict=True)
        ]
        shared = {
            h: same[0][h]
            for h in sorted(same[0].keys() & same[1].keys())
            if same[0][h] == same[1][h]
        }
        assert shared and all(s["compatible_hole_card_pairs"] > 0 for s in rows)
        if rank == 15:
            g["archive_code"] = f"B552_R15_{flop.upper()}_ORIGINAL_GTO"
        board, pin = emit_board(model, g, e, public, line + "/b50 c/", texture(flop))
        assert (
            board["actual_pot_bb"] == pot / 100
            and board["actual_effective_stack_bb"] == stack / 100
        )
        pin.update(
            original_gto_archive=root["identity"], shared_rendered_actions=shared
        )
        board["nl2_locked_variants"][0].update(
            variant_label="原始翻牌 GTO，轉河分街 NL2 鎖頻，SB 河牌下注限半池",
            pool_sha256=POOL,
            gto_parent_source_sha256=root["identity"]["root_sha256"],
            gto_parent_source_run_id=original["run"],
            river_oop_bet_menu="50%",
            original_gto_river_oop_bet_menu=root["job"]["river_oop"],
            applied_street_rates=rates(e),
            first_matching_barrel_rates=first_match_rates(e, epath, pool, line),
            viewer_archive_code=pin.get(
                "locked_viewer_archive_code", pin["viewer_archive_code"]
            ),
            viewer_sha256=pin.get("locked_viewer_sha256", pin["viewer_sha256"]),
        )
        board.update(
            frozen_gto_flop=True,
            gto_river_oop_bet_menu=("50%" if rank == 16 else root["job"]["river_oop"]),
        )
        for path in files:
            shutil.copyfile(path, EVIDENCE / path.name)
        parent_name = (
            f"NL2_{g['archive_code']}.zip"
            if rank == 15
            else f"NL2_B552_R16_{flop.upper()}_ORIGINAL_GTO.zip"
        )
        shutil.copyfile(args.originals / f"{aid}.zip", EVIDENCE / parent_name)
        pin["original_gto_archive"]["repository_file"] = parent_name
        groups[str(rank)] = dict(
            rank=rank,
            model_id=mid,
            boards=[board],
            pins=[pin],
            gto_observation=rows[0],
            locked_observation=rows[1],
        )
    if not args.driver:
        Path("data/nl2_hu_b552_sb_river_checkpoints.json").write_bytes(
            json_bytes(dict(run=args.run, groups=groups))
        )


if __name__ == "__main__":
    main()
