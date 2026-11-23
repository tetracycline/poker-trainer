"""Replay the original CO-vs-BTN 3-bet-pot arrays and intersect both seats' legal private deals."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from hu_sequential_cfr_reach import compatible_node_reach, game_reach


RUN = 44522421850
FLOP = "As9h8d"
SPOT = "CO3_BTN"
POOL = "c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a"
FILES = {
    "gto": (14528208109, "c0d0f6b1cfa57a762799303388876487a2d65fbdb6b6fc0607aae24594cdd86b"),
    "exp_oop": (14529596879, "a9f1428e545a6f951b4590b7da12a412529f415268e3cedb8a5bde5ad5b86f41"),
    "exp_ip": (14529072231, "266e8a9fa7b2cc51a27e3ad0a4cede032e46004021f3b781fae60df3b71f2508"),
}
PROFILE = dict(oop="CO", ip="BTN", oopc=[["COrfi", "open"], ["COopen>BTN3b", "call"]],
               ipc=[["COopen>BTN", "3bet"]], pot=16.5, stack=92.5, pfr="ip", kind="3BP")
# Rank, actual action tokens and model pot/stack in bb. Probe and model children can share a named node.
TARGETS = {
    131: ("x x/", 16.5, 92.5),
    173: ("x b75 c/x", 41.25, 80.125),
    242: ("x x/b100 c/", 49.5, 76),
    244: ("x x/b50 c/", 33, 84.25),
    260: ("x x/x x/", 16.5, 92.5),
    261: ("x x/x x/", 16.5, 92.5),
    326: ("x b75 c/x b50 c/x", 82.5, 59.5),
}
PRIOR = Path("data/nl2_hu_b175_v32_248_exact_GTO_source_provenance.json")
OUT = Path("data/nl2_hu_b482_co3btn_joint_reach.json")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_source(archive, version, solver, pipeline, ranges):
    blob = lambda name: archive.read(name)
    read = lambda name: json.loads(blob(name))
    assert blob("evidence/poker-solver-commit.txt").decode().strip() == SOLVER
    assert blob("evidence/upstream-engine-commit.txt").decode().strip() == RUST
    manifest = read(f"evidence/{SPOT}-{version}.json")
    assert (manifest["spot"], manifest["selected_flops"], manifest["version"]) == (SPOT, [FLOP], version)
    assert manifest["derived_spot_profile"] == PROFILE and not manifest["failures"]
    for tag, rel in (("source_pipeline_sha256", "postflop/py/pipeline.py"), ("source_ranges_sha256", "postflop/py/ranges.py"),
                     ("source_preflop_tree_sha256", "preflop/pfsolve.py")):
        assert manifest[tag] == sha((solver / rel).read_bytes())
    locks, metadata = pipeline.lock_list(SPOT, version, FLOP)
    # Convert tuples to the JSON representation from the original serialized Rust job.
    locks = json.loads(json.dumps(locks))
    chosen = {}
    for c in manifest["cases"]:
        if c["line"] not in ("x x", "x b75 c"):
            continue
        line, turn = c["line"], c["turn"]
        assert c["flop"] == FLOP and turn in ("9s", "Tc")
        rootpath = "solver/postflop/" + c["flop_json"]
        subpath = "solver/postflop/" + c["sub_json"]
        assert sha(blob(rootpath)) == c["flop_sha256"] and sha(blob(subpath)) == c["sub_sha256"]
        root, sub = read(rootpath), read(subpath)
        rootjob, subjob = read(rootpath.replace(".json", ".job.json")), read(subpath.replace(".json", ".job.json"))
        hero = {"exp_oop": 0, "exp_ip": 1, "gto": None}[version]
        assert [rootjob["oop"], rootjob["ip"]] == [ranges.to_str(w) for w in ranges.ranges(SPOT, version)]
        assert (rootjob["flop"], root["flop"], root["pot"], root["stack"]) == (FLOP, FLOP, 1650, 9250)
        for job, game in ((rootjob, root), (subjob, sub)):
            assert (job.get("hero"), job.get("locks", [])) == (hero, locks)
            assert (job["rake_rate"], job["rake_cap"]) == (.05, 1000)
            if hero is None:
                assert 0 <= game["info"]["gto_expl_pct"] <= .5 and not locks
            else:
                assert 0 <= game["info"]["hero_gap_pct"] <= .5 and game["info"]["lock_stats"]
                assert set(game["info"]["lock_stats"]) <= {l["pat"] for l in locks}
                assert all(l["n"] >= 500 for l in metadata)
        parent, = [n for n in root["nodes"] if (n["line"], n["board"][-2:]) == (line + "/", turn)]
        assert (sub["flop"], sub["line0"], sub["turn"]) == (FLOP, line, turn)
        assert (sub["pot"], sub["stack"]) == (parent["pot"], root["stack"] - parent["bets"][0])
        for seat, key in enumerate(("oop_w", "ip_w")):
            assert subjob[key] == [[h,w] for h,w in zip(root["hands"][seat], parent["wr"][seat]) if w > 1e-4]
        assert subjob["root_no_bet"] == (line == "x b75 c")
        masks, _ = game_reach(root, sub)
        chosen[line, turn] = (root, sub, masks, c["sub_sha256"], c["flop_sha256"])
    assert len(chosen) == 4
    return chosen


def classify(rank, old, all_sources):
    line, pot, stack = TARGETS[rank]
    actor = old["hero_seat"]
    assert actor == int(rank in (173, 326))
    assert abs(stack / pot - old["model_SPR"]) < .001
    nl2 = "exp_oop" if actor == 0 else "exp_ip"
    previous = {p["source_sha"] for p in old["exact_authentic_gto_source_proofs"] if p["exact_line"] == line
                and p["flop"] == FLOP and p["source_run"] == RUN and p["paired_lock_runs"] == [RUN]}
    assert previous
    by_board = {}
    flop_line = line.split("/")[0]
    for turn in ("9s", "Tc"):
        for ver in ("gto", nl2):
            root, sub, masks, digest, _ = all_sources[ver][flop_line, turn]
            for n in sub["nodes"]:
                if (n["line"], n["player"]) != (line, actor):
                    continue
                actual_stack = (sub["stack"] - max(n["bets"])) / 100
                assert abs(n["pot"] / 100 - pot) < .021 and abs(actual_stack - stack) < .021
                key = "|".join((n["board"], line, str(actor)))
                legal = compatible_node_reach(root, sub, n, masks[key])
                by_board.setdefault(n["board"], {})[ver] = dict(source_sha256=digest,
                    actor_only_combos=masks[key]["count"], joint_actor_combos=legal["count"],
                    compatible_deals=legal["compatible_hole_card_pairs"], actions=n["acts"])
    eligible = sorted(b for b,s in by_board.items() if all(s.get(v, {}).get("compatible_deals", 0) > 0 for v in ("gto", nl2)))
    assert all(any(s["gto"]["source_sha256"] == d for s in by_board.values() if "gto" in s) for d in previous)
    return dict(rank=rank, model_id=old["model_id"], line=line, actor=actor, public_nodes=by_board,
                paired_public_boards=eligible, distinct_paired_flops=[FLOP] if eligible else [])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--downloads", required=True, type=Path)
    p.add_argument("--solver", required=True, type=Path)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git", "-C", str(solver), "rev-parse", "HEAD"], text=True).strip() == SOLVER
    assert sha((solver / "inputs/pool_stats.json").read_bytes()) == POOL
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges
    ranges.SPOTS[SPOT] = PROFILE
    sources = {}
    for version, (artifact, digest) in FILES.items():
        path = args.downloads / f"b482-{artifact}.zip"
        assert sha(path.read_bytes()) == digest
        with zipfile.ZipFile(path) as archive:
            sources[version] = load_source(archive, version, solver, pipeline, ranges)
    old = {r["rank"]: r for r in json.loads(PRIOR.read_bytes())["rows"]}
    rows = [classify(rank, old[rank], sources) for rank in TARGETS]
    result = dict(source_run_id=RUN, flop=FLOP, profile=PROFILE, solver=SOLVER, rust=RUST, pool_sha256=POOL,
                  original_artifacts={v: dict(id=a, sha256=d) for v,(a,d) in FILES.items()},
                  convergence_by_source={v: [
                      dict(flop_line=line, turn=turn, flop_sha256=rootsha, subgame_sha256=subsha,
                           root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],
                           subgame_gto_stage_gap_pct=sub["info"]["gto_expl_pct"],
                           root_locked_hero_gap_pct=root["info"].get("hero_gap_pct"),
                           subgame_locked_hero_gap_pct=sub["info"].get("hero_gap_pct"))
                      for (line, turn), (root, sub, _, subsha, rootsha) in games.items()]
                      for v,games in sources.items()},
                  prior_acting_seat_ledger_sha256=sha(PRIOR.read_bytes()),
                  reach="BOTH_SEATS_SEQUENTIAL_ACTION_MASKS_AND_MUTUALLY_DISJOINT_PRIVATE_CARDS", rows=rows)
    data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    if args.verify:
        assert OUT.read_bytes() == data
    else:
        OUT.write_bytes(data)
    print("Distinct jointly reachable flops:", [(r["rank"], len(r["distinct_paired_flops"])) for r in rows])


if __name__ == "__main__":
    main()
