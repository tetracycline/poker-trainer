#!/usr/bin/env python3
"""Run authentic poker-solver HU postflop batches; do not fabricate strategies.

Execute after checking out tetracycline/poker-solver and compiling pfdriver.
Outputs are immutable evidence artifacts, NOT automatically accepted NL2 rules.
"""
import argparse
import hashlib
import importlib
import json
import os
import pathlib
import sys
import time
import traceback

SPOTS = ("BTN_BB", "CO_BB", "SB_BB", "UTG_BB", "HJ_BB", "SB3_BTN", "BB3_BTN")
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for buf in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--solver-root", required=True, type=pathlib.Path)
    a.add_argument("--spot", choices=SPOTS, required=True)
    a.add_argument("--start", type=int, default=0)
    a.add_argument("--count", type=int, default=1)
    a.add_argument("--version", choices=("gto", "exp_ip", "exp_oop"), default="gto")
    a.add_argument("--manifest", type=pathlib.Path, required=True)
    opts = a.parse_args()
    if opts.start < 0 or opts.count <= 0:
        a.error("start must be >=0 and count >0")
    root = opts.solver_root.resolve()
    pf = root / "postflop"
    driver = pf / "pfdriver/target/release/pfdriver"
    if not driver.is_file():
        raise SystemExit("BLOCKED: missing compiled pfdriver: " + str(driver))
    sys.path.insert(0, str(pf / "py"))
    pipeline = importlib.import_module("pipeline")
    selected = pipeline.flops_for(opts.spot)[opts.start:opts.start + opts.count]
    if not selected:
        raise SystemExit("BLOCKED: empty requested flop slice")
    evidence = {"spot": opts.spot, "version": opts.version,
                "start": opts.start, "count": opts.count, "selected_flops": selected,
                "solver_repository": "tetracycline/poker-solver",
                "external_engine_commit": "9d1509fe5077d019825f833eed04b16d342dfda1",
                "source_pipeline_sha256": sha256(pf / "py/pipeline.py"),
                "results": [], "failures": [], "files": []}
    # The upstream solve_sub() builds a CFR subgame from reach-weighted
    # flop descendants. Zero weight for either player is an unreachable path,
    # never a solved river node (upstream Rust otherwise panics at unwrap()).
    evidence["unreachable_subgames"] = []
    def check_reach(fr, line, turn):
        node = next((n for n in fr["nodes"]
                     if n["line"] == line + "/" and n["board"][-2:] == turn), None)
        if node is None:
            return False, "MISSING_TURN_NODE"
        ranges = node.get("wr", ())
        if len(ranges) != 2:
            return False, "MISSING_RANGE_WEIGHTS"
        weights = [sum(float(w) for w in side if float(w) > 1e-4)
                   for side in ranges]
        if weights[0] <= 0 or weights[1] <= 0:
            return False, ("OOP_RANGE_EMPTY" if weights[0] <= 0
                           else "IP_RANGE_EMPTY")
        return True, None
    started = time.monotonic()
    for flop in selected:
        try:
            fr = pipeline.solve_flop(opts.spot, opts.version, flop)
            ml = pipeline.main_line(fr, opts.spot)
            # Preserve the reference pipeline's two supported flop-to-turn branches.
            # Other NL2 paths are NOT implicitly solved by this.
            lines = list(dict.fromkeys((ml, "x x")))
            for line in lines:
                for turn in fr.get("turns", pipeline.turns_for(flop)):
                    reachable, reason = check_reach(fr, line, turn)
                    if not reachable:
                        evidence["unreachable_subgames"].append({
                            "flop": flop, "line": line, "turn": turn,
                            "reason": reason, "status": "NOT_SOLVED_UNREACHABLE"})
                        continue
                    pipeline.solve_sub(opts.spot, opts.version, flop, fr, line, turn)
            evidence["results"].append({"flop": flop, "flop_lines": lines,
                                        "turns": fr.get("turns", []),
                                        "status": "SOLVED_RAW_NOT_MAPPED_TO_NL2"})
        except Exception as exc:
            evidence["failures"].append({"flop": flop, "error": str(exc),
                                         "trace": traceback.format_exc()[-1500:]})
    out = pf / "out" / opts.spot / opts.version
    for file in sorted(out.glob("*.json")):
        if any(file.name.startswith(flop) for flop in selected) and not file.name.endswith(".job.json"):
            evidence["files"].append({"path": str(file.relative_to(pf)),
                                      "sha256": sha256(file), "bytes": file.stat().st_size})
    evidence["elapsed_seconds"] = round(time.monotonic() - started, 2)
    evidence["solved_flops"] = len(evidence["results"])
    evidence["failed_flops"] = len(evidence["failures"])
    evidence["unreachable_subgame_count"] = len(evidence["unreachable_subgames"])
    evidence["nl2_verified_river_coverage_delta"] = 0
    opts.manifest.parent.mkdir(parents=True, exist_ok=True)
    opts.manifest.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(json.dumps({k: evidence[k] for k in ("spot","selected_flops","solved_flops","failed_flops","nl2_verified_river_coverage_delta")}))
    if evidence["failures"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
