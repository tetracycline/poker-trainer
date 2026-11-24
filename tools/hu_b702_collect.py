"""Collect authenticated B696 original roots, including completed guard failures.

The source jobs finished real native flop CFR before a board-order assertion
blocked every turn. These are incomplete workers, never strategy negatives.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile
from hu_b679_collect import api

RUN=45316213646
HEAD="8230583230176e9f43527f44c3beca3b2fd5bdb6"
WORKFLOW=".github/workflows/nl2-hu-b696-turn-call-rivers.yml"
REPOSITORY_ID=1438346845
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
    "tools/hu_sequential_cfr_reach.py": "f26df926c088e5b4117bb911956cbc5031e2458d"
}
PRICE={
    "id": 14885586314,
    "name": "B696-verified-turn-call-prices",
    "job": 138183580209,
    "job_id": 138183580209,
    "run": 45316213646,
    "head": "8230583230176e9f43527f44c3beca3b2fd5bdb6",
    "sha256": "f4cd71fdb70a576307eb89354618a2fbe1270e79304faaa4a13b7d165b994e5f",
    "conclusion": "success"
}
# Filled only after original jobs and their GitHub artifacts have completed.
WORKERS=[
    {
        "id": 14886921030,
        "name": "B696-R76-7h5d2c",
        "rank": 76,
        "flop": "7h5d2c",
        "run": 45316213646,
        "head": "8230583230176e9f43527f44c3beca3b2fd5bdb6",
        "sha256": "aeecd5d4e335000c3d5ac139e3699e3b59a108753ae835f7719e7f80db327cd1",
        "job": 138184250414,
        "job_id": 138184250414,
        "conclusion": "failure"
    },
    {
        "id": 14886835938,
        "name": "B696-R76-8c6h3d",
        "rank": 76,
        "flop": "8c6h3d",
        "run": 45316213646,
        "head": "8230583230176e9f43527f44c3beca3b2fd5bdb6",
        "sha256": "081856dbd7627416deef4ca1a87b228528401f871f3203ece5dac98a1c7da05f",
        "job": 138184250310,
        "job_id": 138184250310,
        "conclusion": "failure"
    },
    {
        "id": 14886285658,
        "name": "B696-R76-9d6d4c",
        "rank": 76,
        "flop": "9d6d4c",
        "run": 45316213646,
        "head": "8230583230176e9f43527f44c3beca3b2fd5bdb6",
        "sha256": "28a067d240b6a6ec44931dd44a09850f759295366972e3738deedbb7317b14de",
        "job": 138184250324,
        "job_id": 138184250324,
        "conclusion": "failure"
    },
    {
        "id": 14885617897,
        "name": "B696-R89-Jc6d2s",
        "rank": 89,
        "flop": "Jc6d2s",
        "run": 45316213646,
        "head": "8230583230176e9f43527f44c3beca3b2fd5bdb6",
        "sha256": "922ac17df4c0a7dea45166b684ca16cc807d7ac71c6f45bfae0aef82655b32cf",
        "job": 138184250364,
        "job_id": 138184250364,
        "conclusion": "failure"
    },
    {
        "id": 14885399571,
        "name": "B696-R89-Kd8c4h",
        "rank": 89,
        "flop": "Kd8c4h",
        "run": 45316213646,
        "head": "8230583230176e9f43527f44c3beca3b2fd5bdb6",
        "sha256": "c77a19fc950b03145f4222ca37e9b4f2cb850df0e7b7910d0b691bd284cbd1ba",
        "job": 138184250240,
        "job_id": 138184250240,
        "conclusion": "failure"
    },
    {
        "id": 14886385932,
        "name": "B696-R89-Qs7h3d",
        "rank": 89,
        "flop": "Qs7h3d",
        "run": 45316213646,
        "head": "8230583230176e9f43527f44c3beca3b2fd5bdb6",
        "sha256": "52518eb9023c364493eb202f854afddc2f7706bfa669e7a07467535e8c52a668",
        "job": 138184250371,
        "job_id": 138184250371,
        "conclusion": "failure"
    }
]
SOLVE_STEP="Solve original native roots and reachable exact-priced GTO and measured NL2 river pairs"
PRICE_STEP="Preserve all existing certificates and all390 other models while fixing two named prices"


def source_bytes():
    for path,expected in SOURCE_BLOBS.items():
        raw=Path(path).read_bytes()
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()==expected,path


def authenticate(run,job,artifact,pin):
    assert pin in WORKERS or pin==PRICE
    assert (run["id"],run["head_sha"],run["path"],run["repository"]["id"],run["head_repository"]["id"])==(
        RUN,HEAD,WORKFLOW,REPOSITORY_ID,REPOSITORY_ID)
    assert run["status"] in ("in_progress","completed") and run["conclusion"] in (None,"success","failure")
    expected_name="prices-and-audit" if pin==PRICE else "solve ("+str(pin["rank"])+", "+pin["flop"]+")"
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        pin["job"],RUN,HEAD,expected_name,"completed",pin["conclusion"])
    step=PRICE_STEP if pin==PRICE else SOLVE_STEP
    assert any(s["name"]==step and s["status"]=="completed" and s["conclusion"]==pin["conclusion"] for s in job["steps"])
    assert any(s["name"]=="Run actions/upload-artifact@v4" and s["status"]=="completed" and s["conclusion"]=="success" for s in job["steps"])
    origin=artifact["workflow_run"]
    assert (artifact["id"],artifact["name"],artifact["digest"],artifact["expired"],origin["id"],
        origin["head_sha"],origin["repository_id"],origin["head_repository_id"])==(
        pin["id"],pin["name"],"sha256:"+pin["sha256"],False,RUN,HEAD,REPOSITORY_ID,REPOSITORY_ID)
    assert pin["job_id"]==pin["job"]


def authenticate_failure_log(raw):
    text=raw.decode("utf8")
    assert text.count("Traceback (most recent call last):")==1
    assert 'tools/hu_b696_turn_call_rivers.py", line 67, in parent_candidates' in text
    assert 'assert all((n["board"],n["pot"],n["bets"])==(root["flop"],c["pot"],[0,0]) for n in (first,response))' in text
    assert "AssertionError" in text and "Process completed with exit code 1." in text
    start=text.index("Traceback (most recent call last):")
    end=text.index("AssertionError",start)+len("AssertionError")
    return dict(reason="FLOP_CARD_ORDER_ASSERTION_BEFORE_ANY_TURN_SOLVE",original_job_log_sha256=hashlib.sha256(raw).hexdigest(),traceback=text[start:end],
        not_a_policy_negative=True,not_a_certification=True)


def authenticate_root_archive(pin,archive):
    assert hashlib.sha256(archive).hexdigest()==pin["sha256"]
    with ZipFile(io.BytesIO(archive)) as z:
        assert set(z.namelist())=={"flop/job.json","flop/result.json"}
        job_raw=z.read("flop/job.json");root_raw=z.read("flop/result.json")
    job,root=json.loads(job_raw),json.loads(root_raw)
    pot,stack=(600,9700) if pin["rank"]==76 else (550,9750)
    assert (root["flop"],root["pot"],root["stack"])==(pin["flop"],pot,stack)
    assert (job["flop"],job["pot"],job["stack"],job["rake_rate"],job["rake_cap"])==(pin["flop"],pot,stack,.05,1000)
    assert not job.get("locks") and job.get("hero") is None
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    first,=[n for n in root["nodes"] if (n["line"],n["player"])==("",0)]
    response,=[n for n in root["nodes"] if (n["line"],n["player"])==("x",1)]
    cards=lambda text:{text[i:i+2] for i in range(0,len(text),2)}
    assert len(cards(root["flop"]))==3
    for node in (first,response):
        assert len(node["board"])==6 and cards(node["board"])==cards(root["flop"])
        assert (node["pot"],node["bets"])==(pot,[0,0])
    assert first["board"]==response["board"]!=root["flop"]
    return dict(origin_root_run=RUN,origin_root_head=HEAD,origin_root_artifact=pin["id"],
        origin_root_archive_sha256=pin["sha256"],origin_root_job=pin["job"],rank=pin["rank"],flop=pin["flop"],
        original_root_job_sha256=hashlib.sha256(job_raw).hexdigest(),
        original_root_result_sha256=hashlib.sha256(root_raw).hexdigest(),
        native_node_flop_order=first["board"],root_pot=pot,root_stack=stack,gto_gap_pct=root["info"]["gto_expl_pct"],
        flop_cardset_and_prices_identical=True,original_guard_failed_only_on_order=True,
        original_native_root_preserved=True,turn_solves=0,actor_locks=0,medium_assessed=0,
        not_a_policy_negative=True,not_a_certification=True)


def collect(args):
    source_bytes()
    assert len(WORKERS)==6
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
    assert len(artifacts)==len({a["name"] for a in artifacts})==7
    roots=[]
    for pin in [PRICE,*WORKERS]:
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
        if pin!=PRICE:
            logs=api("actions/jobs/"+str(pin["job"])+"/logs")
            failure=authenticate_failure_log(logs)
            roots.append(dict(authenticate_root_archive(pin,archive),failure=failure))
            (args.output/("job."+str(pin["job"])+".log")).write_bytes(logs)
            (args.output/("failure."+str(pin["job"])+".json")).write_text(json.dumps(failure))
    (args.output/"workers.json").write_text(json.dumps(WORKERS))
    (args.output/"roots.json").write_text(json.dumps(roots))
    print(json.dumps(dict(authenticated_completed_guard_failures=6,authenticated_price_audit=1,source_run=RUN,source_blobs=len(SOURCE_BLOBS),policy_negatives=0)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    collect(cli.parse_args())

