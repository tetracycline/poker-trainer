"""Replay authenticated B676 jobs; stage independent rank229/rank230 evidence.

Only ranks with at least three positive, distinct flop structures enter
reverified/. Partial positives and negatives never enter the live registry or
the global medium-report glob.
"""
import argparse
import base64
import contextlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b676_checked_rivers as native
from hu_b679_collect import WORKERS, authenticate
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b514_turn_stab import rates
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key, summarize
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import cardkey, game_reach
from hu_trainer_route_gate import compatible
from verify_hu_multiboard_100bb import lock_scope


def decision(source,public,route):
    root,sub=source["root"],source["subgame"]
    node,=[n for n in sub["nodes"] if (n["board"],n["line"],n["player"])==(public,native.LINE,0)]
    assert (node["pot"],node["bets"])==(2100,[0,0])
    row=proof(root,sub,node,game_reach(root,sub)[0])
    info=sub["info"]
    row.update(version=source["version"],spot="SB3_BTN",family="3BP",flop=sub["flop"],turn=sub["turn"],
        source_run_id=source["run"],source_sha256=source["source_sha256"],archive_sha256=source["archive_sha256"],
        root_sha256=source["root_sha256"],root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],
        root_locked_hero_gap_pct=None,gto_gap_pct=info["gto_expl_pct"],locked_hero_gap_pct=info.get("hero_gap_pct"),
        lock_scope=lock_scope(sub,source["manifest"]["locks"],source["version"]),root_applied_rust_lock_nodes=0,
        subgame_applied_rust_lock_nodes=sum(s["nodes"] for s in info.get("lock_stats",{}).values()))
    summarize(row)
    masks=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    found={}
    for i,(hole,bits) in enumerate(zip(sub["hands"][0],masks,strict=True)):
        if not bits:continue
        hand="".join(cardkey(hole))
        cells=[hand_cell(hand,public[:end]) for end in (6,8,10)]
        if any(cell[0] not in route[street] for street,cell in zip(("flop","turn","river"),cells,strict=True)):
            continue
        label=route["river"][cells[-1][0]]
        action=native.ACTION[label]
        if action not in node["acts"] or not bits&(1<<node["acts"].index(action)):continue
        weights=[max(0,node["strat"][a*len(masks)+i]) for a in range(len(node["acts"]))]
        total=sum(weights);assert total>0
        policy=dict(action_order=node["acts"],accepted_mask=bits,
            accepted_actions=[a for k,a in enumerate(node["acts"]) if bits&(1<<k)],
            strategy={a:round(w/total,7) for a,w in zip(node["acts"],weights,strict=True)})
        found[hand]=([c[1] for c in cells],label,policy)
    return row,found


def sources(folder,pin,selection,pipeline,pool,code):
    root=json.loads((folder/"flop/result.json").read_bytes())
    root_sha=sha(compact(root))
    turn=selection["turn"]
    original=json.loads((folder/(turn+"-gto")/"job.json").read_bytes())
    rivers=[e["prefix"][-1] for e in original["extract"] if e["prefix"]]
    g=dict(root=root,run=pin["run"],version="gto",root_sha256=root_sha,
        archive_code=code,archive_sha256=pin["sha256"],
        manifest=dict(spot="SB3_BTN",pot_family="3BP",locks=[],
            preflop_ranges=dict(source="PINNED_POKER_SOLVER_PREFLOP_CFR",spot="SB3_BTN")))
    locked_job,meta=native.prepare_job(dict(source=g,job=original),"exp_oop",pool,pipeline)
    locked_job["out"]="result.json"
    assert json.loads((folder/(turn+"-exp_oop")/"job.json").read_bytes())==json.loads(compact(locked_job))
    e=dict(g,version="exp_oop",verified_gto_parent=dict(run=pin["run"],sha256=root_sha),
        manifest=dict(g["manifest"],locks=meta,gto_parent_source_run_id=pin["run"],gto_parent_source_sha256=root_sha))
    for source,version in ((g,"gto"),(e,"exp_oop")):
        raw=(folder/(turn+"-"+version)/"result.json").read_bytes()
        sub=json.loads(raw);sub.update(line0="x x",turn=turn,rivers=rivers)
        source.update(subgame=sub,source_sha256=sha(raw))
    e.update(applied_rust_rates=e["subgame"]["info"]["lock_stats"],
        measured_lock_application=native.audit_patterns(e["subgame"],locked_job,e["manifest"],pool,hero_seat=0))
    assert e["measured_lock_application"]
    return g,e


