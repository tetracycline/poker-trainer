"""Audit a priced UTG flop bet and two consecutive checks by the same rendered weak draw."""

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
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b471_rank146_prior import ID, LINE, OUT as PRIOR
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, prepare_job
from hu_multiboard_promote import texture as archive_texture
from hu_native_turn_result import replay, run_native
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from solve_hu_multiboard_100bb import EXTRA_SPOTS

sys.path.insert(0, str(Path(__file__).resolve().parent / "lines_pipeline"))
from run10_common import classes, hcls, texture

DATA = Path("data")
# Three independently solved paired flops in the existing half-pot UTG abstraction.
FLOPS = ("7d7c4s", "6c6h3s", "8h8c5d")


def fetch(args):
    args.originals.mkdir(parents=True, exist_ok=True)
    api = "repos/tetracycline/poker-trainer/actions/"
    if args.artifact_id:
        assert args.flop
        items = [
            json.loads(
                subprocess.check_output(
                    ["gh", "api", api + f"artifacts/{args.artifact_id}"]
                )
            )
        ]
    else:
        items = json.loads(
            subprocess.check_output(
                ["gh", "api", api + f"runs/{args.run}/artifacts?per_page=100"]
            )
        )["artifacts"]
    for flop in [args.flop] if args.flop else FLOPS:
        match = [m for m in items if m["name"] == f"B548-{flop}-gto"]
        if not match:
            continue
        (listed,) = match
        aid = listed["id"]
        page = api + f"artifacts/{aid}"
        meta = subprocess.check_output(["gh", "api", page])
        (args.originals / f"{aid}.json").write_bytes(meta)
        with (args.originals / f"{aid}.zip").open("wb") as out:
            subprocess.run(["gh", "api", page + "/zip"], stdout=out, check=True)


def hands(src, public, route, masks, turn_only=False):
    game = src["subgame"]
    line = "b50 c/" if turn_only else LINE
    (node,) = (
        n
        for n in game["nodes"]
        if (n["line"], n["board"], n["player"]) == (line, public, 0)
    )
    assert node["bets"] == [0, 0] and node["pot"] == 1300 and "b50" in node["acts"]
    aud = compatible_node_reach(src["root"], game, node, masks[f"{public}|{line}|0"])
    mask = base64.b64decode(aud["mask"], validate=True)
    bit = 1 << node["acts"].index("x")
    return {
        "".join(cardkey(h))
        for h, act in zip(game["hands"][0], mask, strict=True)
        if act & bit
        and hcls(h, public[:6]) in route["flop"]
        and hcls(h, public[:8]) in route["turn"]
        and (turn_only or set(classes(h, public)) & set(route["river"]))
    }


def rivers(boundary):
    public = boundary["public"]
    occupied = {public[i : i + 2] for i in range(0, 8, 2)}
    return [r + s for r in "23456789TJQKA" for s in "cdhs" if r + s not in occupied]


def make_job(boundary, version, pool, pipeline):
    if version == "gto":
        job, locks = deepcopy(boundary["job"]), []
    else:
        job, locks = prepare_job(boundary, version, pool, pipeline)
    job["out"] = "turn.json"
    job["extract"] = [dict(prefix=[], street=True)] + [
        dict(prefix=["x", "x", river], street=False) for river in rivers(boundary)
    ]
    return job, locks


def compare(boundary, args, route, pool, pipeline):
    g = boundary["source"]
    flop = g["subgame"]["flop"]
    turn = boundary["job"]["turn"]
    public = boundary["public"]
    if not hands(g, public, route, game_reach(g["root"], g["subgame"])[0], True):
        return None, "NO_RENDERED_TURN_CHECK"
    sources = []
    paths = []
    by_river = []
    for version in ("gto", "exp_oop"):
        code = f"B548_R146_{flop}_{turn}_{version}".upper()
        name = f"NL2_{code}.zip"
        if args.driver:
            job, locks = make_job(boundary, version, pool, pipeline)
            path = run_native(
                args.results / code,
                args.driver,
                boundary,
                job,
                locks,
                args.run,
                version,
                name,
            )
        else:
            files = list(args.results.rglob(name))
            if not files:
                return None, "MISSING_NATIVE_SOURCE"
            (path,) = files
        src = replay(boundary, version, pool, pipeline, path, args.run, code, make_job)
        game = src["subgame"]
        game["rivers"] = rivers(boundary)
        gap = game["info"]
        keys = (
            ["gto_expl_pct"] if version == "gto" else ["gto_expl_pct", "hero_gap_pct"]
        )
        if not all(0 <= gap[k] <= 0.5 for k in keys):
            return None, "CONVERGENCE_GATE"
        nodes = [n for n in game["nodes"] if n["line"] == LINE and n["player"] == 0]
        assert {n["board"] for n in nodes} == {
            public + river for river in game["rivers"]
        } and len(nodes) == 48
        reach = game_reach(src["root"], game)[0]
        by_river.append(
            {
                n["board"]: h
                for n in nodes
                if (h := hands(src, n["board"], route, reach))
            }
        )
        if not by_river[-1]:
            return None, "NO_RENDERED_RIVER_CHECK_" + version.upper()
        sources.append(src)
        paths.append(path)
    for board in sorted(by_river[0].keys() & by_river[1].keys()):
        shared = sorted(by_river[0][board] & by_river[1][board])
        if shared:
            return (board, shared, sources, paths), "POSITIVE_RENDERED_PAIR"
    return None, "NO_SHARED_RENDERED_RIVER_CHECK"


