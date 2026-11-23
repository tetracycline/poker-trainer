"""Replay five native continuations from two checked 3-bet flop archives."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import sha
from hu_b483_locked_medium import POOL
from hu_b527_checked_barrels import classes, hcls
from hu_b546_rank70_conditional import current_texture
from hu_checked_gto_boundary import load_original, prepare_job
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from solve_hu_missing_branches import EXTRA_SPOTS

EVIDENCE = Path("data/solver_evidence/NL2_B562_R263_NATIVE_CONTINUATIONS.zip")
DIGEST = "f0545edfadf8e14794b58fe4ed7e157a1dc365bf31b8ef5d847a0018d9595cdb"
CASES = {"KsTh3d": (14528716811, "Qc"), "Ks7h2d": (14593390837, "9d")}
RUNOUTS = ["2c", "5h", "9c", "8c", "7h", "8s"]
LINE = "x x/x x/"


def originals(directory, pipeline, ranges):
    first = json.loads(Path("data/nl2_hu_b485_original_artifacts.json").read_bytes())["44521980749"]
    pin, = (r for r in first["artifacts"] if r["id"] == CASES["KsTh3d"][0])
    pins = json.loads(Path("data/nl2_hu_b502_rank120_artifacts.json").read_bytes())
    pins[str(pin["id"])] = dict(pin, run=44521980749, head=first["trainer_commit"])
    for flop, (aid, turn) in CASES.items():
        yield flop, load_original(directory, aid, pins[str(aid)], "BB3_BTN", flop, turn, "gto",
                                  pot=2050, stack=9000, pipeline=pipeline, ranges=ranges)


def rendered_middle_hand(hand, public):
    return (current_texture(public[:6]) in ("A_high", "KQ_high", "paired", "mono")
            and current_texture(public[:8]) in ("KQ_high", "mono")
            and current_texture(public) in ("KQ_high", "mono")
            and hcls(hand, public[:6]) == hcls(hand, public[:8]) == classes(hand, public)[0] == "MID")


def reached(game, root, public, masks):
    node, = (n for n in game["nodes"] if (n["board"], n["line"], n["player"]) == (public, LINE, 0))
    assert (node["bets"], node["pot"]) == ([0, 0], 2050) and "b50" in node["acts"]
    key = "|".join([public, LINE, "0"])
    proof = compatible_node_reach(root, game, node, masks[key])
    eligible = set()
    for h, mask in zip(game["hands"][0], base64.b64decode(proof["mask"], validate=True), strict=True):
        if mask and rendered_middle_hand(h, public):
            eligible.add("".join(cardkey(h)))
    return dict(legal_deals=proof["compatible_hole_card_pairs"], eligible_hands=sorted(eligible))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--originals", required=True, type=Path)
    parser.add_argument("--solver", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git", "-C", str(solver), "rev-parse", "HEAD"], text=True).strip() == SOLVER
    poolraw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(poolraw) == POOL and sha(EVIDENCE.read_bytes()) == DIGEST
    pool = json.loads(poolraw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    report = dict(rank=263, model_id="ln-3bp-3b_r_model-1nr3lqx", solver=SOLVER, rust=RUST,
                  measured_NL2_pool_sha256=POOL, native_archive_sha256=DIGEST, sources={}, boards={})
    with ZipFile(EVIDENCE) as z:
        for flop, parent in originals(args.originals, pipeline, ranges):
            root, source = parent["source"]["root"], parent["source"]["subgame"]
            turn = CASES[flop][1]
            assert parent["public"][-2:] == turn
            export = [r for r in RUNOUTS if r not in [flop[i:i+2] for i in (0, 2, 4)] + [turn]]
            variants = [("medium", "gto"), ("medium", "exp_oop")]
            if flop == "KsTh3d":
                variants += [("original_menu", "gto"), ("original_menu", "exp_oop")]
            for menu, version in variants:
                if menu == "original_menu" and version == "gto":
                    game = source
                    digest = parent["identity"]["source_sha256"]
                else:
                    stem = "native" if menu == "original_menu" else flop + "-" + version
                    job = json.loads(z.read(stem + ".job.json"))
                    raw = z.read(stem + ".json")
                    digest = sha(raw)
                    game = json.loads(raw)
                    expected = (dict(parent["job"]) if version == "gto"
                                else prepare_job(parent, version, pool, pipeline)[0])
                    if menu == "medium":
                        expected.update(turn_oop="50%", turn_ip="50%", river_oop="50%,a", river_ip="50%,a",
                                        iters=2000, target_pct=.35, out=stem + ".json",
                                        extract=[dict(prefix=[], street=True)] +
                                        [dict(prefix=["x","x",r], street=True) for r in export])
                    assert job == expected
                    assert (game["pot"], game["stack"], game["hands"]) == (2050, 9000, source["hands"])
                    game.update(line0="x x", turn=turn, rivers=export if menu == "medium" else source["rivers"])
                info = game["info"]
                assert 0 <= info["gto_expl_pct"] <= .5
                if version == "exp_oop":
                    assert info["lock_stats"] and 0 <= info["hero_gap_pct"] <= .5
                ident = f"{flop}/{menu}/{version}"
                report["sources"][ident] = dict(parent=parent["identity"], native_sha256=digest,
                        gto_gap_pct=info["gto_expl_pct"], locked_hero_gap_pct=info.get("hero_gap_pct"),
                        applied_lock_nodes={k:v["nodes"] for k,v in info.get("lock_stats",{}).items()})
                masks = game_reach(root, game)[0]
                for n in game["nodes"]:
                    if n["player"] == 0 and n["line"] == LINE:
                        key = menu + "/" + n["board"]
                        report["boards"].setdefault(key, {})[version] = reached(game, root, n["board"], masks)
    for policies in report["boards"].values():
        assert set(policies) == {"gto", "exp_oop"}
        common = set(policies["gto"]["eligible_hands"]) & set(policies["exp_oop"]["eligible_hands"])
        policies["common_eligible_hands"] = sorted(common)
        assert not common
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
