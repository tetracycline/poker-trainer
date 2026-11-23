"""Verify the named rank16 river after a pot-sized SB flop bet and half-pot turn barrel."""

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_b492_half_pot_leads import zip_payload
from hu_b514_turn_stab import rates
from hu_b519_sb_barrels import MODELS, observations
from hu_b536_sb_barrels import COLUMNS, tx
from hu_b552_measured_sb_rivers import (
    PINS,
    classes,
    first_match_rates,
    hcls,
    priced_job,
)
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, lock_metadata
from hu_multiboard_promote import texture
from hu_native_turn_result import replay
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import accepted, cardkey
from solve_hu_multiboard_100bb import make_fallbacks

MID, FLOP_LINE, POT, STACK = MODELS[16]
LINE = FLOP_LINE + "/b50 c/"
TURNS = {"Kc9h4d": ("2s", "6d", "Tc"), "Qd7c3h": ("2s", "6d", "Jc")}
RIVERS = ("2c", "3s", "4c", "5s", "6h", "7d", "8c", "9d", "Td", "Jc", "Qh", "Kd")
B552_RUN = 45124508379
DATA = Path("data")


def root_job(flop, pipeline):
    extracts = [dict(prefix=[], street=True)]
    extracts += [dict(prefix=["b100", "c", turn], street=False, raw=True) for turn in TURNS[flop]]
    job = pipeline.make_job(
        "SB_BB", "gto", flop, "result.json", iters=1700, target=0.5, extract=extracts, compress=True
    )
    job.update(flop_ip="100%", flop_oop="100%")
    return job


def turn_job(root, flop, turn, version, pool, pipeline):
    (parent,) = (n for n in root["nodes"] if n["line"] == FLOP_LINE + "/" and n["board"].endswith(turn))
    assert (parent["bets"], parent["pot"]) == ([600, 600], 1800)
    public = parent["board"]
    rivers = [
        r
        for r in RIVERS
        if r not in {public[i : i + 2] for i in (0, 2, 4, 6)}
        and tx(public + r) in ("KQ_high", "mid_high", "paired")
    ]
    rows, meta = make_fallbacks("SB_BB", version, pool, pipeline.lock_list, flop, by_street=True)
    job = pipeline.make_job(
        "SB_BB",
        version,
        flop,
        "result.json",
        compress=False,
        target=0.45,
        rank=0.45,
        iters=2000,
        locks=rows,
    )
    job.update(pipeline.SUB)
    extracts = [dict(prefix=[], street=True)]
    for river in rivers:
        extracts += [
            dict(prefix=["b50", "c", river], street=False),
            dict(prefix=["b50", "c", river, "b50"], street=False),
        ]
    job.update(
        oop="",
        ip="",
        turn=turn,
        pot=1800,
        stack=9100,
        line0=["b100", "c", "/"],
        root_no_bet=False,
        turn_oop="50%",
        river_oop="50%",
        extract=extracts,
    )
    for seat, key in enumerate(("oop_w", "ip_w")):
        job[key] = [
            [h, w] for h, w in zip(root["hands"][seat], parent["wr"][seat], strict=True) if w > 1e-4
        ]
    return job, lock_metadata(meta), rivers, public


def read_job(folder, job, driver):
    if driver:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "job.json").write_bytes(compact(job))
        subprocess.run([str(driver.resolve()), "job.json"], cwd=folder, check=True, timeout=1100)
    assert json.loads((folder / "job.json").read_bytes()) == json.loads(compact(job))
    return (folder / "result.json").read_bytes()


