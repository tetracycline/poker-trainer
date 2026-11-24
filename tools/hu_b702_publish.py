"""Replay B705 continuations and their preserved B696 roots at exact UI prices.

All original ZIPs and all negative proofs remain traceable. Only three to five
positive, nonisomorphic original flops per rank enter reverified/. Live prices,
registry, references and queue are never changed by this publisher.
"""
import argparse
import base64
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b696_turn_call_rivers as native
import hu_b696_stage_prices as prices
import hu_b702_collect as root_collector
import hu_b705_resume_turn_call as resumed
from hu_b702_resume_collect import HEAD, RUN, ROOTS, SOURCE_BLOBS, WORKERS, authenticate, source_bytes, unpack_roots
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

SCHEMA="NL2_HU_B702_ORIGINAL_LOCKED_MEDIUM_V1"


def extract(raw,folder):
    with ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        assert len(names)==len(set(names))
        for name in names:
            path=PurePosixPath(name);assert not path.is_absolute() and ".." not in path.parts
            target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    return names


def isolated_prices(args):
    """Load the pinned staged model without replacing any live source file."""
    source_bytes()
    live={name:prices.digest(name) for name in prices.PINS}
    states=[]
    for name,(old,new,staged) in prices.PINS.items():
        assert prices.digest(staged)==new and live[name] in (old,new)
        states.append(live[name]==new)
    assert len(set(states))==1
    root=Path.cwd()
    routes_raw=(args.routes.read_bytes() if args.routes else subprocess.check_output([
        "node","tools/hu_b696_turn_call_routes.cjs","--model-file",prices.PINS["nl2_hu_model.js"][2]]))
    routes=json.loads(routes_raw)
    original=json.loads(args.registry.read_bytes())["records"]
    with TemporaryDirectory(prefix="b702-priced-contract-") as td:
        folder=Path(td)
        for name in ("lines_data.js","nl2_rules.js","hwrange.js","nl2_reach.js","nl2_titles.js","nl2.js","data"):
            (folder/name).symlink_to(root/name,target_is_directory=name=="data")
        (folder/"nl2_hu_model.js").symlink_to(root/prices.PINS["nl2_hu_model.js"][2])
        raw=subprocess.check_output(["node",str(root/prices.PINS["tools/hu_trainer_route_contract.cjs"][2])],
            input=json.dumps(list(original)).encode(),cwd=folder)
    contract=json.loads(raw)
    assert set(contract["routes"])==set(original) and len(original)==392
    contract["routes"]={mid:contract["routes"][mid] for mid in native.MODELS.values()}
    models={}
    for rank,mid in native.MODELS.items():
        c=routes[str(rank)];model=deepcopy(original[mid])
        assert (model["model_id"],model["frequency_rank"],model["solver_profile"],model["family"],model["street"],model["label"])==(
            mid,rank,c["spot"],"SRP",2,"APPROX")
        assert c["id"]==mid and c["spr"]==(7.833 if rank==76 else 8.614)
        assert contract["routes"][mid]["priced_model_spr"]==c["spr"]
        assert contract["routes"][mid]["seat"]==c["actor"]
        assert contract["routes"][mid]["streets"]==c["line"].split("/")
        model["assumed_model_node_spr"]=c["spr"];models[rank]=model
    assert live=={name:prices.digest(name) for name in prices.PINS}
    manifest=dict(schema="NL2_B702_ISOLATED_PRICE_CONTRACT_V1",source_head=HEAD,
        staged_sources={name:dict(old=old,new=new,path=staged) for name,(old,new,staged) in prices.PINS.items()},
        unchanged_ui_blob=prices.UI,trainer_route_contract=contract,
        model_prices={str(rank):dict(model_id=native.MODELS[rank],pot_bb=routes[str(rank)]["river_pot"]/100,
            remaining_bb=routes[str(rank)]["river_stack"]/100,spr=models[rank]["assumed_model_node_spr"]) for rank in native.MODELS},
        live_sources_written=False)
    return routes_raw,routes,contract,models,manifest


