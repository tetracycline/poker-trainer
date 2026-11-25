"""B860: archive B859 successful preflight; byte-pin original ZIP, independently replay, never call native solver."""
import json, sys, subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b859_limp_boundaries import main as replay, api
from hu_b467_river_source_gate import sha,json_bytes

RUN=45617152008
AUDIT=45617151705
HEAD="f36083ccaa5abee36afa6a9045d0aeadc287b4a1"
BRANCH="fix/nl2-hu-lines-audit-20261118"
AID=15023361079
JID=139215389425
DIGEST="5a52c0e8fc3d158e86c6a12fb9fbcc2188b52338f8e90e38fe152931ae6f5c25"
NAME="B859-cancelled-receipts-and-original-boundary-screen"
WF=".github/workflows/nl2-hu-b859-limp-boundaries.yml"

def read(path): return json.loads(api(path))
def main(stage):
    assert not stage.exists() and not stage.is_relative_to(Path("data").resolve())
    stage.mkdir()
    run=read(f"actions/runs/{RUN}")
    assert (run["id"],run["head_sha"],run["head_branch"],run["status"],run["conclusion"],run["path"])==(RUN,HEAD,BRANCH,"completed","success",WF)
    audit=read(f"actions/runs/{AUDIT}")
    assert (audit["head_sha"],audit["status"],audit["conclusion"],audit["name"])==(HEAD,"completed","success","NL2 full batch audit")
    job=read(f"actions/jobs/{JID}")
    assert (job["run_id"],job["head_sha"],job["status"],job["conclusion"])==(RUN,HEAD,"completed","success")
    for path in (WF,"tools/hu_b859_limp_boundaries.py","data/nl2_hu_b859_b858_cancelled_receipts.json"):
        assert subprocess.check_output(["git","hash-object",path],text=True).strip()==read(f"contents/{path}?ref={HEAD}")["sha"]
    meta=read(f"actions/artifacts/{AID}")
    assert (meta["id"],meta["name"],meta["digest"],meta["size_in_bytes"],meta["expired"])==(AID,NAME,"sha256:"+DIGEST,5121,False)
    assert (meta["workflow_run"]["id"],meta["workflow_run"]["head_sha"])==(RUN,HEAD)
    raw=api(f"actions/artifacts/{AID}/zip")
    assert len(raw)==5121 and sha(raw)==DIGEST
    with ZipFile(BytesIO(raw)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if not n.endswith("/")}
    expected={"report.json","rendered-routes.json","15021586702.zip","15020377371.zip"}
    assert set(files)==expected,set(files)
    temp=stage.parent/"b860-independent-replay"
    replay(temp)
    assert set(x.name for x in temp.iterdir())==expected
    for n,v in files.items():
        assert (temp/n).read_bytes()==v,n
    report=json.loads(files["report.json"])
    rows=report["root_boundary_screen"]
    assert len(rows)==36 and {x["rank"] for x in rows}=={115,116,118}
    assert all(not x["gate"]["river_witnesses"] for x in rows)
    assert all(sum(x["rank"]==r for x in rows)==12 for r in (115,116,118))
    assert all(report[k]==0 for k in ("native_solves","cert_promotions","locked_public_boards","joint_halfpot_assessed","nonpolarized_candidates"))
    assert all(x["status"]=="CANCELLED_NO_CERT" for x in report["cancelled_sources"])
    evidence=stage/"solver_evidence"
    partial=evidence/"partial"
    partial.mkdir(parents=True)
    (evidence/"NL2_B859_ORIGINAL_BOUNDARY_SCREEN.zip").write_bytes(raw)
    (partial/"b860_b859_boundary_screen.json").write_bytes(files["report.json"])
    summary=dict(schema="NL2_B860_AUTHENTIC_B859_BOUNDARY_ARCHIVE_V1",source_run=RUN,source_head=HEAD,static_audit_run=AUDIT,source_job=JID,source_artifact=AID,zip_sha256=DIGEST,member_sha256={n:sha(v) for n,v in files.items()},independent_replay_byte_equal=True,screened=36,eligible_by_rank={"115":0,"116":0,"118":0},scope="Boundary preflight only; cancellation is not zero reach. No inference on unseen roots.",cert_promotions=0,locked_public_boards=0,joint_halfpot_assessed=0,nonpolarized_candidates=0,native_solves=0,model_opportunity_coverage_pct=report["model_opportunity_coverage_pct"])
    (stage/"nl2_hu_b860_results.json").write_bytes(json_bytes(summary))
    (stage/"nl2_hu_b860_source_receipts.json").write_bytes(json_bytes(dict(run=run,job=job,artifact=meta,audit=audit)))
    print(json.dumps(summary))

if __name__=="__main__": main(Path(sys.argv[1]).resolve())
