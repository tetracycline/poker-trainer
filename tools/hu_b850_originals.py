"""B850: preserve the already successful B847 dual-policy held-out gate, without re-solving."""
import json
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import subprocess, os, sys
from hu_b805_original import api
from hu_b467_river_source_gate import sha,json_bytes

RUN=45555973067
JOB=139007981035
ART=14994838946
HEAD="7da55f4a044964a4f5471a2f7c8e47f55bb2a90b"
DIGEST="e77ce275057b46f2f0ef27ac270331c6a13ccd5db39af1e8ce47bc6bc130120e"
WF=".github/workflows/nl2-hu-b847-btn-heldout-turn.yml"
BRANCH="fix/nl2-hu-lines-audit-20261118"
def read(path):
    return json.loads(api(path))
def main():
    stage=Path(sys.argv[1]).resolve()
    assert not stage.exists() and not stage.is_relative_to(Path("data").resolve())
    stage.mkdir()
    run=read(f"actions/runs/{RUN}")
    assert (run["id"],run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(RUN,HEAD,BRANCH,WF,"completed","success")
    assert run["repository"]["full_name"]=="tetracycline/poker-trainer" and run["repository"]["id"]==1438346845
    job=read(f"actions/jobs/{JOB}")
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(JOB,RUN,HEAD,"original-turn-gate","completed","success")
    assert {"Authenticate both original B524 artifacts and successful source jobs","Replay held-out exact turn history twice without any native solver","Run actions/upload-artifact@v4"} <= {s["name"] for s in job["steps"] if s["conclusion"]=="success"}
    meta=read(f"actions/artifacts/{ART}")
    assert (meta["id"],meta["name"],meta["digest"],meta["expired"])==(ART,"B847-B524-6s5h4d-Kd-prior-gate","sha256:"+DIGEST,False)
    assert meta["workflow_run"]["id"]==RUN and meta["workflow_run"]["head_sha"]==HEAD
    raw=api(f"actions/artifacts/{ART}/zip")
    assert len(raw)==meta["size_in_bytes"] and sha(raw)==DIGEST
    with ZipFile(BytesIO(raw)) as z:
        assert z.namelist()==["b847-19.json"] and z.testzip() is None
        proofraw=z.read("b847-19.json")
    p=json.loads(proofraw)
    assert (p["schema"],p["flop"],p["turn"],p["source_run"],p["source_head"])==("NL2_B847_B524_HELDOUT_EXACT_TURN_PRIOR_GATE_V1","6s5h4d","Kd",45118153398,"d1b22cd54e8c5391f2ee6d9411488923979ac797")
    assert p["rank104_status"]=="B75_NOT_PRESENT_IN_ORIGINAL_TURN_MENU"
    assert p["rank105_status"]=="NO_COMMON_PHYSICAL_ROUTE_PAIR_BEFORE_RIVER" and p["rank105_possible_rivers"]=={}
    assert all(p[k]==0 for k in ("native_solve_invocations","cert_promotions","new_locks","new_joint_halfpot","new_nonpolarized"))
    assert p["not_a_certification"] and p["requires_actual_river_action_and_full_source_replay"]
    for mode,aid,name,digest in (("gto",14792976867,"GTO","df887d5566b9f99505a5310b3e236205c6bfbd55b19013266fbf3e91071a442b"),("exp_ip",14793655339,"EXP_IP","5725c811a63ba90be177b3c40ef3a7f240248f6cfa1ccf2096d05c18da8292e7")):
        assert p["source_identities"][mode]["artifact_id"]==aid
        assert sha(Path(f"data/solver_evidence/NL2_B524_R8_6S5H4D_{name}.zip").read_bytes())==digest
    for f in (WF,"tools/hu_b847_btn_heldout_turn.py"):
        assert subprocess.check_output(["git","hash-object",f],text=True).strip()==read(f"contents/{f}?ref={HEAD}")["sha"]
    registry=Path("data/nl2_hu_multiboard_status_current.json").read_bytes()
    status=json.loads(registry)
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["TOTAL"])==(158,234,392)
    priority=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    assert all(status["records"][r["model_id"]]["label"]=="APPROX" for r in priority["rows"] if r["rank"] in (104,105))
    assert priority["current_certified_opportunity_share_pct"]<90
    evidence=stage/"solver_evidence"; partial=evidence/"partial";partial.mkdir(parents=True)
    (evidence/"NL2_B847_R104_105_6S5H4D_KD_GATE.zip").write_bytes(raw)
    (partial/"b850_b847_heldout_gate.json").write_bytes(proofraw)
    result=dict(source_run=RUN,source_job=JOB,source_artifact=ART,artifact_sha256=DIGEST,proof_sha256=sha(proofraw),rank104_status=p["rank104_status"],rank105_status=p["rank105_status"],cert_promotions=0,locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,native_repeated=0,unchanged_registry_sha256=sha(registry),model_node_opportunity_coverage_pct=priority["current_certified_opportunity_share_pct"])
    (stage/"nl2_hu_b850_results.json").write_bytes(json_bytes(result))
    (stage/"nl2_hu_b850_source_receipt.json").write_bytes(json_bytes(dict(run={k:run[k] for k in ("id","head_sha","head_branch","path","status","conclusion","run_attempt")},job={k:job[k] for k in ("id","run_id","head_sha","name","status","conclusion","steps")},artifact=meta)))
    print(json.dumps(result))
if __name__=="__main__":
    main()