def decision_hands(source, row, route, actions):
    public = row["public_board"]
    sub = source["subgame"]
    (node,) = (n for n in sub["nodes"] if (n["board"], n["line"], n["player"]) == (public, LINE, 0))
    masks = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
    hands = sub["hands"][0]
    assert row["source_actions"] == node["acts"] and "b50" in node["acts"]
    result = {}
    for i, (hole, mask) in enumerate(zip(hands, masks, strict=True)):
        if not mask:
            continue
        hand = "".join(cardkey(hole))
        cats = [hcls(hand, public[:6]), hcls(hand, public[:8]), classes(hand, public)[0]]
        textures = [tx(public[:k]) for k in (6, 8, 10)]
        keys = [t + ":" + str(COLUMNS.get(c, -1)) for t, c in zip(textures, cats, strict=True)]
        if keys[0] not in route[0] or keys[1] not in route[1] or keys[2] not in actions:
            continue
        probabilities = [max(0.0, node["strat"][j * len(hands) + i]) for j in range(len(node["acts"]))]
        total = sum(probabilities)
        assert total > 0
        result[hand] = dict(
            hand=hand,
            flop_class=cats[0],
            turn_class=cats[1],
            river_class=cats[2],
            flop_texture=textures[0],
            turn_texture=textures[1],
            river_texture=textures[2],
            displayed_suggestion=actions[keys[2]],
            native=dict(
                accepted_mask=mask,
                action_order=node["acts"],
                accepted_actions=[a for j, a in enumerate(node["acts"]) if mask & (1 << j)],
                strategy={
                    a: round(p / total, 7) for a, p in zip(node["acts"], probabilities, strict=True)
                },
            ),
        )
    return result


def evaluate(g, e, publics, route, actions, rsha):
    for source in (g, e):
        nodes = source["subgame"]["nodes"]
        (open_node,) = (n for n in nodes if n["line"] == FLOP_LINE + "/" and n["player"] == 0)
        (facing,) = (n for n in nodes if n["line"] == FLOP_LINE + "/b50" and n["player"] == 1)
        assert (open_node["pot"], open_node["bets"]) == (1800, [0, 0])
        assert (facing["pot"], facing["bets"]) == (2700, [900, 0])
        assert "b50" in open_node["acts"] and "c" in facing["acts"]
    rows = [observations(s, FLOP_LINE, POT, STACK, rsha) for s in (g, e)]
    stats = {}
    for public in publics:
        assert all(public in allrows for allrows in rows)
        gr, er = (allrows[public] for allrows in rows)
        if not all(r["compatible_hole_card_pairs"] for r in (gr, er)):
            stats[public] = 0
            continue
        gh, eh = (decision_hands(s, r, route, actions) for s, r in ((g, gr), (e, er)))
        shared = []
        for h in sorted(gh.keys() & eh.keys()):
            identical = {k: v for k, v in gh[h].items() if k != "native"}
            assert all(eh[h][k] == v for k, v in identical.items())
            shared.append(dict(identical, gto=gh[h]["native"], nl2=eh[h]["native"]))
        stats[public] = len(shared)
        if shared and all(r["b50"] and r["b50"]["eligible"] for r in (gr, er)):
            return (public, gr, er, shared), stats
    return None, stats


def record(group, report, model, g, e, hit, path, pool, identity, sizing):
    public, gr, er, hands = hit
    board, pin = emit_board(model, g, e, public, LINE, texture(g["root"]["flop"]))
    assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (36.0, 82.0)
    suggestion = {"過": "x", "下注 ½": "b50"}
    agreement = sum(
        all(suggestion[h["displayed_suggestion"]] in h[k]["accepted_actions"] for k in ("gto", "nl2"))
        for h in hands
    )
    pin.update(
        rendered_decision_hands=hands,
        hands_accepting_displayed_suggestion=agreement,
        original_gto_archive=identity,
    )
    board.update(frozen_gto_flop=True, gto_river_oop_bet_menu="50%", flop_sizing_assumption=sizing)
    board["nl2_locked_variants"][0].update(
        variant_label=(
            "翻牌開注限滿池，小盲轉河開注限半池，按 NL2 分街鎖頻"
            if identity["flop_oop_menu"] == "100%"
            else "翻牌保留四種開注尺寸，小盲河牌開注限半池，按 NL2 分街鎖頻"
        ),
        pool_sha256=POOL,
        gto_parent_source_run_id=e["verified_gto_parent"]["run"],
        gto_parent_source_sha256=e["verified_gto_parent"]["sha256"],
        river_oop_bet_menu="50%",
        applied_street_rates=rates(e),
        first_matching_barrel_rates=first_match_rates(e, path, pool, FLOP_LINE),
        viewer_archive_code=pin.get("locked_viewer_archive_code", pin["viewer_archive_code"]),
        viewer_sha256=pin.get("locked_viewer_sha256", pin["viewer_sha256"]),
    )
    group["boards"].append(board)
    group["pins"].append(pin)
    report["gto_references"][source_key(MID, gr)] = gr
    report["references"][source_key(MID, er)] = er


