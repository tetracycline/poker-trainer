"""Publish only the two authenticated half-pot turn-call price corrections.

The completed B696 price job is the immutable source. This step adds no
certification, node lock or native solve, and preserves all other model records.
"""
import argparse
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile

from hu_b679_collect import api
from hu_b704_publish_candidate import B696_CODE,B696_PARENT_CODE,B696_UI,B696_ATOMIC_DATA

RUN=45316213646
HEAD="8230583230176e9f43527f44c3beca3b2fd5bdb6"
JOB=138183580209
ARTIFACT=14885586314
ARCHIVE_SHA="f4cd71fdb70a576307eb89354618a2fbe1270e79304faaa4a13b7d165b994e5f"
WORKFLOW=".github/workflows/nl2-hu-b696-turn-call-rivers.yml"
SOURCE_BLOBS={
    WORKFLOW:"7e12a5cce35fca5ce7233bc3238f3c7cbf2850dc",
    "tools/hu_b696_stage_prices.py":"8b83104a968c501f8524201995ef126db4dc4af5",
    "tools/hu_b696_turn_call_routes.cjs":"c3e61df26eba23f6b15be5f5e9d181c1a4fa7e5b",
    "tools/staged/hu_b696_nl2_hu_model.js":B696_CODE["nl2_hu_model.js"],
    "tools/staged/hu_b696_trainer_route_contract.cjs":B696_CODE["tools/hu_trainer_route_contract.cjs"],
    "nl2.js":B696_UI,
}
TARGETS={
    "ln-opfr-r_model-1phsqr4":dict(rank=76,pot=12.,stack=94.,spr=7.833),
    "ln-ipfr-r_model-bqgbuq":dict(rank=89,pot=11.,stack=94.75,spr=8.614),
}
STATUS="data/nl2_hu_multiboard_status_current.json"
REFERENCES="data/nl2_hu_model_source_references.json"
CROSSWALK="data/nl2_hu_model_history_crosswalk.json"
EXTENSIONS="data/nl2_hu_verified_extensions.json"
QUEUE="data/nl2_hu_stage2_queue.json"


def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def blob(path):return subprocess.check_output(["git","hash-object",str(path)],text=True).strip()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")


def collect(folder):
    folder.mkdir(parents=True,exist_ok=True)
    endpoints={"run.json":"actions/runs/"+str(RUN),
        "job."+str(JOB)+".json":"actions/jobs/"+str(JOB),
        str(ARTIFACT)+".json":"actions/artifacts/"+str(ARTIFACT),
        str(ARTIFACT)+".zip":"actions/artifacts/"+str(ARTIFACT)+"/zip"}
    for name,endpoint in endpoints.items():(folder/name).write_bytes(api(endpoint))
    tree=json.loads(api("git/trees/"+HEAD+"?recursive=1"))
    assert not tree.get("truncated")
    actual={row["path"]:row["sha"] for row in tree["tree"] if row["type"]=="blob"}
    assert all(actual.get(path)==expected for path,expected in SOURCE_BLOBS.items())
    write(folder/"source-blobs.json",dict(head=HEAD,blobs=SOURCE_BLOBS))


def authenticate(folder):
    run=read(folder/"run.json");job=read(folder/("job."+str(JOB)+".json"))
    artifact=read(folder/(str(ARTIFACT)+".json"));source=read(folder/"source-blobs.json")
    assert (run["id"],run["head_sha"],run["path"],run["repository"]["id"],run["head_repository"]["id"])==(
        RUN,HEAD,WORKFLOW,1438346845,1438346845)
    # Later solver jobs failed their independent flop-order guard. The price
    # audit itself completed successfully and is checked by its exact job id.
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        JOB,RUN,HEAD,"prices-and-audit","completed","success")
    required={"Preserve all existing certificates and all390 other models while fixing two named prices",
        "Run actions/upload-artifact@v4"}
    assert required<={s["name"] for s in job["steps"] if s["status"]=="completed" and s["conclusion"]=="success"}
    origin=artifact["workflow_run"]
    assert (artifact["id"],artifact["name"],artifact["digest"],artifact["expired"],origin["id"],
        origin["head_sha"],origin["repository_id"],origin["head_repository_id"])==(
        ARTIFACT,"B696-verified-turn-call-prices","sha256:"+ARCHIVE_SHA,False,RUN,HEAD,1438346845,1438346845)
    assert source["head"]==HEAD and all(source["blobs"].get(path)==expected for path,expected in SOURCE_BLOBS.items())
    assert all(blob(path)==expected for path,expected in SOURCE_BLOBS.items())
    archive=(folder/(str(ARTIFACT)+".zip")).read_bytes();assert digest(archive)==ARCHIVE_SHA
    with ZipFile(io.BytesIO(archive)) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        price=read_bytes(z.read("price-gate.json"));routes=z.read("rendered-routes.json")
    assert (price["schema"],price["total"],price["other_models_unchanged"],price["labels_unchanged"])==(
        "NL2_B696_ISOLATED_TURN_PRICE_GATE_V1",392,390,True)
    assert price["certified_unchanged"]>=148
    assert price["corrected_prices"]=={mid:[value["pot"],value["stack"],value["spr"]] for mid,value in TARGETS.items()}
    return archive,routes,price


def read_bytes(raw):return json.loads(raw)