def source_turn(folder,pin,turn_record,c,pipeline,pool,code,origin):
    raw=(folder/"flop/result.json").read_bytes();root=json.loads(raw);root_sha=sha(compact(root))
    turn=turn_record["turn"];rivers=turn_record["parent_gate"]["river_extracts"]
    job=native.make_turn(root,turn,rivers,c,pipeline)
    assert json.loads((folder/(turn+"-gto")/"job.json").read_bytes())==json.loads(compact(job))
    g=dict(root=root,run=pin["run"],version="gto",root_sha256=root_sha,original_root_sha256=sha(raw),
        archive_code=code,archive_sha256=pin["sha256"],root_origin=origin,manifest=dict(spot=c["spot"],pot_family="SRP",locks=[],
        preflop_ranges=dict(source="PINNED_POKER_SOLVER_PREFLOP_CFR",spot=c["spot"])))
    e=None
    if turn_record["paired_policies"]:
        version="exp_ip" if c["actor"] else "exp_oop"
        locked_job,metadata=native.prepare_job(dict(source=g,job=job),version,pool,pipeline)
        locked_job["out"]="result.json"
        assert json.loads((folder/(turn+"-"+version)/"job.json").read_bytes())==json.loads(compact(locked_job))
        e=dict(g,version=version,verified_gto_parent=dict(run=origin["original_root_run"],sha256=root_sha),
            manifest=dict(g["manifest"],locks=metadata,gto_parent_source_run_id=origin["original_root_run"],gto_parent_source_sha256=root_sha))
    for source,prefix in ((g,"gto"),(e,"nl2")):
        if source is None:continue
        raw=(folder/(turn+"-"+source["version"])/"result.json").read_bytes()
        sub=json.loads(raw);sub.update(line0="x x",turn=turn,rivers=rivers)
        assert sha(raw)==turn_record[prefix+"_source_sha256"]
        source.update(subgame=sub,source_sha256=sha(raw))
    if e is not None:
        e.update(applied_rust_rates=e["subgame"]["info"]["lock_stats"],
            measured_lock_application=native.audit_patterns(e["subgame"],locked_job,e["manifest"],pool,c["actor"]))
        assert e["measured_lock_application"]==turn_record["measured_lock_application"]
    return g,e


def observations(source,c):
    root,sub=source["root"],source["subgame"];actor=c["actor"];route=c["routes"]
    masks=game_reach(root,sub)[0];result={};info=sub["info"]
    for node in sub["nodes"]:
        if (node["line"],node["player"])!=(c["line"],actor):continue
        public=node["board"];bet=(c["pot"]*50+50)//100
        assert (node["pot"],node["bets"],sub["stack"]-max(node["bets"]))==(c["river_pot"],[bet,bet],c["river_stack"])
        row=proof(root,sub,node,masks);raw_proof=deepcopy(row)
        row.update(version=source["version"],spot=c["spot"],family="SRP",flop=sub["flop"],turn=sub["turn"],
            source_run_id=source["run"],source_sha256=source["source_sha256"],archive_sha256=source["archive_sha256"],
            root_sha256=source["root_sha256"],original_root_sha256=source["original_root_sha256"],
            original_root_run_id=source["root_origin"]["original_root_run"],
            original_root_artifact=source["root_origin"]["original_root_artifact"],
            original_root_archive_sha256=source["root_origin"]["original_root_archive_sha256"],
            root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],root_locked_hero_gap_pct=None,
            gto_gap_pct=info["gto_expl_pct"],locked_hero_gap_pct=info.get("hero_gap_pct"),
            lock_scope=lock_scope(sub,source["manifest"]["locks"],source["version"]),root_applied_rust_lock_nodes=0,
            subgame_applied_rust_lock_nodes=sum(x["nodes"] for x in info.get("lock_stats",{}).values()))
        summarize(row)
        bits=base64.b64decode(row["compatible_action_mask_b64"],validate=True);found={}
        for i,(hole,mask) in enumerate(zip(sub["hands"][actor],bits,strict=True)):
            if not mask:continue
            hand="".join(cardkey(hole));cells=[hand_cell(hand,public[:end]) for end in (6,8,10)]
            if any(cell[0] not in route[street] for street,cell in zip(("flop","turn","river"),cells,strict=True)):continue
            label=route["river"][cells[-1][0]];action=native.ACTION[label]
            if action not in node["acts"] or not mask&(1<<node["acts"].index(action)):continue
            weights=[max(0,node["strat"][a*len(bits)+i]) for a in range(len(node["acts"]))]
            total=sum(weights);assert total>0
            policy=dict(action_order=node["acts"],accepted_mask=mask,
                accepted_actions=[a for k,a in enumerate(node["acts"]) if mask&(1<<k)],
                strategy={a:round(w/total,7) for a,w in zip(node["acts"],weights,strict=True)})
            found[hand]=dict(classes=[x[1] for x in cells],displayed_suggestion=label,policy=policy)
        result[public]=dict(row=row,hands=found,raw_proof=raw_proof)
    assert {p[-2:] for p in result}==set(sub["rivers"])
    return result


