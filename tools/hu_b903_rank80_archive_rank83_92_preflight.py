"""B903: authenticate and retain B902 two-root negative; preflight ranks 83,92-94.
No native dispatch, no promotion, no branch mutation."""
import io,json,sys,zipfile,subprocess
from pathlib import Path
import hu_b902_rank75_archive_rank80_screen as prev
import hu_b901_rank57_archive_rank75_screen as archive
from hu_b886_detached_price_candidate import api,git,sha,BRANCH
from hu_b895_archive_r158 import coverage
PARENT="7188a7ff388c5dec75e332edc309e6b20fcb0777"
HEAD902="3d28f0579efc3ab750b37a10211136cb543b1768"
RUN=45919151213
AUDIT=45919151153
ART=15164280044
DIGEST="217260f628a91f3f4d45077314a8729237bee390bae9940ff2a0db337a4aba36"
PREFIX="data/solver_evidence/b903_rank80_root_negative/"
TARGETS={92:"ln-bb-r_model-1t7cwh6",93:"ln-bb-r_model-d919qu",94:"ln-bb-r_model-lf823j"}
def dump(p,x): p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    archive.PARENT=PARENT
    return archive.guard()
def prepare(out):
    h=guard();cov=coverage()
    runs={}
    for rid in (RUN,AUDIT):
        r=api("/actions/runs/"+str(rid))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(HEAD902,BRANCH,"completed","success")
        runs[str(rid)]=r
    j=api("/actions/jobs/140245455665")
    assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(RUN,HEAD902,"rank80-saved-root-screen","completed","success")
    a=api("/actions/artifacts/"+str(ART))
    assert not a["expired"] and a["digest"]=="sha256:"+DIGEST
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==(RUN,HEAD902)
    raw=api("/actions/artifacts/"+str(ART)+"/zip",raw=True)
    assert sha(raw)==DIGEST
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        rb=z.read("rank80-screen.json")
    r=json.loads(rb)
    assert r["rank"]==80 and r["coverage"]==cov and r["native_solves"]==r["cert_promotions"]==0
    counts={"6c6d3h":(62,0),"KdJd5c":(0,0)}
    assert {x["flop"] for x in r["rows"]}==set(counts)
    for x in r["rows"]:
        assert (x["strict_flop_bettors"],x["strict_flop_callers"])==counts[x["flop"]]
        assert len(x["untested_turns"])==45 and not x["leads"]
        assert x["stage"]=="NO_STRICT_ROOT_ACTOR_ACTION_ANY_TURN"
    out.mkdir(parents=True,exist_ok=False)
    # B902's rank80 calls its guard; explicitly bind it to the new parent.
    prev.BASE=PARENT
    prev.rank80(out/"independent")
    assert (out/"independent/rank80-screen.json").read_bytes()==rb
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    (root/"b902-rank80-screen.zip").write_bytes(raw)
    (root/"rank80-screen.json").write_bytes(rb)
    dump(root/"receipts.json",dict(runs=runs,job=j,artifact=a,independent_byte_equal=True))
    dump(out/"prepared.json",dict(parent=h,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},coverage=cov,native_solves=0,cert_promotions=0))
def upload(out):
    # Same detached-only uploader, explicitly batch-specific prefix and message.
    import base64,hashlib
    h=guard();p=json.loads((out/"prepared.json").read_bytes())
    assert p["parent"]==h and p["coverage"]==coverage()
    assert p["native_solves"]==p["cert_promotions"]==0 and not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        b=Path(path).read_bytes();assert sha(b)==d
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        got=api("/git/blobs",{"content":base64.b64encode(b).decode(),"encoding":"base64"})["sha"]
        assert got==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=got))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B903 archive authenticated rank80 two-root strict reach negatives",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    receipt=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",receipt);print(json.dumps(receipt))
def preflight(out):
    guard();cov=coverage()
    reg=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    refs=json.loads(Path("data/nl2_hu_model_source_references.json").read_bytes())["items"]
    xwalk=json.loads(Path("data/nl2_hu_model_history_crosswalk.json").read_bytes())["records"]
    priority=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())["rows"]
    r83=json.loads(subprocess.check_output(["node","tools/hu_rank83_ingress_price_audit.cjs"]))
    assert r83["finding"]=="NO_LEGAL_PRIMARY_INGRESS_WITHIN_EXISTING_5PCT_SPR_GATE"
    assert r83["native_solves"]==0 and not r83["labels_or_prices_changed"]
    routes=json.loads(subprocess.check_output(["node","tools/hu_trainer_route_contract.cjs",*TARGETS.values()],input=json.dumps(list(reg)).encode()))["routes"]
    rows=[]
    for rank,mid in TARGETS.items():
        model=reg[mid];p=next(x for x in priority if x["rank"]==rank)
        assert (model["frequency_rank"],model["solver_profile"],model["label"])==(rank,"CO_BB","APPROX")
        assert p["model_id"]==mid and p["passes_min_0_2_pct_frequency"]
        route=routes[mid];assert route["seat"]==0
        # Inventory exact model mentions in currently tracked manifests and tools.
        # A mention is not a solve receipt, and absence is not a dedup clearance.
        proc=subprocess.run(["git","grep","-Il","-F",mid,"--","tools","docs",".github/workflows","data/solver_evidence"],capture_output=True,text=True)
        assert proc.returncode in (0,1)
        paths=proc.stdout.splitlines()
        # Commit messages are supplementary history, not exhaustive dispatch evidence.
        hist=git("log","--format=%H%x09%s","--regexp-ignore-case","--extended-regexp","--grep=rank[ _-]?"+str(rank)+"([^0-9]|$)").splitlines()
        rows.append(dict(rank=rank,model_id=mid,model_spr=model["assumed_model_node_spr"],
            frequency=p["estimated_per_hand_frequency_pct"],route=route,references=refs[mid],
            historical_crosswalk=xwalk[mid],tracked_mentions=paths,history_message_matches=hist,
            can_dispatch_native=False,reason="Need source-level actor, exact size, SPR, prior dispatch and GTO+NL2 same-deal validation"))
    out.mkdir(parents=True,exist_ok=False)
    dump(out/"rank83-ingress.json",r83)
    dump(out/"rank92-94-source-inventory.json",dict(rows=rows,coverage=cov,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Reference and rendered route inventory only; no native clearance or global exhaustion."))
    print(json.dumps(dict(rank83=r83["finding"],rank92_94=[dict(rank=x["rank"],spr=x["model_spr"],route=x["route"]["streets"],refs=x["references"]["reference_count"],mentions=len(x["tracked_mentions"]),history=len(x["history_message_matches"])) for x in rows],coverage=cov)))
if __name__=="__main__":
    {"prepare":prepare,"upload":upload,"preflight":preflight}[sys.argv[1]](Path(sys.argv[2]).resolve())