def replay(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==native.SOLVER
    py=solver/"postflop/py"
    assert sha((py/"pipeline.py").read_bytes())==PIPELINE
    assert sha((py/"ranges.py").read_bytes())==RANGES
    sys.path.insert(0,str(py))
    import pipeline
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    routes_raw=args.routes.read_bytes() if args.routes else subprocess.check_output(["node","tools/hu_b676_checked_routes.cjs"])
    routes=json.loads(routes_raw)
    registry=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    contracts=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"]
    data=args.output/"data";evidence=data/"solver_evidence"
    partial=evidence/"partial";partial.mkdir(parents=True,exist_ok=True)
    pairs.EVIDENCE=evidence
    groups={rank:dict(rank=rank,model_id=mid,boards=[],pins=[]) for rank,mid in native.MODELS.items()}
    mediums={rank:dict(schema="NL2_HU_B679_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={}) for rank in native.MODELS}
    run=json.loads((args.receipts/"run.json").read_bytes())
    report=[];auth=[]
    for pin in WORKERS:
        rank=pin["rank"];mid=native.MODELS[rank];flop=pin["flop"]
        receipt=json.loads((args.receipts/(str(pin["id"])+".json")).read_bytes())
        job=json.loads((args.receipts/("job."+str(pin["job"])+".json")).read_bytes())
        authenticate(run,job,receipt,pin)
        archive=(args.receipts/(str(pin["id"])+".zip")).read_bytes()
        assert sha(archive)==pin["sha256"]
        auth.append(dict(artifact=receipt,job=job))
        with TemporaryDirectory(prefix="b679-replay-") as td:
            folder=Path(td)
            with ZipFile(io.BytesIO(archive)) as z:
                files=[n for n in z.namelist() if not n.endswith("/")]
                assert len(files)==len(set(files))
                for name in files:
                    p=PurePosixPath(name)
                    assert not p.is_absolute() and ".." not in p.parts
                    target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(z.read(name))
            expected=json.loads((folder/"proof.json").read_bytes())
            assert json.loads((folder/"rendered-routes.json").read_bytes())==routes
            routefile=folder/"current-routes.json";routefile.write_bytes(routes_raw)
            with contextlib.redirect_stdout(io.StringIO()):
                native.run(SimpleNamespace(solver=solver,flop=flop,output=folder,routes=routefile,driver=None))
            assert json.loads((folder/"proof.json").read_bytes())==expected
            assert (expected["batch"],expected["target_rank"],expected["flop"])==(676,rank,flop)
            expected_files={"flop/job.json","flop/result.json","proof.json","rendered-routes.json"}
            for turn in expected["turns"]:
                if turn["legal_rivers"]:
                    expected_files|={turn["turn"]+"-gto/"+f for f in ("job.json","result.json")}
                if turn["paired_policies"]:
                    expected_files|={turn["turn"]+"-exp_oop/"+f for f in ("job.json","result.json")}
            assert set(files)==expected_files
            selected=expected["selected"][str(rank)]
            record=dict(rank=rank,flop=flop,source_run_id=pin["run"],worker_artifact=pin["id"],
                worker_sha256=pin["sha256"],proof=expected,status="NO_SHARED_RENDERED_HAND")
            if selected is None:
                assert not any(t["checks"][str(rank)] for t in expected["turns"])
                report.append(record);continue
            public=selected["board"]
            assert compatible(contracts[mid],dict(public_board=public,actual_exact_action_line=native.LINE,acting_seat=0))
            code="B676_SB3_"+flop.upper()
            (evidence/("NL2_"+code+".zip")).write_bytes(archive)
            original,locked=sources(folder,pin,selected,pipeline,pool,code)
            observations=[decision(s,public,routes[str(rank)]) for s in (original,locked)]
            rows,hands=zip(*observations,strict=True)
            common=sorted(hands[0].keys()&hands[1].keys())
            assert common==selected["hands"] and common
            comparisons=[]
            for hand in common:
                labels,label,gpolicy=hands[0][hand]
                assert hands[1][hand][:2]==hands[0][hand][:2]
                comparisons.append(dict(hand=hand,flop_class=labels[0],turn_class=labels[1],river_class=labels[2],
                    displayed_suggestion=label,gto=gpolicy,nl2=hands[1][hand][2]))
            for prefix,row in zip(("gto","locked"),rows,strict=True):
                assert row["b50"]==selected[prefix+"_b50"]
                assert row["strict_legal_combos"]==selected[prefix+"_strict_combos"]
                assert row["compatible_hole_card_pairs"]==selected[prefix+"_compatible_pairs"]
                row["rendered_decision_hands"]=comparisons
            board,p=pairs.emit_board(registry[mid],original,locked,public,native.LINE,texture(flop),
                viewer_code="B679_R"+str(rank)+"_"+flop.upper())
            assert board and p["GTO_compatible_hole_card_pairs"]>0 and p["NL2_compatible_hole_card_pairs"]>0
            board.update(source_run_role="ORIGINAL_WORKFLOW_NATIVE_CFR",origin_solve_run_id=pin["run"],
                restricted_flop_bet_sizes_pct=[50],flop_bet_size_menu="50%",
                certification_scope="FROZEN_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_MARGINALS")
            p.update(rendered_decision_hands=comparisons,source_run_role=board["source_run_role"],
                worker_artifact=pin["id"],worker_sha256=pin["sha256"],
                exact_root_sizing=dict(pot_bb=21,effective_stack_bb=90,flop_open_pct=[50]))
            board["nl2_locked_variants"][0].update(source_run_role=board["source_run_role"],
                origin_solve_run_id=pin["run"],pool_sha256=POOL,
                measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",applied_street_rates=rates(locked),
                gto_parent_source_run_id=pin["run"],gto_parent_source_sha256=original["root_sha256"],
                viewer_archive_code=p["viewer_archive_code"],viewer_sha256=p["viewer_sha256"])
            groups[rank]["boards"].append(board);groups[rank]["pins"].append(p)
            for key,row in zip(("gto_references","references"),rows,strict=True):
                mediums[rank][key][source_key(mid,row)]=row
            record.update(status="BOTH_POLICIES_RENDERED_HAND_POSITIVE",public_board=public,
                shared_hands=len(common),compatible_pairs=[r["compatible_hole_card_pairs"] for r in rows],
                actor_locked=True,half_pot_assessed=True,half_pot_candidate=rows[1]["b50"]["candidate"])
            report.append(record)
    eligible=[]
    global_medium=dict(schema="NL2_HU_B679_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    for rank,group in groups.items():
        flops=[b["flop"] for b in group["boards"]]
        assert len({suit_isomorphism_class(f) for f in flops})==len(flops)<=5
        certified=len(flops)>=3
        if certified:eligible.append(rank)
        destination=evidence/("reverified" if certified else "partial")
        destination.mkdir(exist_ok=True)
        (destination/("rank"+str(rank)+".json")).write_bytes(json_bytes(group))
        if certified:
            for key in ("references","gto_references"):global_medium[key].update(mediums[rank][key])
        else:
            (partial/("b679_rank"+str(rank)+"_locked_medium.json")).write_bytes(json_bytes(mediums[rank]))
    if eligible:(data/"nl2_hu_b679_locked_medium.json").write_bytes(json_bytes(global_medium))
    (data/"nl2_hu_b679_workers.json").write_bytes(json_bytes(WORKERS))
    (data/"nl2_hu_b679_results.json").write_bytes(json_bytes(report))
    (partial/"b679_auth_receipt.json").write_bytes(json_bytes(dict(run=run,workers=auth)))
    summary=dict(cert_eligible_ranks=eligible,positive_boards_by_rank={str(r):len(g["boards"]) for r,g in groups.items()},
        actor_locked_boards=sum(r.get("actor_locked",False) for r in report),
        half_pot_assessed=sum(r.get("half_pot_assessed",False) for r in report),
        half_pot_candidates=sum(r.get("half_pot_candidate",False) for r in report),
        negatives=sum(r["status"]=="NO_SHARED_RENDERED_HAND" for r in report))
    (data/"nl2_hu_b679_summary.json").write_bytes(json_bytes(summary))
    print(json.dumps(summary))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output"):cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--routes",type=Path)
    replay(cli.parse_args())

