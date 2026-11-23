"""Replay the BB caller's river decision after two actual half-pot SB bets and calls."""

import argparse
import base64
import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b492_half_pot_leads import zip_payload
from hu_b514_turn_stab import rates
from hu_b536_sb_barrels import COLUMNS, tx
from hu_b552_measured_sb_rivers import classes, hcls
from hu_b560_rank16 import read_job
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import lock_metadata
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import accepted, cardkey, compatible_node_reach, game_reach
from solve_hu_multiboard_100bb import make_fallbacks
from verify_hu_multiboard_100bb import lock_scope

DATA = Path("data")
MID = "ln-ipc-r_model-1a3ai9a"
TURNS = {"9c6h2d": ("4s", "7d", "3h"), "8s5d3c": ("2h", "6s", "7c"), "7h5c3s": ("2d", "8h", "6c")}
RIVERS = ("2c", "3s", "4c", "5s", "6h", "7d", "8c", "9d", "2s", "3d", "4h", "5c", "6s", "7c", "8h", "9s")
FLOP_LINE = "b50 c"
LINE = "b50 c/b50 c/x"


def root_job(flop, pipeline):
    exports = [dict(prefix=[], street=True)] + [
        dict(prefix=["b50", "c", t], street=False, raw=True) for t in TURNS[flop]
    ]
    j = pipeline.make_job(
        "SB_BB", "gto", flop, "result.json", iters=1700, target=0.5, extract=exports, compress=True
    )
    j.update(flop_oop="50%", flop_ip="50%")
    return j


def turn_job(root, flop, turn, version, pool, pipeline):
    (node,) = (n for n in root["nodes"] if n["line"] == FLOP_LINE + "/" and n["board"].endswith(turn))
    assert (node["pot"], node["bets"]) == (1200, [300, 300])
    public = node["board"]
    rivers = [
        r
        for r in RIVERS
        if r not in set(public[i : i + 2] for i in (0, 2, 4, 6))
        and tx(public + r) in ("low", "paired", "mono")
    ]
    rows, meta = make_fallbacks("SB_BB", version, pool, pipeline.lock_list, flop, by_street=True)
    job = pipeline.make_job(
        "SB_BB",
        version,
        flop,
        "result.json",
        iters=2000,
        target=0.45,
        rank=0.45,
        compress=False,
        locks=rows,
    )
    exports = [dict(prefix=[], street=True)]
    for r in rivers:
        prefix = ["b50", "c", r]
        exports.extend(dict(prefix=prefix + end, street=False) for end in ([], ["x"], ["x", "b50"]))
    job.update(pipeline.SUB)
    job.update(
        oop="",
        ip="",
        turn=turn,
        pot=1200,
        stack=9400,
        line0=["b50", "c", "/"],
        root_no_bet=False,
        turn_oop="50%",
        river_oop="33%,50%,75%,100%,a",
        river_ip="50%,75%,100%,a",
        extract=exports,
    )
    for seat, name in enumerate(("oop_w", "ip_w")):
        job[name] = [
            [h, w] for h, w in zip(root["hands"][seat], node["wr"][seat], strict=True) if w > 1e-4
        ]
    return job, lock_metadata(meta), public, rivers


def conditional_source(root, raw, job, meta, version, run, pool, rivers):
    sub = json.loads(raw)
    assert (sub["flop"], sub["pot"], sub["stack"]) == (root["flop"], 1200, 9400)
    sub.update(line0=FLOP_LINE, turn=job["turn"], rivers=rivers)
    m = dict(spot="SB_BB", pot_family="SRP", locks=meta)
    s = dict(
        root=root,
        subgame=sub,
        manifest=m,
        version=version,
        run=run,
        source_sha256=sha(raw),
        applied_rust_rates=sub["info"].get("lock_stats", {}),
    )
    if version == "gto":
        assert not s["applied_rust_rates"] and not job.get("locks")
    else:
        assert job["hero"] == 1 and s["applied_rust_rates"]
        digest = sha(compact(root))
        m.update(gto_parent_source_run_id=run, gto_parent_source_sha256=digest)
        s.update(
            verified_gto_parent=dict(run=run, sha256=digest),
            measured_lock_application=audit_patterns(sub, job, m, pool, 1),
        )
    return s


