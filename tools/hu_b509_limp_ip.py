"""Verify CO's conditional NL2 replies after a genuine BB half-pot flop lead and call."""
import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import POOL, proof
from hu_b496_rank71_baseline import read_source
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

DATA = Path("data")
# Frozen turns. Use the first paired positive public board in lexical order for each decision.
TURNS = {"3c3d4h": "7h", "5c5d2h": "Kc", "2c2d4h": "4c", "7s5h3d": "6c"}
LINES = {10: "b50 c/x", 63: "b50 c/b50 c/x", 81: "b50 c/x x/x",
         117: "b50 c/x b50 c/x", 118: "b50 c/x b50 c/x"}
ATTEMPTS = DATA / "nl2_hu_b509_limp_ip_outcomes.json"
MEDIUM = DATA / "nl2_hu_b509_locked_medium.json"


def read(path):
    return json.loads(path.read_bytes())


def boundary(folder, flop, pin):
    historic = flop == "7s5h3d"
    turn = TURNS[flop]
    source = read_source(folder, pin, "gto", flop, historic)[turn]
    origin = source["provenance"]
    with ZipFile(folder / f"{pin['id']}.zip") as archive:
        job_path = "solver/postflop/" + origin["original_subgame_path"].removesuffix(".json") + ".job.json"
        raw = archive.read(job_path)
    job = json.loads(raw)
    assert not job.get("locks") and job["line0"] == ["b50", "c", "/"]
    assert (job["pot"], job["stack"], job["turn"]) == (500, 9775, turn)
    identity = dict(origin, root_sha256=origin["original_root_sha256"], original_turn_job_sha256=sha(raw))
    return dict(source=source, identity=identity, job=job)


def observations(source, line, depth, root_sha):
    game = source["subgame"]
    masks = game_reach(source["root"], game)[0]
    result = {}
    version = source["version"]
    scope = lock_scope(game, source["manifest"]["locks"], version)
    applied = sum(r["nodes"] for r in game["info"].get("lock_stats", {}).values())
    if version == "exp_ip":
        assert source["measured_lock_application"]["first_pattern_visible_nodes"]
        assert applied > 0 and scope["observed_marginal_source_nodes"] > 0
    for node in game["nodes"]:
        if (node["line"], node["player"], len(node["board"])) != (line, 1, depth):
            continue
        assert len(node["acts"]) >= 2 and node["acts"][0] == "x"
        row = proof(source["root"], game, node, masks)
        row.update(spot="LMP_CO_BB", family="LMP", flop=game["flop"], turn=game["turn"], version=version,
                   root_sha256=root_sha, source_run_id=source["run"], source_sha256=source["source_sha256"],
                   archive_sha256=source["archive_sha256"], gto_gap_pct=game["info"]["gto_expl_pct"],
                   locked_hero_gap_pct=game["info"].get("hero_gap_pct"), root_applied_rust_lock_nodes=0,
                   subgame_applied_rust_lock_nodes=applied, lock_scope={k:v for k,v in scope.items() if k not in ("matching_examples","caveat")})
        result[node["board"]] = row
    return result


