"""Preserve B691's genuine root negatives and GTO/NL2 displayed-policy disagreement.

The old B688 positive is a fixed source reference. This batch replays only new
workers and emits no certification group or global medium-report entries.
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

import hu_b691_rank121_extra as worker
from hu_b694_collect import HEAD, SOURCE_BLOBS, WORKERS, authenticate, source_bytes
from hu_b688_publish import sources, observe, POLICY_FIELDS
from hu_b467_river_source_gate import json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_board_reach_corrections import source_key
from hu_sequential_cfr_reach import cardkey

PREVIOUS={
    "verification_batch":688,
    "verification_tool_blob":"b9285bd88a44ca5638bd20716cf788678ba7c10d",
    "partial_path":"data/solver_evidence/partial/rank121.json",
    "archive_path":"data/solver_evidence/NL2_B686_R121_TS8S6H.zip",
    "source_run_id":45310712825,
    "source_head":"30c81f5d06a94610cdb2b9aa3100f4c495352c5f",
    "worker_artifact":14883755418,
    "archive_sha256":"b9f78b9777657d760ec75d2a64fbb41082fb850b6ebb90707202999a0f6c64a6",
    "flop":"Ts8s6h","turn":"2c","public_board":"6h8sTs2c",
    "original_GTO_SHA256":"c2fa42a75ea2bec943faa5975f0228c9723385e210b0bb8225b8ffa63d8c08c2",
    "actual_NL2_SHA256":"3361c46680c452eea03b60000ebc2bdcccee54d356f77ce26734e6cfb4bd9e3f",
}


def route_policies(source,row,route):
    game=source["subgame"];public=row["public_board"]
    node,=[n for n in game["nodes"] if (n["board"],n["line"],n["player"])==(public,worker.native.LINE,0)]
    masks=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    before=route["routes"].get(worker.native.tx(public[:6]),{}).get("parents",[])
    after=route["routes"].get(worker.native.tx(public),{}).get("decisions",{})
    found={}
    for i,(hole,bits) in enumerate(zip(game["hands"][0],masks,strict=True)):
        if not bits:continue
        fc,tc=worker.native.hcls(hole,public[:6]),worker.native.hcls(hole,public)
        if fc not in before or tc not in after:continue
        label=after[tc];action=worker.native.ACTIONS[label]
        weights=[max(0,node["strat"][a*len(masks)+i]) for a in range(len(node["acts"]))]
        total=sum(weights);assert total>0
        found["".join(cardkey(hole))]=dict(flop_class=fc,turn_class=tc,displayed_suggestion=label,
            displayed_action_accepted=action in node["acts"] and bool(bits&(1<<node["acts"].index(action))),
            action_order=node["acts"],accepted_mask=bits,
            accepted_actions=[a for k,a in enumerate(node["acts"]) if bits&(1<<k)],
            strategy={a:round(w/total,7) for a,w in zip(node["acts"],weights,strict=True)})
    return found


def replay(args):
    source_bytes()
    source_receipt=json.loads((args.receipts/"source-blobs.json").read_bytes())
    assert source_receipt==dict(head=HEAD,blobs=SOURCE_BLOBS)
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==worker.native.SOLVER
    py=solver/"postflop/py"
    assert sha((py/"pipeline.py").read_bytes())==PIPELINE and sha((py/"ranges.py").read_bytes())==RANGES
    sys.path.insert(0,str(py))
    import pipeline
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    routes_raw=args.routes.read_bytes();route=json.loads(routes_raw)
    old=Path(PREVIOUS["archive_path"])
    if old.exists():assert sha(old.read_bytes())==PREVIOUS["archive_sha256"]
    # A previous summary is never used to create a new certificate.
    old_group=Path(PREVIOUS["partial_path"])
    if old_group.exists():
        previous=json.loads(old_group.read_bytes())
        pin,=[p for p in previous["pins"] if p["public_board"]==PREVIOUS["public_board"]]
        for field in ("flop","turn","source_run_id","worker_artifact","archive_sha256","original_GTO_SHA256","actual_NL2_SHA256"):
            assert pin[field]==PREVIOUS[field]
    data=args.output/"data";evidence=data/"solver_evidence";partial=evidence/"partial"
    partial.mkdir(parents=True,exist_ok=True)
    medium=dict(schema="NL2_HU_B694_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    run=json.loads((args.receipts/"run.json").read_bytes())
    report=[];receipts=[];comparisons=[]
    for pin in WORKERS:
        artifact=json.loads((args.receipts/(str(pin["id"])+".json")).read_bytes())
        job=json.loads((args.receipts/("job."+str(pin["job"])+".json")).read_bytes())
        authenticate(run,job,artifact,pin)
        archive=(args.receipts/(str(pin["id"])+".zip")).read_bytes();assert sha(archive)==pin["sha256"]
        receipts.append(dict(artifact=artifact,job=job))
        with TemporaryDirectory(prefix="b694-new-source-") as td:
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
            assert (expected["schema"],expected["rank"],expected["flop"],expected["positive_distinct_flops"])==(
                "NL2_B691_R121_ORIGINAL_WORKER_V1",121,pin["flop"],0)
            assert expected["source_algorithm_batch"]==686 and expected["new_source_batch"]==691
            assert all(not t["shared_hands"] for t in expected["turns"])
            required={"flop/job.json","flop/result.json","proof.json","rendered-routes.json"}
            for turn in expected["turns"]:
                if turn["gto_solved"]:required|={turn["turn"]+"-gto/"+n for n in ("job.json","result.json")}
                if turn["paired"]:required|={turn["turn"]+"-exp_oop/"+n for n in ("job.json","result.json")}
            assert set(names)==required
            proof_name="b694_"+pin["flop"].upper()+"_proof.json"
            (partial/proof_name).write_bytes(raw_proof)
            record=dict(flop=pin["flop"],status="NO_COMMON_RENDERED_ACTION_HAND",source_run_id=pin["run"],
                worker_artifact=pin["id"],archive_sha256=pin["sha256"],
                proof_path="data/solver_evidence/partial/"+proof_name,proof_sha256=sha(raw_proof),
                gto_turns=sum(t["gto_solved"] for t in expected["turns"]),
                actor_locked_public_boards=sum(t["paired"] for t in expected["turns"]),
                half_pot_assessed_public_boards=sum(t["gto_solved"] for t in expected["turns"]),
                layer_diagnostics=expected["turns"])
            code="B691_R121_"+pin["flop"].upper()
            if record["actor_locked_public_boards"]:
                (evidence/("NL2_"+code+".zip")).write_bytes(archive)
            for turn in expected["turns"]:
                if not turn["paired"]:continue
                pair=sources(folder,pin,turn,pipeline,pool,code)
                observations=[observe(s,turn["turn"],route) for s in pair]
                rows,hands,diagnostics=zip(*observations,strict=True)
                assert not (hands[0].keys()&hands[1].keys())
                policies=[route_policies(s,row,route) for s,row in zip(pair,rows,strict=True)]
                shared=sorted(policies[0].keys()&policies[1].keys())
                assert shared and len(shared)==turn["gto_diagnostic"]["turn_ui_combos"]==turn["nl2_diagnostic"]["turn_ui_combos"]
                detail=[]
                for hand in shared:
                    g,e=policies[0][hand],policies[1][hand]
                    assert all(g[k]==e[k] for k in ("flop_class","turn_class","displayed_suggestion"))
                    assert not (g["displayed_action_accepted"] and e["displayed_action_accepted"])
                    detail.append(dict(hand=hand,flop_class=g["flop_class"],turn_class=g["turn_class"],
                        displayed_suggestion=g["displayed_suggestion"],gto_displayed_action_accepted=g["displayed_action_accepted"],
                        nl2_displayed_action_accepted=e["displayed_action_accepted"],
                        gto={k:g[k] for k in POLICY_FIELDS},nl2={k:e[k] for k in POLICY_FIELDS}))
                for prefix,key,row,diagnostic in zip(("gto","nl2"),("gto_references","references"),rows,diagnostics,strict=True):
                    assert row["source_sha256"]==turn[prefix+"_sha256"]
                    assert row["b50"]==turn[prefix+"_b50"] and diagnostic==turn[prefix+"_diagnostic"]
                    row.update(rendered_decision_hands=[],rendered_policy_disagreement_hands=detail,
                        no_common_rendered_action=True,not_a_certification=True)
                    medium[key][source_key(worker.native.MODEL,row)]=row
                comparisons.append(dict(flop=pin["flop"],public_board=turn["public_board"],
                    source_run_id=pin["run"],original_GTO_SHA256=rows[0]["source_sha256"],
                    actual_NL2_SHA256=rows[1]["source_sha256"],gto_rendered_hands=len(hands[0]),
                    nl2_rendered_hands=len(hands[1]),common_rendered_hands=0,
                    gto_half_pot=rows[0]["b50"],nl2_half_pot=rows[1]["b50"],policy_disagreements=detail,
                    not_a_certification=True))
            report.append(record)
    (partial/"b694_rank121_locked_medium.json").write_bytes(json_bytes(medium))
    (partial/"b694_policy_disagreements.json").write_bytes(json_bytes(comparisons))
    (partial/"b694_auth_receipt.json").write_bytes(json_bytes(dict(run=run,source=source_receipt,workers=receipts)))
    summary=dict(new_positive_flops=0,new_negative_flops=3,prior_positive_flops=1,total_positive_flops=1,
        certification_eligible=False,previous_source_replayed=False,
        new_gto_turns=sum(r["gto_turns"] for r in report),
        new_actor_locked_public_boards=sum(r["actor_locked_public_boards"] for r in report),
        new_half_pot_assessed_public_boards=sum(r["half_pot_assessed_public_boards"] for r in report),
        nonpolarized_candidates=sum(c["nl2_half_pot"]["candidate"] for c in comparisons))
    assert summary["new_gto_turns"]==summary["new_actor_locked_public_boards"]==summary["new_half_pot_assessed_public_boards"]==3
    assert summary["nonpolarized_candidates"]==0 and len(comparisons)==3
    result=dict(schema="NL2_HU_B694_NEW_RANK121_NEGATIVES_V1",rank=121,model_id=worker.native.MODEL,
        previously_verified_source=PREVIOUS,summary=summary,workers=WORKERS,records=report)
    (data/"nl2_hu_b694_rank121_negatives.json").write_bytes(json_bytes(result))
    print(json.dumps(summary))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output","routes"):cli.add_argument("--"+key,type=Path,required=True)
    replay(cli.parse_args())

