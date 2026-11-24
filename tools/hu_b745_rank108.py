"""Rebuild the rank 108 comparison from the original B739 and B744 native files."""
import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import hu_b739_rank108 as native
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b679_collect import api
from hu_b710_publish import unpack_original
from hu_b719_integrate import CENTRAL
from hu_b738_collect import run_receipt, job_receipt, artifact_receipt
from hu_board_reach_corrections import source_key, summarize
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible

SOURCE = {
    739: (45331727303, "b970b1d1f94b7a3e143c2d2f1220fcf69a85021f", "nl2-hu-b739-rank108-turns.yml",
          "tools/hu_b739_rank108.py", {"2c2d4h":138234269317, "3s3h2d":138234269259, "4s4h2d":138234268890}),
    744: (45332914536, "13682d9c3a7356cd24f43f9fb8615f86e59c52e0", "nl2-hu-b744-rank108-extra.yml",
          "tools/hu_b744_rank108_extra.py", {"3c3d4h":138238068860, "5c5d2h":138238069129}),
}
PINS = {
    "2c2d4h": (14892591803, "90a3b17cbcccc70f414f6207cf3f9dbde3721cdcf14c1beb093374067c3c0d7f"),
    "3s3h2d": (14892253160, "4127bea4146cbb05f4e65dfe574c4ac74d6a7e65a631d13a72384affab968aa5"),
    "4s4h2d": (14892408047, "70513e76d4e64bb067144ebbd07a6d39faa457cd97121bce705315c782e0b94a"),
    "3c3d4h": (14893515351, "00450998856bdeaf810956b36534f67f54a7b287404cd343b237812ee8f1bd8b"),
    "5c5d2h": (14893775140, "74f6ea1879959b3ec1a88fb195e3cc3bbd253e160896aed0d3d4d9941241defe"),
}
STEPS = ["Verify the exact BB lead, CO raise and two-seat reach on the original GTO roots",
         "Extract missing raise-call boundary weights, verify every old node and solve new priced turns",
         "Run actions/upload-artifact@v4"]
MODEL = native.MODEL
LINE = native.LINE + "/"


def read(path):
    return json.loads(path.read_bytes())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def receipt(raw, batch):
    rid, head, workflow, _, jobs = SOURCE[batch]
    run = run_receipt(raw["run"], rid, head, ".github/workflows/"+workflow)
    assert len(raw["jobs"]) == len(raw["artifacts"]) == len(jobs)
    out = dict(run=run, jobs=[], artifacts=[])
    for flop,jid in jobs.items():
        job, = (j for j in raw["jobs"] if j["id"]==jid)
        name = f"B{batch}-R108-{flop}"
        art, = (a for a in raw["artifacts"] if a["name"]==name)
        aid, digest = PINS[flop]
        out["jobs"].append(job_receipt(job,run,jid,f"solve ({flop})",STEPS))
        out["artifacts"].append(artifact_receipt(art,run,aid,name,digest))
    return out


def collect(directory):
    directory.mkdir(parents=True,exist_ok=True)
    rid,_,_,_,jobs=SOURCE[744]
    raw=dict(run=json.loads(api(f"actions/runs/{rid}")),
             jobs=[json.loads(api(f"actions/jobs/{jid}")) for jid in jobs.values()],
             artifacts=[json.loads(api("actions/artifacts/"+str(PINS[f][0]))) for f in jobs])
    save(directory/"receipt.json",receipt(raw,744))
    for f in jobs:
        aid,digest=PINS[f]
        raw=api(f"actions/artifacts/{aid}/zip")
        assert sha(raw)==digest
        (directory/f"{aid}.zip").write_bytes(raw)


def displayed(row, sub, route):
    node, = (n for n in sub["nodes"] if n["line"]==LINE and n["player"]==0)
    board = node["board"]
    mask = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
    out = {}
    hands = sub["hands"][0]
    for i,(h,bits) in enumerate(zip(hands,mask,strict=True)):
        flop_key,flop_class = native.hand_cell(h,board[:6])
        turn_key,turn_class = native.hand_cell(h,board)
        if flop_key not in route["flop"] or turn_key not in route["turn"]:
            continue
        label = route["turn"][turn_key]
        action = native.ACTIONS[label]
        if not bits & (1 << node["acts"].index(action)):
            continue
        strategy = [max(0,w) for w in node["strat"][i::len(hands)]]
        assert len(strategy)==len(node["acts"]) and sum(strategy)>0
        out["".join(native.cardkey(h))]=dict(flop_class=flop_class,turn_class=turn_class,displayed_suggestion=label,
            policy=dict(action_order=node["acts"],accepted_mask=bits,accepted_actions=[a for j,a in enumerate(node["acts"]) if bits&(1<<j)],
                        strategy={a:round(w/sum(strategy),7) for a,w in zip(node["acts"],strategy,strict=True)}))
    return out