def common_hands(gto, lock):
    gm = base64.b64decode(gto["compatible_action_mask_b64"], validate=True)
    lm = base64.b64decode(lock["compatible_action_mask_b64"], validate=True)
    assert gto["source_hand_order_sha256"] == lock["source_hand_order_sha256"]
    return sum(bool(x and y) for x, y in zip(gm, lm, strict=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--originals", type=Path, required=True)
    parser.add_argument("--flop", choices=TURNS)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--run", type=int)
    parser.add_argument("--driver", type=Path)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip() == SOLVER
    pool_raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    previous = read(DATA / "nl2_hu_b496_rank71_baseline_attempts.json")["attempts"]
    live = read(DATA / "nl2_hu_multiboard_status_current.json")["records"]
    frozen = read(DATA / "nl2_hu_multiboard_status_v53_b465_rank218.json")["records"]
    models = {r["frequency_rank"]: r for r in live.values() if r["frequency_rank"] in LINES}
    groups = {rank: dict(rank=rank, model_id=model["model_id"], boards=[], pins=[]) for rank,model in models.items()}
    reports = {rank: [] for rank in groups}
    outcomes = []
    for flop in TURNS:
        if args.flop and args.flop != flop:
            continue
        pin = previous[flop]["originals"]["gto"]
        original = boundary(args.originals, flop, pin)
        gto = original["source"]
        root_sha = original["identity"]["root_sha256"]
        job, meta = prepare_job(original, "exp_ip", pool, pipeline)
        assert job["hero"] == 1 and job["line0"] == ["b50", "c", "/"] and meta
        code = f"B509_{flop.upper()}_{TURNS[flop].upper()}_EXP_IP"
        if args.driver:
            assert args.flop and args.results and args.run
            path = solve_native(original, "exp_ip", pool, pipeline, args.results, args.driver, args.run, code)
            replay_native(original, "exp_ip", pool, pipeline, path, args.run, code)
            return
        if args.results:
            assert args.run and not args.flop
            filename = f"NL2_{code}.json.gz"
            files = list(args.results.rglob(filename))
            assert len(files) == 1, filename
            dest = EVIDENCE / filename
            shutil.copyfile(files[0], dest)
            lock = replay_native(original, "exp_ip", pool, pipeline, dest, args.run, code)
            info = lock["subgame"]["info"]
            if not (0 <= info["gto_expl_pct"] <= .5 and 0 <= info["hero_gap_pct"] <= .5):
                outcomes.append(dict(flop=flop,status="OUTSIDE_CONVERGENCE_GATE",gto_gap_pct=info["gto_expl_pct"],hero_gap_pct=info["hero_gap_pct"]))
                continue
        for rank, line in LINES.items():
            model = models[rank]
            mid = model["model_id"]
            assert (model["family"], model["solver_profile"], model["preflop_text"]) == ("LMP","LMP_CO_BB","翻前： 你 CO 溜入 ，BB 過")
            assert {(b["actual_exact_action_line"],b["acting_seat"]) for b in frozen[mid]["certified_3_to_5_exact_flop_boards"]} == {(line,1)}
            depth = 6 + 2*model["street"]
            gs = observations(gto, line, depth, root_sha)
            assert gs
            if not args.results:
                print(rank, flop, sum(r["compatible_hole_card_pairs"] for r in gs.values()))
                continue
            ls = observations(lock, line, depth, root_sha)
            assert set(gs) == set(ls)
            selected = None
            counts = {}
            for public in sorted(gs):
                g,e = gs[public],ls[public]
                assert g["source_actions"] == e["source_actions"]
                shared = common_hands(g,e)
                counts[public] = [g["compatible_hole_card_pairs"], e["compatible_hole_card_pairs"], shared]
                if not shared or selected:
                    continue
                board,p = emit_board(model,gto,lock,public,line,texture(flop))
                assert p["common_legal_hero_combos"] == shared
                p.update(original_gto_archive=original["identity"], historical_restricted_flop_game_tree=True)
                rates = []
                for pattern, target in lock["measured_lock_application"]["marginal_targets"].items():
                    actual = lock["applied_rust_rates"].get(pattern)
                    if actual and actual["nodes"]:
                        rates.append(dict(street=target["street"], token=pattern.split(")?")[-1][:-1],
                            n=target["n"], nodes=actual["nodes"], fold_pct=100*actual["fold"], raise_pct=100*actual["agg"]))
                assert rates
                board["nl2_locked_variants"][0].update(applied_street_rates=rates,variant_label="原始 GTO 翻牌範圍，轉河牌分街 NL2 鎖頻",
                    measurement_policy="STREET_SPECIFIC_POOL_MARGINALS", pool_sha256=POOL,
                    gto_parent_source_run_id=gto["run"], gto_parent_source_sha256=root_sha,
                    viewer_archive_code=p["locked_viewer_archive_code"],viewer_sha256=p["locked_viewer_sha256"])
                groups[rank]["boards"].append(board)
                groups[rank]["pins"].append(p)
                reports[rank].append((g,e))
                selected = public
            outcomes.append(dict(rank=rank,flop=flop,line=line,selected=selected,
                                 counts_gto_deals_lock_deals_common_hands=counts))
    if args.results and not args.driver:
        medium = dict(schema="NL2_HU_B509_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
        for rank,group in groups.items():
            if len(group["boards"]) < 3:
                continue
            assert len({b["flop"] for b in group["boards"]}) == len(group["boards"]) <= 5
            (EVIDENCE / "reverified" / f"rank{rank}.json").write_bytes(json_bytes(group))
            for g,e in reports[rank]:
                mid = group["model_id"]
                medium["gto_references"][source_key(mid,g)] = g
                medium["references"][source_key(mid,e)] = e
        MEDIUM.write_bytes(json_bytes(medium))
        ATTEMPTS.write_bytes(json_bytes(dict(run=args.run,outcomes=outcomes)))

if __name__ == "__main__":
    main()
