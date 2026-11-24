"""Authenticate B705 continuations and preserve their exact B696 root receipts."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import hu_b702_collect as original
from hu_b679_collect import api

RUN=45320372683
HEAD="610d867a828115e80285e5aebe49fc0059c788c3"
WORKFLOW=".github/workflows/nl2-hu-b705-resume-turn-call-rivers.yml"
SOURCE_BLOBS={
    ".github/workflows/nl2-hu-b696-turn-call-rivers.yml": "7e12a5cce35fca5ce7233bc3238f3c7cbf2850dc",
    "tools/hu_b696_stage_prices.py": "8b83104a968c501f8524201995ef126db4dc4af5",
    "tools/hu_b696_turn_call_routes.cjs": "c3e61df26eba23f6b15be5f5e9d181c1a4fa7e5b",
    "tools/hu_b696_turn_call_rivers.py": "ca9d29bbe212262dd5f834714779a339e8204c3c",
    "tools/staged/hu_b696_nl2_hu_model.js": "b4a308a0f65b707f43f41f0b354cec87c08d5af6",
    "tools/staged/hu_b696_trainer_route_contract.cjs": "3b10524228c357552bb3f1eac88e17f9b2459b32",
    "nl2.js": "15aee97e53a156fe073c96a120638a8a3679958f",
    "tools/hu_b463_rank45_gate.py": "3f2fb4378667b9bb8397f7929e1469e86dd3c77b",
    "tools/hu_b467_river_source_gate.py": "57d9eac04b074eb58e54ede0de384682fad35062",
    "tools/hu_b470_rank73_new_rivers.py": "39336981ae910b385744a2b0aaea237397babb38",
    "tools/hu_b483_locked_medium.py": "018ac485d3fc115f125c777399d96ce38b0f5f04",
    "tools/hu_b568_caller_rivers.py": "e69bda7fe46c3dd18a48dee1bb97f965ab2813f7",
    "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
    "tools/hu_checked_gto_boundary.py": "219f46b0a259fa3e71f1225046ab5b12c44c28c6",
    "tools/hu_sequential_cfr_reach.py": "f26df926c088e5b4117bb911956cbc5031e2458d",
    "tools/hu_b702_collect.py": "e6037de9d285166b919608d773edbee2a316a965",
    "tools/hu_b705_resume_turn_call.py": "65da6780b509e42873a6fce2aaeda37f3dcba4dc",
    ".github/workflows/nl2-hu-b705-resume-turn-call-rivers.yml": "b10d343d75e375eded804c98e087c30c505879e4"
}
ROOTS={
    "id": 14886609148,
    "name": "B705-authenticated-B696-roots",
    "sha256": "4d193ea16e2887363fae9989b2a5459b9bef5480079d17f3dcb7f6a0c2f0fd36",
    "run": 45320372683,
    "head": "610d867a828115e80285e5aebe49fc0059c788c3",
    "job": 138197190428,
    "job_id": 138197190428
}
# Fixed completed original workers only; collection requires all six final pins.
WORKERS=[
    {
        "id": 14887247264,
        "name": "B705-R76-7h5d2c",
        "rank": 76,
        "flop": "7h5d2c",
        "sha256": "aa0df731ad3f1c02f5f6c5e040625dcdabb35395842a1b15ca0bcb02609b8347",
        "run": 45320372683,
        "head": "610d867a828115e80285e5aebe49fc0059c788c3",
        "job": 138197524351,
        "job_id": 138197524351,
        "original_root_artifact": 14886921030,
        "original_root_archive_sha256": "aeecd5d4e335000c3d5ac139e3699e3b59a108753ae835f7719e7f80db327cd1"
    },
    {
        "id": 14887396304,
        "name": "B705-R76-8c6h3d",
        "rank": 76,
        "flop": "8c6h3d",
        "sha256": "4b2ef1bdbbcce854c7537e668fcd9e9fc8daa7bed7641876c9da14a765fa430d",
        "run": 45320372683,
        "head": "610d867a828115e80285e5aebe49fc0059c788c3",
        "job": 138197524312,
        "job_id": 138197524312,
        "original_root_artifact": 14886835938,
        "original_root_archive_sha256": "081856dbd7627416deef4ca1a87b228528401f871f3203ece5dac98a1c7da05f"
    },
    {
        "id": 14888170203,
        "name": "B705-R76-9d6d4c",
        "rank": 76,
        "flop": "9d6d4c",
        "sha256": "74dbd57130ba0fd4ee0cbd188d5ef4b6e8351e429020fb3ca539de43e6dc0185",
        "run": 45320372683,
        "head": "610d867a828115e80285e5aebe49fc0059c788c3",
        "job": 138197524368,
        "job_id": 138197524368,
        "original_root_artifact": 14886285658,
        "original_root_archive_sha256": "28a067d240b6a6ec44931dd44a09850f759295366972e3738deedbb7317b14de"
    },
    {
        "id": 14886929899,
        "name": "B705-R89-Jc6d2s",
        "rank": 89,
        "flop": "Jc6d2s",
        "sha256": "3dd4257e7d3767eb6a4735d6a5a9ff1d4d314f080d5f57841f25dd895ee3e7b1",
        "run": 45320372683,
        "head": "610d867a828115e80285e5aebe49fc0059c788c3",
        "job": 138197524403,
        "job_id": 138197524403,
        "original_root_artifact": 14885617897,
        "original_root_archive_sha256": "922ac17df4c0a7dea45166b684ca16cc807d7ac71c6f45bfae0aef82655b32cf"
    },
    {
        "id": 14888100188,
        "name": "B705-R89-Kd8c4h",
        "rank": 89,
        "flop": "Kd8c4h",
        "sha256": "ef0ee388bc8663b45f7d0f8d06f90260e967ef6d3e69d4ccb96660fb32cee052",
        "run": 45320372683,
        "head": "610d867a828115e80285e5aebe49fc0059c788c3",
        "job": 138197524416,
        "job_id": 138197524416,
        "original_root_artifact": 14885399571,
        "original_root_archive_sha256": "c77a19fc950b03145f4222ca37e9b4f2cb850df0e7b7910d0b691bd284cbd1ba"
    },
    {
        "id": 14886954846,
        "name": "B705-R89-Qs7h3d",
        "rank": 89,
        "flop": "Qs7h3d",
        "sha256": "852d07b176da3f191521489ef1381eae4f84c25260f9fffbcbb5f3949195006d",
        "run": 45320372683,
        "head": "610d867a828115e80285e5aebe49fc0059c788c3",
        "job": 138197524394,
        "job_id": 138197524394,
        "original_root_artifact": 14886385932,
        "original_root_archive_sha256": "52518eb9023c364493eb202f854afddc2f7706bfa669e7a07467535e8c52a668"
    }
]
STEPS={
    "collect":"Authenticate the completed original roots and reuse the successful price audit",
    "resume":"Replay the original root and solve only missing turn, river and actor-lock results",
}


def source_bytes():
    for path,expected in SOURCE_BLOBS.items():
        raw=Path(path).read_bytes()
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()==expected,path


def authenticate(run,job,artifact,pin):
    assert pin in WORKERS or pin==ROOTS
    assert (run["id"],run["head_sha"],run["path"],run["repository"]["id"],run["head_repository"]["id"])==(
        RUN,HEAD,WORKFLOW,original.REPOSITORY_ID,original.REPOSITORY_ID)
    assert run["status"] in ("in_progress","completed") and run["conclusion"] in (None,"success","failure")
    name="collect" if pin==ROOTS else "resume ("+str(pin["rank"])+", "+pin["flop"]+")"
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        pin["job"],RUN,HEAD,name,"completed","success")
    step=STEPS["collect" if pin==ROOTS else "resume"]
    assert {step,"Run actions/upload-artifact@v4"}<={s["name"] for s in job["steps"]
        if s["status"]=="completed" and s["conclusion"]=="success"}
    origin=artifact["workflow_run"]
    assert (artifact["id"],artifact["name"],artifact["digest"],artifact["expired"],origin["id"],
        origin["head_sha"],origin["repository_id"],origin["head_repository_id"])==(
        pin["id"],pin["name"],"sha256:"+pin["sha256"],False,RUN,HEAD,original.REPOSITORY_ID,original.REPOSITORY_ID)
    assert pin["job"]==pin["job_id"]
    if pin!=ROOTS:
        prior,=[p for p in original.WORKERS if (p["rank"],p["flop"])==(pin["rank"],pin["flop"])]
        assert (pin["original_root_artifact"],pin["original_root_archive_sha256"])==(prior["id"],prior["sha256"])


def unpack_roots(raw,folder):
    assert hashlib.sha256(raw).hexdigest()==ROOTS["sha256"]
    required={"run.json","source-blobs.json","workers.json","roots.json","current-rendered-routes.json"}
    price=original.PRICE
    required|={str(price["id"])+".json",str(price["id"])+".zip","job."+str(price["job"])+".json"}
    for pin in original.WORKERS:
        required|={str(pin["id"])+".json",str(pin["id"])+".zip","job."+str(pin["job"])+".json",
            "job."+str(pin["job"])+".log","failure."+str(pin["job"])+".json"}
    with ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        assert len(names)==len(set(names)) and set(names)==required
        for name in names:
            p=PurePosixPath(name);assert not p.is_absolute() and ".." not in p.parts
            target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    source=json.loads((folder/"source-blobs.json").read_bytes())
    assert source==dict(head=original.HEAD,blobs=original.SOURCE_BLOBS)
    assert json.loads((folder/"workers.json").read_bytes())==original.WORKERS
    run=json.loads((folder/"run.json").read_bytes());replayed=[]
    for pin in [price,*original.WORKERS]:
        job=json.loads((folder/("job."+str(pin["job"])+".json")).read_bytes())
        artifact=json.loads((folder/(str(pin["id"])+".json")).read_bytes())
        original.authenticate(run,job,artifact,pin)
        archive=(folder/(str(pin["id"])+".zip")).read_bytes()
        assert hashlib.sha256(archive).hexdigest()==pin["sha256"]
        if pin!=price:
            failure=original.authenticate_failure_log((folder/("job."+str(pin["job"])+".log")).read_bytes())
            assert json.loads((folder/("failure."+str(pin["job"])+".json")).read_bytes())==failure
            replayed.append(dict(original.authenticate_root_archive(pin,archive),failure=failure))
    assert json.loads((folder/"roots.json").read_bytes())==replayed
    with ZipFile(folder/(str(price["id"])+".zip")) as z:
        assert z.read("rendered-routes.json")==(folder/"current-rendered-routes.json").read_bytes()
    return replayed


def collect(args):
    assert len(WORKERS)==6,"Incomplete source workers cannot be published"
    source_bytes();args.output.mkdir(parents=True,exist_ok=True)
    tree=json.loads(api("git/trees/"+HEAD+"?recursive=1"));assert not tree.get("truncated")
    actual={r["path"]:r["sha"] for r in tree["tree"] if r["type"]=="blob"}
    assert all(actual.get(p)==s for p,s in SOURCE_BLOBS.items())
    (args.output/"source-blobs.json").write_text(json.dumps(dict(head=HEAD,blobs=SOURCE_BLOBS)))
    raw=api("actions/runs/"+str(RUN));run=json.loads(raw)
    assert run["status"]=="completed"
    (args.output/"run.json").write_bytes(raw)
    jobs=json.loads(api("actions/runs/"+str(RUN)+"/jobs?per_page=100"))["jobs"]
    artifacts=json.loads(api("actions/runs/"+str(RUN)+"/artifacts?per_page=100"))["artifacts"]
    assert len(artifacts)==len({a["name"] for a in artifacts})==7
    for pin in [ROOTS,*WORKERS]:
        job,=[j for j in jobs if j["id"]==pin["job"]]
        listed,=[a for a in artifacts if a["id"]==pin["id"]]
        authenticate(run,job,listed,pin)
        raw=api("actions/artifacts/"+str(pin["id"]));artifact=json.loads(raw)
        authenticate(run,job,artifact,pin)
        archive=api("actions/artifacts/"+str(pin["id"])+"/zip")
        assert hashlib.sha256(archive).hexdigest()==pin["sha256"]
        (args.output/(str(pin["id"])+".json")).write_bytes(raw)
        (args.output/(str(pin["id"])+".zip")).write_bytes(archive)
        (args.output/("job."+str(pin["job"])+".json")).write_text(json.dumps(job))
        if pin==ROOTS:unpack_roots(archive,args.output/"original-roots")
    (args.output/"workers.json").write_text(json.dumps(WORKERS))
    print(json.dumps(dict(authenticated_resumed_workers=6,authenticated_original_roots=6,
        source_run=RUN,source_blobs=len(SOURCE_BLOBS),repeated_native_flops=0)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    collect(cli.parse_args())

