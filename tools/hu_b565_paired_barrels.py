"""Freeze an actual SB half-pot flop range and compare measured and GTO 75% turn barrels."""

import argparse
import base64
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns, original
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b492_half_pot_leads import zip_payload
from hu_b527_checked_barrels import COLUMNS, board_row, classes, hcls
from hu_b545_sb_half_pot import MENU, first_rates, parent_entries, register, river_rows
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import cardkey

OLD = "TdTs4h"
FRESH = ["JdJh3c", "QcQd4s"]
FLOPS = [OLD, *FRESH]
VERSIONS = ("gto", "exp_oop")
RIVERS = ["2c", "3d", "4h", "5c", "6h", "7s", "8h", "9d", "Tc", "Jh", "Qs", "Kd", "Ah"]
OLD_SHA = "aa727f334a4c80d549e268d50031548a81a56e9bd10443dedefad8873b3b202d"
MID = "ln-opfr-r_model-ka3vbv"
DATA = Path("data")
LINE = "b50 c/b75 c/"


def read_zip(path):
    with ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def boundary(folder, files, flop, turn, pipeline, ranges):
    name = f"NL2-B565-{flop}-gto"
    for path, raw in files.items():
        if not path.startswith(("trainer/evidence/", "solver/postflop/out/SB_BB/gto/")):
            continue
        relative = Path(path)
        assert not relative.is_absolute() and ".." not in relative.parts
        dest = folder / name / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    turns = ["5d"] if flop == OLD else pipeline.turns_for(flop)
    g = original(
        folder,
        flop,
        turn,
        "gto",
        batch="B565",
        spot="SB_BB",
        flop_line="b50 c",
        flop_policy="oop-b50only",
        root_pot=600,
        root_stack=9700,
        flop_profile="sb-50-only",
        turn_policy="default",
        turn_extracts=["b33 c", "b50 c", "b75 c", "b100 c"],
        turn_mode="33-50-75-100",
        turn_menu=MENU,
        frozen_turns=turns,
    )
    assert sha(compact(g["root"])) == g["root_sha256"]
    assert (g["manifest"]["solver_pin"], g["manifest"]["solver_ranges_sha256"]) == (
        PIPELINE,
        RANGES,
    )
    assert (g["root_job"]["oop"], g["root_job"]["ip"]) == tuple(
        ranges.to_str(w) for w in ranges.ranges("SB_BB", "gto")
    )
    if g["subgame"] is None:
        return g
    job = g["subgame_job"]
    (parent,) = (
        n
        for n in g["root"]["nodes"]
        if n["line"] == "b50 c/" and n["board"].endswith(turn)
    )
    assert (parent["bets"], parent["pot"], job["pot"], job["stack"]) == (
        [300, 300],
        1200,
        1200,
        9400,
    )
    assert not job["root_no_bet"] and job["line0"] == ["b50", "c", "/"]
    for seat, k in enumerate(("oop_w", "ip_w")):
        assert job[k] == [
            [h, w]
            for h, w in zip(g["root"]["hands"][seat], parent["wr"][seat], strict=True)
            if w > 1e-4
        ]
    return g


def jobs(g, version, pool, pipeline):
    if version == "gto":
        job, locks = deepcopy(g["subgame_job"]), []
    else:
        job, locks = prepare_job(
            {"source": g, "job": g["subgame_job"]}, "exp_oop", pool, pipeline
        )
        obs = pool["postflop_HU"]["SRP_PFR_OOP"]["vs_turn_barrel_by_size"]["56-80%"]
        assert obs["n"] == 10906
        pat = "^b50 c/b75$"
        job["locks"].insert(
            0, {"pat": pat, "fold": obs["fold"] / 100, "raise": obs["raise"] / 100}
        )
        locks.insert(
            0,
            {
                "pat": pat,
                "source": "SRP_PFR_OOP.vs_turn_barrel_by_size[56-80%]",
                "scope": "PINNED_MEASURED_NL2_SOURCE",
                "n": obs["n"],
            },
        )
    river_cards = [
        r
        for r in RIVERS
        if r not in [job["flop"][i : i + 2] for i in (0, 2, 4)] + [job["turn"]]
    ]
    job.update(
        turn_oop="75%",
        turn_ip="50%,100%",
        river_oop="50%,75%,a",
        river_ip="50%,75%,a",
        iters=2000,
        target_pct=0.40,
        extract=[{"prefix": [], "street": True}]
        + [{"prefix": ["b75", "c", r], "street": True} for r in river_cards],
        out="conditional.json",
    )
    return job, locks, river_cards