def street_rates(source, job, pool):
    observed = {}
    p = pool["postflop_HU"]["SRP_PFR_OOP"]
    for state, metric in (
        ("b50 c/", "turn_barrel"),
        ("b50 c/b50 c/", "river_barrel"),
        ("b50 c/b50 c/x b50", "facing_half"),
    ):
        idx = next(i for i, rule in enumerate(job["locks"]) if re.search(rule["pat"], state))
        rule, meta = job["locks"][idx], source["manifest"]["locks"][idx]
        pat = rule["pat"]
        stats = source["applied_rust_rates"][pat]
        assert pat == meta["pat"] and stats["nodes"] > 0
        if metric == "facing_half":
            sample = pool["HU_facing_bet"]["3"]["by_size"]["34-55%"]
            assert (
                meta["n"] == sample["n"]
                and rule["fold"] == sample["fold"] / 100
                and rule["raise"] == sample["raise"] / 100
            )
            record = dict(fold=rule["fold"], raise_frequency=rule["raise"])
        else:
            sample = p[metric]
            buckets = p[metric + "_size"]
            order = ("≤33%", "34-55%", "56-80%", "81-110%", ">110%")
            total = sum(buckets[k] for k in order)
            assert (
                meta["source"] == "SRP_PFR_OOP." + metric
                and meta["n"] == sample["n"]
                and rule["bet"] == sample["pct"] / 100
            )
            assert all(
                abs(rate - buckets[bucket] / total) < 1e-10
                for (_, rate), bucket in zip(rule["sizes"], order, strict=True)
            )
            assert abs(stats["agg"] - rule["bet"]) < 0.001
            record = dict(bet_frequency=rule["bet"], measured_size_distribution=rule["sizes"])
        observed[state] = dict(
            record,
            source=meta["source"],
            n=sample["n"],
            first_matching_pattern=pat,
            nodes=stats["nodes"],
        )
    return observed


def hand_cell(hole, public):
    cls = classes(hole, public)[0] if len(public) == 10 else hcls(hole, public)
    return tx(public) + ":" + str(COLUMNS.get(cls, -1)), cls


def rendered(source, row, node, route):
    sub = source["subgame"]
    masks = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
    public = node["board"]
    actions = node["acts"]
    hands = sub["hands"][1]
    assert row["source_actions"] == actions
    result = {}
    for i, (hole, bits) in enumerate(zip(hands, masks, strict=True)):
        if not bits:
            continue
        hand = "".join(cardkey(hole))
        cats = {}
        suggestion = None
        for key, k in [("flop", 6), ("turn", 8), ("river", 10)]:
            cell, cat = hand_cell(hand, public[:k])
            cats[key + "_class"] = cat
            cats[key + "_texture"] = tx(public[:k])
            if cell not in route[key]:
                break
            suggestion = route[key][cell]
        else:
            assert suggestion in ("過", "下注 ½", "下注 ¾")
            probabilities = [max(0.0, node["strat"][j * len(hands) + i]) for j in range(len(actions))]
            total = sum(probabilities)
            assert total > 0
            result[hand] = dict(
                cats,
                hand=hand,
                displayed_suggestion=suggestion,
                native=dict(
                    accepted_mask=bits,
                    action_order=actions,
                    accepted_actions=[a for j, a in enumerate(actions) if bits & (1 << j)],
                    strategy={
                        a: round(p / total, 7) for a, p in zip(actions, probabilities, strict=True)
                    },
                ),
            )
    return result


