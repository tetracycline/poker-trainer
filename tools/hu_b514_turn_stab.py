"""Solve CO-IP / BB-IP pot-size flop bets followed by an explicit one-third-pot turn bet."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_b492_half_pot_leads import zip_payload
from hu_b509_limp_ip import common_hands, observations
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board

DATA = Path("data")
PINS = DATA / "nl2_hu_b514_originals.json"
PARENT = "x b100 c"
LINE = PARENT + "/x b33 c/x"
TARGETS = {191: ("ln-ipc-r_model-i19djk", "SB_BB", 600, 9700),
           215: ("ln-ipfr-r_model-2h1iyv", "CO_BB", 550, 9750)}
VERSIONS = ("gto", "exp_ip")


def read(path):
    return json.loads(path.read_bytes())


def turn_job(original, version, pool, pipeline):
    if version == "exp_ip":
        job, locks = prepare_job(original, version, pool, pipeline)
    else:
        job, locks = deepcopy(original["job"]), []
    assert job["root_no_bet"] and job["turn_ip"] == "50%,100%" and job["line0"] == ["x","b100","c","/"]
    job.update(turn_ip="33%,50%,100%", out="turn.json", target_pct=.45, iters=max(2000, job["iters"]))
    for river in original["source"]["subgame"]["rivers"]:
        job["extract"].append(dict(prefix=["x","b33","c",river], street=True))
    return job, locks


def replay(original, version, pool, pipeline, path, run, code):
    job, locks = turn_job(original, version, pool, pipeline)
    gto = original["source"]
    frozen = original["identity"]
    with ZipFile(path) as archive:
        raw = archive.read("turn.json")
        meta = json.loads(archive.read("provenance.json"))
        assert archive.read("job.json") == compact(job) and archive.read("locks.json") == compact(locks)
        assert sha(archive.read("original-flop.json")) == frozen["root_sha256"]
    assert meta == dict(solver=SOLVER, rust=RUST, pool_sha256=POOL, run=run, version=version,
                        original=frozen, result_sha256=sha(raw), job_sha256=sha(compact(job)))
    sub = json.loads(raw)
    assert all(sub[k] == gto["subgame"][k] for k in ("hands","pot","stack","flop"))
    sub.update(line0=PARENT, turn=job["turn"], rivers=gto["subgame"]["rivers"])
    manifest = dict(gto["manifest"], locks=locks)
    source = dict(root=gto["root"], subgame=sub, manifest=manifest, version=version, run=run,
                  source_sha256=sha(raw), archive_code=code, archive_sha256=sha(path.read_bytes()))
    if version == "exp_ip":
        parent = dict(run=gto["run"], sha256=frozen["root_sha256"])
        manifest.update(gto_parent_source_run_id=parent["run"],gto_parent_source_sha256=parent["sha256"])
        source.update(verified_gto_parent=parent, measured_lock_application=audit_patterns(sub,job,manifest,pool,1))
    else:
        assert not sub["info"].get("lock_stats") and not job.get("locks")
    source["applied_rust_rates"] = sub["info"].get("lock_stats",{})
    return source


def rates(source):
    result = []
    for pattern, target in source["measured_lock_application"]["marginal_targets"].items():
        observed = source["applied_rust_rates"].get(pattern)
        if observed and observed["nodes"]:
            result.append(dict(street=target["street"], token=pattern.split(")?")[-1][:-1], n=target["n"],
                               nodes=observed["nodes"], fold_pct=100*observed["fold"], raise_pct=100*observed["agg"]))
    assert result
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--originals", required=True, type=Path)
    cli.add_argument("--solver", required=True, type=Path)
    cli.add_argument("--artifact")
    cli.add_argument("--driver", type=Path)
    cli.add_argument("--version", choices=VERSIONS)
    cli.add_argument("--results", type=Path)
    cli.add_argument("--run", type=int)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip() == SOLVER
    pool_data = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_data) == POOL
    pool = json.loads(pool_data)["NL2"]
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    models = read(DATA/"nl2_hu_multiboard_status_current.json")["records"]
    groups = {rank:dict(rank=rank,model_id=spec[0],boards=[],pins=[]) for rank,spec in TARGETS.items()}
    observations_by_rank = {rank:[] for rank in TARGETS}
    attempts = []
    for aid,pin in read(PINS).items():
        if args.artifact and aid != args.artifact:
            continue
        rank = pin["rank"]
        mid, spot, pot, stack = TARGETS[rank]
        model = models[mid]
        assert (model["frequency_rank"],model["solver_profile"],model["street"]) == (rank,spot,2)
        original = load_original(args.originals,int(aid),pin,spot,pin["flop"],pin["turn"],"gto",
                                 pot=pot,stack=stack,pipeline=pipeline,ranges=ranges,flop_line=PARENT)
        root_sha = original["identity"]["root_sha256"]
        pair = {}
        reason = None
        for version in VERSIONS:
            if args.version and version != args.version:
                continue
            code = f"B514_{aid}_{version.upper()}"
            name = "NL2_" + code + ".zip"
            job,lock_meta = turn_job(original,version,pool,pipeline)
            if args.driver:
                assert args.artifact and args.version and args.run and args.results
                folder = args.results.resolve()
                folder.mkdir(parents=True,exist_ok=True)
                (folder/"job.json").write_bytes(compact(job))
                subprocess.run([str(args.driver.resolve()),"job.json"],cwd=folder,check=True,timeout=360)
                raw = (folder/"turn.json").read_bytes()
                provenance = dict(solver=SOLVER,rust=RUST,pool_sha256=POOL,run=args.run,version=version,
                                  original=original["identity"],result_sha256=sha(raw),job_sha256=sha(compact(job)))
                zip_payload(folder/name,{"turn.json":raw,"job.json":compact(job),"locks.json":compact(lock_meta),
                          "original-flop.json":compact(original["source"]["root"]),"provenance.json":compact(provenance)})
                replay(original,version,pool,pipeline,folder/name,args.run,code)
                return
            if args.results:
                found, = args.results.rglob(name)
                shutil.copyfile(found,EVIDENCE/name)
                source = replay(original,version,pool,pipeline,found,args.run,code)
                pair[version] = source
                info = source["subgame"]["info"]
                if not 0 <= info["gto_expl_pct"] <= .5 or version=="exp_ip" and not 0 <= info["hero_gap_pct"] <= .5:
                    reason = "OUTSIDE_CONVERGENCE_GATE"
        if not args.results:
            print(rank, pin["flop"], pin["turn"], original["public"])
            continue
        assert not args.artifact and not args.version and args.run
        row = dict(rank=rank,flop=pin["flop"],turn=pin["turn"],original=original["identity"],rivers={},
                   gaps={v: {k:s["subgame"]["info"].get(k) for k in ("gto_expl_pct","hero_gap_pct")} for v,s in pair.items()})
        if reason:
            row["status"]=reason
            attempts.append(row)
            continue
        g, e = pair["gto"],pair["exp_ip"]
        gs, es = (observations(s,LINE,10,root_sha) for s in (g,e))
        assert set(gs)==set(es)
        common = sorted(gs)
        chosen = None
        for board in common:
            gr, er = gs[board], es[board]
            for s in (g,e):
                sub = s["subgame"]
                turn_bet, = (n for n in sub["nodes"] if n["board"]==board[:8] and n["line"]==PARENT+"/x b33")
                node, = (n for n in sub["nodes"] if n["board"]==board and n["line"]==LINE)
                invest = (job["pot"] * 33 + 50)//100
                assert turn_bet["bets"] == [0,invest] and node["bets"] == [invest,invest]
                assert node["pot"] == job["pot"] + 2*invest and node["player"]==1
            shared = common_hands(gr,er)
            row["rivers"][board] = [gr["compatible_hole_card_pairs"],er["compatible_hole_card_pairs"],shared]
            if chosen or not shared:
                continue
            b,p = emit_board(model,g,e,board,LINE,texture(pin["flop"]))
            assert p["common_legal_hero_combos"]==shared
            p["original_flop_source"]=original["identity"]
            b["nl2_locked_variants"][0].update(variant_label="原始 GTO 翻牌範圍，轉河牌分街 NL2 鎖頻",
                gto_parent_source_run_id=pin["run"], gto_parent_source_sha256=root_sha, applied_street_rates=rates(e),
                measurement_policy="STREET_SPECIFIC_POOL_MARGINALS", pool_sha256=POOL)
            groups[rank]["boards"].append(b)
            groups[rank]["pins"].append(p)
            observations_by_rank[rank].append((gr,er))
            chosen = board
        row["selected"] = chosen
        attempts.append(row)
    if args.results and not args.driver:
        report = dict(schema="NL2_HU_B514_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
        for rank,group in groups.items():
            if len(group["boards"]) < 3:
                continue
            assert len(group["boards"]) == len({b["flop"] for b in group["boards"]}) <= 5
            (EVIDENCE/"reverified"/f"rank{rank}.json").write_bytes(json_bytes(group))
            for g,e in observations_by_rank[rank]:
                report["references"][source_key(group["model_id"],e)] = e
                report["gto_references"][source_key(group["model_id"],g)] = g
        (DATA/"nl2_hu_b514_locked_medium.json").write_bytes(json_bytes(report))
        (DATA/"nl2_hu_b514_actual_size_attempts.json").write_bytes(json_bytes(dict(run=args.run,attempts=attempts)))

if __name__ == "__main__":
    main()
