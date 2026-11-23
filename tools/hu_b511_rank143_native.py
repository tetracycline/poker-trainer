"""Reconstruct the original 3x SB check-raise and solve BB's measured responses on four turns."""
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

MODEL = "ln-opfr-t_model-712wim"
FLOP_LINE = "x b75 r c"
LINE = FLOP_LINE + "/"
PINS = Path("data/nl2_hu_b511_rank143_artifacts.json")
CASES = {
    "8s8h3d": ("5s", 14598504895),
    "Js9h4d": ("Ts", 14599361276),
    "9s6h3d": ("Ts", 14626804686),
    "Jh9d6s": ("3c", 14628394918),
}


def measure(source, public, root_sha):
    node = audit_decision(source, public, LINE, 0, root_sha)
    assert node and node["source_actions"] == ["x", "b50", "b100"]
    bet, = (n for n in source["subgame"]["nodes"] if (n["board"], n["line"], n["player"]) == (public, LINE + "b50", 1))
    assert (bet["pot"], bet["bets"]) == (4950, [1650, 0])
    return node


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
    current = json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    model = current["records"][MODEL]
    assert (model["frequency_rank"], model["solver_profile"], model["family"], model["street"], model["assumed_model_node_spr"]) == (143, "SB_BB", "SRP", 1, 2.594)
    group = dict(rank=143, model_id=MODEL, boards=[], pins=[])
    report = dict(schema="NL2_HU_B511_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
    attempts = []
    for flop, (turn, aid) in CASES.items():
        if args.flop and args.flop != flop:
            continue
        original = load_original(args.originals, aid, pins[str(aid)], "SB_BB", flop, turn, "gto",
            pot=600, stack=9700, flop_line=FLOP_LINE, pipeline=pipeline, ranges=ranges)
        g, public, ident = original["source"], original["public"], original["identity"]
        assert (ident["flop_oop_menu"], ident["flop_ip_menu"]) == ("33%,50%,75%,100%", "33%,50%,75%,100%")
        assert (original["job"]["pot"], original["job"]["stack"], original["job"]["root_no_bet"]) == (3300, 8350, False)
        gto = measure(g, public, ident["root_sha256"])
        assert gto["status"] == "POSITIVE_JOINT_REACH"
        code = f"B511_R143_{flop.upper()}_{turn.upper()}_EXP_OOP"
        if args.driver:
            assert args.results and args.run and args.flop
            file = solve_native(original, "exp_oop", pool, pipeline, args.results, args.driver, args.run, code)
            replay_native(original, "exp_oop", pool, pipeline, file, args.run, code)
            return
        if not args.results:
            continue
        filename = f"NL2_{code}.json.gz"
        inputs = list(args.results.rglob(filename))
        assert len(inputs) <= 1
        row = dict(flop=flop, public_board=public, original_gto=ident, gto=gto)
        attempts.append(row)
        if not inputs:
            row["status"] = "MISSING_COMPLETED_NATIVE_OUTPUT"
            continue
        shutil.copyfile(inputs[0], EVIDENCE / filename)
        e = replay_native(original, "exp_oop", pool, pipeline, inputs[0], args.run, code)
        locked = measure(e, public, ident["root_sha256"])
        assert locked["subgame_applied_rust_lock_nodes"] > 0 and locked["lock_scope"]["observed_marginal_source_nodes"] > 0
        row.update(exp_oop=locked, verified_street_locks=e["measured_lock_application"], status=locked["status"])
        if not (0 <= locked["gto_gap_pct"] <= .5 and 0 <= locked["locked_hero_gap_pct"] <= .5):
            row["status"] = "CONVERGENCE_OUTSIDE_GATE"
        if row["status"] == "POSITIVE_JOINT_REACH":
            board, pin = emit_board(model, g, e, public, LINE, texture(flop))
            assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (33.0, 83.5)
            assert abs(board["actual_spr"] / model["assumed_model_node_spr"] - 1) <= current["spr_relative_tolerance"]
            assert (pin["GTO_compatible_hole_card_pairs"], pin["NL2_compatible_hole_card_pairs"]) == (
                gto["compatible_hole_card_pairs"], locked["compatible_hole_card_pairs"])
            pin.update(original_gto_archive=ident, conditional_gto_flop_root_sha256=ident["root_sha256"])
            rates = []
            for pattern, target in e["measured_lock_application"]["marginal_targets"].items():
                actual = e["applied_rust_rates"].get(pattern)
                if actual and actual["nodes"]:
                    rates.append(dict(street=target["street"], token=pattern.split(")?")[-1][:-1], n=target["n"],
                        nodes=actual["nodes"], fold_pct=100 * actual["fold"], raise_pct=100 * actual["agg"]))
            assert rates
            board["nl2_locked_variants"][0].update(variant_label="原始 GTO 翻牌範圍，轉河牌分街 NL2 鎖頻",
                pool_sha256=POOL, measurement_policy="STREET_SPECIFIC_POOL_MARGINALS", applied_street_rates=rates,
                viewer_archive_code=pin["locked_viewer_archive_code"], viewer_sha256=pin["locked_viewer_sha256"],
                gto_parent_source_run_id=ident["artifact_run"], gto_parent_source_sha256=ident["root_sha256"])
            group["boards"].append(board)
            group["pins"].append(pin)
            report["references"][source_key(MODEL, locked)] = locked
            report["gto_references"][source_key(MODEL, gto)] = gto
    if args.results:
        assert args.run and not args.flop
        trainer = json.loads(subprocess.check_output(["node", "tools/hu_b511_rank143_route.cjs"]))
        group["trainer_scope"] = trainer
        Path("data/nl2_hu_b511_rank143_attempts.json").write_bytes(json_bytes(dict(rank=143, model_id=MODEL,
            run_id=args.run, trainer_scope=trainer, attempts=attempts)))
        if len(group["boards"]) >= 3:
            assert len(group["boards"]) == len({b["flop"] for b in group["boards"]}) <= 5
            (EVIDENCE / "reverified/rank143.json").write_bytes(json_bytes(group))
            Path("data/nl2_hu_b511_locked_medium.json").write_bytes(json_bytes(report))


if __name__ == "__main__":
    main()
