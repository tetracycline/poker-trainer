"""Replay authenticated B686 sources and preserve rank121's partial exact evidence."""
import argparse
import contextlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b686_rank121 as native
from hu_b688_collect import HEAD, SOURCE_BLOBS, WORKERS, authenticate, source_bytes
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key, summarize
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible
from verify_hu_multiboard_100bb import lock_scope

POLICY_FIELDS=("action_order","accepted_mask","accepted_actions","strategy")


def sources(folder,pin,selected,pipeline,pool,code):
    root_raw=(folder/"flop/result.json").read_bytes();root=json.loads(root_raw)
    root_sha=sha(compact(root));turn=selected["turn"]
    job=native.turn_job(root,turn,pipeline)
    assert json.loads((folder/(turn+"-gto")/"job.json").read_bytes())==json.loads(compact(job))
    g=dict(root=root,run=pin["run"],version="gto",root_sha256=root_sha,
        original_root_sha256=sha(root_raw),archive_code=code,archive_sha256=pin["sha256"],
        manifest=dict(spot="BB3_BTN",pot_family="3BP",locks=[],
            preflop_ranges=dict(source="PINNED_POKER_SOLVER_PREFLOP_CFR",spot="BB3_BTN")))
    locked_job,meta=native.prepare_job(dict(source=g,job=job),"exp_oop",pool,pipeline)
    locked_job["out"]="result.json"
    assert json.loads((folder/(turn+"-exp_oop")/"job.json").read_bytes())==json.loads(compact(locked_job))
    e=dict(g,version="exp_oop",verified_gto_parent=dict(run=pin["run"],sha256=root_sha),
        manifest=dict(g["manifest"],locks=meta,gto_parent_source_run_id=pin["run"],gto_parent_source_sha256=root_sha))
    for source,version in ((g,"gto"),(e,"exp_oop")):
        raw=(folder/(turn+"-"+version)/"result.json").read_bytes()
        sub=json.loads(raw);sub.update(line0=native.FLOP_LINE,turn=turn,rivers=[])
        source.update(subgame=sub,source_sha256=sha(raw))
    e.update(applied_rust_rates=e["subgame"]["info"]["lock_stats"],
        measured_lock_application=native.audit_patterns(e["subgame"],locked_job,e["manifest"],pool,hero_seat=0))
    assert e["measured_lock_application"]==selected["measured_lock_application"]
    return g,e


def observe(source,turn,route):
    root,sub=source["root"],source["subgame"]
    row,hands,diagnostic=native.decision(root,sub,turn,route)
    info=sub["info"]
    row.update(version=source["version"],spot="BB3_BTN",family="3BP",flop=sub["flop"],turn=turn,
        source_run_id=source["run"],source_sha256=source["source_sha256"],archive_sha256=source["archive_sha256"],
        root_sha256=source["root_sha256"],original_root_sha256=source["original_root_sha256"],
        root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],root_locked_hero_gap_pct=None,
        gto_gap_pct=info["gto_expl_pct"],locked_hero_gap_pct=info.get("hero_gap_pct"),
        lock_scope=lock_scope(sub,source["manifest"]["locks"],source["version"]),
        root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(v["nodes"] for v in info.get("lock_stats",{}).values()),
        rendered_diagnostic=diagnostic)
    summarize(row)
    return row,hands,diagnostic


