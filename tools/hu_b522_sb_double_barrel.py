"""Solve the SB's explicit one-third and three-quarter turn barrels after a half-pot flop."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b509_limp_ip import common_hands, observations
from hu_b514_turn_stab import rates
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, prepare_job
from hu_multiboard_promote import texture
from hu_native_turn_result import replay, run_native
from hu_reverified_board_pair import emit_board

DATA = Path("data")
PARENT = "b50 c"
TARGETS = {33: (17, "ln-opfr-r_model-j5b75a"), 75: (18, "ln-opfr-r_model-ka3vbv")}


def turn_job(original, version, pool, pipeline):
    if version == "exp_oop":
        job, locks = prepare_job(original, version, pool, pipeline)
    else:
        assert version == "gto"
        job, locks = deepcopy(original["job"]), []
    assert not job["root_no_bet"] and job["turn_oop"] == "50%,100%"
    assert job["line0"] == ["b50", "c", "/"] and (job["pot"], job["stack"]) == (1200, 9400)
    job.update(turn_oop="33%,50%,75%,100%", out="turn.json", target_pct=.45, iters=max(2000,job["iters"]))
    for river in original["source"]["subgame"]["rivers"]:
        for pct in TARGETS:
            job["extract"].append(dict(prefix=[f"b{pct}", "c", river], street=True))
    return job, locks


def match_boards(pair, pct, root_sha):
    line = f"{PARENT}/b{pct} c/"
    observations_by_version = []
    for source in pair:
        sub = source["subgame"]
        rows = observations(source, line, 10, root_sha, seat=0)
        for public in rows:
            bet, = (n for n in sub["nodes"] if (n["board"],n["line"]) == (public[:8],f"{PARENT}/b{pct}"))
            river, = (n for n in sub["nodes"] if (n["board"],n["line"]) == (public,line))
            chips = (sub["pot"] * pct + 50) // 100
            assert (bet["bets"], bet["player"], bet["pot"]) == ([chips,0],1,sub["pot"]+chips)
            assert (river["bets"], river["player"], river["pot"]) == ([chips,chips],0,sub["pot"]+2*chips)
        observations_by_version.append(rows)
    gto, lock = observations_by_version
    for public in sorted(gto.keys() | lock.keys()):
        gr, er = gto.get(public), lock.get(public)
        yield public, line, gr, er, common_hands(gr,er) if gr and er else 0


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--originals", required=True, type=Path)
    cli.add_argument("--solver", required=True, type=Path)
    cli.add_argument("--artifact")
    cli.add_argument("--version", choices=("gto","exp_oop"))
    cli.add_argument("--driver", type=Path)
    cli.add_argument("--results", type=Path)
    cli.add_argument("--run", type=int)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip() == SOLVER
    raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0, str(solver/"postflop/py"))
    import pipeline
    import ranges

    records = json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    groups = {rank: dict(rank=rank,model_id=mid,boards=[],pins=[]) for rank,mid in TARGETS.values()}
    for rank,mid in TARGETS.values():
        model = records[mid]
        assert (model["frequency_rank"],model["street"],model["solver_profile"]) == (rank,2,"SB_BB")
    report = dict(schema="NL2_HU_B522_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    attempts = []
    for aid,pin in json.loads((DATA/"nl2_hu_b522_originals.json").read_bytes()).items():
        if args.artifact and args.artifact != aid:
            continue
        orig = load_original(args.originals,int(aid),pin,"SB_BB",pin["flop"],pin["turn"],"gto",
                             pot=600,stack=9700,pipeline=pipeline,ranges=ranges,flop_line=PARENT)
        pair = []
        for version in ("gto","exp_oop"):
            if args.version and version != args.version:
                continue
            code = f"B522_{aid}_{version.upper()}"
            name = f"NL2_{code}.zip"
            job,locks = turn_job(orig,version,pool,pipeline)
            if args.driver:
                assert args.artifact and args.version and args.results and args.run
                path = run_native(args.results,args.driver,orig,job,locks,args.run,version,name)
                replay(orig,version,pool,pipeline,path,args.run,code,turn_job)
                return
            if args.results:
                path, = args.results.rglob(name)
                shutil.copyfile(path,EVIDENCE/name)
                pair.append(replay(orig,version,pool,pipeline,path,args.run,code,turn_job))
        if not args.results:
            print(aid, orig["public"])
            continue
        assert len(pair) == 2 and args.run
        g,e = pair
        gaps = [g["root"]["info"]["gto_expl_pct"],g["subgame"]["info"]["gto_expl_pct"],
                e["subgame"]["info"]["gto_expl_pct"],e["subgame"]["info"]["hero_gap_pct"]]
        for pct,(rank,mid) in TARGETS.items():
            row = dict(rank=rank,original=orig["identity"],gaps_pct=gaps,rivers={},selected=None)
            attempts.append(row)
            if not all(0 <= gap <= .5 for gap in gaps):
                row["status"] = "OUTSIDE_CONVERGENCE_GATE"
                continue
            for public,line,gr,er,count in match_boards(pair,pct,orig["identity"]["root_sha256"]):
                row["rivers"][public] = dict(gto_pairs=gr["compatible_hole_card_pairs"] if gr else 0,
                                             nl2_pairs=er["compatible_hole_card_pairs"] if er else 0,
                                             shared_hands=count)
                if not count or row["selected"]:
                    continue
                b,p = emit_board(records[mid],g,e,public,line,texture(pin["flop"]))
                assert p["common_legal_hero_combos"] == count
                p["original_flop_source"] = orig["identity"]
                b["nl2_locked_variants"][0].update(variant_label="原始 GTO 翻牌範圍，轉河牌分街 NL2 鎖頻",
                    gto_parent_source_run_id=pin["run"],gto_parent_source_sha256=orig["identity"]["root_sha256"],
                    applied_street_rates=rates(e),measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",pool_sha256=POOL)
                groups[rank]["boards"].append(b)
                groups[rank]["pins"].append(p)
                report["references"][source_key(mid,er)] = er
                report["gto_references"][source_key(mid,gr)] = gr
                row["selected"] = public
            row["status"] = "POSITIVE" if row["selected"] else "NO_COMMON_LEGAL_HAND"
    if args.results and not args.driver:
        for rank,group in groups.items():
            assert len(group["boards"]) == len({b["flop"] for b in group["boards"]}) <= 5
            if len(group["boards"]) >= 3:
                (EVIDENCE/"reverified"/f"rank{rank}.json").write_bytes(json_bytes(group))
        (DATA/"nl2_hu_b522_locked_medium.json").write_bytes(json_bytes(report))
        (DATA/"nl2_hu_b522_turn_size_outcomes.json").write_bytes(json_bytes(dict(run=args.run,attempts=attempts)))


if __name__ == "__main__":
    main()