def opponent_rates(archive, source, pool):
    with ZipFile(archive) as z:
        metadata = json.loads(z.read("locks.json"))
        rules = json.loads(z.read("job.json"))["locks"]
    result = {}
    for line in ("b50 c/x", "b50 c/x x/x", "b50 c/x x/b50"):
        index = next(i for i, rule in enumerate(rules) if re.search(rule["pat"], line))
        rule, record = rules[index], metadata[index]
        assert rule["pat"] == record["pat"]
        native = source["applied_rust_rates"][rule["pat"]]
        assert native["nodes"] > 0
        result[line] = dict(
            pattern=rule["pat"],
            source=record["source"],
            scope=record["scope"],
            observations=record["n"],
            target={k: v for k, v in rule.items() if k in ("bet", "fold", "raise")},
            driver_pattern_aggregate=native,
        )
    turn = result["b50 c/x"]
    sample = pool["postflop_HU"]["SRP_turn_stab_ip_after_pfr_checks"]
    assert (
        turn["source"] == "SRP_turn_stab_ip_after_pfr_checks"
        and turn["observations"] == sample["n"]
        and turn["target"]["bet"] == sample["pct"] / 100
    )
    turn["size_distribution_source"] = "SRP_donk.sizes proxy from the pinned solver"
    assert result["b50 c/x x/x"]["observations"] == 0 and result["b50 c/x x/x"][
        "target"
    ] == {"bet": 0.45}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("originals", "results", "solver", "driver"):
        p.add_argument("--" + n, type=Path, required=n == "originals")
    p.add_argument("--artifact-id", type=int)
    p.add_argument("--flop", choices=FLOPS)
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--fetch", action="store_true")
    args = p.parse_args()
    assert args.run > 0
    if args.fetch:
        fetch(args)
        return
    solver = args.solver.resolve()
    assert (
        subprocess.check_output(
            ["git", "-C", solver, "rev-parse", "HEAD"], text=True
        ).strip()
        == SOLVER
    )
    if args.driver:
        assert (
            args.flop
            and args.driver.resolve()
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

    ranges.SPOTS["UTG_CO"] = pipeline.SPOTS["UTG_CO"] = EXTRA_SPOTS["UTG_CO"]
    routes = json.loads(
        subprocess.check_output(["node", "tools/hu_b548_rank146_route.cjs"])
    )
    raw_prior = PRIOR.read_bytes()
    assert (
        sha(raw_prior)
        == "e63fcbe8e58753ef38d55535fb1e1bb50a8913d07aa91611bb64485cb7bd2bd7"
    )
    prior = json.loads(raw_prior)
    for board, pin in zip(prior["boards"], prior["pins"], strict=True):
        assert (
            board["flop"] == pin["flop"]
            and board["actual_exact_action_line"] == LINE
            and board["acting_seat"] == 0
        )
        assert pin["common_legal_hero_combos"] > 0 and board["actual_spr"] == 7.25
        for key in ("", "locked_"):
            archive = (
                EVIDENCE / f"NL2_MULTIBOARD_{pin[key + 'viewer_archive_code']}.json.gz"
            )
            assert sha(archive.read_bytes()) == pin[key + "viewer_sha256"]
    assert all(texture(b["flop"]) not in routes for b in prior["boards"])
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())[
        "records"
    ][ID]
    assert (
        model["frequency_rank"],
        model["solver_profile"],
        model["assumed_model_node_spr"],
    ) == (146, "UTG_CO", 7.25)
    group = dict(rank=146, model_id=ID, boards=[], pins=[])
    report = {}
    checks = dict(
        schema="NL2_HU_B548_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={}
    )
    metadata = [json.loads(p.read_bytes()) for p in args.originals.glob("*.json")]
    for flop in [args.flop] if args.flop else FLOPS:
        attempts = report[flop] = {}
        route = routes[texture(flop)]
        selected = [m for m in metadata if m["name"] == f"B548-{flop}-gto"]
        if not selected:
            attempts["status"] = "NO_NEW_GTO_ARTIFACT"
            continue
        (m,) = selected
        aid = m["id"]
        pin = dict(name=m["name"], run=args.run, head=args.head, sha256=m["digest"][7:])
        assert (
            m["workflow_run"]["id"] == args.run
            and m["workflow_run"]["head_sha"] == args.head
        )
        archive = args.originals / f"{aid}.zip"
        assert m["digest"] == "sha256:" + sha(archive.read_bytes())
        with ZipFile(archive) as z:
            manifest = json.loads(z.read(f"trainer/evidence/{flop}-gto.json"))
            assert sha(z.read("trainer/evidence/pool_stats.json")) == POOL
        assert (
            manifest["flop_size_profile"] == "utg-50-only"
            and manifest["restricted_tree_assumption"] is True
        )
        assert manifest["selected_lines"] == ["b50 c"] and manifest[
            "selected_turn_lines"
        ] == ["x x"]
        if manifest["failures"]:
            attempts["status"] = "GTO_SOURCE_FAILED"
            continue
        for c in manifest["cases"]:
            turn = c["turn"]
            boundary = load_original(
                args.originals,
                aid,
                pin,
                "UTG_CO",
                flop,
                turn,
                "gto",
                pot=650,
                stack=9750,
                pipeline=pipeline,
                ranges=ranges,
                flop_line="b50 c",
            )
            menu = "50%"
            assert (
                boundary["identity"]["flop_oop_menu"]
                == boundary["identity"]["flop_ip_menu"]
                == menu
            )
            pair, attempts[turn] = compare(boundary, args, route, pool, pipeline)
            if not pair:
                continue
            if args.driver:
                break
            public, shared, sources, paths = pair
            g, e = sources
            board, ident = emit_board(model, g, e, public, LINE, archive_texture(flop))
            assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (
                13,
                94.25,
            )
            ident.update(
                original_gto_archive=boundary["identity"],
                shared_rendered_action_hands=shared,
                trainer_texture=texture(flop),
            )
            board.update(
                frozen_gto_flop=True,
                flop_bet_menu=menu,
                restricted_tree_assumption=True,
            )
            board["nl2_locked_variants"][0].update(
                variant_label="翻牌下注限半池，沿用原始 GTO 範圍，轉河牌使用 NL2 分街鎖頻",
                pool_sha256=POOL,
                gto_parent_source_run_id=pin["run"],
                gto_parent_source_sha256=boundary["identity"]["root_sha256"],
                viewer_archive_code=ident["viewer_archive_code"],
                viewer_sha256=ident["viewer_sha256"],
                applied_street_rates=rates(e),
                opponent_history_rates=opponent_rates(paths[1], e, pool),
            )
            for s, path, k in zip(
                sources, paths, ("gto_references", "references"), strict=True
            ):
                row = audit_decision(
                    s, public, LINE, 0, boundary["identity"]["root_sha256"]
                )
                checks[k][source_key(ID, row)] = row
                shutil.copyfile(path, EVIDENCE / path.name)
            parent_name = f"NL2_B548_PARENT_{flop.upper()}.zip"
            shutil.copyfile(archive, EVIDENCE / parent_name)
            ident["original_gto_archive"]["repository_file"] = parent_name
            group["boards"].append(board)
            group["pins"].append(ident)
            break
    if args.driver:
        return
    count = len(group["boards"])
    assert len({b["flop"] for b in group["boards"]}) == count
    if count >= 3:
        (EVIDENCE / "reverified/rank146.json").write_bytes(json_bytes(group))
        (DATA / "nl2_hu_b548_locked_medium.json").write_bytes(json_bytes(checks))
    (DATA / "nl2_hu_b548_rank146_results.json").write_bytes(
        json_bytes(
            dict(
                rank=146,
                model_id=ID,
                run=args.run,
                qualified_distinct_flops=count,
                attempts=report,
                excluded_originals={
                    b["flop"]: "NO_RENDERED_RIVER_CELL_FOR_" + texture(b["flop"])
                    for b in prior["boards"]
                },
                verified_pairs=group,
            )
        )
    )


if __name__ == "__main__":
    main()
