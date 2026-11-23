"""Audit the retained and alternative rank80 original rivers from their immutable Rust output and jobs."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import POOL, proof
from hu_board_reach_corrections import source_key
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

DATA = Path("data")
MID = "ln-iso-lmp_r_model-17pklmg"
LINE = "b33 c/x x/x"
ANCHORS = {"4s4h2d": "2d4h4s8s5c", "7s5h3d": "3d5h7s6c9s"}
PAIRS = ((14631178346,14689986225), (14690603344,14691413915), (14599037935,14599454837),
         (14600026283,14599769541), (14601426559,14602013161))
PINS = DATA/"nl2_hu_b501_rank80_artifacts.json"
REPORT = DATA/"nl2_hu_b501_rank80_original_rivers.json"
MEDIUM = DATA/"nl2_hu_b501_locked_medium.json"


def replay(folder, artifact, meta, version):
    file = folder/f"{artifact}.zip"
    assert sha(file.read_bytes()) == meta["sha256"]
    with ZipFile(file) as z:
        name, = [n for n in z.namelist() if n.startswith("evidence/") and n.endswith(".json")]
        assert {SOLVER,RUST} <= {z.read(n).decode().strip() for n in z.namelist() if n.startswith("evidence/") and n.endswith(".txt")}
        manifest = json.loads(z.read(name))
        flop = manifest["flop"]
        assert (manifest["spot"],manifest["pot_family"],manifest["version"],manifest["pool_source_sha256"],manifest["failures"]) == (
            "LMP_CO_BB","LMP",version,POOL,[])
        ranges = manifest["preflop_ranges"]
        assert ranges["source"] == "ASSUMED_EXPLICIT_169CLASS" and len(ranges["oop_169"]) == len(ranges["ip_169"]) == 169
        c, = [c for c in manifest["cases"] if c["line"] == "b33 c"]
        def original(path, digest):
            path = "solver/postflop/"+path
            raw, job = z.read(path), z.read(path[:-5]+".job.json")
            assert sha(raw) == digest
            return json.loads(raw), json.loads(job), sha(job)
        root,rj,rj_sha = original(manifest["file_flop"],manifest["file_flop_sha256"])
        sub,j,j_sha = original(c["source_path"],c["source_sha256"])
    assert (root["flop"],root["pot"],root["stack"],rj["flop_oop"],rj["flop_ip"]) == (flop,250,9900,"33%,50%,75%,100%","33%,50%,75%,100%")
    assert (sub["flop"],sub["turn"],sub["line0"],sub["pot"],sub["stack"]) == (flop,c["turn"],"b33 c",416,9817)
    assert j["line0"] == ["b33","c","/"] and j["turn"] == c["turn"]
    assert (j["turn_oop"],j["turn_ip"],j["river_ip"]) == ("50%,100%","50%,100%","50%,100%,a")
    inherited = manifest.get("gto_parent_source_run_id")
    patterns = manifest.get("locks", [])
    if inherited:
        assert version == "exp_ip" and manifest["flop_parent_mode"] == "PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK"
        assert manifest["gto_parent_source_sha256"] == manifest["file_flop_sha256"]
    for game,job,hero,expected in ((root,rj,None if inherited or version=="gto" else 1,[] if inherited else patterns),
                                   (sub,j,1 if version=="exp_ip" else None,patterns)):
        assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"]) == (game["pot"],game["stack"],.05,1000)
        assert job.get("hero")==hero and [r["pat"] for r in job.get("locks",[])]==[r["pat"] for r in expected]
        assert 0 <= game["info"]["gto_expl_pct"] <= .5
        if hero is not None:
            assert expected and 0 <= game["info"]["hero_gap_pct"] <= .5
    parent, = [n for n in root["nodes"] if n["line"]=="b33 c/" and n["board"][-2:]==c["turn"]]
    assert (parent["pot"],root["stack"]-max(parent["bets"])) == (j["pot"],j["stack"])
    for seat,k in enumerate(("oop_w","ip_w")):
        assert j[k] == [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    scope = lock_scope(sub,patterns,version)
    applied = [sum(x["nodes"] for x in g["info"].get("lock_stats",{}).values()) for g in (root,sub)]
    if version=="exp_ip":
        assert applied[1]>0 and scope["observed_marginal_source_nodes"]>0
    masks = game_reach(root,sub)[0]
    observations={}
    for n in sub["nodes"]:
        if (n["line"],n["player"])!=(LINE,1):continue
        assert len(n["board"])==10 and n["pot"]==416 and n["bets"]==[0,0] and n["acts"]==["x","b50","b100","a"]
        child, = [x for x in sub["nodes"] if (x["board"],x["line"],x["player"])==(n["board"],LINE+" b50",0)]
        assert child["pot"]==624 and child["bets"]==[0,208]
        result=proof(root,sub,n,masks)
        observations[n["board"]]=dict(result,version=version,spot="LMP_CO_BB",family="LMP",flop=flop,turn=c["turn"],
            source_run_id=meta["run"],source_sha256=c["source_sha256"],archive_id=artifact,archive_sha256=meta["sha256"],
            source_archive=meta["name"],root_sha256=manifest["file_flop_sha256"],gto_gap_pct=sub["info"]["gto_expl_pct"],
            locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),root_applied_rust_lock_nodes=applied[0],subgame_applied_rust_lock_nodes=applied[1],
            lock_scope={k:v for k,v in scope.items() if k not in ("matching_examples","caveat")})
    assert len(observations)==2
    origin=dict(artifact=artifact,run=meta["run"],root_sha256=manifest["file_flop_sha256"],source_sha256=c["source_sha256"],
                flop_job_sha256=rj_sha,turn_job_sha256=j_sha,inherited_gto_run=inherited,
                preflop_job_range_sha256=sha(compact([rj["oop"],rj["ip"]])))
    return flop, observations, origin


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("originals",type=Path)
    cli.add_argument("--verify",action="store_true")
    args=cli.parse_args()
    pins=json.loads(PINS.read_bytes())
    historical=json.loads((DATA/"nl2_hu_multiboard_status_v32_b168_rank80.json").read_bytes())["records"][MID]
    assert (historical["frequency_rank"],historical["solver_profile"],historical["assumed_model_node_spr"])==(80,"LMP_CO_BB",23.558)
    raw=dict(schema="NL2_HU_B501_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    attempts=[]
    for gi,ei in PAIRS:
        flop,gs,gp=replay(args.originals,gi,pins[str(gi)],"gto")
        eflop,es,ep=replay(args.originals,ei,pins[str(ei)],"exp_ip")
        assert eflop==flop and gs.keys()==es.keys() and gp["preflop_job_range_sha256"]==ep["preflop_job_range_sha256"]
        if ep["inherited_gto_run"]:
            assert ep["inherited_gto_run"]==gp["run"] and ep["root_sha256"]==gp["root_sha256"] and ep["flop_job_sha256"]==gp["flop_job_sha256"]
        if flop in ANCHORS:
            public=ANCHORS[flop]
            board, = (b for b in historical["certified_3_to_5_exact_flop_boards"] if b["public_board"]==public and b["actual_exact_action_line"]==LINE)
            assert (board["source_run_id"],board["source_sha256"])==(gp["run"],gp["source_sha256"])
            assert any((v["run_id"],v["sha256"])==(ep["run"],ep["source_sha256"]) for v in board["nl2_locked_variants"])
            for field,source in (("references",es[public]),("gto_references",gs[public])):
                raw[field][source_key(MID,source)]=source
        rivers={}
        for public,g in gs.items():
            e=es[public]
            assert not (g["compatible_hole_card_pairs"] and e["compatible_hole_card_pairs"])
            rivers[public]={v["version"]:{k:v[k] for k in ("status","strict_legal_combos","compatible_hole_card_pairs","b50")} for v in (g,e)}
        attempts.append(dict(flop=flop,gto=gp,exp_ip=ep,rivers=rivers))
    summary=dict(schema="NL2_HU_B501_RANK80_ORIGINAL_RIVER_REPLAY_V1",rank=80,model_id=MID,line=LINE,acting_seat=1,
                 original_pairs=attempts,distinct_joint_positive_flops=0)
    for path,data in ((REPORT,json_bytes(summary)),(MEDIUM,compact(raw)+b"\n")):
        if args.verify:assert path.read_bytes()==data,path
        else:path.write_bytes(data)


if __name__=="__main__":
    main()