def replay(args):
    source_bytes()
    source_receipt=json.loads((args.receipts/"source-blobs.json").read_bytes())
    assert source_receipt==dict(head=HEAD,blobs=SOURCE_BLOBS)
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==native.SOLVER
    py=solver/"postflop/py"
    assert sha((py/"pipeline.py").read_bytes())==PIPELINE
    assert sha((py/"ranges.py").read_bytes())==RANGES
    sys.path.insert(0,str(py))
    import pipeline
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    routes_raw=args.routes.read_bytes();route=json.loads(routes_raw)
    model=(json.loads(args.model.read_bytes()) if args.model else
        json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][native.MODEL])
    assert (model["model_id"],model["frequency_rank"],model["solver_profile"],model["family"])==(native.MODEL,121,"BB3_BTN","3BP")
    assert abs(8323/3404/model["assumed_model_node_spr"]-1)<.001
    assert model["street"]==1
    contract=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][native.MODEL]
    data=args.output/"data";evidence=data/"solver_evidence";partial=evidence/"partial"
    partial.mkdir(parents=True,exist_ok=True);pairs.EVIDENCE=evidence
    group=dict(rank=121,model_id=native.MODEL,boards=[],pins=[])
    medium=dict(schema="NL2_HU_B688_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    run=json.loads((args.receipts/"run.json").read_bytes())
    report=[];receipts=[]
    for pin in WORKERS:
        artifact=json.loads((args.receipts/(str(pin["id"])+".json")).read_bytes())
        job=json.loads((args.receipts/("job."+str(pin["job"])+".json")).read_bytes())
        authenticate(run,job,artifact,pin)
        archive=(args.receipts/(str(pin["id"])+".zip")).read_bytes();assert sha(archive)==pin["sha256"]
        receipts.append(dict(artifact=artifact,job=job))
        with TemporaryDirectory(prefix="b688-replay-") as td:
            folder=Path(td)
            with ZipFile(io.BytesIO(archive)) as z:
                names=[n for n in z.namelist() if not n.endswith("/")]
                assert len(names)==len(set(names))
                for name in names:
                    p=PurePosixPath(name);assert not p.is_absolute() and ".." not in p.parts
                    target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
            raw_proof=(folder/"proof.json").read_bytes();expected=json.loads(raw_proof)
            assert json.loads((folder/"rendered-routes.json").read_bytes())==route
            current=folder/"current-routes.json";current.write_bytes(routes_raw)
            with contextlib.redirect_stdout(io.StringIO()):
                native.run(SimpleNamespace(solver=solver,flop=pin["flop"],output=folder,routes=current,driver=None))
            assert json.loads((folder/"proof.json").read_bytes())==expected
            assert (expected["schema"],expected["rank"],expected["flop"])==("NL2_B686_R121_ORIGINAL_WORKER_V1",121,pin["flop"])
            required={"flop/job.json","flop/result.json","proof.json","rendered-routes.json"}
            for turn in expected["turns"]:
                if turn["gto_solved"]:required|={turn["turn"]+"-gto/"+n for n in ("job.json","result.json")}
                if turn["paired"]:required|={turn["turn"]+"-exp_oop/"+n for n in ("job.json","result.json")}
            assert set(names)==required
            proof_name="b688_"+pin["flop"].upper()+"_proof.json"
            (partial/proof_name).write_bytes(raw_proof)
            selected=[t for t in expected["turns"] if t["shared_hands"]]
            assert len(selected)==expected["positive_distinct_flops"]<=1
            record=dict(flop=pin["flop"],source_run_id=pin["run"],worker_artifact=pin["id"],
                archive_sha256=pin["sha256"],positive=bool(selected),
                proof_path="data/solver_evidence/partial/"+proof_name,proof_sha256=sha(raw_proof),
                native_gto_turns=sum(t["gto_solved"] for t in expected["turns"]),
                native_locked_turns=sum(t["paired"] for t in expected["turns"]),root_and_turn_diagnostics=expected["turns"])
            if not selected:report.append(record);continue
            selected,=selected;turn=selected["turn"];public=selected["public_board"]
            assert compatible(contract,dict(public_board=public,actual_exact_action_line=native.LINE,acting_seat=0))
            code="B686_R121_"+pin["flop"].upper()
            (evidence/("NL2_"+code+".zip")).write_bytes(archive)
            original,locked=sources(folder,pin,selected,pipeline,pool,code)
            observations=[observe(s,turn,route) for s in (original,locked)]
            rows,hands,diagnostics=zip(*observations,strict=True)
            common=sorted(hands[0].keys()&hands[1].keys())
            assert common==selected["shared_hands"] and common
            comparisons=[]
            for hand in common:
                g,e=hands[0][hand],hands[1][hand]
                assert g==selected["gto_witnesses"][hand] and e==selected["nl2_witnesses"][hand]
                assert all(g[k]==e[k] for k in ("flop_class","turn_class","displayed_suggestion"))
                comparisons.append(dict(hand=hand,flop_class=g["flop_class"],turn_class=g["turn_class"],
                    displayed_suggestion=g["displayed_suggestion"],
                    gto={k:g[k] for k in POLICY_FIELDS},nl2={k:e[k] for k in POLICY_FIELDS}))
            for prefix,row,diagnostic in zip(("gto","nl2"),rows,diagnostics,strict=True):
                assert row["source_sha256"]==selected[prefix+"_sha256"]
                assert row["b50"]==selected[prefix+"_b50"] and diagnostic==selected[prefix+"_diagnostic"]
                row["rendered_decision_hands"]=comparisons
            board,p=pairs.emit_board(model,original,locked,public,native.LINE,texture(pin["flop"]),
                viewer_code="B688_R121_"+pin["flop"].upper())
            assert board and p["GTO_compatible_hole_card_pairs"]>=p["GTO_strict_combos"]>0
            assert p["NL2_compatible_hole_card_pairs"]>=p["NL2_strict_combos"]>0
            board.update(source_run_role="ORIGINAL_WORKFLOW_NATIVE_CFR",origin_solve_run_id=pin["run"],
                restricted_flop_bet_sizes_pct=[33],flop_bet_size_menu="33%",
                certification_scope=expected["lock_scope"])
            p.update(rendered_decision_hands=comparisons,source_run_role=board["source_run_role"],
                worker_artifact=pin["id"],worker_sha256=pin["sha256"],
                exact_root_sizing=dict(pot_bb=20.5,effective_stack_bb=90,flop_bet_chips=677,turn_pot_chips=3404,turn_stack_chips=8323),
                root_gate=selected["root_gate"],source_blob_head=HEAD)
            board["nl2_locked_variants"][0].update(source_run_role=board["source_run_role"],
                origin_solve_run_id=pin["run"],pool_sha256=POOL,measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",
                applied_street_rates=rates(locked),gto_parent_source_run_id=pin["run"],
                gto_parent_source_sha256=original["root_sha256"],viewer_archive_code=p["viewer_archive_code"],viewer_sha256=p["viewer_sha256"])
            group["boards"].append(board);group["pins"].append(p)
            for key,row in zip(("gto_references","references"),rows,strict=True):medium[key][source_key(native.MODEL,row)]=row
            record.update(public_board=public,shared_rendered_hands=len(common),
                compatible_pairs=[r["compatible_hole_card_pairs"] for r in rows],
                gto_half_pot_combos=rows[0]["b50"]["eligible"],nl2_half_pot_combos=rows[1]["b50"]["eligible"],
                nl2_nonpolarized_candidate=rows[1]["b50"]["candidate"])
            report.append(record)
    flops=[b["flop"] for b in group["boards"]]
    assert len({suit_isomorphism_class(f) for f in flops})==len(flops)<=5
    certified=len(flops)>=3
    target=evidence/("reverified" if certified else "partial");target.mkdir(exist_ok=True)
    (target/"rank121.json").write_bytes(json_bytes(group))
    medium_path=(data/"nl2_hu_b688_locked_medium.json") if certified else (partial/"b688_rank121_locked_medium.json")
    medium_path.write_bytes(json_bytes(medium))
    (data/"nl2_hu_b688_workers.json").write_bytes(json_bytes(WORKERS))
    (data/"nl2_hu_b688_results.json").write_bytes(json_bytes(report))
    (partial/"b688_auth_receipt.json").write_bytes(json_bytes(dict(run=run,source=source_receipt,workers=receipts)))
    summary=dict(positive_distinct_flops=len(flops),negative_flops=sum(not r["positive"] for r in report),
        certification_eligible=certified,native_flop_solves=len(WORKERS),
        native_gto_turns=sum(r["native_gto_turns"] for r in report),
        native_locked_turns=sum(r["native_locked_turns"] for r in report),
        actor_locked_boards=len(flops),half_pot_assessed=len(flops),
        nl2_half_pot_eligible_combos=sum(r.get("nl2_half_pot_combos",0) for r in report),
        nonpolarized_candidates=sum(r.get("nl2_nonpolarized_candidate",False) for r in report))
    (data/"nl2_hu_b688_summary.json").write_bytes(json_bytes(summary))
    print(json.dumps(summary))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output","routes"):cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--model",type=Path,help="Optional GitHub model record for isolated local replay; CI reads the current registry")
    replay(cli.parse_args())