def observations(source, route):
    sub = source["subgame"]
    root = source["root"]
    version = source["version"]
    m = source["manifest"]
    masks = game_reach(root, sub)[0]
    (facing,) = (n for n in sub["nodes"] if n["line"] == "b50 c/b50" and n["player"] == 1)
    assert (facing["pot"], facing["bets"]) == (1800, [600, 0]) and "c" in facing["acts"]
    scope = lock_scope(sub, m["locks"], version)
    result = {}
    for n in sub["nodes"]:
        if (n["line"], n["player"]) != (LINE, 1):
            continue
        public = n["board"]
        assert (n["pot"], n["bets"]) == (2400, [600, 600]) and {"x", "b50", "b75"} <= set(n["acts"])
        (prior,) = (
            f
            for f in sub["nodes"]
            if f["board"] == public and f["line"] == LINE[:-1] and f["player"] == 0
        )
        (half,) = (
            f
            for f in sub["nodes"]
            if f["board"] == public and f["line"] == LINE + " b50" and f["player"] == 0
        )
        assert (prior["pot"], prior["bets"]) == (2400, [600, 600]) and "x" in prior["acts"]
        assert (half["pot"], half["bets"]) == (3600, [600, 1800])
        row = proof(root, sub, n, masks)
        row.update(
            version=version,
            spot="SB_BB",
            family="SRP",
            flop=sub["flop"],
            turn=sub["turn"],
            source_run_id=source["run"],
            source_sha256=source["source_sha256"],
            archive_sha256=source["archive_sha256"],
            root_sha256=sha(compact(root)),
            gto_gap_pct=sub["info"]["gto_expl_pct"],
            locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),
            root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],
            root_locked_hero_gap_pct=None,
            root_applied_rust_lock_nodes=0,
            subgame_applied_rust_lock_nodes=sum(
                v["nodes"] for v in source["applied_rust_rates"].values()
            ),
            lock_scope=scope,
        )
        result[public] = (row, rendered(source, row, n, route))
    return result


