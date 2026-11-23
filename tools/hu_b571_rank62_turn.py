"""Replay native CO 75%-flop barrels and BB turn checks on their real card ranges."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b492_half_pot_leads import zip_payload
from hu_b518_rank220_native import RANGES as CO_RANGE_PINS
from hu_b527_checked_barrels import COLUMNS, board_row
from hu_b534_rank62 import LINE, MODEL
from hu_b556_iso_decisions import decision_hands
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, lock_metadata
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from solve_hu_multiboard_100bb import make_fallbacks

TURNS = {
    "AhKd6c": ["2s", "Tc", "7d"],
    "Ac9d4s": ["2h", "8c", "Js"],
    "TdTc5c": ["3h", "9c", "2s"],
}
VERSIONS = ["gto", "exp_ip"]
DATA = Path("data")
CATALOG = DATA / "nl2_hu_b571_rank62_sources.json"
REPORT = DATA / "nl2_hu_b571_rank62_checkpoints.json"
TOKENS = {"過": "x", "下注 ½": "b50", "下注 ¾": "b75"}


def name(flop):
    return "B571_R62_" + flop.upper()


def node(game, line, public):
    (result,) = (n for n in game["nodes"] if n["line"] == line and n["board"] == public)
    return result


def root_job(pipeline, flop):
    extracts = [{"prefix": [], "street": True}] + [
        {"prefix": ["x", "b75", "c", t], "street": False, "raw": True}
        for t in TURNS[flop]
    ]
    job = pipeline.make_job(
        "CO_BB",
        "gto",
        flop,
        "result.json",
        iters=1700,
        target=0.5,
        extract=extracts,
        compress=True,
    )
    job.update(flop_ip="75%", flop_oop="50%")
    assert sha(compact([job["oop"], job["ip"]])) == CO_RANGE_PINS["gto"]
    return job


def turn_job(pipeline, pool, root, turn, version):
    flop = root["flop"]
    rows, meta = make_fallbacks(
        "CO_BB", version, pool, pipeline.lock_list, flop, by_street=True
    )
    job = pipeline.make_job(
        "CO_BB",
        version,
        flop,
        "result.json",
        compress=False,
        target=0.40,
        rank=0.40,
        iters=2000,
        locks=rows,
    )
    job.update(pipeline.SUB)
    job.update(
        oop="",
        ip="",
        turn=turn,
        pot=1376,
        stack=9337,
        line0=["x", "b75", "c", "/"],
        root_no_bet=False,
        extract=[{"prefix": [], "street": True}],
    )
    (parent,) = (
        n
        for n in root["nodes"]
        if n["line"] == "x b75 c/" and n["board"].endswith(turn)
    )
    assert (parent["bets"], parent["pot"]) == ([413, 413], 1376) and root[
        "stack"
    ] - 413 == 9337
    for i, k in enumerate(("oop_w", "ip_w")):
        job[k] = [
            [h, w]
            for h, w in zip(root["hands"][i], parent["wr"][i], strict=True)
            if w > 1e-4
        ]
    return job, lock_metadata(meta)


def capture(directory, solver):
    assert (
        subprocess.check_output(
            ["git", "-C", solver / "postflop/postflop-solver", "rev-parse", "HEAD"],
            text=True,
        ).strip()
        == RUST
    )
    result = {}
    for flop, turns in TURNS.items():
        scope = directory / flop
        if not (scope / "flop/result.json").exists():
            continue
        entries = {}
        for sub in ["flop"] + [t + "-" + v for t in turns for v in VERSIONS]:
            if not (scope / sub / "result.json").exists():
                continue
            for fn in ["job.json", "result.json"]:
                entries[sub + "/" + fn] = (scope / sub / fn).read_bytes()
        pack = EVIDENCE / ("NL2_" + name(flop) + ".zip")
        zip_payload(pack, entries)
        result[flop] = {
            "name": pack.name,
            "sha256": sha(pack.read_bytes()),
            "members": {k: sha(b) for k, b in entries.items()},
        }
    assert result
    CATALOG.write_bytes(
        json_bytes(
            {
                "solver": SOLVER,
                "engine": RUST,
                "pipeline": PIPELINE,
                "ranges": RANGES,
                "pool": POOL,
                "originals": result,
            }
        )
    )


def read_game(z, prefix, job):
    assert z.read(prefix + "/job.json") == compact(job)
    raw = z.read(prefix + "/result.json")
    game = json.loads(raw)
    assert all(job[k] == game[k] for k in ("flop", "pot", "stack"))
    assert (
        0 <= game["info"]["gto_expl_pct"] <= 0.5
        and job["rake_rate"] == 0.05
        and job["rake_cap"] == 1000
    )
    return game, sha(raw)


def responder(source, public, pool):
    sub = source["subgame"]
    job = source["subgame_job"]
    records = source["manifest"]["locks"]
    target = node(sub, LINE, public)
    assert target["player"] == 1 and target["bets"] == [0, 0] and target["pot"] == 1376
    assert {"x", "b50", "b100"} <= set(target["acts"])
    opener = node(sub, "x b75 c/", public)
    assert (
        opener["player"] == 0
        and opener["acts"] != ["x"]
        and "x" in opener["acts"]
        and not job["root_no_bet"]
    )
    masks = game_reach(source["root"], sub)[0]
    amounts = {"b50": (688, "34-55%", 15700), "b100": (1376, "81-110%", 4480)}
    rates = []
    for action, (bet, bucket, expected) in amounts.items():
        line = LINE + " " + action
        n = node(sub, line, public)
        assert (n["player"], n["bets"], n["pot"]) == (0, [0, bet], 1376 + bet)
        matches = compatible_node_reach(
            source["root"], sub, n, masks[f"{public}|{line}|0"]
        )
        rule = next(r for r in job["locks"] if re.search(r["pat"], line))
        meta = next(r for r in records if re.search(r["pat"], line))
        stat = sub["info"]["lock_stats"][rule["pat"]]
        metric = "vs_turn_barrel_by_size"
        obs = pool["postflop_HU"]["SRP_PFR_IP"][metric][bucket]
        assert meta["source"] == f"SRP_PFR_IP.{metric}[{bucket}]" and stat["nodes"] > 0
        assert meta["pat"] == rule["pat"] and meta["n"] == obs["n"] == expected
        assert (rule["fold"], rule["raise"]) == (obs["fold"] / 100, obs["raise"] / 100)
        assert (
            abs(stat["fold"] - rule["fold"]) < 0.0001
            and abs(stat["agg"] - rule["raise"]) < 0.0001
        )
        rates.append(
            {
                "street": 2,
                "line": line,
                "token": action,
                "opportunity": "FACING_BET",
                "pattern": rule["pat"],
                "source": meta["source"],
                "scope": meta["scope"],
                "n": obs["n"],
                "nodes": stat["nodes"],
                "compatible_hole_card_pairs": matches["compatible_hole_card_pairs"],
                "target_fold_pct": obs["fold"],
                "target_raise_pct": obs["raise"],
                "fold_pct": 100 * stat["fold"],
                "raise_pct": 100 * stat["agg"],
            }
        )
    lead = next(r for r in job["locks"] if re.search(r["pat"], opener["line"]))
    meta = next(r for r in records if re.search(r["pat"], opener["line"]))
    observed = sub["info"]["lock_stats"][lead["pat"]]
    assert (
        meta["scope"] == "ASSUMED_HISTORY_RATE_OR_SIZE"
        and meta["n"] == 0
        and lead["bet"] == 0.45
        and observed["nodes"] > 0
    )
    return rates, {
        "scope": meta["scope"],
        "source": meta["source"],
        "pat": lead["pat"],
        "assumed_bet": lead["bet"],
        "n": 0,
        "nodes": observed["nodes"],
        "applied_aggression": observed["agg"],
    }


def analyze(z, flop, pin, pipeline, pool, routes, model, run, group, medium):
    assert set(z.namelist()) == set(pin["members"]) and all(
        sha(z.read(k)) == v for k, v in pin["members"].items()
    )
    root, raw_root = read_game(z, "flop", root_job(pipeline, flop))
    canon = sha(compact(root))
    (flop_node,) = (
        n for n in root["nodes"] if n["line"] == "" and len(n["board"]) == 6
    )
    f = flop_node["board"]
    assert (root["pot"], root["stack"]) == (550, 9750) and not root["info"].get(
        "lock_stats"
    )
    for line, seat, pot, bets, action in [
        ("", 0, 550, [0, 0], "x"),
        ("x", 1, 550, [0, 0], "b75"),
        ("x b75", 0, 963, [0, 413], "c"),
    ]:
        n = node(root, line, f)
        assert (n["player"], n["pot"], n["bets"]) == (seat, pot, bets) and action in n[
            "acts"
        ]
    result = {
        "flop": flop,
        "raw_root_sha256": raw_root,
        "canonical_root_sha256": canon,
        "attempts": {},
        "selected": None,
    }
    for turn in TURNS[flop]:
        public = f + turn
        pair = []
        rows = []
        hands = []
        for v in VERSIONS:
            job, locks = turn_job(pipeline, pool, root, turn, v)
            prefix = turn + "-" + v
            if not all(job[k] for k in ("oop_w", "ip_w")):
                assert prefix + "/result.json" not in z.namelist()
                continue
            if prefix + "/result.json" not in z.namelist():
                continue
            sub, digest = read_game(z, prefix, job)
            sub.update(line0="x b75 c", turn=turn)
            assert sub["flop"] == flop and node(sub, LINE, public)["player"] == 1
            manifest = {
                "spot": "CO_BB",
                "pot_family": "SRP",
                "locks": locks,
                "flop_parent_mode": "FROZEN_GTO_FLOP",
                "gto_parent_source_run_id": run,
                "gto_parent_source_sha256": canon,
            }
            src = {
                "root": root,
                "root_sha256": canon,
                "subgame": sub,
                "subgame_job": job,
                "manifest": manifest,
                "source_sha256": digest,
                "version": v,
                "run": run,
                "archive_code": name(flop),
                "archive_sha256": pin["sha256"],
            }
            if v == "exp_ip":
                assert 0 <= sub["info"]["hero_gap_pct"] <= 0.5
                src.update(
                    verified_gto_parent={"run": run, "sha256": canon},
                    measured_lock_application=audit_patterns(
                        sub, job, manifest, pool, 1
                    ),
                )
            else:
                assert not sub["info"].get("lock_stats")
            row = audit_decision(src, public, LINE, 1, canon)
            first = {
                cls
                for j, cls in enumerate(COLUMNS)
                if f"{board_row(f)}:{j}" in routes["flop"]
            }
            actions = {
                cls: routes["turn"][key]
                for j, cls in enumerate(COLUMNS)
                if (key := f"{board_row(public)}:{j}") in routes["turn"]
            }
            d = decision_hands(src, row, first, actions)
            pair.append(src)
            rows.append(row)
            hands.append(d)
        if len(pair) != 2:
            result["attempts"][turn] = {"status": "NO_COMPLETE_NATIVE_PAIR"}
            continue
        rates, assumption = responder(pair[1], public, pool)
        shared = sorted(hands[0].keys() & hands[1].keys())
        record = {
            "public_board": public,
            "gto_pairs": rows[0]["compatible_hole_card_pairs"],
            "nl2_pairs": rows[1]["compatible_hole_card_pairs"],
            "shared_rendered_hands": shared,
            "reply_pairs": rates[0]["compatible_hole_card_pairs"],
        }
        result["attempts"][turn] = record
        if not shared or not record["reply_pairs"] or result["selected"]:
            continue
        assert min(record["gto_pairs"], record["nl2_pairs"]) > 0
        result["selected"] = public
        if not run:
            continue
        b, p = emit_board(model, *pair, public, LINE, texture(flop))
        assert (
            b["actual_pot_bb"],
            b["actual_effective_stack_bb"],
            b["acting_seat"],
        ) == (13.76, 93.37, 1)
        b["restricted_flop_bet_sizes_by_seat"] = {"oop": [50], "ip": [75]}
        applied = b["nl2_locked_variants"][0]
        applied.update(
            applied_street_rates=rates,
            measurement_policy="FROZEN_GTO_FLOP_WITH_MEASURED_BB_TURN_BARREL_RESPONSE",
            pool_sha256=POOL,
            gto_parent_source_run_id=run,
            gto_parent_source_sha256=canon,
            viewer_archive_code=p["viewer_archive_code"],
            viewer_sha256=p["viewer_sha256"],
            variant_label="轉牌 BB 先手下注假設 45%，面對 CO 下注依 NL2 實測回應",
        )
        p.update(
            shared_rendered_route_hands=shared,
            original_raw_flop_sha256=raw_root,
            conditional_gto_flop_root_sha256=canon,
            assumed_bb_turn_lead=assumption,
            raw_archive_code=name(flop),
            source_run_role="AUTHENTICATED_IMPORT",
            original_solver_environment="LOCAL_PINNED_NATIVE_CFR",
        )
        decisions = []
        counts = {k: 0 for k in ("gto", "nl2", "both")}
        for h in shared:
            a, c = (d[h] for d in hands)
            r = {k: x for k, x in a.items() if k != "native"}
            assert r == {k: x for k, x in c.items() if k != "native"}
            r.update(gto=a["native"], nl2=c["native"])
            decisions.append(r)
            token = TOKENS[r["displayed_suggestion"]]
            for k in ("gto", "nl2"):
                counts[k] += token in r[k]["accepted_actions"]
            counts["both"] += all(
                token in r[k]["accepted_actions"] for k in ("gto", "nl2")
            )
        p.update(
            rendered_decision_hands=decisions,
            hands_accepting_displayed_suggestion=counts,
        )
        group["pins"].append(p)
        group["boards"].append(b)
        for k, row in zip(("gto_references", "references"), rows, strict=True):
            medium[k][source_key(MODEL, row)] = row
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver", required=True, type=Path)
    cli.add_argument("--capture", type=Path)
    cli.add_argument("--run", type=int, default=0)
    cli.add_argument("--out", type=Path, default=REPORT)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert (
        subprocess.check_output(
            ["git", "-C", solver, "rev-parse", "HEAD"], text=True
        ).strip()
        == SOLVER
    )
    for path, digest in [
        ("postflop/py/pipeline.py", PIPELINE),
        ("postflop/py/ranges.py", RANGES),
        ("inputs/pool_stats.json", POOL),
    ]:
        assert sha((solver / path).read_bytes()) == digest
    if args.capture:
        capture(args.capture, solver)
    pins = json.loads(CATALOG.read_bytes())
    assert (
        pins["solver"],
        pins["engine"],
        pins["pool"],
        pins["pipeline"],
        pins["ranges"],
    ) == (SOLVER, RUST, POOL, PIPELINE, RANGES)
    pool = json.loads((solver / "inputs/pool_stats.json").read_bytes())["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline

    routes = json.loads(
        subprocess.check_output(["node", "tools/hu_b571_rank62_route.cjs"])
    )
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())[
        "records"
    ][MODEL]
    assert (
        model["frequency_rank"],
        model["solver_profile"],
        model["street"],
        model["assumed_model_node_spr"],
    ) == (62, "CO_BB", 1, 6.791)
    group = {"rank": 62, "model_id": MODEL, "boards": [], "pins": []}
    medium = {
        "schema": "NL2_HU_B571_ORIGINAL_LOCKED_MEDIUM_V1",
        "references": {},
        "gto_references": {},
    }
    found = []
    for f, p in pins["originals"].items():
        path = EVIDENCE / ("NL2_" + name(f) + ".zip")
        assert path.name == p["name"] and sha(path.read_bytes()) == p["sha256"]
        with ZipFile(path) as z:
            found.append(
                analyze(z, f, p, pipeline, pool, routes, model, args.run, group, medium)
            )
    if args.run and len(group["boards"]) >= 3:
        assert len({b["flop"] for b in group["boards"]}) == len(group["boards"]) == 3
        (EVIDENCE / "reverified/rank62.json").write_bytes(json_bytes(group))
        (DATA / "nl2_hu_b571_locked_medium.json").write_bytes(json_bytes(medium))
    args.out.write_bytes(
        json_bytes(
            {
                "schema": "NL2_HU_B571_CO_CHECKED_TURNS_V1",
                "run": args.run,
                "attempts": found,
                "witnesses": group if args.run else None,
                "distinct_flops": sum(bool(r["selected"]) for r in found),
            }
        )
    )
    print([(r["flop"], r["selected"]) for r in found])


if __name__ == "__main__":
    main()
