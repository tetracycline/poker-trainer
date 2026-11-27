"""B905: retain six B904 screens and freeze source-bound continuation jobs.
No native solver, promotion, or branch mutation. History hits require review.
"""
import base64,hashlib,io,itertools,json,os,re,sys,subprocess,zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
import hu_b904_bb_saved_root_screen as prev
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b467_river_source_gate import compact
from hu_b710_publish import unpack_original
import hu_b711_bb_lead_rivers as native
import hu_b766_rank75_chance_turns as chance

PARENT="dc4bf172fef6dc383859d614807a2bccc044cbb8"
RUN=45931138296
AUDIT=45931138200
PREFIX="data/solver_evidence/b905_bb_saved_root_screens/"
PINS={
"9d7h4c":(15168832190,"72ee3b1b9a5d43846c8526c166ae91b8ebf760e4a57a5df7f7d334b80dcceacc",140283778477,147,1,31,(26,22,5)),
"8s6d2c":(15168597839,"4b760fa275da99736920c747f62110a6c764f03faf92c1386c38568492b617dc",140283778594,136,0,0,(0,0,0)),
"7c5d3h":(15168867315,"dc6a1b59b991ac35908554296d5a7f947fea77fb462900f59af1271b60df7861",140283778541,136,0,0,(0,0,0)),
"7h6h2c":(15168961837,"9e7d5f308a0aca1c212e4ab89af3d476bc5e5f3db67be841c566c80c2f4a9f07",140283778293,125,1,23,(16,15,7)),
"8h7h3c":(15169041373,"5880475050f28003d13afea0a73553e9198e90e01e40f4e421b3aae2c7a2d0e6",140283778605,133,6,20,(13,16,4)),
"9h8h2c":(15167989330,"be5c7b60330807c2697cd3e89db5046b5a81695f249d13c77bdffae6e49c3120",140283778551,163,0,0,(0,0,0)),
}
def dump(p,x): p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def read(p): return json.loads(Path(p).read_bytes())
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==PARENT
    p=api("/pulls/2")
    assert p["state"]=="open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==(REPO,BRANCH,h)
    return h
def runs():
    out={}
    for rid in (RUN,AUDIT):
        r=api("/actions/runs/"+str(rid))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(PARENT,BRANCH,"completed","success")
        out[str(rid)]=r
    return out