def policies(source, row, common):
    sub = source["subgame"]
    (node,) = (
        n
        for n in sub["nodes"]
        if (n["board"], n["line"], n["player"]) == (row["public_board"], LINE, 0)
    )
    masks = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
    result = {}
    for i, (hole, mask) in enumerate(zip(sub["hands"][0], masks, strict=True)):
        hand = "".join(cardkey(hole))
        if hand not in common:
            continue
        assert mask
        acts = node["acts"]
        weights = [node["strat"][j * len(masks) + i] for j in range(len(acts))]
        result[hand] = {
            "accepted_mask": mask,
            "action_order": acts,
            "accepted_actions": [a for j, a in enumerate(acts) if mask & (1 << j)],
            "strategy": {
                a: w / sum(weights) for a, w in zip(acts, weights, strict=True)
            },
        }
    assert result.keys() == common
    return result


def turn_proof(
    g, files, flop, turn, route, actions, pool, pipeline, driver=None, folder=None
):
    sources = []
    rows = []
    for version in VERSIONS:
        job, locks, rivers = jobs(g, version, pool, pipeline)
        name = turn + "/" + version + "/"
        jraw = compact(job)
        if driver:
            (folder / "job.json").write_bytes(jraw)
            subprocess.run(
                [str(driver.resolve()), "job.json"], cwd=folder, check=True, timeout=260
            )
            files[name + "conditional.json"] = (
                folder / "conditional.json"
            ).read_bytes()
            files[name + "job.json"] = jraw
            files[name + "locks.json"] = compact(locks)
        assert files[name + "job.json"] == jraw and files[
            name + "locks.json"
        ] == compact(locks)
        raw = files[name + "conditional.json"]
        sub = json.loads(raw)
        assert all(sub[k] == g["subgame"][k] for k in ("flop", "hands", "pot", "stack"))
        assert (
            0 <= g["root"]["info"]["gto_expl_pct"] <= 0.5
            and 0 <= sub["info"]["gto_expl_pct"] <= 0.5
        )
        sub.update(line0="b50 c", turn=turn, rivers=rivers)
        manifest = dict(
            g["manifest"],
            version=version,
            locks=locks,
            flop_parent_mode="FROZEN_GTO_FLOP",
            gto_parent_source_sha256=g["root_sha256"],
        )
        if version != "gto":
            assert 0 <= sub["info"]["hero_gap_pct"] <= 0.5
            audit_patterns(sub, job, manifest, pool, hero_seat=0)
        else:
            assert not sub["info"].get("lock_stats")
        src = {
            "root": g["root"],
            "root_sha256": g["root_sha256"],
            "subgame": sub,
            "manifest": manifest,
            "source_sha256": sha(raw),
            "version": version,
        }
        sources.append(src)
        rows.append(river_rows(src, 75, route))
    counts = {}
    for public, (gr, gh) in rows[0].items():
        er, eh = rows[1][public]
        common = gh & eh
        counts[public] = {
            "shared": len(common),
            "gto": gr["compatible_hole_card_pairs"],
            "locked": er["compatible_hole_card_pairs"],
        }
        if not common:
            continue
        rates = first_rates(sources[1], pool, public, 75)
        if [r["street"] for r in rates] != [2, 3]:
            continue
        assert all(
            r["scope"] == "PINNED_MEASURED_NL2_SOURCE"
            and r["compatible_hole_card_pairs"] > 0
            for r in rates
        )
        assert [r["n"] for r in rates] == [10906, 2230]
        hands_by = [
            policies(s, row, common) for s, row in zip(sources, (gr, er), strict=True)
        ]
        rendered = []
        for h in sorted(common):
            last = classes(h, public)[0]
            suggestion = {"x": "過", "b75": "下注 ¾"}[
                actions[f"{board_row(public)}:{COLUMNS.index(last)}"]
            ]
            rendered.append(
                {
                    "hand": h,
                    "flop_class": hcls(h, public[:6]),
                    "turn_class": hcls(h, public[:8]),
                    "river_class": last,
                    "flop_texture": board_row(public[:6]),
                    "turn_texture": board_row(public[:8]),
                    "river_texture": board_row(public),
                    "displayed_suggestion": suggestion,
                    "gto": hands_by[0][h],
                    "nl2": hands_by[1][h],
                }
            )
        return counts, (sources[0], sources[1], gr, er, sorted(common), rates), rendered
    return counts, None, []