def common_policies(g,e,expected):
    hands=sorted(g["hands"].keys()&e["hands"].keys())
    assert hands==expected["hands"] and hands
    out=[]
    for hand in hands:
        left,right=g["hands"][hand],e["hands"][hand]
        assert (left["classes"],left["displayed_suggestion"])==(right["classes"],right["displayed_suggestion"])
        for prefix,witness in (("gto",left),("nl2",right)):
            assert expected[prefix+"_witnesses"][hand]==dict(classes=witness["classes"],
                displayed_suggestion=witness["displayed_suggestion"],accepted_actions=witness["policy"]["accepted_actions"])
        a,b,d=left["classes"]
        out.append(dict(hand=hand,flop_class=a,turn_class=b,river_class=d,
            displayed_suggestion=left["displayed_suggestion"],gto=left["policy"],nl2=right["policy"]))
    return out


def replay(args):
    assert sys.version_info[:2]==(3,11), "Use source Python 3.11 for exact, unrounded pool-size sums"
    source_receipt=json.loads((args.receipts/"source-blobs.json").read_bytes())
    assert source_receipt==dict(head=HEAD,blobs=SOURCE_BLOBS)
    routes_raw,routes,contract,models,price_manifest=isolated_prices(args)
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==native.SOLVER
    py=solver/"postflop/py"
    assert sha((py/"pipeline.py").read_bytes())==PIPELINE and sha((py/"ranges.py").read_bytes())==RANGES
    sys.path.insert(0,str(py));import pipeline
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    data=args.output/"data";evidence=data/"solver_evidence";partial=evidence/"partial"
    partial.mkdir(parents=True,exist_ok=True);pairs.EVIDENCE=evidence
    run=json.loads((args.receipts/"run.json").read_bytes())
    roots_artifact=json.loads((args.receipts/(str(ROOTS["id"])+".json")).read_bytes())
    roots_job=json.loads((args.receipts/("job."+str(ROOTS["job"])+".json")).read_bytes())
    authenticate(run,roots_job,roots_artifact,ROOTS)
    roots_zip=(args.receipts/(str(ROOTS["id"])+".zip")).read_bytes();assert sha(roots_zip)==ROOTS["sha256"]
    original_dir=args.receipts/"original-roots"
    root_details=unpack_roots(roots_zip,original_dir)
    assert (original_dir/"current-rendered-routes.json").read_bytes()==routes_raw
    (partial/"b702_authenticated_original_roots.zip").write_bytes(roots_zip)
    original_run=json.loads((original_dir/"run.json").read_bytes());price=root_collector.PRICE
    price_artifact=json.loads((original_dir/(str(price["id"])+".json")).read_bytes())
    price_job=json.loads((original_dir/("job."+str(price["job"])+".json")).read_bytes())
    root_collector.authenticate(original_run,price_job,price_artifact,price)
    price_zip=(original_dir/(str(price["id"])+".zip")).read_bytes();assert sha(price_zip)==price["sha256"]
    for prior in root_collector.WORKERS:
        original_archive=(original_dir/(str(prior["id"])+".zip")).read_bytes()
        root_collector.authenticate_root_archive(prior,original_archive)
        original_code="B696_R"+str(prior["rank"])+"_"+prior["flop"].upper()
        (evidence/("NL2_"+original_code+".zip")).write_bytes(original_archive)
    (data/"nl2_hu_b702_original_root_workers.json").write_bytes(json_bytes(root_collector.WORKERS))
    (partial/"b702_original_root_diagnostics.json").write_bytes(json_bytes(root_details))
    with ZipFile(io.BytesIO(price_zip)) as z:
        price_report=json.loads(z.read("price-gate.json"));assert json.loads(z.read("rendered-routes.json"))==routes
    assert (price_report["schema"],price_report["total"],price_report["other_models_unchanged"],
        price_report["labels_unchanged"],price_report["live_branch_modified"])==("NL2_B696_ISOLATED_TURN_PRICE_GATE_V1",392,390,True,False)
    assert price_report["certified_unchanged"]==price_report["CERT_MULTIBOARD"]>=148
    assert price_report["corrected_prices"]=={native.MODELS[76]:[12.,94.,7.833],native.MODELS[89]:[11.,94.75,8.614]}
    (partial/"b702_source_price_gate.zip").write_bytes(price_zip)
    (data/"nl2_hu_b702_price_contract.json").write_bytes(json_bytes(price_manifest))
    groups={rank:dict(rank=rank,model_id=mid,boards=[],pins=[]) for rank,mid in native.MODELS.items()}
    medium={rank:dict(schema=SCHEMA,references={},gto_references={}) for rank in native.MODELS}
    report=[];receipts=[];all_rows={"gto_references":{},"references":{}}
    native_gto_turns=native_locked_turns=0
    for pin in WORKERS:
        rank=pin["rank"];flop=pin["flop"];c=routes[str(rank)];mid=c["id"]
        artifact=json.loads((args.receipts/(str(pin["id"])+".json")).read_bytes())
        job=json.loads((args.receipts/("job."+str(pin["job"])+".json")).read_bytes())
        authenticate(run,job,artifact,pin);receipts.append(dict(artifact=artifact,job=job))
        archive=(args.receipts/(str(pin["id"])+".zip")).read_bytes();assert sha(archive)==pin["sha256"]
        code="B705_R"+str(rank)+"_"+flop.upper()
        (evidence/("NL2_"+code+".zip")).write_bytes(archive)
        with TemporaryDirectory(prefix="b702-native-replay-") as td:
            folder=Path(td);names=extract(archive,folder)
            proof_raw=(folder/"proof.json").read_bytes();expected=json.loads(proof_raw)
            origin_raw=(folder/"resume-source.json").read_bytes();origin=json.loads(origin_raw)
            assert expected["root_origin"]==origin
            assert (origin["resume_run"],origin["resume_head"],origin["flop_native_solves_repeated"])==(pin["run"],pin["head"],0)
            assert json.loads((folder/"rendered-routes.json").read_bytes())==routes
            current=folder/"current-routes.json";current.write_bytes(routes_raw)
            with contextlib.redirect_stdout(io.StringIO()):
                resumed.run(SimpleNamespace(solver=solver,rank=rank,flop=flop,output=folder,routes=current,driver=None,
                    receipts=original_dir,resume_run=pin["run"],resume_head=pin["head"]))
            assert (folder/"proof.json").read_bytes()==proof_raw, "Source Python 3.11 replay must reproduce every original proof byte"
            assert (folder/"resume-source.json").read_bytes()==origin_raw
            assert (expected["schema"],expected["rank"],expected["model_id"],expected["flop"])==(
                "NL2_B705_RESUMED_TURN_CALL_ORIGINAL_WORKER_V1",rank,mid,flop)
            assert expected["original_algorithm_schema"]=="NL2_B696_TURN_CALL_ORIGINAL_WORKER_V1"
            assert expected["flop_native_solves_repeated"]==0
            assert expected["positive_distinct_flops"]==int(expected["selected"] is not None)
            version="exp_ip" if c["actor"] else "exp_oop"
            required={"flop/job.json","flop/result.json","proof.json","rendered-routes.json","resume-source.json"}
            for turn in expected["turns"]:
                if turn["parent_gate"]["river_extracts"]:required|={turn["turn"]+"-gto/"+n for n in ("job.json","result.json")}
                if turn["paired_policies"]:required|={turn["turn"]+"-"+version+"/"+n for n in ("job.json","result.json")}
            assert set(names)==required
            name="b702_R"+str(rank)+"_"+flop.upper()+"_proof.json";(partial/name).write_bytes(proof_raw)
            record=dict(rank=rank,flop=flop,source_run_id=pin["run"],source_blob_head=HEAD,worker_artifact=pin["id"],
                archive_code=code,archive_sha256=pin["sha256"],proof_sha256=sha(proof_raw),root_origin=origin,
                proof_path="data/solver_evidence/partial/"+name,positive=expected["selected"] is not None,proof=expected)
            selected_data=None
            for turn in expected["turns"]:
                if not turn["parent_gate"]["river_extracts"]:continue
                native_gto_turns+=1;native_locked_turns+=int(turn["paired_policies"])
                g,e=source_turn(folder,pin,turn,c,pipeline,pool,code,origin)
                observations_by_version=[]
                for source,prefix,key in ((g,"gto","gto_references"),(e,"nl2","references")):
                    if source is None:continue
                    obs=observations(source,c);observations_by_version.append(obs)
                    original_rows={r["public_board"]:r for r in turn[prefix+"_boards"]}
                    assert set(original_rows)==set(obs)
                    for public,item in obs.items():
                        assert item["raw_proof"]==original_rows[public]["reach"]
                        assert len(item["hands"])==original_rows[public]["displayed_hands"]
                        item["row"]["rendered_decision_hands"]=[]
                        all_rows[key][source_key(mid,item["row"])]=item["row"]
                if e is None:continue
                before,after=observations_by_version
                common={m["public_board"]:m for m in turn["common"]}
                actual={public for public in before if before[public]["hands"].keys()&after[public]["hands"].keys()}
                assert actual==set(common)
                for public,match in common.items():
                    comparisons=common_policies(before[public],after[public],match)
                    for prefix,row in (("gto",before[public]["row"]),("nl2",after[public]["row"])):
                        assert row["b50"]==match[prefix+"_b50"]
                        row["rendered_decision_hands"]=comparisons
                    if expected["selected"] and (turn["turn"],public)==(expected["selected"]["turn"],expected["selected"]["public_board"]):
                        assert dict(turn=turn["turn"],**match)==expected["selected"]
                        selected_data=(g,e,public,comparisons,before[public]["row"],after[public]["row"])
            assert bool(selected_data)==record["positive"]
            if selected_data:
                g,e,public,comparisons,grow,erow=selected_data
                assert compatible(contract["routes"][mid],dict(public_board=public,actual_exact_action_line=c["line"],acting_seat=c["actor"]))
                board,pinout=pairs.emit_board(models[rank],g,e,public,c["line"],texture(flop),viewer_code="B702_R"+str(rank)+"_"+flop.upper())
                assert board and pinout["GTO_compatible_hole_card_pairs"]>=pinout["GTO_strict_combos"]>0
                assert pinout["NL2_compatible_hole_card_pairs"]>=pinout["NL2_strict_combos"]>0
                board.update(source_run_role="ORIGINAL_WORKFLOW_NATIVE_CFR",origin_solve_run_id=pin["run"],
                    restricted_flop_bet_sizes_pct=[33,50,75],flop_bet_size_menu=native.ROOT_MENU,certification_scope=expected["lock_scope"],
                    original_root_run_id=origin["original_root_run"],original_root_result_sha256=origin["original_root_result_sha256"],
                    source_root_reused=True,flop_native_solves_repeated=0)
                pinout.update(rendered_decision_hands=comparisons,source_run_role=board["source_run_role"],
                    worker_artifact=pin["id"],worker_sha256=pin["sha256"],source_blob_head=HEAD,root_origin=origin,
                    original_root_archive_code="B696_R"+str(rank)+"_"+flop.upper(),
                    original_root_archive_sha256=origin["original_root_archive_sha256"],
                    exact_root_sizing=dict(pot_bb=c["pot"]/100,effective_stack_bb=c["stack"]/100,
                        turn_bet_chips=(c["pot"]*50+50)//100,river_pot_chips=c["river_pot"],river_stack_chips=c["river_stack"]))
                board["nl2_locked_variants"][0].update(source_run_role=board["source_run_role"],origin_solve_run_id=pin["run"],
                    pool_sha256=POOL,measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",applied_street_rates=rates(e),
                    gto_parent_source_run_id=origin["original_root_run"],gto_parent_source_sha256=g["root_sha256"],
                    turn_gto_source_run_id=pin["run"],turn_gto_source_sha256=g["source_sha256"],
                    viewer_archive_code=pinout["viewer_archive_code"],viewer_sha256=pinout["viewer_sha256"])
                groups[rank]["boards"].append(board);groups[rank]["pins"].append(pinout)
                for key,row in (("gto_references",grow),("references",erow)):medium[rank][key][source_key(mid,row)]=row
                record.update(public_board=public,shared_rendered_hands=len(comparisons),gto_strict_combos=grow["strict_legal_combos"],
                    nl2_strict_combos=erow["strict_legal_combos"],nonpolarized_candidate=erow["b50"]["candidate"])
            report.append(record)
    eligible=[];global_medium=dict(schema=SCHEMA,references={},gto_references={})
    for rank,group in groups.items():
        flops=[b["flop"] for b in group["boards"]]
        assert len(flops)==len({suit_isomorphism_class(f) for f in flops})<=5
        certified=len(flops)>=3
        if certified:
            eligible.append(rank);destination=evidence/"reverified";destination.mkdir(exist_ok=True)
            (destination/("rank"+str(rank)+".json")).write_bytes(json_bytes(group))
            for key in ("references","gto_references"):global_medium[key].update(medium[rank][key])
        else:
            (partial/("b702_rank"+str(rank)+".json")).write_bytes(json_bytes(group))
            (partial/("b702_rank"+str(rank)+"_locked_medium.json")).write_bytes(json_bytes(medium[rank]))
    if eligible:(data/"nl2_hu_b702_locked_medium.json").write_bytes(json_bytes(global_medium))
    (partial/"b702_all_native_node_observations.json").write_bytes(json_bytes(dict(schema=SCHEMA,**all_rows)))
    (data/"nl2_hu_b702_workers.json").write_bytes(json_bytes(WORKERS))
    (data/"nl2_hu_b702_results.json").write_bytes(json_bytes(report))
    (partial/"b702_auth_receipt.json").write_bytes(json_bytes(dict(run=run,source=source_receipt,
        original_roots=dict(pin=ROOTS,artifact=roots_artifact,job=roots_job,original_run=original_run,
            published_archive="data/solver_evidence/partial/b702_authenticated_original_roots.zip"),
        price_audit=dict(pin=price,artifact=price_artifact,job=price_job,report=price_report),workers=receipts)))
    locked=list(all_rows["references"].values());positive=[r for r in locked if r["strict_legal_combos"]>0]
    summary=dict(cert_eligible_ranks=eligible,positive_boards_by_rank={str(r):len(g["boards"]) for r,g in groups.items()},
        source_workers=len(WORKERS),negative_flops=sum(not r["positive"] for r in report),native_gto_turn_jobs=native_gto_turns,
        native_locked_turn_jobs=native_locked_turns,native_locked_river_nodes=len(locked),actor_locked_boards=len(positive),
        half_pot_assessed=sum(r["b50"] is not None for r in locked),half_pot_candidates=sum(r["b50"]["candidate"] for r in positive),
        both_policies_rendered_positive_rivers=sum(bool(r["rendered_decision_hands"]) for r in locked),
        selected_cert_boards=sum(len(groups[r]["boards"]) for r in eligible),publisher_native_cfr_rerun=False,
        original_root_run_id=root_collector.RUN,original_root_workers=len(root_collector.WORKERS),
        original_native_flop_solves_repeated=0,continuation_source_run_id=RUN,live_prices_written=False)
    (data/"nl2_hu_b702_summary.json").write_bytes(json_bytes(summary));print(json.dumps(summary))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output"):cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--routes",type=Path,help="Optional exact staged render; default renders the pinned staged model")
    cli.add_argument("--registry",type=Path,default=Path("data/nl2_hu_multiboard_status_current.json"))
    replay(cli.parse_args())
