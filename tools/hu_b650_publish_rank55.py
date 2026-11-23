"""Join the verified B644 priced river with the two published rank55 partials."""
import argparse
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b514_turn_stab import rates
from hu_b644_rank55_priced import CASES, MODEL, verify
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

DATA = Path("data")
FLOP = "6d5c3c"
RUN = 45231188164
CODE = "B644_R55_6D5C3C"


def publish(solver, originals, receipt):
    archive = EVIDENCE / f"NL2_{CODE}.zip"
    identity = json.loads(receipt.read_bytes())
    run_info = identity["workflow_run"]
    assert (identity["name"], run_info["id"], run_info["head_sha"], run_info["repository_id"]) == (
        "B644-R55-"+FLOP, RUN, "7b668846bde1bd10d4f11cd588674a01ee24cd7e", 1438346845)
    digest = sha(archive.read_bytes())
    assert identity["digest"] == "sha256:" + digest
    with ZipFile(archive) as z, tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        # Only unpack the seven known native files from the verified worker archive.
        members = {"proof.json","flop/job.json","flop/result.json"}
        members.update("Ad-"+v+"/"+f for v in ("gto","exp_ip") for f in ("job.json","result.json"))
        assert set(z.namelist()) == members and len(z.namelist()) == len(members)
        z.extractall(output)
        report = verify(SimpleNamespace(solver=solver, originals=originals, flop=FLOP, output=output, driver=None, run=RUN))
        assert report == json.loads((output/"proof.json").read_bytes())
        check = report["turns"][0]["checks"][0]
        public, line = check["board"], report["line"]
        assert public == "3c5c6dAd4h" and line == "b75 c/b33 c/x" and check["hands"]
        root = json.loads((output/"flop/result.json").read_bytes())
        root_digest = sha(compact(root))
        pool_raw = (solver/"inputs/pool_stats.json").read_bytes()
        assert sha(pool_raw) == POOL
        pool = json.loads(pool_raw)["NL2"]
        import pipeline
        manifest = dict(spot="BTN_BB",pot_family="SRP",locks=[])
        gto_job = json.loads((output/"Ad-gto/job.json").read_bytes())
        lock_job, rules = prepare_job(dict(source=dict(version="gto",root=root,manifest=manifest),job=gto_job), "exp_ip", pool, pipeline)
        lock_job["out"] = "result.json"
        assert json.loads((output/"Ad-exp_ip/job.json").read_bytes()) == json.loads(compact(lock_job))
        games, observations = {}, {}
        for v in ("gto","exp_ip"):
            raw = (output/("Ad-"+v)/"result.json").read_bytes()
            sub = json.loads(raw)
            rivers = [e["prefix"][-1] for e in gto_job["extract"][1:]]
            sub.update(turn="Ad",rivers=rivers,line0="b75 c")
            source = dict(root=root,subgame=sub,version=v,run=RUN,archive_code=CODE,archive_sha256=digest,
                          source_sha256=sha(raw),root_sha256=root_digest,manifest=dict(manifest))
            if v == "exp_ip":
                source["manifest"].update(locks=rules,gto_parent_source_run_id=RUN,gto_parent_source_sha256=root_digest)
                source.update(verified_gto_parent=dict(run=RUN,sha256=root_digest),
                              applied_rust_rates=sub["info"]["lock_stats"],
                              measured_lock_application=audit_patterns(sub,lock_job,source["manifest"],pool,1))
            node, = (n for n in sub["nodes"] if (n["board"],n["line"],n["player"]) == (public,line,1))
            row = proof(root,sub,node,game_reach(root,sub)[0])
            row.update(version=v,spot="BTN_BB",family="SRP",flop=FLOP,turn="Ad",source_run_id=RUN,archive_sha256=digest,
                       source_sha256=sha(raw),root_sha256=root_digest,gto_gap_pct=sub["info"]["gto_expl_pct"],
                       locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),lock_scope=lock_scope(sub,source["manifest"]["locks"],v),
                       root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(r["nodes"] for r in sub["info"].get("lock_stats",{}).values()))
            games[v], observations[v] = source,row
    assert observations["exp_ip"]["b50"] == check["locked_half_pot"]
    model = json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
    board,pin = emit_board(model,games["gto"],games["exp_ip"],public,line,texture(FLOP),viewer_code=CODE)
    pin.update(shared_rendered_checks=check["hands"],worker_artifact=identity["id"],worker_sha256=digest,
               original_flop_artifact=CASES[FLOP]["artifact"])
    board["nl2_locked_variants"][0].update(variant_label="原始 GTO 翻牌策略及 NL2 轉、河牌玩家池節點鎖",applied_street_rates=rates(games["exp_ip"]),
            measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",pool_sha256=POOL,gto_parent_source_run_id=RUN,
            gto_parent_source_sha256=root_digest,viewer_archive_code=pin["viewer_archive_code"],viewer_sha256=pin["viewer_sha256"])
    group = dict(rank=55,model_id=MODEL,boards=[],pins=[])
    medium = dict(schema="NL2_HU_B650_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    for batch in (613,624):
        part = json.loads((DATA/f"nl2_hu_b{batch}_rank55_partial.json").read_bytes())
        assert part["group"]["model_id"] == MODEL and len(part["group"]["boards"]) == len(part["group"]["pins"]) == 1
        group["boards"].extend(part["group"]["boards"])
        group["pins"].extend(part["group"]["pins"])
        for key in ("references","gto_references"):
            medium[key].update(part["observations"][key])
    group["boards"].append(board)
    group["pins"].append(pin)
    assert len({b["flop"] for b in group["boards"]}) == 3
    for v,key in (("gto","gto_references"),("exp_ip","references")):
        row = observations[v]
        medium[key][source_key(MODEL,row)] = row
    (EVIDENCE/"reverified/rank55.json").write_bytes(json_bytes(group))
    (DATA/"nl2_hu_b650_locked_medium.json").write_bytes(json_bytes(medium))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for option in ("solver","originals","receipt"):
        parser.add_argument("--"+option,type=Path,required=True)
    args=parser.parse_args()
    publish(args.solver.resolve(),args.originals,args.receipt)