def fresh(args, flop, model, group, medium, route, pool, pipeline, ranges):
    folder = args.results / flop
    rootjob = root_job(flop, pipeline)
    assert (rootjob["oop"], rootjob["ip"]) == tuple(
        ranges.to_str(w) for w in ranges.ranges("SB_BB", "gto")
    )
    raw = read_job(folder, rootjob, None if args.saved_root else args.driver)
    root = json.loads(raw)
    assert (root["flop"], root["pot"], root["stack"]) == (flop, 600, 9700) and not root["info"].get(
        "lock_stats"
    )
    ledger = dict(
        flop=flop,
        native_root_sha256=sha(raw),
        root_gto_gap_pct=root["info"]["gto_expl_pct"],
        turns=[],
        selected=None,
    )
    if not 0 <= root["info"]["gto_expl_pct"] <= 0.5:
        return ledger
    (facing,) = (n for n in root["nodes"] if n["line"] == "b50" and n["player"] == 1)
    (first,) = (n for n in root["nodes"] if n["line"] == "" and n["player"] == 0)
    assert (facing["pot"], facing["bets"]) == (900, [300, 0])
    leads = accepted(first, root["hands"], "b50")
    calls = accepted(facing, root["hands"], "c")
    for turn in TURNS[flop]:
        gjob, _, public, rivers = turn_job(root, flop, turn, "gto", pool, pipeline)
        heroes = {
            cardkey(h)
            for h, w in gjob["ip_w"]
            if hand_cell(h, public[:6])[0] in route["flop"]
            and hand_cell(h, public)[0] in route["turn"]
            and turn not in cardkey(h)
        } & calls
        villains = {cardkey(h) for h, w in gjob["oop_w"] if turn not in cardkey(h)} & leads
        rec = dict(
            turn=turn,
            joint_flop_heroes=sum(any(set(h).isdisjoint(v) for v in villains) for h in heroes),
            rivers={},
        )
        ledger["turns"].append(rec)
        if not rec["joint_flop_heroes"]:
            continue
        pair = []
        entries = {"flop.job.json": compact(rootjob), "flop.json": raw}
        for v in ("gto", "exp_ip"):
            job, meta, _, _ = turn_job(root, flop, turn, v, pool, pipeline)
            src = read_job(folder / (turn + "-" + v), job, args.driver)
            source = conditional_source(root, src, job, meta, v, args.run, pool, rivers)
            info = source["subgame"]["info"]
            if not 0 <= info["gto_expl_pct"] <= 0.5 or (
                v == "exp_ip" and not 0 <= info["hero_gap_pct"] <= 0.5
            ):
                rec["status"] = "CONVERGENCE_OUTSIDE_GATE"
                break
            if v == "exp_ip":
                measures = street_rates(source, job, pool)
            entries.update(
                {
                    v + "/job.json": compact(job),
                    v + "/locks.json": compact(meta),
                    v + "/native.json": src,
                }
            )
            pair.append(source)
        if len(pair) != 2:
            continue
        assert pair[0]["subgame"]["hands"] == pair[1]["subgame"]["hands"]
        code = f"B568_R64_{flop}_{turn}".upper()
        entries["provenance.json"] = compact(
            dict(
                solver=SOLVER,
                rust=RUST,
                pool_sha256=POOL,
                run=args.run,
                flop=flop,
                turn=turn,
                sha256={name: sha(b) for name, b in entries.items()},
            )
        )
        archive = folder / ("NL2_" + code + ".zip")
        if args.driver:
            zip_payload(archive, entries)
        else:
            with ZipFile(archive) as z:
                assert set(z.namelist()) == set(entries) and all(
                    z.read(k) == b for k, b in entries.items()
                )
        for s in pair:
            s.update(archive_code=code, archive_sha256=sha(archive.read_bytes()))
        grows, erows = (observations(s, route) for s in pair)
        for river in rivers:
            full = public + river
            gr, gh = grows[full]
            er, eh = erows[full]
            common = []
            for h in sorted(gh.keys() & eh.keys()):
                shared = {k: v for k, v in gh[h].items() if k != "native"}
                assert all(eh[h][k] == v for k, v in shared.items())
                common.append(dict(shared, gto=gh[h]["native"], nl2=eh[h]["native"]))
            rec["rivers"][full] = len(common)
            if not common or not all(r["b50"] and r["b50"]["eligible"] for r in (gr, er)):
                continue
            ledger["selected"] = full
            if args.driver:
                return ledger
            (EVIDENCE / archive.name).write_bytes(archive.read_bytes())
            board, pin = emit_board(model, *pair, full, LINE, texture(flop))
            assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (24.0, 88.0)
            labels = {"過": "x", "下注 ½": "b50", "下注 ¾": "b75"}
            pin.update(
                rendered_decision_hands=common,
                hands_accepting_displayed_suggestion=sum(
                    all(
                        labels[h["displayed_suggestion"]] in h[v]["accepted_actions"]
                        for v in ("gto", "nl2")
                    )
                    for h in common
                ),
            )
            board.update(
                frozen_gto_flop=True,
                trainer_assumed_river_pot_bb=route["model"]["pot_bb"],
                trainer_assumed_river_effective_stack_bb=route["model"]["effective_stack_bb"],
                native_opponent_bet_pct=[50, 50],
                restricted_flop_bet_sizes_pct=[50],
                flop_sizing_assumption="Both flop opening sizes and the small blind’s turn opening size are restricted to 50% of the pot.",
            )
            board["nl2_locked_variants"][0].update(
                variant_label="雙方翻牌與小盲轉牌開注限半池，轉河牌依小盲實測連續下注頻率鎖定",
                pool_sha256=POOL,
                gto_parent_source_sha256=sha(compact(root)),
                gto_parent_source_run_id=args.run,
                first_matching_barrel_rates=measures,
                applied_street_rates=rates(pair[1]),
                viewer_archive_code=pin["viewer_archive_code"],
                viewer_sha256=pin["viewer_sha256"],
            )
            group["boards"].append(board)
            group["pins"].append(pin)
            medium["gto_references"][source_key(MID, gr)] = gr
            medium["references"][source_key(MID, er)] = er
            return ledger
    return ledger