def source(flop,cov):
    aid,digest,jid,hero,villain,leads,rank_counts=PINS[flop]
    a=api("/actions/artifacts/"+str(aid))
    assert a["name"]=="B904-CO-BB-screen-"+flop and not a["expired"] and a["digest"]=="sha256:"+digest
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==(RUN,PARENT)
    j=api("/actions/jobs/"+str(jid))
    assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(RUN,PARENT,"saved-root-screen ("+flop+")","completed","success")
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
    assert sha(raw)==digest
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None and z.namelist()==["screen.json"]
        rb=z.read("screen.json")
    r=json.loads(rb)
    assert (r["flop"],r["strict_bb_check_call"],r["strict_co_halfpot"],len(r["leads"]))==(flop,hero,villain,leads)
    assert r["coverage"]==cov and all(r[k]==0 for k in ("native_solves","cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
    assert len(r["untested_in_this_archive"])==46 and len(set(r["untested_in_this_archive"]))==46
    assert len(r["rows"])==(46 if villain else 0)
    assert tuple(sum(bool(x["rank_picks"][str(rank)]) for x in r["leads"]) for rank in (92,93,94))==rank_counts
    return r,rb,raw,a,j
def prepare(out):
    h=guard();cov=coverage();rr=runs()
    out.mkdir(parents=True,exist_ok=False)
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    receipts={};summ=[]
    # Independent byte replay of the original non-native screen, not a solver rerun.
    old=prev.guard
    prev.guard=lambda: (guard(),coverage())[1]
    try:
        for flop in PINS:
            r,rb,raw,a,j=source(flop,cov)
            prev.screen(flop,out/("replay-"+flop))
            assert (out/("replay-"+flop)/"screen.json").read_bytes()==rb
            (root/(flop+".zip")).write_bytes(raw)
            (root/(flop+".json")).write_bytes(rb)
            receipts[flop]=dict(artifact=a,job=j,independent_byte_equal=True)
            summ.append(dict(flop=flop,stage=r["stage"],screened=len(r["rows"]),leads=len(r["leads"])))
    finally:prev.guard=old
    dump(root/"receipts.json",dict(runs=rr,sources=receipts,coverage=cov,summary=summ,scope="Screen evidence only; no CERT or full independent leave-one job replay"))
    dump(out/"prepared.json",dict(parent=h,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},coverage=cov,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
def upload(out):
    h=guard();p=read(out/"prepared.json")
    assert p["parent"]==h and p["coverage"]==coverage() and p["native_solves"]==p["cert_promotions"]==0
    assert not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        b=Path(path).read_bytes();assert sha(b)==d
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        got=api("/git/blobs",{"content":base64.b64encode(b).decode(),"encoding":"base64"})["sha"]
        assert got==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=got))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B905 archive six independently replayed B904 saved-root screens; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    receipt=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",receipt);print(json.dumps(receipt))
def variants(flop):
    cs=[flop[i:i+2] for i in (0,2,4)]
    ss=sorted({c[1] for c in cs})
    return sorted({"".join(order).lower() for suits in itertools.permutations("cdhs",len(ss)) for order in itertools.permutations([c[0]+dict(zip(ss,suits))[c[1]] for c in cs])})
def orbit(flop,t):
    cs=native.cards(flop);o=set()
    for suits in itertools.permutations("cdhs"):
        m=dict(zip("cdhs",suits))
        if {c[0]+m[c[1]] for c in cs}==cs:o.add(t[0]+m[t[1]])
    return tuple(sorted(o))
def inventory(flop):
    vs=variants(flop);pattern="|".join(vs)
    # Full ancestor dispatch history, not merely current filenames.
    history=git("log","--format=%H%x09%s","--regexp-ignore-case","-G",pattern,PARENT,"--",".github/workflows","tools").splitlines()
    paths=[p for p in git("ls-files","data/solver_evidence").splitlines() if any(v in re.sub(r"[^a-z0-9]","",p.lower()) for v in vs)]
    hits=[];ids=set();initial=None
    for page in range(1,101):
        data=api("/actions/artifacts?per_page=100&page="+str(page))
        if initial is None:initial=data["total_count"]
        for a in data["artifacts"]:
            assert a["id"] not in ids,"listing changed"
            ids.add(a["id"])
            if any(v in re.sub(r"[^a-z0-9]","",a["name"].lower()) for v in vs):
                hits.append({k:a.get(k) for k in ("id","name","expired","digest","workflow_run")})
        if len(data["artifacts"])<100:break
    else:raise RuntimeError("artifact inventory not exhausted")
    assert len(ids)>=initial
    return dict(ancestor_dispatch_matches=history,tracked_named_source_paths=paths,artifact_name_matches=hits,artifact_metadata_rows=len(ids),historical_ref=PARENT,clearance=False,limitations="Matches require source-level line/turn review; expired unlisted artifacts and non-named sources are not cleared.")
def plan(out,solver,flop):
    guard();cov=coverage();runs()
    r,rb,raw,a,j=source(flop,cov)
    assert r["stage"]=="ROOT_UI_PREFLIGHT_ONLY" and r["leads"]
    assert git("-C",str(solver),"rev-parse","HEAD")==native.SOLVER
    py=solver/"postflop/py"
    assert sha((py/"pipeline.py").read_bytes())==native.PIPELINE and sha((py/"ranges.py").read_bytes())==native.RANGES
    assert sha((solver/"inputs/pool_stats.json").read_bytes())==native.POOL
    sys.path.insert(0,str(py));import pipeline
    hist=inventory(flop)
    out.mkdir(parents=True,exist_ok=False)
    batch,digest=prev.PINS[flop]
    original=Path("data/solver_evidence")/("NL2_"+batch+"_CO_BB_"+flop.upper()+".zip")
    root_raw=original.read_bytes();assert sha(root_raw)==digest
    with TemporaryDirectory() as temp:
        d=Path(temp);names=unpack_original(root_raw,d)
        p=read(d/"proof.json")
        assert all(sha((d/n).read_bytes())==v for n,v in p["native_file_sha256"].items())
        root=read(d/"flop/result.json")
        assert sha((d/"flop/result.json").read_bytes())==r["root_source_sha256"]==p["root_source_sha256"]
        assert sha((d/"flop/job.json").read_bytes())==r["root_job_sha256"]==p["root_job_sha256"]
        routes=read(d/"rendered-routes.json")
        assert (d/"rendered-routes.json").read_bytes()==subprocess.check_output(["node","tools/hu_b711_bb_lead_routes.cjs"])
        old=r["prior_turns"]
        observed={n["board"][-2:]:n for n in root["nodes"] if n["line"]=="x b50 c/"}
        assert set(observed)==set(old)
        masks={t:chance.blocked(root["hands"],t) for t in old+r["untested_in_this_archive"]}
        def rebuilt(t):
            w=chance.reconstruct(root,observed,masks,old,t)
            template=observed[old[0]]
            n=dict(template,board=template["board"][:6]+t,wr=w)
            return dict(root,nodes=[x for x in root["nodes"] if x["line"]!="x b50 c/"]+[n])
        old_jobs={}
        for t in old:
            rr=rebuilt(t)
            stats,picks=native.gate(rr,t,routes)
            rec,=[q for q in p["turns"] if q["turn"]==t]
            assert (stats,picks)==(rec["root_gate"],rec["river_extracts_by_rank"])
            if rec["gto_solved"]:
                jb=compact(native.turn_job(rr,t,picks,pipeline))
                assert jb==(d/(t+"-gto")/"job.json").read_bytes()
                old_jobs[t]=sha(jb)
        assert old_jobs,"no archived native continuation job replay"
        # Only freeze rank92 first, with rank93/94 incidental extraction in same job.
        # Exclude old turn suit orbits and mutually isomorphic new turns.
        excluded={orbit(flop,t) for t in old};plans=[]
        for lead in r["leads"]:
            t=lead["turn"];o=orbit(flop,t)
            if o in excluded or not lead["rank_picks"]["92"]:continue
            rr=rebuilt(t);stats,picks=native.gate(rr,t,routes)
            assert picks==lead["rank_picks"]
            job=compact(native.turn_job(rr,t,picks,pipeline))
            (out/(t+"-gto-job.json")).write_bytes(job)
            plans.append(dict(turn=t,rank=92,orbit=o,job_sha256=sha(job),rank_picks=picks,can_dispatch_native=False))
            excluded.add(o)
            if len(plans)==2:break
        assert plans
    dump(out/"plan.json",dict(flop=flop,coverage=cov,source_archive_sha256=digest,source_screen_sha256=sha(rb),historical_inventory=hist,
         full_job_replay_using_all_three_observations=old_jobs,independent_heldout_missing=r["heldout"],plans=plans,
         native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Full job bytes reproduced using all three observations, not complete independent held-out reconstruction. No native clearance."))
    print(json.dumps(dict(flop=flop,history_matches=len(hist["ancestor_dispatch_matches"]),artifact_matches=len(hist["artifact_name_matches"]),old_jobs_replayed=len(old_jobs),plans=plans,coverage=cov)))
if __name__=="__main__":
    mode=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if mode=="plan":plan(out,Path(sys.argv[3]).resolve(),sys.argv[4])
    else:{"prepare":prepare,"upload":upload}[mode](out)
