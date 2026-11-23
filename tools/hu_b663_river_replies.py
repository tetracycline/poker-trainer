"""Re-solve SB/BB after a called flop lead, locking replies to a river half-pot bet after turn checks."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b483_locked_medium import POOL, proof
from hu_b649_srp_turn_stabs import SOURCES, sb_parent
from hu_sequential_cfr_reach import game_reach

RANKS = {43: "ln-opfr-r_model-1e6gydx", 102: "ln-ipc-r_model-1at1re2"}
BOARDS = {
    43: ("2d7hKs9d5s", "2d9hAsKdJh"),
    102: ("2d7hKs9d5s", "2d9hAsKd6s", "3d7hAsKd3s", "3h8cKd5c4c"),
}
RATE = {"n": 64272, "fold": 53.1, "call": 37.6, "raise": 9.3}


def decision(root, turn, board, line, seat):
    node, = (n for n in turn["nodes"] if (n["board"], n["line"], n["player"]) == (board, line, seat))
    assert node["bets"] == [0, 0] and node["acts"] == ["x", "b50", "b100", "a"]
    result = proof(root, turn, node, game_reach(root, turn)[0])
    accepted = base64.b64decode(result["compatible_action_mask_b64"], validate=True)
    actions = node["acts"]
    index = actions.index("b50")
    frequencies = {h: node["strat"][index * len(accepted) + i] for i, h in enumerate(turn["hands"][seat])
                   if accepted[i] & (1 << index)}
    medium = result["b50"]
    assert len(frequencies) == (medium["eligible"] if medium else 0)
    return dict(legal_combos=result["strict_legal_combos"], compatible_pairs=result["compatible_hole_card_pairs"],
                half_pot=medium, eligible_hand_frequencies=frequencies)


def analyze(board, model, ranges, driver, archive, generate):
    public, line, seat = board["public_board"], board["actual_exact_action_line"], board["acting_seat"]
    assert (model["solver_profile"], model["label"]) == ("SB_BB", "CERT-MULTIBOARD")
    assert (seat, line) in [(0, "b50 c/x x/"), (1, "b50 c/x x/x")]
    assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (12, 94)
    code, digest = SOURCES[12][1][public[:8]]
    pin = dict(archive_code=code, archive_sha256=digest, source_sha256=board["source_sha256"], run=board["source_run_id"])
    original = sb_parent(dict(board, public_board=public[:8]), pin, ranges)
    root, turn = original["source"]["root"], original["source"]["subgame"]
    before = decision(root, turn, public, line, seat)
    assert before["legal_combos"] == board["strict_full_street_combo_reachable"]
    assert before["half_pot"]["eligible"] == board["medium_50pct_eligible_combos"]
    assert before["half_pot"]["candidate"] == board["b50_nonpolarized_relative_equity_research_candidate"]
    reply = line + (" " if seat else "") + "b50"
    pattern = "^" + reply + "$"
    job = dict(original["job"], out="result.json", hero=seat, target_pct=.35, rank_pct=.35, iters=2500,
               locks=[{"pat": pattern, "fold": RATE["fold"]/100, "raise": RATE["raise"]/100}])
    key = f"r{model['frequency_rank']}/{public}.json"
    if driver:
        with TemporaryDirectory() as temp:
            Path(temp,"job.json").write_bytes(compact(job))
            subprocess.run([driver.resolve(), "job.json"], cwd=temp, check=True)
            rebuilt = Path(temp,"result.json").read_bytes()
        if generate:
            archive.writestr(key, rebuilt)
    raw = rebuilt if generate else archive.read(key)
    result = json.loads(raw)
    if driver and not generate:
        check = json.loads(rebuilt)
        assert all(check[k] == result[k] for k in ("pot", "stack", "flop", "nodes", "hands"))
        assert all(check["info"][k] == result["info"][k] for k in ("gto_expl_pct", "hero_gap_pct", "lock_stats"))
    assert all(result[k] == turn[k] for k in ("pot", "stack", "flop", "hands"))
    result.update(line0=turn["line0"], turn=turn["turn"], rivers=turn["rivers"])
    metrics = result["info"]
    assert 0 <= metrics["gto_expl_pct"] <= .35 and 0 <= metrics["hero_gap_pct"] <= .35
    assert set(metrics["lock_stats"]) == {pattern}
    stat = metrics["lock_stats"][pattern]
    assert stat["nodes"] > 0 and abs(stat["fold"]-.531)<.001 and abs(stat["agg"]-.093)<.001
    for game in (turn, result):
        facing, = (n for n in game["nodes"] if (n["board"],n["line"],n["player"]) == (public,reply,1-seat))
        assert (facing["pot"],facing["bets"],facing["acts"]) == (1800, [0,600] if seat else [600,0], ["f","c","a"])
    responder = proof(root, result, facing, game_reach(root, result)[0])
    after = decision(root, result, public, line, seat)
    return dict(rank=model["frequency_rank"], model_id=model["model_id"], public_board=public, line=line, seat=seat,
                original=pin, root_sha256=original["identity"]["root_sha256"], job_sha256=sha(compact(job)),
                output_sha256=sha(raw), pattern=pattern, applied_nodes=stat["nodes"], applied_fold=stat["fold"],
                applied_raise=stat["agg"], gto_gap_pct=metrics["gto_expl_pct"], hero_gap_pct=metrics["hero_gap_pct"],
                response_legal_combos=responder["strict_legal_combos"], response_pairs=responder["compatible_hole_card_pairs"],
                gto=before, locked=after)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--rank",type=int,required=True,choices=RANKS)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    drivers=p.add_mutually_exclusive_group()
    drivers.add_argument("--generate",type=Path)
    drivers.add_argument("--verify",type=Path)
    args=p.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    sys.path.insert(0,str(solver/"postflop/py"))
    import ranges
    raw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw)==POOL and json.loads(raw)["NL2"]["HU_facing_bet"]["3"]["by_size"]["34-55%"]==RATE
    registry=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    model=registry[RANKS[args.rank]]
    records=[]
    assert model["frequency_rank"]==args.rank
    with ZipFile(args.archive,"w" if args.generate else "r",compression=ZIP_DEFLATED) as z:
        named = {b["public_board"]: b for b in model["certified_3_to_5_exact_flop_boards"]}
        for public in BOARDS[args.rank]:
            board = named[public]
            records.append(analyze(board,model,ranges,args.generate or args.verify,z,bool(args.generate)))
    report=dict(schema="NL2_HU_B663_RIVER_HALF_POT_REPLY_V1",solver=SOLVER,rust=RUST,pool_sha256=POOL,
                measure="NL2.HU_facing_bet[3].by_size[34-55%]",observations=RATE,
                archive_sha256=sha(args.archive.read_bytes()),records=records)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    main()
