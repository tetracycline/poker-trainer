"""Rebuild the two exact SB double barrels from their distinct flop prices and original CFR jobs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

MODELS = {15: ("ln-opfr-r_model-1bv0680", "b75 c", 3000, 8500), 16: ("ln-opfr-r_model-j55znd", "b100 c", 3600, 8200)}
# First four historical pairs and two authentic GTO parents, with both inspected river draws available.
HISTORY = {
    15: [("AsTh4d", "Td", 14529096110, None), ("Ks7h2d", "9d", 14593610543, 14594206088),
         ("As9h2d", "Kd", 14598935222, None), ("Js9h4d", "Ts", 14599361276, None)],
    16: [("9s6h3d", "Ts", 14626804686, 14627938041), ("KsQh4d", "Tc", 14630030655, 14629408884)],
}
FRESH = ("QsTc5h", "Jh8s5d", "Ks9h5d")
PINS = Path("data/nl2_hu_b519_artifacts.json")


def observations(source, flop_line, river_pot, remaining, root_sha):
    root, sub = source["root"], source["subgame"]
    version = source["version"]
    line = flop_line + "/b50 c/"
    masks = game_reach(root, sub)[0]
    stake = sub["pot"] // 2
    assert (2 * sub["pot"], sub["stack"] - stake) == (river_pot, remaining)
    scope = lock_scope(sub, source["manifest"]["locks"], version)
    root_nodes, sub_nodes = (sum(v["nodes"] for v in game["info"].get("lock_stats", {}).values()) for game in (root, sub))
    if version == "exp_oop":
        assert sub_nodes > 0 and scope["observed_marginal_source_nodes"] > 0
    rows = {}
    for node in sub["nodes"]:
        if (node["line"], node["player"]) != (line, 0):
            continue
        assert len(node["board"]) == 10 and (node["pot"], node["bets"]) == (river_pot, [stake, stake])
        if "b50" in node["acts"]:
            bet, = (n for n in sub["nodes"] if (n["board"], n["line"], n["player"]) == (node["board"], line + "b50", 1))
            assert bet["pot"] == river_pot * 3 // 2 and bet["bets"] == [stake + river_pot // 2, stake]
        row = proof(root, sub, node, masks)
        row.update(version=version, spot="SB_BB", family="SRP", flop=sub["flop"], turn=sub["turn"],
            source_run_id=source["run"], source_sha256=source["source_sha256"], archive_sha256=source["archive_sha256"],
            root_sha256=root_sha, gto_gap_pct=sub["info"]["gto_expl_pct"], locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),
            root_gto_stage_gap_pct=root["info"]["gto_expl_pct"], root_locked_hero_gap_pct=root["info"].get("hero_gap_pct"),
            root_applied_rust_lock_nodes=root_nodes, subgame_applied_rust_lock_nodes=sub_nodes, lock_scope=scope)
        rows[node["board"]] = row
    return rows


def pin_from_metadata(meta):
    return dict(name=meta["name"], run=meta["workflow_run"]["id"], head=meta["workflow_run"]["head_sha"], sha256=meta["digest"].split(":")[1])


def fresh_meta(directory, flop, version, run, head, pool, turn):
    name = f"B519-R16-{flop}-{version}"
    candidates = [json.loads(p.read_bytes()) for p in directory.glob("*.json")]
    matching = [m for m in candidates if isinstance(m,dict) and m.get("name") == name]
    if not matching:
        return None, "MISSING_ORIGINAL_ARTIFACT"
    meta, = matching
    pin = pin_from_metadata(meta)
    assert (pin["run"], pin["head"]) == (run, head)
    aid = meta["id"]
    file = directory / f"{aid}.zip"
    assert sha(file.read_bytes()) == pin["sha256"]
    with ZipFile(file) as z:
        documents = [n for n in z.namelist() if n.startswith("trainer/evidence/") and n.endswith(".json") and not n.endswith("pool_stats.json")]
        if not documents:
            return None, "ORIGINAL_WORKER_DID_NOT_WRITE_MANIFEST"
        document, = documents
        manifest = json.loads(z.read(document))
        assert (manifest["spot"],manifest["version"],manifest["flop"],manifest["turns"]) == ("SB_BB",version,flop,[turn])
        assert (manifest["flop_size_profile"], manifest["flop_line_policy"], manifest["selected_lines"]) == ("full", "oop-b100only", ["b100 c"])
        if manifest["failures"] or not manifest["cases"]:
            return None, "NO_COMPLETED_ORIGINAL_SUBGAME"
        case, = manifest["cases"]
        for key, digest in ((manifest["file_flop"], manifest["file_flop_sha256"]), (case["source_path"], case["source_sha256"])):
            name = "solver/postflop/" + key
            raw = z.read(name)
            assert sha(raw) == digest
            game = json.loads(raw)
            info = game["info"]
            if not 0 <= info["gto_expl_pct"] <= .5:
                return None, "GTO_STAGE_OVER_HALF_PERCENT"
            if version == "exp_oop":
                if not 0 <= info["hero_gap_pct"] <= .5:
                    return None, "LOCKED_HERO_GAP_OVER_HALF_PERCENT"
                audit_patterns(game, json.loads(z.read(name[:-5] + ".job.json")), manifest, pool, hero_seat=0)
    shutil.copyfile(file, EVIDENCE / f"NL2_B519_R16_{flop.upper()}_{version.upper()}.zip")
    return (aid, pin), None


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--originals", type=Path, required=True)
    cli.add_argument("--solver", type=Path, required=True)
    cli.add_argument("--flop", choices=[r[0] for r in HISTORY[15] if not r[3]])
    cli.add_argument("--driver", type=Path)
    cli.add_argument("--results", type=Path)
    cli.add_argument("--run", type=int)
    cli.add_argument("--head")
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip() == SOLVER
    raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    pins = json.loads(PINS.read_bytes())
    reg = json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    # Original whole-tree locked AsTh4d exceeds the root GTO-stage limit.
    legacy = 14529402679
    if not args.flop:
        file = args.originals / f"{legacy}.zip"
        assert sha(file.read_bytes()) == pins[str(legacy)]["sha256"]
        with ZipFile(file) as z:
            mf, = (n for n in z.namelist() if n.startswith("evidence/") and n.endswith(".json"))
            case, = (c for c in json.loads(z.read(mf))["cases"] if (c["flop"], c["turn"], c["line"]) == ("AsTh4d", "Td", "b75 c"))
            root = z.read("solver/postflop/" + case["flop_json"])
            assert sha(root) == case["flop_sha256"]
            gap = json.loads(root)["info"]["gto_expl_pct"]
            assert gap > .5
        all_attempts = [dict(rank=15,flop="AsTh4d",turn="Td",version="exp_oop",original_artifact_id=legacy,
                             root_gto_stage_gap_pct=gap,status="REJECTED_HISTORICAL_ROOT_OVER_HALF_PERCENT")]
    else:
        all_attempts = []
    combined = dict(schema="NL2_HU_B519_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
    for rank, (mid, flop_line, river_pot, remaining) in MODELS.items():
        model = reg["records"][mid]
        assert (model["frequency_rank"],model["solver_profile"],model["family"],model["street"]) == (rank,"SB_BB","SRP",2)
        cases = list(HISTORY[rank])
        group = dict(rank=rank,model_id=mid,boards=[],pins=[])
        positive_rows = []
        if rank==16 and args.results and not args.flop:
            for flop in FRESH:
                turn = pipeline.turns_for(flop)[0]
                pair = []
                for version in ("gto","exp_oop"):
                    value, failure = fresh_meta(args.originals,flop,version,args.run,args.head,pool,turn)
                    if failure:
                        all_attempts.append(dict(rank=rank,flop=flop,version=version,status=failure))
                    else:
                        aid, pin = value
                        pins[str(aid)] = pin
                        pair.append(aid)
                if len(pair)==2:
                    cases.append((flop,turn,*pair))
        for flop,turn,gid,eid in cases:
            if args.flop and flop!=args.flop:
                continue
            def original(artifact,version):
                return load_original(args.originals,artifact,pins[str(artifact)],"SB_BB",flop,turn,version,
                    pot=600,stack=9700,flop_line=flop_line,pipeline=pipeline,ranges=ranges)
            src = original(gid,"gto")
            g=src["source"]
            gs=observations(g,flop_line,river_pot,remaining,src["identity"]["root_sha256"])
            if args.flop and rank==15:
                assert any(x["compatible_hole_card_pairs"] for x in gs.values())
                if args.driver:
                    code=f"B519_R15_{flop.upper()}_EXP_OOP"
                    file=solve_native(src,"exp_oop",pool,pipeline,args.results,args.driver,args.run,code)
                    replay_native(src,"exp_oop",pool,pipeline,file,args.run,code)
                return
            if eid:
                locked=original(eid,"exp_oop")
                e=locked["source"]
                lock_id=locked["identity"]
            else:
                code=f"B519_R15_{flop.upper()}_EXP_OOP"
                files=list(args.results.rglob("NL2_"+code+".json.gz")) if args.results else []
                if not files:
                    all_attempts.append(dict(rank=rank,flop=flop,status="AWAITING_NATIVE_LOCK",gto=gs))
                    continue
                path,=files
                shutil.copyfile(path,EVIDENCE/path.name)
                e=replay_native(src,"exp_oop",pool,pipeline,path,args.run,code)
                lock_id=src["identity"]
            es=observations(e,flop_line,river_pot,remaining,lock_id["root_sha256"])
            matched=[p for p in sorted(gs.keys() & es.keys()) if gs[p]["compatible_hole_card_pairs"] and es[p]["compatible_hole_card_pairs"] and
                     0<=es[p]["gto_gap_pct"]<=.5 and 0<=es[p]["locked_hero_gap_pct"]<=.5]
            row=dict(rank=rank,flop=flop,turn=turn,gto=gs,exp_oop=es,original_gto=src["identity"],selected_public_board=next(iter(matched),None))
            all_attempts.append(row)
            if not matched or not args.results:
                continue
            public=matched[0]
            b,pin=emit_board(model,g,e,public,flop_line+"/b50 c/",texture(flop))
            assert (b["actual_pot_bb"],b["actual_effective_stack_bb"])==(river_pot/100,remaining/100)
            assert (pin["GTO_compatible_hole_card_pairs"],pin["NL2_compatible_hole_card_pairs"]) == (gs[public]["compatible_hole_card_pairs"],es[public]["compatible_hole_card_pairs"])
            pin["original_gto_archive"]=src["identity"]
            if eid:
                pin["original_locked_archive"]=lock_id
                if flop in FRESH:
                    b["nl2_locked_variants"][0]["measurement_policy"]="STREET_SPECIFIC_POOL_MARGINALS"
            else:
                pin["conditional_gto_flop_root_sha256"]=src["identity"]["root_sha256"]
                b["nl2_locked_variants"][0].update(variant_label="原始 GTO 翻牌範圍，轉河牌分街 NL2 鎖頻",
                    pool_sha256=POOL,measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",
                    gto_parent_source_run_id=g["run"],gto_parent_source_sha256=src["identity"]["root_sha256"],
                    viewer_archive_code=pin["locked_viewer_archive_code"],viewer_sha256=pin["locked_viewer_sha256"])
            group["boards"].append(b)
            group["pins"].append(pin)
            positive_rows.append((gs[public],es[public]))
        if args.results and len(group["boards"])>=3:
            assert len({b["flop"] for b in group["boards"]})==len(group["boards"])<=5
            (EVIDENCE/f"reverified/rank{rank}.json").write_bytes(json_bytes(group))
            for gs,es in positive_rows:
                combined["gto_references"][source_key(mid,gs)]=gs
                combined["references"][source_key(mid,es)]=es
    if args.results:
        Path("data/nl2_hu_b519_sb_barrel_results.json").write_bytes(json_bytes(dict(run=args.run,attempts=all_attempts)))
        if combined["references"]:
            Path("data/nl2_hu_b519_locked_medium.json").write_bytes(json_bytes(combined))


if __name__=="__main__":
    main()
