"""B852: authenticate and archive completed B851 rank106 zero-reach native gate.
No new solver call, no certification upgrade from successful Actions alone.
"""
import json,sys,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b805_original import api
from hu_b467_river_source_gate import sha,json_bytes

RUN=45571577896
HEAD="e0f75eb3347e120450f0a61c33bd0d57de5d85ba"
WF=".github/workflows/nl2-hu-b851-rank106.yml"
BRANCH="fix/nl2-hu-lines-audit-20261118"
PINS={
 "7s5h3d":(139059253560,15003220140,"de5a715731c75fdcaf2c1a651a757ac92c33abeca5927dea8cc803e1221df1f1","6c"),
 "QsJh4d":(139059253102,15002047623,"c69c4bd1207a7c957788557159dab4bcf46e7ef4ed9ab9329dbbc5164948fb67","7s"),
}
def read(url):return json.loads(api(url))
def one(z,tail):
    names=[x for x in z.namelist() if x==tail or x.endswith("/"+tail)]
    assert len(names)==1,(tail,names)
    return z.read(names[0])
def main():
    stage=Path(sys.argv[1]).resolve()
    assert not stage.exists() and not stage.is_relative_to(Path("data").resolve())
    stage.mkdir()
    run=read(f"actions/runs/{RUN}")
    assert (run["id"],run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"],run["run_attempt"])==(RUN,HEAD,BRANCH,WF,"completed","success",1)
    assert run["repository"]["full_name"]=="tetracycline/poker-trainer" and run["repository"]["id"]==1438346845
    for path in (WF,"tools/hu_b851_rank106.py","tools/hu_b851_rank106_routes.cjs"):
        actual=subprocess.check_output(["git","hash-object",path],text=True).strip()
        assert actual==read(f"contents/{path}?ref={HEAD}")["sha"],path
    registry=Path("data/nl2_hu_multiboard_status_current.json").read_bytes()
    status=json.loads(registry)
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["EST"],status["TOTAL"])==(158,234,0,392)
    priority=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    row,=[row for row in priority["rows"] if row["rank"]==106]
    assert status["records"][row["model_id"]]["label"]=="APPROX"
    assert priority["current_certified_opportunity_share_pct"]==84.700987
    evidence=stage/"solver_evidence";partial=evidence/"partial";partial.mkdir(parents=True)
    receipts=[];observations=[]
    for flop,(jid,aid,digest,turn) in PINS.items():
        job=read(f"actions/jobs/{jid}")
        assert (job["id"],job["run_id"],job["head_sha"],job["status"],job["conclusion"])==(jid,RUN,HEAD,"completed","success")
        assert "source-gated ("+flop+"," in job["name"]
        assert {"Authenticate original B505 source and freeze previously untested b75 route","New turn only if common physical hand survives and independent replay","Run actions/upload-artifact@v4"} <= {s["name"] for s in job["steps"] if s["conclusion"]=="success"}
        meta=read(f"actions/artifacts/{aid}")
        assert (meta["id"],meta["name"],meta["digest"],meta["expired"])==(aid,"B851-R106-"+flop,"sha256:"+digest,False)
        assert meta["workflow_run"]["id"]==RUN and meta["workflow_run"]["head_sha"]==HEAD
        raw=api(f"actions/artifacts/{aid}/zip")
        assert len(raw)==meta["size_in_bytes"] and sha(raw)==digest
        with ZipFile(BytesIO(raw)) as z:
            assert z.testzip() is None
            proofraw=one(z,"proof.json");preflight=one(z,"preflight.json")
            route=one(z,"b851-route.json")
        proof=json.loads(proofraw);early=json.loads(preflight);routes=json.loads(route)
        for p in (proof,early):
            assert (p["schema"],p["flop"],p["turn"])==("NL2_B851_R106_FROZEN_B33_ROOT_NEW_B75_V1",flop,turn)
            assert p["route_sha256"]==sha(route)
            assert p["prior_pair_count"]==0 and p["preselected_rivers"]==[]
            assert p["original_flop_solves"]==0 and p["cert_promotions"]==0
            assert all(p[k]==0 for k in ("positive_distinct_flops","locked_public_boards","joint_halfpot_assessed","halfpot_candidates"))
            assert p["observations"]=={}
            assert len(p["origins"])==2 and all(x["archive_sha256"] and x["root_sha256"] and x["old_subgame_sha256"] for x in p["origins"])
        assert (routes["id"],routes["actor"],routes["line"])==("ln-ipfr-r_model-5ce65m",1,"b33 c/x b75 c/x")
        assert sha(route)==proof["route_sha256"]
        (evidence/("NL2_B851_R106_"+flop.upper()+".zip")).write_bytes(raw)
        receipts.append(dict(job={k:job[k] for k in ("id","run_id","head_sha","name","status","conclusion","steps")},artifact=meta))
        observations.append(dict(flop=flop,turn=turn,artifact_id=aid,archive_sha256=digest,proof_sha256=sha(proofraw),prior_pair_count=0,cert_promotions=0,preselected_rivers=[]))
    result=dict(schema="NL2_B852_B851_AUTHENTIC_TWO_ROOT_ZERO_PAIR_ARCHIVE_V1",source_run=RUN,head=HEAD,source_artifacts=[x["artifact_id"] for x in observations],observations=observations,original_flop_solves_repeated=0,locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,cert_promotions=0,unchanged_registry_sha256=sha(registry),model_node_opportunity_coverage_pct=priority["current_certified_opportunity_share_pct"])
    (partial/"b852_b851_rank106_zero_gate.json").write_bytes(json_bytes(result))
    (stage/"nl2_hu_b852_results.json").write_bytes(json_bytes(result))
    (stage/"nl2_hu_b852_source_receipts.json").write_bytes(json_bytes(dict(run={k:run[k] for k in ("id","head_sha","head_branch","path","status","conclusion","run_attempt")},receipts=receipts)))
    print(json.dumps(result))
if __name__=="__main__":main()
