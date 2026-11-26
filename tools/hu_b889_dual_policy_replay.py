"""B889: independently authenticate and replay B888, intersect physical deals.
No driver, no native invocation, no registry edit or certificate promotion.
"""
import hashlib,json,math,os,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
from hu_b888_r158_exact_third import cards, FLOP, TURN, MODEL

D=Path("data")
BRANCH="fix/nl2-hu-lines-audit-20261118"
REPO="tetracycline/poker-trainer"
RID=1438346845
P=D/"nl2_hu_b889_dual_policy_pins.json"
OLD=D/"nl2_hu_b888_r158_raw_dedup.json"
REG=D/"nl2_hu_multiboard_status_current.json"

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(obj):return (json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
def read(path):return json.loads(path.read_bytes())
def git(*args):return subprocess.check_output(["git",*args],text=True).strip()
def api(path):return subprocess.check_output(["gh","api",f"repos/{REPO}/{path}"])
def meta(path):return json.loads(api(path))
def verify_run(run_id,head,name=None,path=None):
    r=meta(f"actions/runs/{run_id}")
    assert (r["id"],r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(run_id,head,BRANCH,"completed","success")
    if name:assert r["name"]==name
    if path:assert r["path"]==path
    return r
def archive(aid,digest,name,run,head,path,size=None):
    m=meta(f"actions/artifacts/{aid}")
    assert (m["id"],m["name"],m["digest"],m["expired"])==(aid,name,"sha256:"+digest,False)
    w=m["workflow_run"]
    assert (w["id"],w["head_sha"],w["head_branch"],w["repository_id"])==(run,head,BRANCH,RID)
    raw=api(f"actions/artifacts/{aid}/zip")
    assert sha(raw)==digest
    if size is not None:assert len(raw)==size==m["size_in_bytes"]
    path.write_bytes(raw)
    return m
def unpack(path,out):
    with ZipFile(path) as z:
        names=z.namelist()
        assert len(names)==len(set(names))
        assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in names)
        z.extractall(out)
        return {n:sha(z.read(n)) for n in names if not n.endswith("/")}
def pair_set(row,board):
    assert row["public_board"]==board and row["acting_seat"]==0
    assert row["line"]=="x b50 c/b33 c/"
    assert "x" in row["source_actions"] and "b50" in row["source_actions"]
    result=set()
    for h,vs in row["rendered_exact_deals"].items():
        assert len(cards(h))==2 and cards(h).isdisjoint(cards(board))
        for v in vs:
            assert len(cards(v))==2 and cards(v).isdisjoint(cards(board)|cards(h))
            result.add(("".join(sorted(cards(h))),"".join(sorted(cards(v)))))
    return result

def main(stage,solver):
    stage=stage.resolve();solver=solver.resolve()
    assert not stage.exists()
    stage.mkdir(parents=True)
    inp=stage/"replay-input";inp.mkdir()
    rawdir=stage/"archive";rawdir.mkdir()
    pins=read(P);old=read(OLD)
    assert old["flop"]==FLOP and old["turn"]==TURN and old["model"]==MODEL
    before=REG.read_bytes();reg=json.loads(before)
    assert sha(before)==pins["registry_sha256"] and git("hash-object",str(REG))==pins["registry_git_blob"]
    assert git("rev-parse","HEAD:"+str(REG))==git("rev-parse",pins["head"]+":"+str(REG))
    rank=read(D/"nl2_hu_multiboard_prerank.json")
    w={n["model_id"]:n["estimated_NL2_hand_opportunity_fraction"] for n in rank["nodes"]}
    assert set(w)==set(reg["records"]) and len(w)==392
    cert=[k for k,v in reg["records"].items() if v["label"]=="CERT-MULTIBOARD"]
    approx=[k for k,v in reg["records"].items() if v["label"]=="APPROX"]
    cov=round(100*math.fsum(w[k] for k in cert)/math.fsum(w.values()),6)
    assert (len(cert),len(approx),cov)==(158,234,84.700987)
    assert MODEL in approx and w[MODEL]>=.002
    for f in (pins["workflow"],"tools/hu_b888_r158_exact_third.py",str(OLD)):
        assert git("hash-object",f)==git("rev-parse",pins["head"]+":"+f)
    receipts={"run":verify_run(pins["run"],pins["head"],path=pins["workflow"]),
              "audit":verify_run(pins["audit"],pins["head"],name="NL2 full batch audit")}
    prev=old["b887"]
    receipts["prior_run"]=verify_run(prev["run"],prev["head"])
    receipts["prior_audit"]=verify_run(prev["full_audit_run"],prev["head"],name="NL2 full batch audit")
    prev_meta=meta(f'actions/artifacts/{prev["artifact"]}')
    receipts["prior_artifact"]=archive(prev["artifact"],prev["sha256"],prev_meta["name"],prev["run"],prev["head"],inp/"b887.zip")
    receipts["original_run"]=verify_run(old["source_run"],old["source_head"])
    receipts["original_artifacts"]=[]
    for s in old["sources"]:
        receipts["original_artifacts"].append(archive(s["artifact"],s["sha256"],s["name"],old["source_run"],old["source_head"],inp/(s["name"]+".zip")))
    listing=meta(f'actions/runs/{pins["run"]}/artifacts')
    assert {a["id"] for a in listing["artifacts"]}=={p["artifact"] for p in pins["modes"]}
    proofs={}; plans={}; receipts["native"]={}
    for p in pins["modes"]:
        mode=p["mode"]
        job=meta(f'actions/jobs/{p["job"]}')
        assert (job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(pins["run"],pins["head"],f"native ({mode})","completed","success")
        assert all(s["conclusion"]=="success" for s in job["steps"])
        name=f"B888-R158-{FLOP}-{TURN}-{mode}"
        rawpath=rawdir/(name+".zip")
        m=archive(p["artifact"],p["sha256"],name,pins["run"],pins["head"],rawpath,p["size"])
        out=stage/("unpacked-"+mode)
        hashes=unpack(rawpath,out)
        proof_file,=out.rglob("proof.json")
        native=proof_file.parent
        proof=read(proof_file);plan=read(native/"plan.json")
        assert (proof["rank"],proof["mode"],proof["flop"],proof["turn"])==(158,mode,FLOP,TURN)
        assert proof["plan_sha256"]==sha((native/"plan.json").read_bytes())
        assert proof["job_sha256"]==sha((native/"native/job.json").read_bytes())
        assert proof["result_sha256"]==sha((native/"native/result.json").read_bytes())
        assert proof["original_flop_solves_repeated"]==proof["CERT_promotions"]==0
        assert proof["private_card_empirical_frequencies"] is False
        assert plan["registry_sha256"]==sha(before) and plan["coverage_pct"]==cov
        assert (plan["target_paid_cents"],plan["target_pot"],plan["target_stack"])==(433,2166,8992)
        assert len(proof["rows"])==8 and sum(bool(x["rendered_exact_deals"]) for x in proof["rows"].values())==p["log_rendered_positive"]
        # Recompute the archived proof twice using independent Python hash seeds.
        # No --driver is passed; the original job/result must already exist.
        for seed in ("23","867"):
            subprocess.run([sys.executable,"tools/hu_b888_r158_exact_third.py","--mode",mode,"--input",str(inp),"--solver",str(solver),"--output",str(native)],check=True,env=dict(os.environ,PYTHONHASHSEED=seed))
            assert all(sha((out/n).read_bytes())==h for n,h in hashes.items())
        proofs[mode]=proof;plans[mode]=plan
        receipts["native"][mode]=dict(job=job,artifact=m,archive_sha256=p["sha256"],member_sha256=hashes)
    assert plans["gto"]==plans["exp_oop"]
    g,e=proofs["gto"],proofs["exp_oop"]
    assert g["measured_partial_lock"] is None and e["measured_partial_lock"]
    assert set(g["rows"])==set(e["rows"]) and len(g["rows"])==8
    assert {b[-2:] for b in g["rows"]}==set(plans["gto"]["rivers"])
    assert all(len(b)==10 and len(cards(b))==5 and cards(b[:6])==cards(FLOP) and b[6:8]==TURN for b in g["rows"])
    rows=[]
    for board in sorted(g["rows"]):
        gr,er=g["rows"][board],e["rows"][board]
        gp,ep=pair_set(gr,board),pair_set(er,board)
        shared=sorted(gp&ep)
        # Half-pot proof is retained exactly as computed on each policy's
        # reachable node, not inferred to hold on all shared check deals.
        rows.append(dict(board=board,gto_pairs=len(gp),nl2_pairs=len(ep),
            shared_physical_pairs=len(shared),shared_hero_combos=len({h for h,v in shared}),
            shared_deals=[list(x) for x in shared],gto_b50=gr["b50"],nl2_b50=er["b50"],
            status="POSITIVE_EXACT_SHARED_DEALS_PENDING_BOARD_CERT_REVIEW" if shared else "ZERO_SHARED_EXACT_DEALS",
            formal_b50_recommendation=False))
    result=dict(schema="NL2_B889_R158_DUAL_POLICY_RAW_REPLAY_V1",rank=158,model=MODEL,
        source_run=pins["run"],source_audit=pins["audit"],source_head=pins["head"],
        registry_sha256=sha(before),CERT=len(cert),APPROX=len(approx),EST=0,
        weighted_model_opportunity_coverage_pct=cov,
        remaining_high_frequency_approx=sum(w[k]>=.002 for k in approx),
        rows=rows,positive_rivers=sum(x["shared_physical_pairs"]>0 for x in rows),
        distinct_positive_flops=int(any(x["shared_physical_pairs"]>0 for x in rows)),
        original_flop_solves_repeated=0,native_solves=0,CERT_promotions=0,
        formal_new_lock_variants=0,formal_new_nonpolarized=0,
        scope="One distinct original flop, exact conditional turn sizing. GTO and NL2 same physical two-seat deals intersected. Half-pot evidence is source-node scope, not a recommendation or a new CERT. Pool marginals are not private-card observations.")
    (stage/"report.json").write_bytes(dump(result))
    (stage/"receipts.json").write_bytes(dump(receipts))
    assert REG.read_bytes()==before
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False))
    print(json.dumps([{k:r[k] for k in ("board","gto_pairs","nl2_pairs","shared_physical_pairs","status")} for r in rows]))
if __name__=="__main__":main(Path(sys.argv[1]),Path(sys.argv[2]))