def make_board(root, folder, report, turn, batch, archive_code, digest, model, route, contract, pool, pipeline, group, medium):
    flop=report["flop"]
    game_root_sha=sha(compact(root))
    public=turn["gto"]["reach"]["public_board"]
    t=turn["turn"]
    rid,head,_,_,jobs=SOURCE[batch]
    source_job=read(folder/t/"gto/job.json")
    m=dict(spot="LMP_CO_BB",pot_family="LMP",locks=[])
    original=dict(source=dict(root=root,manifest=m,version="gto"),job=source_job)
    lock_job,rules=native.prepare_job(original,"exp_oop",pool,pipeline)
    lock_job["out"]="result.json"
    assert lock_job==read(folder/t/"exp_oop/job.json")
    sources=[]; evidence=[]; policies=[]
    for version,key,source_hash in (("gto","gto","source_gto_sha256"),("exp_oop","nl2","source_nl2_sha256")):
        data=(folder/t/version/"result.json").read_bytes()
        assert sha(data)==turn[source_hash]
        sub=json.loads(data)
        sub.update(line0=native.LINE,turn=t,rivers=[])
        manifest=dict(m)
        s=dict(root=root,subgame=sub,version=version,run=rid,manifest=manifest,root_sha256=game_root_sha,
               source_sha256=sha(data),archive_sha256=digest,archive_code=archive_code)
        if version=="exp_oop":
            manifest.update(locks=rules,gto_parent_source_run_id=rid,gto_parent_source_sha256=game_root_sha)
            application=native.audit_patterns(sub,lock_job,manifest,pool,0)
            assert application==turn["measured_lock"]
            s.update(verified_gto_parent=dict(run=rid,sha256=game_root_sha),measured_lock_application=application,
                     applied_rust_rates=sub["info"]["lock_stats"])
        row=audit_decision(s,public,LINE,0,game_root_sha)
        assert row and {k:row[k] for k in turn[key]["reach"]}==turn[key]["reach"]
        assert row["compatible_hole_card_pairs"]>=row["strict_legal_combos"]>0 and row["b50"] is not None
        summarize(row)
        policy=displayed(row,sub,route)
        assert sorted(policy)==turn[key]["displayed_hands"]
        sources.append(s);evidence.append(row);policies.append(policy)
    shared=sorted(policies[0].keys()&policies[1].keys())
    assert shared and shared==turn["shared_displayed_hands"]
    witnesses=[]
    for h in shared:
        g,e=(p[h] for p in policies)
        assert all(g[k]==e[k] for k in ("flop_class","turn_class","displayed_suggestion"))
        witnesses.append(dict(hand=h,flop_class=g["flop_class"],turn_class=g["turn_class"],
                              displayed_suggestion=g["displayed_suggestion"],gto=g["policy"],nl2=e["policy"]))
    board,pin=pairs.emit_board(model,*sources,public,LINE,texture(flop),viewer_code="B745_R108_"+flop.upper())
    assert board and compatible(contract,board)
    assert (board["actual_pot_bb"],board["actual_effective_stack_bb"],board["actual_spr"],board["acting_seat"])==(10,95.25,9.525,0)
    assert pin["pool_observed_marginal_lock_nodes"]>0
    board.update(source_run_role="ORIGINAL_GTO_ROOT_EXTENDED_WITH_NEW_RAISE_CALL_BOUNDARY",origin_solve_run_id=rid,
                 original_flop_source_sha256=report["original"]["original_root_sha256"],old_root_nodes_verified=report["old_nodes_reproduced"])
    board["nl2_locked_variants"][0].update(source_run_role=board["source_run_role"],origin_solve_run_id=rid,pool_sha256=native.POOL,
        measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",applied_street_rates=rates(sources[1]),
        gto_parent_source_run_id=rid,gto_parent_source_sha256=game_root_sha,viewer_archive_code=pin["viewer_archive_code"],viewer_sha256=pin["viewer_sha256"])
    pin.update(worker_head=head,worker_artifact=PINS[flop][0],original_job_id=jobs[flop],rendered_decision_hands=witnesses,
               original_flop_source_sha256=report["original"]["original_root_sha256"])
    for key,row in zip(("gto_references","references"),evidence,strict=True):
        row["rendered_decision_hands"]=witnesses; medium[key][source_key(MODEL,row)]=row
    group["boards"].append(board);group["pins"].append(pin)


