"""Authenticate the completed rank126 workers and publish positive exact-board pairs."""
import argparse
import json
import subprocess
from pathlib import Path
import tempfile
from types import SimpleNamespace
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b514_turn_stab import rates
from hu_b665_rank126 import LINE, MODEL, run
from hu_b568_caller_rivers import rendered
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

DATA=Path("data")
RUN=45272740409
HEAD="27eeaf21c16596754636e9fd0a4e9b83e17a20ee"


def publish(args):
    pool_raw=(args.solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    model=json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
    route=json.loads(subprocess.check_output(["node","tools/hu_b665_rank126_routes.cjs"]))
    group=dict(rank=126,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema="NL2_HU_B665_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    inputs=json.loads((DATA/"nl2_hu_b665_rank126_workers.json").read_bytes())
    summary=[]
    for spec in inputs:
        flop=spec["flop"]
        receipt=json.loads((args.originals/(str(spec["artifact_id"])+".json")).read_bytes())
        identity=receipt["workflow_run"]
        assert (receipt["id"],identity["id"],identity["head_sha"],identity["repository_id"],receipt["name"])==(
            spec["artifact_id"],RUN,HEAD,1438346845,"B665-R126-"+flop)
        code="B665_R126_"+flop.upper()
        archive=EVIDENCE/("NL2_"+code+".zip")
        digest=sha(archive.read_bytes())
        assert receipt["digest"]=="sha256:"+digest and digest==spec["artifact_sha256"]
        with ZipFile(archive) as z, tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)
            expected={"proof.json","flop/job.json","flop/result.json"}
            report=json.loads(z.read("proof.json"))
            for turn in report["turns"]:
                if turn["legal_rivers"]:
                    expected.update(turn["turn"]+"-gto/"+n for n in ("job.json","result.json"))
                if turn["paired_policies"]:
                    expected.update(turn["turn"]+"-exp_ip/"+n for n in ("job.json","result.json"))
            assert set(z.namelist())==expected and len(z.namelist())==len(expected)
            for name in expected:
                p=output/name
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(z.read(name))
            run(SimpleNamespace(solver=args.solver,flop=flop,output=output,driver=None))
            assert json.loads((output/"proof.json").read_bytes())==report
            checks=[(turn["turn"],c) for turn in report["turns"] for c in turn["checks"]]
            summary.append(dict(flop=flop,positive_rivers=len(checks)))
            if not checks:
                continue
            turn,check=checks[0]
            public=check["board"]
            root=json.loads((output/"flop/result.json").read_bytes())
            root_digest=sha(compact(root))
            manifest=dict(spot="SB_BB",pot_family="SRP",locks=[])
            original_job=json.loads((output/(turn+"-gto/job.json")).read_bytes())
            import pipeline
            lock_job,rules=prepare_job(dict(source=dict(version="gto",root=root,manifest=manifest),job=original_job),"exp_ip",pool,pipeline)
            lock_job["out"]="result.json"
            assert json.loads((output/(turn+"-exp_ip/job.json")).read_bytes())==json.loads(compact(lock_job))
            sources,views={},{}
            for version,key in (("gto","gto_references"),("exp_ip","references")):
                raw=(output/(turn+"-"+version)/"result.json").read_bytes()
                sub=json.loads(raw)
                sub.update(turn=turn,line0="b33 c",rivers=[entry["prefix"][-1] for entry in original_job["extract"][1:]])
                source=dict(root=root,subgame=sub,version=version,run=RUN,archive_code=code,archive_sha256=digest,
                            source_sha256=sha(raw),root_sha256=root_digest,manifest=dict(manifest))
                if version=="exp_ip":
                    source["manifest"].update(locks=rules,gto_parent_source_run_id=RUN,gto_parent_source_sha256=root_digest)
                    source.update(verified_gto_parent=dict(run=RUN,sha256=root_digest),applied_rust_rates=sub["info"]["lock_stats"],
                                  measured_lock_application=audit_patterns(sub,lock_job,source["manifest"],pool,1))
                node,=[n for n in sub["nodes"] if (n["board"],n["line"],n["player"])==(public,LINE,1)]
                row=proof(root,sub,node,game_reach(root,sub)[0])
                row.update(version=version,spot="SB_BB",family="SRP",flop=flop,turn=turn,source_run_id=RUN,
                    archive_sha256=digest,source_sha256=sha(raw),root_sha256=root_digest,gto_gap_pct=sub["info"]["gto_expl_pct"],
                    locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),lock_scope=lock_scope(sub,source["manifest"]["locks"],version),
                    root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(v["nodes"] for v in sub["info"].get("lock_stats",{}).values()))
                assert row["b50"]==check["gto_b50" if version=="gto" else "locked_b50"]
                medium[key][source_key(MODEL,row)]=row
                sources[version]=source
                views[version]=rendered(source,row,node,route)
            board,pin=emit_board(model,sources["gto"],sources["exp_ip"],public,LINE,texture(flop),viewer_code=code)
            assert board is not None and check["hands"]
            comparisons=[]
            for hand in check["hands"]:
                g,e=views["gto"][hand],views["exp_ip"][hand]
                assert all(g[k]==e[k] for k in ("flop_class","turn_class","river_class","displayed_suggestion"))
                comparisons.append(dict(hand=hand,flop_class=g["flop_class"],turn_class=g["turn_class"],
                    river_class=g["river_class"],displayed_suggestion=g["displayed_suggestion"],gto=g["native"],nl2=e["native"]))
            pin.update(shared_rendered_checks=check["hands"],rendered_decision_hands=comparisons,
                       worker_artifact=receipt["id"],worker_sha256=digest)
            board["nl2_locked_variants"][0].update(
                variant_label="原始 GTO 翻牌策略及 NL2 轉、河牌玩家池節點鎖",
                applied_street_rates=rates(sources["exp_ip"]),measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",
                pool_sha256=POOL,gto_parent_source_run_id=RUN,gto_parent_source_sha256=root_digest,
                viewer_archive_code=pin["viewer_archive_code"],viewer_sha256=pin["viewer_sha256"])
            group["boards"].append(board)
            group["pins"].append(pin)
    assert 3<=len(group["boards"])<=5 and len({b["flop"] for b in group["boards"]})==len(group["boards"])
    (EVIDENCE/"reverified/rank126.json").write_bytes(json_bytes(group))
    (DATA/"nl2_hu_b665_locked_medium.json").write_bytes(json_bytes(medium))
    print(json.dumps(dict(boards=len(group["boards"]),workers=summary)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ("solver","originals"):
        cli.add_argument("--"+name,type=Path,required=True)
    args=cli.parse_args()
    args.solver=args.solver.resolve()
    publish(args)