def historical_screen(route):
    first = json.loads((DATA / "nl2_hu_b545_local_originals.json").read_bytes())["originals"]
    later = json.loads((DATA / "nl2_hu_b557_completed_archives.json").read_bytes())["artifacts"]
    pins = [(r["flop"], "NL2_" + r["archive_code"] + ".zip", r["archive_sha256"]) for r in first]
    pins += [(r["flop"], r["source_file"], r["source_sha256"]) for r in later]
    assert len(pins) == len({flop for flop, _, _ in pins}) == 8
    results = []
    for flop, name, digest in pins:
        path = EVIDENCE / name
        assert sha(path.read_bytes()) == digest
        with ZipFile(path) as archive:
            manifest = json.loads(archive.read(f"trainer/evidence/{flop}-gto.json"))
            (case,) = manifest["cases"]
            rootbytes = archive.read("solver/postflop/" + manifest["file_flop"])
            subbytes = archive.read("solver/postflop/" + case["source_path"])
        assert (sha(rootbytes), sha(subbytes)) == (manifest["file_flop_sha256"], case["source_sha256"])
        root, sub = json.loads(rootbytes), json.loads(subbytes)
        assert case["line"] == sub["line0"] == FLOP_LINE and sub["pot"] == 1200
        masks = game_reach(root, sub)[0]
        boards = {}
        for node in sub["nodes"]:
            if (node["player"], node["line"]) != (1, LINE):
                continue
            public = node["board"]
            assert (node["pot"], node["bets"]) == (2400, [600, 600])
            legal = compatible_node_reach(root, sub, node, masks[f"{public}|{LINE}|1"])
            row = dict(compatible_action_mask_b64=legal["mask"], source_actions=node["acts"])
            count = len(rendered({"subgame": sub}, row, node, route))
            assert count == 0
            boards[public] = dict(
                original_compatible_deals=legal["compatible_hole_card_pairs"], rendered_gto_hands=count
            )
        assert boards
        results.append(dict(flop=flop, archive=name, sha256=digest, boards=boards))
    old = "2d7hKs9d5s"
    assert all(
        not any(c.startswith(tx(old[:size]) + ":") for c in route[street])
        for size, street in ((8, "turn"), (10, "river"))
    )
    return dict(
        previous_partial=dict(public_board=old, reason="NO_RENDERED_TURN_OR_RIVER_CELL"),
        original_gto_flops=results,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for n in ("solver", "results"):
        ap.add_argument("--" + n, type=Path, required=True)
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--flop", choices=TURNS)
    ap.add_argument("--driver", type=Path)
    ap.add_argument("--saved-root", action="store_true")
    args = ap.parse_args()
    solver = args.solver.resolve()
    assert (
        args.run > 0
        and subprocess.check_output(["git", "-C", solver, "rev-parse", "HEAD"], text=True).strip()
        == SOLVER
    )
    if args.driver:
        assert (
            args.flop and args.driver.resolve() == solver / "postflop/pfdriver/target/release/pfdriver"
        )
        assert (
            subprocess.check_output(
                ["git", "-C", solver / "postflop/postflop-solver", "rev-parse", "HEAD"], text=True
            ).strip()
            == RUST
        )
    blob = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(blob) == POOL
    pool = json.loads(blob)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges

    route = json.loads(subprocess.check_output(["node", "tools/hu_b568_caller_routes.cjs"]))
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())["records"][MID]
    assert (model["frequency_rank"], model["solver_profile"], model["assumed_model_node_spr"]) == (
        64,
        "SB_BB",
        3.667,
    )
    group = dict(rank=64, model_id=MID, boards=[], pins=[])
    medium = dict(schema="NL2_HU_B568_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
    if args.driver:
        out = fresh(args, args.flop, model, group, medium, route, pool, pipeline, ranges)
        (args.results / args.flop / "verification.json").write_bytes(json_bytes(out))
        print(json.dumps(out), flush=True)
        return
    records = []
    for flop in TURNS:
        receipt = args.results / flop / "verification.json"
        if not receipt.exists():
            records.append(dict(flop=flop, status="NO_COMPLETED_NATIVE_RESULT"))
            continue
        ledger = fresh(args, flop, model, group, medium, route, pool, pipeline, ranges)
        assert ledger == json.loads(receipt.read_bytes())
        records.append(ledger)
    count = len(group["boards"])
    assert count == len({b["flop"] for b in group["boards"]}) <= 3
    if count == 3:
        destination = EVIDENCE / "reverified/rank64.json"
        if destination.exists() and json.loads(destination.read_bytes()) != group:
            raise ValueError("A separate verified rank64 publication is present")
        destination.write_bytes(json_bytes(group))
        patch = "tools/hu_b568_board_amounts.patch"
        present = subprocess.run(["git", "apply", "--reverse", "--check", patch], capture_output=True)
        if present.returncode:
            subprocess.run(["git", "apply", patch], check=True)
        (DATA / "nl2_hu_b568_locked_medium.json").write_bytes(json_bytes(medium))
    (DATA / "nl2_hu_b568_caller_results.json").write_bytes(
        json_bytes(
            dict(
                run=args.run,
                count=count,
                records=records,
                paired=group,
                historical=historical_screen(route),
            )
        )
    )


if __name__ == "__main__":
    main()