def integrate(args):
    if not args.existing_receipts:collect(args.receipts)
    archive,source_routes,source_price=authenticate(args.receipts)
    assert all(blob(path)==expected for path,expected in B696_PARENT_CODE.items())
    assert blob("nl2.js")==B696_UI
    before_raw=Path(STATUS).read_bytes();before=json.loads(before_raw)
    assert before["TOTAL"]==len(before["records"])==392
    protected={mid:value for mid,value in before["records"].items() if value["label"]=="CERT-MULTIBOARD"}
    assert len(protected)==before["CERT_MULTIBOARD"]>=150
    assert all((before["records"][mid]["label"],before["records"][mid]["frequency_rank"])==("APPROX",value["rank"])
        for mid,value in TARGETS.items())
    before_refs=read(REFERENCES);before_queue=read(QUEUE);before_extensions=read(EXTENSIONS)
    fixed_before={CROSSWALK:Path(CROSSWALK).read_bytes()}
    with tempfile.TemporaryDirectory(prefix="b704-price-") as temporary:
        snapshot=Path(temporary)/"before-render.json"
        subprocess.run(["node","tools/hu_b696_turn_call_routes.cjs","--snapshot",str(snapshot)],check=True)
        subprocess.run([sys.executable,"tools/hu_b696_stage_prices.py","--apply"],check=True)
        current_routes=subprocess.check_output(["node","tools/hu_b696_turn_call_routes.cjs","--compare",str(snapshot)])
    assert current_routes==source_routes,"Reviewed current routes must reproduce the completed source price audit"
    assert all(blob(path)==expected for path,expected in B696_CODE.items()) and blob("nl2.js")==B696_UI
    subprocess.run([sys.executable,"tools/hu_apply_cert_extensions.py","--out",STATUS],check=True)
    subprocess.run(["node","tools/hu_cert_inventory.js",QUEUE],check=True)
    after=read(STATUS);expected=deepcopy(before)
    for mid,value in TARGETS.items():expected["records"][mid]["assumed_model_node_spr"]=value["spr"]
    assert after==expected,"Price-only publication must preserve every other registry field and all labels"
    for mid,value in protected.items():assert after["records"][mid]==value,mid
    expected_refs=deepcopy(before_refs)
    for mid,value in TARGETS.items():expected_refs["items"][mid]["model_node_spr"]=value["spr"]
    assert read(REFERENCES)==expected_refs
    expected_extensions=deepcopy(before_extensions)
    for mid,value in TARGETS.items():
        route=expected_extensions["trainer_route_contract"]["routes"][mid]
        route["streets"][1]="x b50 c" if value["rank"]==76 else "b50 c"
        route["priced_model_spr"]=value["spr"]
    assert read(EXTENSIONS)==expected_extensions,"Only the same two exact turn-call route contracts may change"
    assert all(Path(path).read_bytes()==raw for path,raw in fixed_before.items())
    expected_queue=deepcopy(before_queue)
    expected_queue["source_sha256"]["nl2_hu_model.js"]=digest(Path("nl2_hu_model.js").read_bytes())
    for row in expected_queue["records"]:
        if row["model_id"] in TARGETS:
            value=TARGETS[row["model_id"]]
            row["approx_pot_bb"],row["approx_remaining_bb"],row["approx_spr"]=value["pot"],value["stack"],value["spr"]
    assert read(QUEUE)==expected_queue,"Queue changed outside the same two prices and exact model source SHA"
    for name,value in expected_queue["source_sha256"].items():assert digest(Path(name).read_bytes())==value,name
    receipt_root=Path("data/solver_evidence/partial/b704_price_receipts");receipt_root.mkdir(parents=True,exist_ok=True)
    receipt_paths=[]
    for name in ("run.json","job."+str(JOB)+".json",str(ARTIFACT)+".json","source-blobs.json"):
        target=receipt_root/name;target.write_bytes((args.receipts/name).read_bytes());receipt_paths.append(str(target))
    raw_path=Path("data/solver_evidence/partial/B704_PRICE_GATE.zip");raw_path.write_bytes(archive)
    report=dict(schema="NL2_HU_B704_ATOMIC_TURN_CALL_PRICE_ONLY_V1",source_run=RUN,source_head=HEAD,
        source_price_job=JOB,source_price_artifact=ARTIFACT,source_price_archive_sha256=ARCHIVE_SHA,
        original_price_gate=source_price,corrected_prices=TARGETS,
        previous_model_spr={mid:before["records"][mid]["assumed_model_node_spr"] for mid in TARGETS},
        unchanged_other_records=390,preserved_certified_records=len(protected),
        CERT_MULTIBOARD=after["CERT_MULTIBOARD"],APPROX=after["APPROX"],TOTAL=392,
        new_certifications=0,new_native_solves=0,new_node_locked_boards=0,new_medium_boards=0,
        code_blobs=B696_CODE,unchanged_ui_blob=B696_UI,legacy_queue_regenerated_atomically=True,
        before_registry_sha256=digest(before_raw),after_registry_sha256=digest(Path(STATUS).read_bytes()),
        protected_record_sha256={mid:digest(canonical(value)) for mid,value in protected.items()})
    report_path="data/nl2_hu_b704_price_fix.json";write(report_path,report)
    args.paths.write_text("\n".join(sorted(set(B696_CODE)|B696_ATOMIC_DATA|set(receipt_paths)|{str(raw_path),report_path}))+"\n")
    print(json.dumps(dict(CERT_MULTIBOARD=after["CERT_MULTIBOARD"],APPROX=after["APPROX"],
        unchanged_other_records=390,preserved_certified_records=len(protected),new_certifications=0)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--receipts",type=Path,required=True)
    cli.add_argument("--paths",type=Path,required=True)
    cli.add_argument("--existing-receipts",action="store_true")
    integrate(cli.parse_args())