def publish(args):
    assert sys.version_info[:2]==(3,11)
    stage=args.stage.resolve();dest=Path("data").resolve()
    assert not stage.exists() and not stage.is_relative_to(dest)
    ev=stage/"solver_evidence";ev.mkdir(parents=True);pairs.EVIDENCE=ev
    root_path=Path(CENTRAL[0]);before=read(root_path);model=before["records"][MODEL]
    assert (model["frequency_rank"],model["label"],model["assumed_model_node_spr"])==(108,"APPROX",9.525)
    contract=read(dest/"nl2_hu_verified_extensions.json")["trainer_route_contract"]["routes"][MODEL]
    assert (contract["seat"],contract["streets"],contract["priced_model_spr"])==(0,["b50 r c",""],9.525)
    solver=args.solver.resolve();sys.path.insert(0,str(solver/"postflop/py"));import pipeline
    pool=json.loads((solver/"inputs/pool_stats.json").read_bytes())["NL2"]
    current=json.loads(subprocess.check_output(["node","tools/hu_b739_rank108_routes.cjs"]))
    medium=dict(schema="NL2_HU_B745_ORIGINAL_LOCKED_MEDIUM_V1",gto_references={},references={})
    group=dict(rank=108,model_id=MODEL,boards=[],pins=[]);rows=[]
    for batch in (739,744):
        if batch==739:
            auth=receipt(read(dest/"nl2_hu_b742_source_receipts.json"),batch)
        else:
            auth=receipt(read(args.receipts/"receipt.json"),batch)
            save(stage/"nl2_hu_b745_source_receipts.json",auth)
        for flop in SOURCE[batch][4]:
            aid,digest=PINS[flop];code=f"B{batch}_R108_{flop.upper()}"
            path=(dest/"solver_evidence"/f"NL2_{code}.zip") if batch==739 else args.receipts/f"{aid}.zip"
            raw=path.read_bytes()
            assert sha(raw)==digest
            if batch==744:(ev/("NL2_"+code+".zip")).write_bytes(raw)
            with TemporaryDirectory(prefix="r108-") as td:
                folder=Path(td)/"archive";unpack_original(raw,folder)
                old=(folder/"proof.json").read_bytes();report=json.loads(old)
                sr=read(folder/"routes.json");assert dict(sr,registry_spr=9.525)==current
                subprocess.run([sys.executable,SOURCE[batch][3],"--flop",flop,"--solver",solver,"--routes",folder/"routes.json","--output",folder],check=True)
                assert (folder/"proof.json").read_bytes()==old
                root=read(folder/"boundary/result.json")
                success=[t for t in report["turns"] if t.get("shared_displayed_hands")]
                assert bool(success)==bool(report["positive_distinct_flops"])
                if success: make_board(root,folder,report,success[0],batch,code,digest,model,sr,contract,pool,pipeline,group,medium)
                rows.append(dict(batch=batch,flop=flop,selected=success[0]["gto"]["reach"]["public_board"] if success else None,
                                 proof_sha256=sha(old),**{k:report[k] for k in ("native_locked_public_boards","joint_halfpot_assessed","nonpolarized_candidates")}))
    old_summary=read(dest/"solver_evidence/partial/b742_rank108.json")
    baseline={row["flop"]:row for row in old_summary["workers"]}
    assert set(baseline)==set(SOURCE[739][4])
    for row in rows:
        if row["batch"]==739:
            old=baseline[row["flop"]]
            assert row["proof_sha256"]==old["proof_sha256"]
            chosen=next((x["public_board"] for x in old["turns"] if x["shared_displayed_hands"]),None)
            assert row["selected"]==chosen
    assert {row["flop"] for row in rows if row["batch"]==739 and row["selected"]}=={"3s3h2d","4s4h2d"}
    count=len(group["boards"])
    assert count==len({suit_isomorphism_class(b["flop"]) for b in group["boards"]}) and count==3
    assert len(group["pins"])==len(medium["references"])==len(medium["gto_references"])==count
    assert {b["flop"]:b["turn"] for b in group["boards"]}=={"3s3h2d":"7c","4s4h2d":"7c","5c5d2h":"6d"}
    save(ev/"reverified/rank108.json",group)
    save(stage/"nl2_hu_b745_locked_medium.json",medium)
    save(stage/"nl2_hu_b745_summary.json",dict(rank=108,workers=rows,positive_distinct_flops=count,source_runs=[SOURCE[i][0] for i in (739,744)]))
    paths=[]
    for source in sorted(p for p in stage.rglob("*") if p.is_file()):
        rel=source.relative_to(stage);target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.exists() or target.read_bytes()==source.read_bytes()
        target.write_bytes(source.read_bytes());paths.append("data/"+str(rel))
    subprocess.run([sys.executable,"tools/hu_apply_cert_extensions.py","--out",CENTRAL[0]],check=True)
    after=read(root_path)
    assert all(after["records"][k]==v for k,v in before["records"].items() if k!=MODEL)
    assert set(after["records"])==set(before["records"]) and len(after["records"])==392
    assert after["records"][MODEL]["label"]=="CERT-MULTIBOARD" and after["records"][MODEL]["proven_exact_board_count"]==count
    assert (after["CERT_MULTIBOARD"],after["APPROX"],after["TOTAL"])==(before["CERT_MULTIBOARD"]+1,before["APPROX"]-1,392)
    args.paths.write_text("\n".join(sorted(set(CENTRAL)|set(paths)))+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect",action="store_true")
    for field in ("solver","stage","receipts","paths"):
        parser.add_argument("--"+field,type=Path,required=True)
    args=parser.parse_args()
    if args.collect:collect(args.receipts)
    publish(args)
