"""Replay four native turn policies from two previously authenticated GTO flop boundaries."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import sha
from hu_b483_locked_medium import POOL, proof
from hu_checked_gto_boundary import load_original
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from solve_hu_missing_branches import EXTRA_SPOTS
from solve_hu_multiboard_100bb import make_fallbacks


ARCHIVE = Path("data/solver_evidence/NL2_B578_CONDITIONAL_TURNS.zip")
PINS = Path("data/nl2_hu_b578_turn_inputs.json")


def evidence_at(root, subgame, line, public, seat):
    masks = game_reach(root, subgame)[0]
    node, = (n for n in subgame["nodes"] if (n["line"], n["board"], n["player"]) == (line, public, seat))
    return node, masks, proof(root, subgame, node, masks)


def original_lock(folder, pin, parent, board, line, public, seat):
    run, aid = pin["run"], pin["id"]
    receipt = json.loads((folder / f"{aid}.json").read_bytes())
    raw = (folder / f"{aid}.zip").read_bytes()
    assert (receipt["id"], receipt["name"], receipt["digest"], receipt["workflow_run"]["id"],
            receipt["workflow_run"]["head_sha"], receipt["workflow_run"]["repository_id"]) == (
        aid, pin["name"], "sha256:" + sha(raw), run, pin["head"], 1438346845)
    assert sha(raw) == pin["sha256"]
    with ZipFile(folder / f"{aid}.zip") as z:
        mf, = (name for name in z.namelist() if name.startswith("evidence/") and name.endswith(".json"))
        manifest = json.loads(z.read(mf))
        assert manifest["version"] == ("exp_ip" if seat else "exp_oop") and not manifest["failures"]
        assert manifest["flop"] == parent["source"]["root"]["flop"]
        assert manifest.get("gto_parent_source_sha256", manifest.get("original_GTO_flop_root_sha256")) == parent["identity"]["root_sha256"]
        assert manifest.get("gto_parent_source_run_id", manifest.get("original_GTO_source_run_id")) == parent["identity"]["artifact_run"]
        case, = (case for case in manifest["cases"] if case["turn"] == public[-2:] and case["source_sha256"] == pin["policy_sha256"])
        path = "solver/postflop/" + (case.get("source_path") or case["original_Rust_exp_subgame_path"])
        output = z.read(path)
        assert sha(output) == case["source_sha256"]
        native = json.loads(z.read(path[:-5] + ".job.json"))
        assert native["hero"] == seat and native["locks"]
        assert all(native[k] == parent["job"][k] for k in ("flop", "turn", "oop_w", "ip_w", "pot", "stack", "line0"))
    lock, = (v for v in board["nl2_locked_variants"] if (v["run_id"],v["sha256"],v["version"]) ==
             (run, sha(output), manifest["version"]))
    sub = json.loads(output)
    assert sub["info"]["lock_stats"] and 0 <= sub["info"]["hero_gap_pct"] <= .5
    assert (sub["pot"],sub["stack"]) == (native["pot"],native["stack"])
    _, _, observed = evidence_at(parent["source"]["root"], sub, line, public, seat)
    assert observed["strict_legal_combos"] > 0 and observed["b50"]["eligible"] == lock["medium_50pct_eligible_combos"] == 0


def policy(archive, parent, version, spec, pool, pipeline):
    seat, line, public, spot = (spec[k] for k in ("seat", "line", "public_board", "spot"))
    g = parent["source"]
    stem = ("r46_" if seat else "") + version
    job = dict(parent["job"], out=stem + ".json", target_pct=.35, iters=2000)
    job["turn_ip" if seat else "turn_oop"] = "50%"
    reply_line = line + (" " if seat else "") + "b50"
    table = pool["HU_facing_bet"]["2"] if seat else pool["postflop_HU"]["SRP_PFR_OOP"]
    measure = table["by_size" if seat else "vs_turn_barrel_by_size"]["34-55%"]
    pattern = "^" + reply_line + "$"
    if version != "gto":
        rows, _ = make_fallbacks(spot, version, pool, pipeline.lock_list, g["root"]["flop"], by_street=True)
        rows.insert(0, dict(pat=pattern, fold=measure["fold"]/100, **{"raise":measure["raise"]/100}))
        job.update(locks=rows, rank_pct=.35, hero=seat)
    job_raw, raw = archive.read(stem + ".job.json"), archive.read(stem + ".json")
    assert json.loads(job_raw) == job
    game = json.loads(raw)
    info = game["info"]
    assert 0 <= info["gto_expl_pct"] <= .5 and game["hands"] == g["subgame"]["hands"]
    assert (game["pot"],game["stack"]) == (job["pot"],job["stack"])
    game.update(line0=g["subgame"]["line0"], turn=public[-2:], rivers=g["subgame"]["rivers"])
    node, masks, reached = evidence_at(g["root"], game, line, public, seat)
    assert node["acts"] == ["x", "b50"] and node["bets"] == [0, 0]
    reply, = (n for n in game["nodes"] if (n["board"],n["line"],n["player"]) == (public,reply_line,1-seat))
    bet = (job["pot"]+1)//2
    assert reply["pot"] == job["pot"]+bet and reply["bets"] == ([0, bet] if seat else [bet, 0])
    after = compatible_node_reach(g["root"],game,reply,masks[f"{public}|{reply_line}|{1-seat}"])
    bits = base64.b64decode(reached["compatible_action_mask_b64"], validate=True)
    hands = {h: round(node["strat"][len(bits)+i],6) for i,(h,mask) in enumerate(zip(game["hands"][seat],bits,strict=True))
             if mask & 2}
    _, _, baseline = evidence_at(g["root"],g["subgame"],line,public,seat)
    assert baseline["b50"]["eligible"] == 0 and reached["strict_legal_combos"] == baseline["strict_legal_combos"] > 0
    assert reached["compatible_hole_card_pairs"] == baseline["compatible_hole_card_pairs"] > 0
    assert len(hands) == reached["b50"]["eligible"] and bool(hands) == bool(after["compatible_hole_card_pairs"])
    result = dict(version=version, parent_version="gto", parent=parent["identity"], source_sha256=sha(raw),
                  input_sha256=sha(job_raw), original_half_pot_eligible=0, actions=node["acts"],
                  legal_combos=reached["strict_legal_combos"], compatible_pairs=reached["compatible_hole_card_pairs"],
                  half_pot=reached["b50"], half_pot_reply_pairs=after["compatible_hole_card_pairs"],
                  eligible_hand_frequencies=hands, gto_gap_pct=info["gto_expl_pct"])
    if version == "gto":
        assert not info.get("lock_stats")
    else:
        stat=info["lock_stats"][pattern]
        assert 0 <= info["hero_gap_pct"] <= .5 and stat["nodes"] == 1
        assert abs(stat["fold"]-measure["fold"]/100)<.001 and abs(stat["agg"]-measure["raise"]/100)<.001
        result.update(locked_hero_gap_pct=info["hero_gap_pct"], response=dict(
            source=("NL2.HU_facing_bet[2].by_size[34-55%]" if seat else
                    "NL2.postflop_HU.SRP_PFR_OOP.vs_turn_barrel_by_size[34-55%]"),
            n=measure["n"], fold_pct=measure["fold"], call_pct=measure["call"], raise_pct=measure["raise"], native=stat))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", required=True,type=Path)
    parser.add_argument("--originals",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    raw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw)==POOL
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pins=json.loads(PINS.read_bytes())
    assert sha(ARCHIVE.read_bytes())==pins["archive_sha256"]
    records=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    reports=[]
    with ZipFile(ARCHIVE) as z:
        for spec in pins["boards"]:
            model=records[spec["model_id"]]
            assert model["label"]=="CERT-MULTIBOARD" and model["frequency_rank"]==spec["rank"]
            board,=(b for b in model["certified_3_to_5_exact_flop_boards"] if b["public_board"]==spec["public_board"])
            assert (board["actual_exact_action_line"],board["acting_seat"],board["medium_50pct_eligible_combos"]) == (
                spec["line"],spec["seat"],0)
            pin=spec["gto"]
            parent=load_original(args.originals,pin["id"],pin,spec["spot"],board["flop"],board["turn"],"gto",
                                 pot=spec["root_pot"],stack=spec["root_stack"],pipeline=pipeline,ranges=ranges,
                                 flop_line=board["exact_flop_action"])
            assert (pin["run"], parent["identity"]["source_sha256"]) == (board["source_run_id"],board["source_sha256"])
            original_lock(args.originals,spec["lock"],parent,board,spec["line"],spec["public_board"],spec["seat"])
            locked="exp_ip" if spec["seat"] else "exp_oop"
            policies={v:policy(z,parent,v,spec,json.loads(raw)["NL2"],pipeline) for v in ("gto",locked)}
            reports.append(dict(rank=spec["rank"], model_id=model["model_id"],public_board=board["public_board"],
                line=spec["line"],seat=spec["seat"],source_run=pin["run"],original_locked_run=spec["lock"]["run"],
                original_locked_sha256=spec["lock"]["policy_sha256"], archive=ARCHIVE.name,archive_sha256=pins["archive_sha256"],
                policies=policies))
    args.out.write_text(json.dumps(dict(schema="NL2_HU_B578_RESTRICTED_TURNS_V1", solver=SOLVER,rust=RUST,
                                       pool_sha256=POOL,records=reports),indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    main()