def assess(files, flop, route, actions, pool, pipeline, ranges, driver=None):
    tested = {}
    with TemporaryDirectory() as dirname:
        folder = Path(dirname)
        for turn in ["5d"] if flop == OLD else pipeline.turns_for(flop):
            g = boundary(folder, files, flop, turn, pipeline, ranges)
            if not g["subgame"]:
                tested[turn] = "NO_ORIGINAL_TURN_SOURCE"
                continue
            tested[turn], pair, hands = turn_proof(
                g, files, flop, turn, route, actions, pool, pipeline, driver, folder
            )
            if pair:
                return tested, pair, hands
    return tested, None, []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solver", required=True, type=Path)
    ap.add_argument("--inputs", required=True, type=Path)
    ap.add_argument("--flop", choices=FLOPS)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--run", type=int)
    args = ap.parse_args()
    solver = args.solver.resolve()
    assert (
        subprocess.check_output(
            ["git", "-C", solver, "rev-parse", "HEAD"], text=True
        ).strip()
        == SOLVER
    )
    poolraw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(poolraw) == POOL
    pool = json.loads(poolraw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges

    route = json.loads(
        subprocess.check_output(["node", "tools/hu_b545_sb_routes.cjs"])
    )["18"]
    actions = json.loads(
        subprocess.check_output(["node", "tools/hu_b557_sb_river_actions.cjs"])
    )["18"]
    assert route["model"] == MID
    args.inputs.mkdir(exist_ok=True, parents=True)
    if args.flop:
        if args.flop == OLD:
            old = EVIDENCE / "NL2_B545_R18_TDTS4H.zip"
            assert sha(old.read_bytes()) == OLD_SHA and not args.manifest
            files = {
                n: b
                for n, b in read_zip(old).items()
                if n.startswith(("trainer/", "solver/"))
            }
        else:
            files = parent_entries(solver, args.flop, args.manifest)
        proof, pair, hands = assess(
            files,
            args.flop,
            route,
            actions,
            pool,
            pipeline,
            ranges,
            solver / "postflop/pfdriver/target/release/pfdriver",
        )
        files["outcome.json"] = compact(
            {
                "flop": args.flop,
                "checked": proof,
                "selected": pair[2]["public_board"] if pair else None,
                "hands": hands,
            }
        )
        zip_payload(args.inputs / f"NL2_B565_R18_{args.flop.upper()}.zip", files)
        print(files["outcome.json"].decode())
        return
    assert args.run and args.run > 0
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())[
        "records"
    ][MID]
    assert (
        model["frequency_rank"],
        model["solver_profile"],
        model["assumed_model_node_spr"],
    ) == (18, "SB_BB", 2.833)
    refs = {
        "schema": "NL2_HU_B565_ORIGINAL_LOCKED_MEDIUM_V1",
        "gto_references": {},
        "references": {},
    }
    group = {"rank": 18, "model_id": MID, "boards": [], "pins": []}
    results = {}
    for f in FLOPS:
        code = "B565_R18_" + f.upper()
        path = args.inputs / ("NL2_" + code + ".zip")
        if not path.is_file():
            continue
        files = read_zip(path)
        if f == OLD:
            old = EVIDENCE / "NL2_B545_R18_TDTS4H.zip"
            assert sha(old.read_bytes()) == OLD_SHA
            assert all(
                files[n] == raw
                for n, raw in read_zip(old).items()
                if n.startswith(("trainer/", "solver/"))
            )
        proof, pair, hands = assess(files, f, route, actions, pool, pipeline, ranges)
        record = {
            "flop": f,
            "checked": proof,
            "selected": pair[2]["public_board"] if pair else None,
            "hands": hands,
        }
        assert files["outcome.json"] == compact(record)
        results[f] = record
        if not pair:
            continue
        register(model, group, refs, args.run, code, sha(path.read_bytes()), pair)
        board, pin = group["boards"][-1], group["pins"][-1]
        board["conditional_turn_oop_bet_sizes_pct"] = [75]
        pin["rendered_decision_hands"] = hands
        counts = {k: 0 for k in ("gto", "nl2", "both")}
        for h in hands:
            action = {"過": "x", "下注 ¾": "b75"}[h["displayed_suggestion"]]
            for k in ("gto", "nl2"):
                counts[k] += action in h[k]["accepted_actions"]
            counts["both"] += all(
                action in h[k]["accepted_actions"] for k in ("gto", "nl2")
            )
        pin["hands_accepting_displayed_suggestion"] = counts
        if f == OLD:
            pin["original_b545_flop_archive_sha256"] = OLD_SHA
        assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (30, 85)
    assert results and len(group["boards"]) == len({b["flop"] for b in group["boards"]})
    record = {
        "schema": "NL2_HU_B565_RENDERED_RANK18_CHECKPOINTS_V1",
        "run": args.run,
        "attempts": results,
        "group": group,
    }
    (DATA / "nl2_hu_b565_rank18_checkpoints.json").write_bytes(json_bytes(record))
    if len(group["boards"]) >= 3:
        (EVIDENCE / "reverified/rank18.json").write_bytes(json_bytes(group))
        (DATA / "nl2_hu_b565_locked_medium.json").write_bytes(json_bytes(refs))
    print("rank18", len(group["boards"]), "dual-positive flops")


if __name__ == "__main__":
    main()
