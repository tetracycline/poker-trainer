"""Authenticate new B698 workers and pin the already published B688 positive files."""
import argparse
import hashlib
import json
from pathlib import Path
from hu_b679_collect import api

RUN=45314875785
HEAD="0b380efff4d043e750bc5d5262566036d3634499"
WORKFLOW=".github/workflows/nl2-hu-b698-rank121-thigh.yml"
REPOSITORY_ID=1438346845
SOURCE_BLOBS={
    "tools/hu_b686_rank121.py": "80d01bbd2a2bee37724fd25f05f6d86df3dd53ca",
    "tools/hu_b686_rank121_routes.cjs": "61f1f2d90e0599dda765fc78a4aa5ab96801a7e2",
    ".github/workflows/nl2-hu-b686-rank121-checkcalls.yml": "8d5c9c9cf036dcabf752fc68607bffd3de16ac27",
    "tools/hu_b682_stage_prices.py": "7de31f3302c7656c3bf989f4ccc32ebcddd59e15",
    "tools/hu_sequential_cfr_reach.py": "f26df926c088e5b4117bb911956cbc5031e2458d",
    "tools/hu_b483_locked_medium.py": "018ac485d3fc115f125c777399d96ce38b0f5f04",
    "tools/hu_b470_rank73_new_rivers.py": "39336981ae910b385744a2b0aaea237397babb38",
    "tools/hu_checked_gto_boundary.py": "219f46b0a259fa3e71f1225046ab5b12c44c28c6",
    "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
    "tools/lines_pipeline/run10_common.py": "9422f8fdff8dfeca245bae48ded7fc38353332f0",
    "tools/hu_b536_sb_barrels.py": "35a120d45ed01523800cc89fbe5523ab30b9fb9e",
    "tools/hu_b467_river_source_gate.py": "57d9eac04b074eb58e54ede0de384682fad35062",
    "tools/hu_b698_rank121_thigh.py": "a14c056ad353c6e15e28ad1a7f259488699f3cb5",
    ".github/workflows/nl2-hu-b698-rank121-thigh.yml": "ea339294956ed2af49b40179d50ae842cd75ae93"
}
PREVIOUS_BLOBS={
    "NL2_B686_R121_TS8S6H.zip": "c2e665252c8b0b28e240d35872eeccee808f587a",
    "NL2_MULTIBOARD_B688_R121_TS8S6H.json.gz": "2d04d51bbeb7a4713e291ca821711806eb3dbfdd",
    "partial/rank121.json": "ecae1abde4a7a02be6c7ba42b3b557b1af32dd40",
    "partial/b688_rank121_locked_medium.json": "4d406376247d42986d82dc809ac3dd25056c8ed7",
    "partial/b688_auth_receipt.json": "838d0fb11d49ad21000928cc787d4c0a6ac909e8"
}
WORKERS=[
    {
        "id": 14884189340,
        "name": "B698-R121-Td8d4s",
        "flop": "Td8d4s",
        "run": 45314875785,
        "head": "0b380efff4d043e750bc5d5262566036d3634499",
        "sha256": "d9782c1b9eb81e033e120c8d8246bf01fa2761495f97c8360318af8b222d055f",
        "job": 138179186233
    },
    {
        "id": 14885022569,
        "name": "B698-R121-Th9h5c",
        "flop": "Th9h5c",
        "run": 45314875785,
        "head": "0b380efff4d043e750bc5d5262566036d3634499",
        "sha256": "ddf227f21664469ae2eef043fd56ec1b92f7d9f1619b0207fd1b0f41b612d67e",
        "job": 138179186521
    },
    {
        "id": 14884179324,
        "name": "B698-R121-Ts9s6h",
        "flop": "Ts9s6h",
        "run": 45314875785,
        "head": "0b380efff4d043e750bc5d5262566036d3634499",
        "sha256": "d736a36d2ce50bca7795efdb06cc9130096776574a6370a00fdadd610b7fd98c",
        "job": 138179186638
    }
]
STEPS={
    "Verify exact BB check-call prices and build the pinned engine",
    "Solve original roots and only reachable displayed turn decisions with actor locks",
    "Run actions/upload-artifact@v4",
}


def source_bytes():
    for path,expected in SOURCE_BLOBS.items():
        raw=Path(path).read_bytes()
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()==expected,path


def previous_bytes(directory):
    for name,expected in PREVIOUS_BLOBS.items():
        raw=(directory/name).read_bytes()
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()==expected,name


def authenticate(run,job,artifact,pin):
    assert pin in WORKERS
    assert (run["id"],run["head_sha"],run["status"],run["conclusion"],run["path"],
            run["repository"]["id"],run["head_repository"]["id"])==(
        RUN,HEAD,"completed","success",WORKFLOW,REPOSITORY_ID,REPOSITORY_ID)
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        pin["job"],RUN,HEAD,"solve ("+pin["flop"]+")","completed","success")
    assert STEPS<={s["name"] for s in job["steps"] if s["status"]=="completed" and s["conclusion"]=="success"}
    origin=artifact["workflow_run"]
    assert (artifact["id"],artifact["name"],artifact["digest"],artifact["expired"],origin["id"],
            origin["head_sha"],origin["repository_id"],origin["head_repository_id"])==(
        pin["id"],pin["name"],"sha256:"+pin["sha256"],False,RUN,HEAD,REPOSITORY_ID,REPOSITORY_ID)


def collect(args):
    source_bytes()
    previous_bytes(args.previous_evidence)
    args.output.mkdir(parents=True,exist_ok=True)
    tree=json.loads(api("git/trees/"+HEAD+"?recursive=1"))
    assert not tree.get("truncated")
    actual={r["path"]:r["sha"] for r in tree["tree"] if r["type"]=="blob"}
    assert all(actual.get(p)==s for p,s in SOURCE_BLOBS.items())
    assert all(actual.get("data/solver_evidence/"+p)==s for p,s in PREVIOUS_BLOBS.items())
    (args.output/"previous-blobs.json").write_text(json.dumps(dict(head=HEAD,blobs=PREVIOUS_BLOBS)))
    (args.output/"source-blobs.json").write_text(json.dumps(dict(head=HEAD,blobs=SOURCE_BLOBS)))
    raw=api("actions/runs/"+str(RUN));run=json.loads(raw)
    (args.output/"run.json").write_bytes(raw)
    jobs=json.loads(api("actions/runs/"+str(RUN)+"/jobs?per_page=100"))["jobs"]
    artifacts=json.loads(api("actions/runs/"+str(RUN)+"/artifacts?per_page=100"))["artifacts"]
    assert len(artifacts)==len({a["name"] for a in artifacts})==3
    for pin in WORKERS:
        job,=[j for j in jobs if j["id"]==pin["job"]]
        listed,=[a for a in artifacts if a["id"]==pin["id"]]
        authenticate(run,job,listed,pin)
        raw=api("actions/artifacts/"+str(pin["id"]));receipt=json.loads(raw)
        authenticate(run,job,receipt,pin)
        archive=api("actions/artifacts/"+str(pin["id"])+"/zip")
        assert hashlib.sha256(archive).hexdigest()==pin["sha256"]
        (args.output/(str(pin["id"])+".json")).write_bytes(raw)
        (args.output/(str(pin["id"])+".zip")).write_bytes(archive)
        (args.output/("job."+str(pin["job"])+".json")).write_text(json.dumps(job))
    print(json.dumps(dict(authenticated_workers=3,source_run=RUN,source_blobs=len(SOURCE_BLOBS))))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--previous-evidence",type=Path,default=Path("data/solver_evidence"))
    collect(cli.parse_args())