def historical(model, group, report, pool, pipeline, ranges, route, actions, metadata):
    flop, turn, river = "KsQh4d", "Tc", "2c"
    pin = json.loads(PINS.read_bytes())["16"]
    aid = pin["id"]
    name = "NL2_B552_R16_KSQH4D_ORIGINAL_GTO.zip"
    # The exact original GitHub archive and its original identity are already published in B552.
    with TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / f"{aid}.zip").symlink_to((EVIDENCE / name).resolve())
        (folder / f"{aid}.json").symlink_to(metadata.resolve())
        boundary = load_original(
            folder,
            aid,
            pin,
            "SB_BB",
            flop,
            turn,
            "gto",
            pot=600,
            stack=9700,
            pipeline=pipeline,
            ranges=ranges,
            flop_line=FLOP_LINE,
        )
    # These two native variants are retained in the registry history. The old full-menu
    # KQ river has legal deals, but no original GTO decision hand reaches its rendered
    # river cell. On the nine-high flop, the priced opening link is absent on every hand.
    originals = {
        row["public_board"]: row
        for row in (
            json.loads(path.read_bytes())
            for path in (EVIDENCE / "lock_variants").glob("rank16_b530_*.json")
        )
    }
    assert set(originals) == {"4dQhKsTc4c", "3d6h9sTs7c"}
    parent_source = boundary["source"]
    historical_rows = observations(
        parent_source, FLOP_LINE, POT, STACK, boundary["identity"]["root_sha256"]
    )
    retired = []
    for public, variant in sorted(originals.items()):
        if public in historical_rows:
            assert parent_source["source_sha256"] == variant["gto_sha256"]
            observed = historical_rows[public]
            assert observed["compatible_hole_card_pairs"] > 0
            assert not decision_hands(parent_source, observed, route, actions)
            reason = "NO_RENDERED_ORIGINAL_GTO_HAND"
        else:
            assert not any(cell.startswith(tx(public[:6]) + ":") for cell in route[0])
            reason = "NO_PRICED_FLOP_LINK_ON_ACTUAL_TEXTURE"
        assert (
            sha((EVIDENCE / variant["original_package"]).read_bytes())
            == variant["original_package_sha256"]
        )
        retired.append(
            dict(
                public_board=public,
                gto_run=variant["gto_run"],
                gto_sha256=variant["gto_sha256"],
                lock_run=variant["lock"]["run_id"],
                lock_sha256=variant["lock"]["sha256"],
                original_package_sha256=variant["original_package_sha256"],
                common_rendered_hands=0,
                reason=reason,
            )
        )
    group["superseded_native_variants"] = retired
    sources = []
    for v in ("gto", "exp_oop"):
        code = f"B552_R16_{flop}_{turn}_{river}_{v}".upper()
        archive = EVIDENCE / ("NL2_" + code + ".zip")
        s = replay(boundary, v, pool, pipeline, archive, B552_RUN, code, priced_job)
        sources.append(s)
    hit, summary = evaluate(
        *sources, [boundary["public"] + river], route, actions, boundary["identity"]["root_sha256"]
    )
    assert hit and summary[boundary["public"] + river] >= 6
    identity = dict(boundary["identity"], repository_file=name)
    record(
        group,
        report,
        model,
        *sources,
        hit,
        archive,
        pool,
        identity,
        "Full flop opening menu 33%, 50%, 75%, 100%",
    )


