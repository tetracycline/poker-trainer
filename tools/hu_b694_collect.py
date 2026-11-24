"""Authenticate only the three new B691 original workers and unchanged source gates."""
import argparse
import hashlib
import json
from pathlib import Path
from hu_b679_collect import api

RUN=45312594603
HEAD="e4a29f3b5ff31229b5648fa78d3bb08f5a312471"
WORKFLOW=".github/workflows/nl2-hu-b691-rank121-extra.yml"
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
    "tools/hu_b691_rank121_extra.py": "2fedb88cc604ae1821532508f22830c73cab18ee",
    ".github/workflows/nl2-hu-b691-rank121-extra.yml": "c7d2cbbd63d99bc6549075d5eeee16cdb30e9559"
}
WORKERS=[
    {
        "id": 14883074683,
        "name": "B691-R121-Jd9d6h",
        "flop": "Jd9d6h",
        "run": 45312594603,
        "head": "e4a29f3b5ff31229b5648fa78d3bb08f5a312471",
        "sha256": "677120d881016b749b8a1735ee090af45910f42ec45e95f9495d82f303d10622",
        "job": 138171725072
    },
    {
        "id": 14884000826,
        "name": "B691-R121-QhTh7s",
        "flop": "QhTh7s",
        "run": 45312594603,
        "head": "e4a29f3b5ff31229b5648fa78d3bb08f5a312471",
        "sha256": "f0305fb5ce480fa194ee1151c3d061fe77be7aa6d80d4dd72364ea26108c1e38",
        "job": 138171725481
    },
    {
        "id": 14883633849,
        "name": "B691-R121-Tc8c5d",
        "flop": "Tc8c5d",
        "run": 45312594603,
        "head": "e4a29f3b5ff31229b5648fa78d3bb08f5a312471",
        "sha256": "d674065aa0490acfea9cdd0a8df47280c17a34759738c600eedfc07d58b96cb2",
        "job": 138171726696
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
    args.output.mkdir(parents=True,exist_ok=True)
    tree=json.loads(api("git/trees/"+HEAD+"?recursive=1"))
    assert not tree.get("truncated")
    actual={r["path"]:r["sha"] for r in tree["tree"] if r["type"]=="blob"}
    assert all(actual.get(p)==s for p,s in SOURCE_BLOBS.items())
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
    collect(cli.parse_args())


