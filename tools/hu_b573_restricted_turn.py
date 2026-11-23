"""Replay a half-pot-only turn lead from each policy's authenticated SB flop ranges."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, sha
from hu_b483_locked_medium import POOL, proof
from hu_checked_gto_boundary import load_original
from hu_sequential_cfr_reach import game_reach, compatible_node_reach
from solve_hu_multiboard_100bb import make_fallbacks

PUBLIC = "2d9hAsKd"
LINE = "b100 c/"
MODEL = "ln-opfr-t_model-19esov6"
RUN = 44666285424
PINS = Path("data/nl2_hu_b573_turn_inputs.json")
ARCHIVE = EVIDENCE / "NL2_B573_R2_AS9H2D_KD.zip"


def replay(parent, version, pool, pipeline, archive, *, stem=None, public=PUBLIC, line=LINE):
    stem = stem or version
    source = parent["source"]
    root, original = source["root"], source["subgame"]
    spot = source["manifest"]["spot"]
    flop = root["flop"]
    assert (spot,line) in {("SB_BB","b100 c/"),("UTG_CO","x x/")}
    job = dict(parent["job"])
    job.update(turn_oop="50%", out=stem + ".json", target_pct=.35, iters=2000)
    if version == "exp_oop":
        rows, _ = make_fallbacks(spot, version, pool, pipeline.lock_list, flop, by_street=True)
        table = pool["postflop_HU"]["SRP_PFR_OOP"]
        if line == "b100 c/":
            measure = table["vs_turn_barrel_by_size"]["34-55%"]
            label = "NL2.postflop_HU.SRP_PFR_OOP.vs_turn_barrel_by_size[34-55%]"
            sample = 11019
        else:
            measure = table["vs_delayed_cbet"]
            label = "NL2.postflop_HU.SRP_PFR_OOP.vs_delayed_cbet"
            sample = 26780
        rows.insert(0, dict(pat="^"+line+"b50$", fold=measure["fold"]/100, **{"raise":measure["raise"]/100}))
        job.update(locks=rows, rank_pct=.35, hero=0)
    assert json.loads(archive.read(stem + ".job.json")) == job
    raw = archive.read(stem + ".json")
    game = json.loads(raw)
    info = game["info"]
    assert 0 <= info["gto_expl_pct"] <= .5
    assert game["hands"] == original["hands"] and (game["pot"], game["stack"]) == (original["pot"], original["stack"])
    game.update(line0=line[:-1], turn=public[-2:], rivers=original["rivers"])
    observations = []
    for sub in (original, game):
        n, = (n for n in sub["nodes"] if (n["line"], n["board"], n["player"]) == (line, public, 0))
        masks = game_reach(root, sub)[0]
        row = proof(root, sub, n, masks)
        observations.append(row)
    baseline, new = observations
    assert baseline["source_actions"] == ["x","b50","b100"] and baseline["b50"]["eligible"] == 0
    assert new["source_actions"] == ["x","b50"] and new["b50"]["eligible"] > 0
    assert new["compatible_hole_card_pairs"] == baseline["compatible_hole_card_pairs"] > 0
    assert new["strict_legal_combos"] == baseline["strict_legal_combos"] > 0
    reply, = (n for n in game["nodes"] if (n["line"],n["board"],n["player"]) == (line+"b50",public,1))
    half = (game["pot"] + 1) // 2
    assert (reply["pot"],reply["bets"]) == (game["pot"]+half,[half,0]) and "c" in reply["acts"]
    reach = compatible_node_reach(root, game, reply, masks["|".join((public,line+"b50","1"))])
    assert reach["compatible_hole_card_pairs"] > 0
    result = dict(version=version, parent=parent["identity"], source_sha256=sha(raw),
                  original_actions=baseline["source_actions"], original_half_pot_eligible=baseline["b50"]["eligible"],
                  actions=new["source_actions"], legal_combos=new["strict_legal_combos"],
                  compatible_pairs=new["compatible_hole_card_pairs"], half_pot=new["b50"],
                  half_pot_reply_pairs=reach["compatible_hole_card_pairs"], gto_gap_pct=info["gto_expl_pct"])
    if version == "exp_oop":
        assert 0 <= info["hero_gap_pct"] <= .5
        first = next(rule for rule in job["locks"] if re.search(rule["pat"],reply["line"]))
        assert first["pat"] == "^"+line+"b50$" and measure["n"] == sample
        stat = info["lock_stats"][first["pat"]]
        assert stat["nodes"] > 0 and abs(stat["fold"]-first["fold"]) < .001 and abs(stat["agg"]-first["raise"]) < .001
        result.update(locked_hero_gap_pct=info["hero_gap_pct"], response=dict(
            source=label, n=measure["n"],
            fold_pct=measure["fold"],call_pct=measure["call"],raise_pct=measure["raise"],native=stat))
    else:
        assert not info.get("lock_stats")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver", required=True, type=Path)
    p.add_argument("--originals", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    solver = a.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip() == SOLVER
    raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    pins = json.loads(PINS.read_bytes())
    assert sha(ARCHIVE.read_bytes()) == pins["archive_sha256"]
    registry = json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    model = registry["records"][MODEL]
    board, = (b for b in model["certified_3_to_5_exact_flop_boards"] if b["public_board"] == PUBLIC)
    assert (model["frequency_rank"],board["actual_exact_action_line"],board["acting_seat"]) == (2,LINE,0)
    report = dict(model_id=MODEL, public_board=PUBLIC, line=LINE, seat=0, source_run=RUN, solver=SOLVER, rust=RUST,
                  pool_sha256=POOL, archive=ARCHIVE.name, archive_sha256=pins["archive_sha256"], policies={})
    with ZipFile(ARCHIVE) as z:
        for v,pin in pins["originals"].items():
            assert pin["run"] == RUN
            parent=load_original(a.originals,pin["id"],pin,"SB_BB","As9h2d","Kd",v,
                                 pot=600,stack=9700,pipeline=pipeline,ranges=ranges,flop_line="b100 c")
            expected=({(board["source_run_id"],board["source_sha256"])} if v=="gto" else
                      {(l["run_id"],l["sha256"]) for l in board["nl2_locked_variants"] if l["version"]==v})
            assert (RUN,parent["identity"]["source_sha256"]) in expected
            report["policies"][v]=replay(parent,v,pool,pipeline,z)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    main()
