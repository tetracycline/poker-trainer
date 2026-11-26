"""B881: verify cancelled B879 native attempts, including ZIP membership and digests.
Never count job-only evidence as solved or as a negative reach result.
"""
import hashlib,json,sys,zipfile
from pathlib import Path
PINS={
  15080371470:("Jh9d5c","eb7b402fefac75a96aa4da5c2bd6a1fca825fc90544c111ce41f81893de0d2e0",139627734742),
  15079797499:("Ts8d4c","49fe602554c4cbb61aa55086b01911a589787e848d5be2e9ca51a8d3ae682e83",139627734298),
}
RUN=45735534620
HEAD="a42cf04c5008d0abaa10bff3f512ff132b946048"
def load(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def main(d):
    run=load(d/"run.json")
    assert (run["id"],run["head_sha"],run["status"],run["conclusion"])==(RUN,HEAD,"completed","cancelled")
    jobs={j["id"]:j for j in load(d/"jobs.json")["jobs"]}
    rows=[]
    for aid,(flop,digest,jid) in sorted(PINS.items()):
        j=jobs[jid]
        assert j["conclusion"]=="cancelled" and j["name"]==f"original-root ({flop})"
        step,=[s for s in j["steps"] if s["name"]=="Solve only one original root and verify exact byte-replay without solver rerun"]
        assert step["conclusion"]=="cancelled"
        meta=load(d/f"{aid}.json")
        assert meta["id"]==aid and meta["digest"]=="sha256:"+digest and meta["workflow_run"]["id"]==RUN
        assert meta["workflow_run"]["head_sha"]==HEAD
        raw=(d/f"{aid}.zip").read_bytes()
        assert sha(raw)==digest and len(raw)==meta["size_in_bytes"]
        with zipfile.ZipFile(d/f"{aid}.zip") as z:
            names=z.namelist()
            assert len(names)==len(set(names))
            assert all(not n.startswith("/") and ".." not in Path(n).parts for n in names)
            members=[dict(name=n,size=len(z.read(n)),sha256=sha(z.read(n))) for n in sorted(names) if not n.endswith("/")]
            results=[n for n in names if Path(n).name in ("result.json","proof.json")]
            # If any unexpected result exists, fail closed for manual independent replay.
            assert not results, f"Unexpected possible native output: {results}"
            jobnames=[n for n in names if Path(n).name=="job.json"]
            assert len(jobnames)==1
            nativejob=json.loads(z.read(jobnames[0]))
            assert nativejob["flop"]==flop
            assert (nativejob["pot"],nativejob["stack"],nativejob["rake_rate"],nativejob["rake_cap"])==(250,9900,.05,1000)
            assert nativejob.get("hero") is None and not nativejob.get("locks")
        rows.append(dict(flop=flop,artifact_id=aid,artifact_sha256=digest,job_id=jid,job_conclusion="cancelled",native_step_conclusion="cancelled",members=members,complete_native_result=False,reach_result=None,status="BLOCKED_NATIVE_CANCELLED_NO_RESULT",certifications_granted=0))
    report=dict(schema="NL2_B881_B879_CANCELLED_NATIVE_RECEIPTS_V1",run=RUN,head=HEAD,rows=rows,certifications_granted=0,new_native_solves=0,scope="Cancelled native attempts only; do not retry identical jobs or infer zero reach.")
    print(json.dumps(report,sort_keys=True))
    (d/"report.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":main(Path(sys.argv[1]))