def fresh(args, flop, model, group, report, pool, pipeline, ranges, route, actions):
    folder = args.results / flop
    rootjob = root_job(flop, pipeline)
    assert tuple(rootjob[k] for k in ("oop", "ip")) == tuple(
        ranges.to_str(w) for w in ranges.ranges("SB_BB", "gto")
    )
    raw = read_job(folder, rootjob, None if args.saved_root else args.driver)
    root = json.loads(raw)
    (first,) = (n for n in root["nodes"] if n["line"] == "")
    (facing,) = (n for n in root["nodes"] if n["line"] == "b100")
    assert (root["flop"], root["pot"], root["stack"]) == (flop, 600, 9700)
    assert not root["info"].get("lock_stats") and (facing["pot"], facing["bets"]) == (1200, [600, 0])
    identity = dict(
        root_sha256=sha(compact(root)),
        native_file_sha256=sha(raw),
        job_sha256=sha(compact(rootjob)),
        flop_oop_menu="100%",
        flop_ip_menu="100%",
        run=args.run,
    )
    ledger = dict(
        flop=flop, root=identity, convergence=root["info"]["gto_expl_pct"], turns=[], selected=None
    )
    if not 0 <= root["info"]["gto_expl_pct"] <= 0.5:
        ledger["status"] = "ROOT_GAP_OVER_LIMIT"
        return ledger
    leads = accepted(first, root["hands"], "b100")
    calls = accepted(facing, root["hands"], "c")
    for turn in TURNS[flop]:
        rec = dict(turn=turn)
        ledger["turns"].append(rec)
        gj, _, rivers, public = turn_job(root, flop, turn, "gto", pool, pipeline)
        allowed = {
            cardkey(h)
            for h, w in gj["oop_w"]
            if tx(public[:6]) + ":" + str(COLUMNS.get(hcls(h, public[:6]), -1)) in route[0]
            and tx(public) + ":" + str(COLUMNS.get(hcls(h, public), -1)) in route[1]
            and turn not in cardkey(h)
        } & leads
        opponents = {cardkey(h) for h, w in gj["ip_w"] if turn not in cardkey(h)} & calls
        rec["joint_flop_heroes"] = sum(any(set(h).isdisjoint(v) for v in opponents) for h in allowed)
        if not rec["joint_flop_heroes"]:
            continue
        pair = []
        archives = []
        for version in ("gto", "exp_oop"):
            job, meta, _, _ = turn_job(root, flop, turn, version, pool, pipeline)
            dest = folder / (turn + "-" + version)
            subraw = read_job(dest, job, args.driver)
            sub = json.loads(subraw)
            assert (sub["flop"], sub["pot"], sub["stack"]) == (flop, 1800, 9100)
            info = sub["info"]
            if not 0 <= info["gto_expl_pct"] <= 0.5 or (
                version == "exp_oop" and not 0 <= info["hero_gap_pct"] <= 0.5
            ):
                rec["status"] = "SUBGAME_GAP_OVER_LIMIT"
                break
            sub.update(line0=FLOP_LINE, turn=turn, rivers=rivers)
            code = f"B560_R16_{flop}_{turn}_{version}".upper()
            archive = dest / ("NL2_" + code + ".zip")
            provenance = dict(
                solver=SOLVER,
                rust=RUST,
                pool_sha256=POOL,
                run=args.run,
                version=version,
                original=identity,
                result_sha256=sha(subraw),
                job_sha256=sha(compact(job)),
            )
            entries = {
                "original-flop.json": raw,
                "flop.job.json": compact(rootjob),
                "job.json": compact(job),
                "locks.json": compact(meta),
                "turn.json": subraw,
                "provenance.json": compact(provenance),
            }
            if args.driver:
                zip_payload(archive, entries)
            else:
                with ZipFile(archive) as z:
                    assert set(z.namelist()) == set(entries) and all(
                        z.read(k) == v for k, v in entries.items()
                    )
            manifest = dict(spot="SB_BB", pot_family="SRP", locks=meta)
            s = dict(
                root=root,
                subgame=sub,
                source_sha256=sha(subraw),
                manifest=manifest,
                version=version,
                run=args.run,
                archive_code=code,
                archive_sha256=sha(archive.read_bytes()),
                applied_rust_rates=info.get("lock_stats", {}),
            )
            if version == "exp_oop":
                parent = dict(run=args.run, sha256=identity["root_sha256"])
                manifest.update(
                    gto_parent_source_run_id=args.run, gto_parent_source_sha256=parent["sha256"]
                )
                s.update(
                    verified_gto_parent=parent,
                    measured_lock_application=audit_patterns(sub, job, manifest, pool, 0),
                )
            else:
                assert not meta and not info.get("lock_stats")
            pair.append(s)
            archives.append(archive)
        if len(pair) != 2:
            continue
        assert pair[0]["subgame"]["hands"] == pair[1]["subgame"]["hands"]
        hit, stats = evaluate(
            *pair, [public + r for r in rivers], route, actions, identity["root_sha256"]
        )
        rec["joint_river_heroes"] = stats
        if hit:
            if not args.driver:
                for f in archives:
                    (EVIDENCE / f.name).write_bytes(f.read_bytes())
                record(
                    group,
                    report,
                    model,
                    *pair,
                    hit,
                    archives[1],
                    pool,
                    identity,
                    "Both flop opening menus restricted to 100%; SB turn and river open 50%",
                )
            ledger["selected"] = hit[0]
            break
    return ledger


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for n in ("solver", "results"):
        ap.add_argument("--" + n, type=Path, required=True)
    ap.add_argument("--original-metadata", type=Path)
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--driver", type=Path)
    ap.add_argument(
        "--saved-root", action="store_true", help="Use an already completed native flop from this batch"
    )
    ap.add_argument("--flop", choices=TURNS)
    args = ap.parse_args()
    if not args.driver and args.original_metadata is None:
        ap.error("--original-metadata is required for original-source replay")
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
    raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges

    route = json.loads(subprocess.check_output(["node", "tools/hu_b536_sb_route_cells.cjs"]))["16"]
    actions = json.loads(subprocess.check_output(["node", "tools/hu_b552_river_action_cells.cjs"]))["16"]
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())["records"][MID]
    assert (model["frequency_rank"], model["solver_profile"], model["assumed_model_node_spr"]) == (
        16,
        "SB_BB",
        2.278,
    )
    group = dict(rank=16, model_id=MID, boards=[], pins=[])
    report = dict(schema="NL2_HU_B560_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
    if args.driver:
        ledger = fresh(args, args.flop, model, group, report, pool, pipeline, ranges, route, actions)
        (args.results / args.flop / "verification.json").write_bytes(json_bytes(ledger))
        print(json.dumps(ledger), flush=True)
        return
    historical(model, group, report, pool, pipeline, ranges, route, actions, args.original_metadata)
    records = []
    for flop in TURNS:
        folder = args.results / flop
        if not (folder / "verification.json").exists():
            records.append(dict(flop=flop, status="NO_COMPLETED_NATIVE_RESULT"))
            continue
        ledger = fresh(args, flop, model, group, report, pool, pipeline, ranges, route, actions)
        assert ledger == json.loads((folder / "verification.json").read_bytes())
        records.append(ledger)
    count = len(group["boards"])
    assert 1 <= count == len({b["flop"] for b in group["boards"]}) <= 3
    if count == 3:
        (EVIDENCE / "reverified/rank16.json").write_bytes(json_bytes(group))
        (DATA / "nl2_hu_b560_locked_medium.json").write_bytes(json_bytes(report))
    (DATA / "nl2_hu_b560_sb_river_results.json").write_bytes(
        json_bytes(dict(run=args.run, records=records, count=count, paired=group))
    )


if __name__ == "__main__":
    main()
