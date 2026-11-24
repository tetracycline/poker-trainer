"""Resume B696 after authenticating its completed original flop solve.

The only policy-gate repair accepts the native canonical order of the same
three flop cards. Original jobs, result bytes, prices, masks, UI and locks
remain pinned. An existing native result is always replayed without a driver.
"""
import argparse
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

import hu_b696_turn_call_rivers as native
import hu_b702_collect as collector
from hu_b467_river_source_gate import compact,json_bytes,sha

ORIGINAL_PARENT=native.parent_candidates
ORIGINAL_SOLVE=native.solve
ALGORITHM_BLOB="ca9d29bbe212262dd5f834714779a339e8204c3c"


def canonical_parent_candidates(root,turn,route):
    """Validate actual cards and prices before reusing every original reach gate."""
    first,=(n for n in root["nodes"] if (n["line"],n["player"])==("",0))
    response,=(n for n in root["nodes"] if (n["line"],n["player"])==("x",1))
    cards=native.public_cards(root["flop"])
    assert len(root["flop"])==6 and len(cards)==3
    for node in (first,response):
        assert len(node["board"])==6 and native.public_cards(node["board"])==cards
        assert (node["pot"],node["bets"])==(route["pot"],[0,0])
    # A temporary view makes the old order-sensitive assertion use native order.
    # Neither the root object nor its original raw bytes are rewritten.
    view=dict(root,flop=first["board"])
    return ORIGINAL_PARENT(view,turn,route)


def authenticate_inputs(args):
    collector.source_bytes()
    assert collector.SOURCE_BLOBS["tools/hu_b696_turn_call_rivers.py"]==ALGORITHM_BLOB
    receipts=args.receipts
    run=json.loads((receipts/"run.json").read_bytes())
    source=json.loads((receipts/"source-blobs.json").read_bytes())
    assert source==dict(head=collector.HEAD,blobs=collector.SOURCE_BLOBS)
    workers=json.loads((receipts/"workers.json").read_bytes())
    assert workers==collector.WORKERS and len(workers)==6
    pin,=(w for w in workers if (w["rank"],w["flop"])==(args.rank,args.flop))
    job=json.loads((receipts/("job."+str(pin["job"])+".json")).read_bytes())
    artifact=json.loads((receipts/(str(pin["id"])+".json")).read_bytes())
    collector.authenticate(run,job,artifact,pin)
    failure=collector.authenticate_failure_log((receipts/("job."+str(pin["job"])+".log")).read_bytes())
    outer=(receipts/(str(pin["id"])+".zip")).read_bytes()
    assert sha(outer)==pin["sha256"]
    with ZipFile(io.BytesIO(outer)) as archive:
        assert len(archive.namelist())==2 and set(archive.namelist())=={"flop/job.json","flop/result.json"}
        originals={name:archive.read("flop/"+name) for name in ("job.json","result.json")}
    root=json.loads(originals["result.json"])
    price=collector.PRICE
    collector.authenticate(run,json.loads((receipts/("job."+str(price["job"])+".json")).read_bytes()),
        json.loads((receipts/(str(price["id"])+".json")).read_bytes()),price)
    price_raw=(receipts/(str(price["id"])+".zip")).read_bytes()
    assert sha(price_raw)==price["sha256"]
    with ZipFile(io.BytesIO(price_raw)) as archive:
        price_gate=json.loads(archive.read("price-gate.json"))
        routes=archive.read("rendered-routes.json")
    assert (price_gate["schema"],price_gate["total"],price_gate["other_models_unchanged"],price_gate["labels_unchanged"])==(
        "NL2_B696_ISOLATED_TURN_PRICE_GATE_V1",392,390,True)
    assert price_gate["certified_unchanged"]>=148
    assert args.routes.read_bytes()==routes,"Current displayed routes differ from the completed source price audit"
    route=json.loads(routes)[str(args.rank)]
    assert root["flop"]==args.flop and (root["pot"],root["stack"])==(route["pot"],route["stack"])
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    gates={t:canonical_parent_candidates(root,t,route)[0] for t in native.CASES[args.rank][args.flop]}
    origin=dict(original_root_run=pin["run"],original_root_head=pin["head"],original_root_artifact=pin["id"],
        original_root_job_id=pin["job"],original_root_archive_sha256=sha(outer),
        original_root_job_sha256=sha(originals["job.json"]),original_root_result_sha256=sha(originals["result.json"]),
        original_root_canonical_sha256=sha(compact(root)),original_root_gto_gap_pct=root["info"]["gto_expl_pct"],
        original_algorithm_blob=ALGORITHM_BLOB,original_failure=failure,completed_price_audit=price,
        source_blobs=collector.SOURCE_BLOBS,canonical_card_order_parent_gates=gates,
        flop_native_solves_repeated=0,original_root_is_not_a_policy_negative=True)
    return pin,originals,origin


