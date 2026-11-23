"""Reverify BTN's checked river after a half-pot flop c-bet/call and a checked turn."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board

MODEL = "ln-ipfr-r_model-1iypoop"
LINE = "x b50 c/x x/x"
PINS = Path("data/nl2_hu_b508_rank134_artifacts.json")
# Freeze one named river per distinct flop before running the new native locks.
CASES = {
    "Jh9d6s": ("3c", "4h", 14628385508, 14626854645),
    "8s8h3d": ("5s", "4s", 14592317474, None),
    "Js9h4d": ("Ts", "Ah", 14591863023, None),
    "KsQh4d": ("Tc", "3h", 14591903053, None),
}


def observe(source, public, root_sha):
    row = audit_decision(source, public, LINE, 1, root_sha)
    assert row and "b50" in row["source_actions"]
    child, = (n for n in source["subgame"]["nodes"] if (n["board"], n["line"], n["player"]) == (public, LINE + " b50", 0))
    assert child["pot"] == 1650 and child["bets"] == [0, 550]
    return row


def mark_conditional(board, pin, source, original):
    rates = []
    for pattern, target in source["measured_lock_application"]["marginal_targets"].items():
        actual = source["applied_rust_rates"].get(pattern)
        if actual and actual["nodes"]:
            token = pattern.split(")?")[-1][:-1]
            rates.append(dict(street=target["street"], token=token, n=target["n"], nodes=actual["nodes"],
                fold_pct=100 * actual["fold"], raise_pct=100 * actual["agg"]))
    assert rates
    pin["conditional_gto_flop_root_sha256"] = original["root_sha256"]
    pin["historical_restricted_flop_game_tree"] = True
    board["nl2_locked_variants"][0].update(
        variant_label="原始限尺寸翻牌 GTO 範圍，轉河牌分街 NL2 鎖頻", measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",
        pool_sha256=POOL, applied_street_rates=rates, viewer_archive_code=pin["locked_viewer_archive_code"],
        viewer_sha256=pin["locked_viewer_sha256"], gto_parent_source_run_id=original["artifact_run"],
        gto_parent_source_sha256=original["root_sha256"])


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--originals", type=Path, required=True)
    cli.add_argument("--solver", type=Path, required=True)
    cli.add_argument("--flop", choices=CASES)
    cli.add_argument("--driver", type=Path)
    cli.add_argument("--results", type=Path)
    cli.add_argument("--run", type=int)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git", "-C", str(solver), "rev-parse", "HEAD"], text=True).strip() == SOLVER
    pool_raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges
    pins = json.loads(PINS.read_bytes())
    registry = json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    model = registry["records"][MODEL]
    assert (model["frequency_rank"], model["solver_profile"], model["family"], model["street"], model["assumed_model_node_spr"]) == (134, "BTN_BB", "SRP", 2, 8.614)
    assert model["abstract_action_history"] == "對手過、你下注、對手跟|對手過、你過|對手過"
    group = dict(rank=134, model_id=MODEL, boards=[], pins=[])
    report = dict(schema="NL2_HU_B508_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
    attempts = []
    for flop, (turn, river, gid, eid) in CASES.items():
        if args.flop and args.flop != flop:
            continue
        def load(artifact, version):
            return load_original(args.originals, artifact, pins[str(artifact)], "BTN_BB", flop, turn, version,
                                 flop_line="x b50 c", pot=550, stack=9750, pipeline=pipeline, ranges=ranges)
        original = load(gid, "gto")
        g, identity = original["source"], original["identity"]
        public = original["public"] + river
        gr = observe(g, public, identity["root_sha256"])
        assert gr["status"] == "POSITIVE_JOINT_REACH" and "b50" in gr["source_actions"]
        code = f"B508_R134_{flop.upper()}_{turn.upper()}_EXP_IP"
        filename = f"NL2_{code}.json.gz"
        if args.driver:
            assert args.flop and args.run and args.results and not eid
            output = solve_native(original, "exp_ip", pool, pipeline, args.results, args.driver, args.run, code)
            replay_native(original, "exp_ip", pool, pipeline, output, args.run, code)
            return
        if eid:
            previous = load(eid, "exp_ip")
            e, lockroot = previous["source"], previous["identity"]["root_sha256"]
        elif not args.results:
            continue
        else:
            matches = list(args.results.rglob(filename))
            assert len(matches) <= 1
            if not matches:
                attempts.append(dict(flop=flop, public_board=public, gto=gr, status="MISSING_COMPLETED_NATIVE_OUTPUT"))
                continue
            # Legacy GTO permits only the listed IP flop bet sizes. Carry the identical GTO boundary into the lock.
            assert (identity["flop_oop_menu"], identity["flop_ip_menu"]) == ("", "33%,50%,75%")
            shutil.copyfile(matches[0], EVIDENCE / filename)
            e = replay_native(original, "exp_ip", pool, pipeline, matches[0], args.run, code)
            lockroot = identity["root_sha256"]
        er = observe(e, public, lockroot)
        assert er["source_actions"] == gr["source_actions"] and er["subgame_applied_rust_lock_nodes"] > 0
        assert er["lock_scope"]["observed_marginal_source_nodes"] > 0
        row = dict(flop=flop, public_board=public, original_gto=identity, gto=gr, exp_ip=er)
        if eid:
            row["original_lock"] = previous["identity"]
        else:
            row.update(frozen_gto_flop=True, verified_street_locks=e["measured_lock_application"])
        if not (0 <= er["gto_gap_pct"] <= .5 and 0 <= er["locked_hero_gap_pct"] <= .5):
            row["status"] = "CONVERGENCE_OUTSIDE_GATE"
        else:
            row["status"] = er["status"]
        if row["status"] == "POSITIVE_JOINT_REACH" and args.results:
            board, pin = emit_board(model, g, e, public, LINE, texture(flop))
            assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (11.0, 94.75)
            assert gr["compatible_hole_card_pairs"] == pin["GTO_compatible_hole_card_pairs"] > 0
            assert er["compatible_hole_card_pairs"] == pin["NL2_compatible_hole_card_pairs"] > 0
            pin["original_gto_archive"] = identity
            if eid:
                pin["original_locked_archive"] = previous["identity"]
            else:
                mark_conditional(board, pin, e, identity)
            group["boards"].append(board)
            group["pins"].append(pin)
            report["references"][source_key(MODEL, er)] = er
            report["gto_references"][source_key(MODEL, gr)] = gr
        attempts.append(row)
    if args.results:
        assert args.run and not args.flop
        Path("data/nl2_hu_b508_rank134_attempts.json").write_bytes(json_bytes(dict(rank=134, model_id=MODEL, run_id=args.run, attempts=attempts)))
        if len(group["boards"]) >= 3:
            assert len({b["flop"] for b in group["boards"]}) == len(group["boards"]) <= 5
            (EVIDENCE / "reverified/rank134.json").write_bytes(json_bytes(group))
            Path("data/nl2_hu_b508_locked_medium.json").write_bytes(json_bytes(report))


if __name__ == "__main__":
    main()
