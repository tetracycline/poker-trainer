"""Stage rank121 from authenticated B698 originals and the pinned B700 positive."""
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

import hu_b698_rank121_thigh as worker
native=worker.native
import hu_b688_collect as previous_collector
import hu_apply_cert_extensions as certification
from hu_b700_collect import HEAD, SOURCE_BLOBS, PREVIOUS_BLOBS, WORKERS, authenticate, source_bytes, previous_bytes
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


def extract_archive(raw, folder):
    with ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        assert len(names)==len(set(names))
        for name in names:
            path=PurePosixPath(name)
            assert not path.is_absolute() and ".." not in path.parts
            target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(z.read(name))
    return names


def policy_comparisons(hands, selected):
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
    return comparisons


def previous_positive(args, solver, pipeline, pool, route, routes_raw, model, contract):
    """Recheck the one published positive's original jobs/strategies; never rerun CFR."""
    directory=args.previous_evidence
    previous_bytes(directory)
    receipt=json.loads((directory/"partial/b688_auth_receipt.json").read_bytes())
    assert receipt["source"]==dict(head=previous_collector.HEAD,blobs=previous_collector.SOURCE_BLOBS)
    previous_collector.source_bytes()
    pin,=[p for p in previous_collector.WORKERS if p["flop"]=="Ts8s6h"]
    r,=[r for r in receipt["workers"] if r["artifact"]["id"]==pin["id"]]
    previous_collector.authenticate(receipt["run"],r["job"],r["artifact"],pin)
    group=json.loads((directory/"partial/rank121.json").read_bytes())
    assert (group["rank"],group["model_id"],len(group["boards"]),len(group["pins"]))==(121,native.MODEL,1,1)
    board,=group["boards"];published,=group["pins"]
    assert (board["flop"],board["turn"],board["public_board"],board["acting_seat"],board["actual_exact_action_line"])==(
        "Ts8s6h","2c","6h8sTs2c",0,native.LINE)
    assert compatible(contract,board)
    assert published["archive_code"]=="B686_R121_TS8S6H"
    archive=(directory/("NL2_"+published["archive_code"]+".zip")).read_bytes()
    assert sha(archive)==pin["sha256"]==published["archive_sha256"]
    medium=json.loads((directory/"partial/b688_rank121_locked_medium.json").read_bytes())
    assert len(medium["references"])==len(medium["gto_references"])==1
    with TemporaryDirectory(prefix="b700-prior-positive-") as td:
        folder=Path(td);names=extract_archive(archive,folder)
        expected=json.loads((folder/"proof.json").read_bytes())
        assert expected["schema"]=="NL2_B686_R121_ORIGINAL_WORKER_V1"
        assert json.loads((folder/"rendered-routes.json").read_bytes())==route
        current=folder/"current-routes.json";current.write_bytes(routes_raw)
        with contextlib.redirect_stdout(io.StringIO()):
            native.run(SimpleNamespace(solver=solver,flop=pin["flop"],output=folder,routes=current,driver=None))
        assert json.loads((folder/"proof.json").read_bytes())==expected
        selected,=[t for t in expected["turns"] if t["shared_hands"]]
        assert selected["turn"]=="2c" and expected["positive_distinct_flops"]==1
        required={"flop/job.json","flop/result.json","proof.json","rendered-routes.json"}
        for turn in expected["turns"]:
            if turn["gto_solved"]:required|={turn["turn"]+"-gto/"+n for n in ("job.json","result.json")}
            if turn["paired"]:required|={turn["turn"]+"-exp_oop/"+n for n in ("job.json","result.json")}
        assert set(names)==required
        original,locked=sources(folder,pin,selected,pipeline,pool,published["archive_code"])
        rows,hands,diagnostics=zip(*(observe(source,"2c",route) for source in (original,locked)),strict=True)
        comparisons=policy_comparisons(hands,selected)
        assert comparisons==published["rendered_decision_hands"]
        for prefix,key,row,diagnostic in zip(("gto","nl2"),("gto_references","references"),rows,diagnostics,strict=True):
            assert row["source_sha256"]==selected[prefix+"_sha256"]
            assert row["b50"]==selected[prefix+"_b50"] and diagnostic==selected[prefix+"_diagnostic"]
            row["rendered_decision_hands"]=comparisons
            assert medium[key][source_key(native.MODEL,row)]==row
        old_source=certification.SOURCE
        try:
            certification.SOURCE=directory
            for source,prefix in ((original,"GTO"),(locked,"NL2")):
                case,node=certification.verify_case(published["viewer_archive_code"],published["viewer_sha256"],
                    pin["run"],model,board,source["version"],source["source_sha256"],published[prefix+"_strict_combos"])
                replayed,legal,pair_count=pairs.source_case(model,source,board["public_board"],native.LINE,0)
                assert replayed==case and len(legal)==published[prefix+"_strict_combos"]>0
                assert pair_count==published[prefix+"_compatible_hole_card_pairs"]>0
        finally:
            certification.SOURCE=old_source
        assert published["original_GTO_SHA256"]==original["source_sha256"]
        assert published["actual_NL2_SHA256"]==locked["source_sha256"]
    medium["schema"]="NL2_HU_B700_ORIGINAL_LOCKED_MEDIUM_V1"
    prior=dict(published_blob_head=HEAD,published_blobs=PREVIOUS_BLOBS,source=receipt["source"],
        run=receipt["run"],worker=r,positive_flop="Ts8s6h",turn="2c",original_jobs_and_strategies_replayed=True,
        native_cfr_rerun=False,negative_workers_replayed=0)
    return group,medium,prior


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
    routes_raw=(args.routes.read_bytes() if args.routes else subprocess.check_output(["node","tools/hu_b686_rank121_routes.cjs"]))
    route=json.loads(routes_raw)
    model=(json.loads(args.model.read_bytes()) if args.model else
        json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][native.MODEL])
    assert (model["model_id"],model["frequency_rank"],model["solver_profile"],model["family"])==(native.MODEL,121,"BB3_BTN","3BP")
    assert abs(8323/3404/model["assumed_model_node_spr"]-1)<.001
    assert model["street"]==1
    contract=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][native.MODEL]
    data=args.output/"data";evidence=data/"solver_evidence";partial=evidence/"partial"
    partial.mkdir(parents=True,exist_ok=True);pairs.EVIDENCE=evidence
    assert json.loads((args.receipts/"previous-blobs.json").read_bytes())==dict(head=HEAD,blobs=PREVIOUS_BLOBS)
    group,medium,prior_receipt=previous_positive(args,solver,pipeline,pool,route,routes_raw,model,contract)
    run=json.loads((args.receipts/"run.json").read_bytes())
    report=[];receipts=[]
    for pin in WORKERS:
        artifact=json.loads((args.receipts/(str(pin["id"])+".json")).read_bytes())
        job=json.loads((args.receipts/("job."+str(pin["job"])+".json")).read_bytes())
        authenticate(run,job,artifact,pin)
        archive=(args.receipts/(str(pin["id"])+".zip")).read_bytes();assert sha(archive)==pin["sha256"]
        receipts.append(dict(artifact=artifact,job=job))
        with TemporaryDirectory(prefix="b700-replay-") as td:
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
                worker.run(SimpleNamespace(solver=solver,flop=pin["flop"],output=folder,routes=current,driver=None))
            assert json.loads((folder/"proof.json").read_bytes())==expected
            assert (expected["schema"],expected["rank"],expected["flop"])==("NL2_B698_R121_ORIGINAL_WORKER_V1",121,pin["flop"])
            assert (expected["source_algorithm_batch"],expected["new_source_batch"],expected["preregistered_new_flops"])==(686,698,list(worker.CASES))
            required={"flop/job.json","flop/result.json","proof.json","rendered-routes.json"}
            for turn in expected["turns"]:
                if turn["gto_solved"]:required|={turn["turn"]+"-gto/"+n for n in ("job.json","result.json")}
                if turn["paired"]:required|={turn["turn"]+"-exp_oop/"+n for n in ("job.json","result.json")}
            assert set(names)==required
            proof_name="b700_"+pin["flop"].upper()+"_proof.json"
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
            code="B698_R121_"+pin["flop"].upper()
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
                viewer_code="B700_R121_"+pin["flop"].upper())
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
    medium_path=(data/"nl2_hu_b700_locked_medium.json") if certified else (partial/"b700_rank121_locked_medium.json")
    medium_path.write_bytes(json_bytes(medium))
    (data/"nl2_hu_b700_workers.json").write_bytes(json_bytes(WORKERS))
    (data/"nl2_hu_b700_results.json").write_bytes(json_bytes(report))
    (partial/"b700_auth_receipt.json").write_bytes(json_bytes(dict(run=run,source=source_receipt,workers=receipts,previous_positive=prior_receipt)))
    summary=dict(positive_distinct_flops=len(flops),prior_positive_distinct_flops=1,
        new_positive_distinct_flops=sum(r["positive"] for r in report),negative_flops=sum(not r["positive"] for r in report),
        certification_eligible=certified,native_flop_solves=len(WORKERS),
        native_gto_turns=sum(r["native_gto_turns"] for r in report),
        native_locked_turns=sum(r["native_locked_turns"] for r in report),
        actor_locked_boards=sum(r["native_locked_turns"] for r in report),
        half_pot_assessed=sum(r["native_locked_turns"] for r in report),
        selected_cert_actor_locked_boards=len(flops),selected_cert_half_pot_assessed=len(flops),
        prior_source_original_jobs_and_strategies_replayed=True,native_cfr_rerun=False,
        selected_new_nl2_half_pot_eligible_combos=sum(r.get("nl2_half_pot_combos",0) for r in report),
        new_nl2_half_pot_eligible_combos=sum(t["nl2_b50"]["eligible"] for r in report for t in r["root_and_turn_diagnostics"] if t["paired"]),
        new_locked_policy_disagreement_boards=sum(t["paired"] and not t["shared_hands"] for r in report for t in r["root_and_turn_diagnostics"]),
        nonpolarized_candidates=sum(t["nl2_b50"]["candidate"] for r in report for t in r["root_and_turn_diagnostics"] if t["paired"]))
    (data/"nl2_hu_b700_summary.json").write_bytes(json_bytes(summary))
    print(json.dumps(summary))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output"):cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--routes",type=Path,help="Optional actual rendered route snapshot; CI renders the current UI")
    cli.add_argument("--previous-evidence",type=Path,default=Path("data/solver_evidence"))
    cli.add_argument("--model",type=Path,help="Optional GitHub model record for isolated local replay; CI reads the current registry")
    replay(cli.parse_args())