def run(args):
    assert args.resume_run>0 and re.fullmatch("[0-9a-f]{40}",args.resume_head)
    pin,originals,origin=authenticate_inputs(args)
    root_folder=(args.output/"flop").resolve()
    root_folder.mkdir(parents=True,exist_ok=True)
    for name,raw in originals.items():
        target=root_folder/name
        if target.exists():assert target.read_bytes()==raw,(name,"Original root bytes changed")
        else:target.write_bytes(raw)
    origin.update(resume_run=args.resume_run,resume_head=args.resume_head)
    (args.output/"resume-source.json").write_bytes(json_bytes(origin))
    calls=dict(root_replays=0,new_continuation_solves=0,cached_continuation_replays=0)

    def resume_solve(folder,job,driver):
        folder=folder.resolve()
        if folder==root_folder:
            assert all((folder/name).read_bytes()==raw for name,raw in originals.items())
            calls["root_replays"]+=1
            result=ORIGINAL_SOLVE(folder,job,None)
            assert all((folder/name).read_bytes()==raw for name,raw in originals.items())
            return result
        assert folder.parent==args.output.resolve(),"Unexpected native solve output folder"
        stored_job,stored_result=folder/"job.json",folder/"result.json"
        if stored_result.exists():
            assert stored_job.is_file(),"An existing result without its exact job cannot be replayed"
            before={p.name:sha(p.read_bytes()) for p in (stored_job,stored_result)}
            result=ORIGINAL_SOLVE(folder,job,None)
            assert before=={p.name:sha(p.read_bytes()) for p in (stored_job,stored_result)}
            calls["cached_continuation_replays"]+=1
            return result
        assert driver is not None,"A missing continuation result cannot be claimed by replay"
        if stored_job.exists():assert json.loads(stored_job.read_bytes())==json.loads(compact(job))
        calls["new_continuation_solves"]+=1
        return ORIGINAL_SOLVE(folder,job,driver)

    native.parent_candidates=canonical_parent_candidates
    native.solve=resume_solve
    try:native.run(args)
    finally:
        native.parent_candidates=ORIGINAL_PARENT
        native.solve=ORIGINAL_SOLVE
    assert calls["root_replays"]==1
    assert all((root_folder/name).read_bytes()==raw for name,raw in originals.items())
    proof_path=args.output/"proof.json"
    report=json.loads(proof_path.read_bytes())
    assert report["schema"]=="NL2_B696_TURN_CALL_ORIGINAL_WORKER_V1"
    assert report["root_sha256"]==origin["original_root_result_sha256"]
    assert report["root_job_sha256"]==origin["original_root_job_sha256"]
    report.update(schema="NL2_B705_RESUMED_TURN_CALL_ORIGINAL_WORKER_V1",original_algorithm_schema=report["schema"],
        root_origin=origin,flop_native_solves_repeated=0,
        resume_scope="ORIGINAL_COMPLETED_GTO_FLOP_WITH_NEW_TURN_RIVER_AND_ACTOR_LOCKS")
    proof_path.write_bytes(json_bytes(report))
    print(json.dumps(dict(rank=args.rank,flop=args.flop,positive=report["positive_distinct_flops"],**calls)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ("solver","receipts","routes","output"):cli.add_argument("--"+field,type=Path,required=True)
    cli.add_argument("--rank",type=int,choices=native.CASES,required=True)
    cli.add_argument("--flop",required=True)
    cli.add_argument("--driver",type=Path)
    cli.add_argument("--resume-run",type=int,required=True)
    cli.add_argument("--resume-head",required=True)
    run(cli.parse_args())
