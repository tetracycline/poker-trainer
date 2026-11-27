"""B902: preserve B901 rank75 negative screen; diagnose B841 rank80 roots.
Read-only native evidence, no solver dispatch, no label changes."""
import hashlib, io, json, sys, zipfile, subprocess
from pathlib import Path
import hu_b901_rank57_archive_rank75_screen as b901
import hu_b900_priority_source_diagnostics as prev
import hu_b766_rank75_chance_turns as chance
import hu_b732_rank80_boundaries as b732
import hu_b841_rank80_new_originals as b841
import hu_b671_rank80 as r80
from hu_b886_detached_price_candidate import api, git, sha, BRANCH
from hu_b895_archive_r158 import coverage
from hu_b467_river_source_gate import compact
from hu_sequential_cfr_reach import accepted

BASE="ba6371304736541dbb510f927f2773c695b72d30"
H901="a55b7536a6939828ea95280979ec0a8162aa8c88"
R901=45913269104
A901=45913269073
ART=15161356332
DIGEST="8da56f9086f767e6197961fa250047446328f1cd78e7b89d590dabbff770c7e5"
PREFIX="data/solver_evidence/b902_rank75_saved_root_screen/"
H841="a64d376fce5068f92789b903526186b661b5682a"
R841=45527456112
SOURCES={
    "6c6d3h":(14983542296,138914220210,"3a648696315c00c5820288270f4b04468aaab2efa4af022ad79e5ad27eb4edb0"),
    "KdJd5c":(14983332243,138914220593,"8f87058407d926d87606a38a55b1420069c130ecfbfdbd17ab51aeae6249339c"),
}
def dump(p,x):
    p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    b901.PARENT=BASE
    return b901.guard()
def archive(out):
    h=guard();cov=coverage()
    assert not git("status","--porcelain")
    runs={}
    for rid in (R901,A901):
        r=api("/actions/runs/"+str(rid))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(H901,BRANCH,"completed","success")
        runs[str(rid)]=r
    j=api("/actions/jobs/140226394311")
    assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(R901,H901,"rank75-saved-root-screen","completed","success")
    a=api("/actions/artifacts/"+str(ART))
    assert not a["expired"] and a["digest"]=="sha256:"+DIGEST
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==(R901,H901)
    raw=api("/actions/artifacts/"+str(ART)+"/zip",raw=True)
    assert sha(raw)==DIGEST
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        rb=z.read(prev.unique(z,"rank75-screen.json"))
    r=json.loads(rb)
    assert (r["rank"],r["flop"],r["coverage"])==(75,"Td8d5d",cov)
    assert r["native_solves"]==r["cert_promotions"]==0
    assert r["heldout_binary64_replay"]==["2d","3d","4d"]
    assert [x["turn"] for x in r["rows"]]==["6d","7d","9d","Jd","Qd","Kd","Ad"]
    assert all(not x["weak_draw_hands"] and not x["can_dispatch_native"] for x in r["rows"])
    out.mkdir(parents=True,exist_ok=False)
    b901.screen(out/"independent")
    assert (out/"independent/rank75-screen.json").read_bytes()==rb
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    (root/"b901-rank75-screen.zip").write_bytes(raw)
    (root/"rank75-screen.json").write_bytes(rb)
    dump(root/"receipts.json",dict(runs=runs,job=j,artifact=a,independent_byte_equal=True))
    files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())}
    dump(out/"prepared.json",dict(parent=h,files=files,coverage=cov,native_solves=0,cert_promotions=0))
    print(json.dumps(dict(rank=75,screened_unseen_turns=7,weak_draw_witnesses=0,files=files,coverage=cov)))
def upload(out):
    import base64
    h=guard();p=json.loads((out/"prepared.json").read_bytes())
    assert p["parent"]==h and p["native_solves"]==p["cert_promotions"]==0 and p["coverage"]==coverage()
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
    c=api("/git/commits",dict(message="B902 archive authenticated B901 rank75 unseen-turn negative screen; no CERT promotion",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
def rank80(out):
    guard();cov=coverage()
    receipt=json.loads(Path("data/nl2_hu_b843_source_receipts.json").read_bytes())
    rec,=[r for r in receipt if r["run"]["id"]==R841]
    assert (rec["run"]["head_sha"],rec["run"]["head_branch"],rec["run"]["status"],rec["run"]["conclusion"])==(H841,BRANCH,"completed","success")
    route=json.loads(subprocess.check_output(["node","tools/hu_b671_rank80_routes.cjs"]))
    model=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][r80.MODEL]
    assert (model["frequency_rank"],model["solver_profile"],model["label"])==(80,"LMP_CO_BB","APPROX")
    assert abs(9817/416/model["assumed_model_node_spr"]-1)<=.05
    rows=[]
    for flop,(aid,jid,digest) in SOURCES.items():
        a,=[a for a in rec["artifacts"] if a["id"]==aid]
        j,=[j for j in rec["jobs"] if j["id"]==jid]
        assert a["digest"]=="sha256:"+digest and a["workflow_run"]["head_sha"]==H841
        assert (j["name"],j["head_sha"],j["status"],j["conclusion"])==("solve ("+flop+")",H841,"completed","success")
        path=Path("data/solver_evidence/NL2_B841_R80_"+flop.upper()+".zip")
        raw=path.read_bytes();assert sha(raw)==digest
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            p=prev.read(z,"proof.json");root=prev.read(z,"flop/result.json");job=prev.read(z,"flop/job.json")
        assert (p["rank"],p["model_id"],p["flop"],p["line"])==(80,r80.MODEL,flop,r80.LINE)
        assert (p["actual_river_pot_bb"],p["actual_river_effective_stack_bb"])==(4.16,98.17)
        assert sha(compact(root))==p["root_sha256"]
        assert (root["flop"],root["pot"],root["stack"],job["pot"],job["stack"])==(flop,250,9900,250,9900)
        assert job["flop_oop"]=="33%" and not job.get("locks") and not root["info"].get("lock_stats")
        assert 0<=root["info"]["gto_expl_pct"]<=.5
        old=list(b841.CASES[flop])
        assert [x["turn"] for x in p["turns"]]==old
        assert all(not x["checks"] for x in p["turns"])
        opening,=[n for n in root["nodes"] if n["line"]==""]
        facing,=[n for n in root["nodes"] if n["line"]=="b33"]
        assert (opening["player"],opening["pot"],facing["player"],facing["pot"])==(0,250,1,333)
        bb=accepted(opening,root["hands"],"b33");co=accepted(facing,root["hands"],"c")
        observed={n["board"][-2:]:n for n in root["nodes"] if n["line"]=="b33 c/"}
        assert set(observed)==set(old)
        assert all((n["player"],n["pot"],n["bets"])==(0,416,[83,83]) for n in observed.values())
        new=[t for t in r80.DECK if t not in r80.cards(flop) and t not in old]
        assert len(new)==45
        item=dict(flop=flop,artifact=aid,archive_sha256=digest,root_sha256=p["root_sha256"],
                  root_job_sha256=sha(compact(job)),strict_flop_bettors=len(bb),strict_flop_callers=len(co),
                  tested_turns=old,untested_turns=new,root_gap=root["info"]["gto_expl_pct"],leads=[],heldout=[])
        if not bb or not co:
            item["stage"]="NO_STRICT_ROOT_ACTOR_ACTION_ANY_TURN"
        else:
            masks={t:chance.blocked(root["hands"],t) for t in old+new}
            for t in old:
                w=chance.reconstruct(root,observed,masks,[u for u in old if u!=t],t)
                assert all(chance.weight_bytes(x)==chance.weight_bytes(y) for x,y in zip(w,observed[t]["wr"],strict=True))
                item["heldout"].append(t)
            for t in new:
                w=chance.reconstruct(root,observed,masks,old,t)
                n=dict(next(iter(observed.values())),board=flop+t,wr=w)
                synthetic=dict(root,nodes=[x for x in root["nodes"] if x["line"]!="b33 c/"]+[n])
                _,row=b732.gate(synthetic,t,route)
                if row["river_witnesses"]:
                    item["leads"].append(row)
            item["stage"]="UNTESTED_BOUNDARY_PREFLIGHT_ONLY"
        rows.append(item)
    out.mkdir(parents=True,exist_ok=False)
    report=dict(rank=80,coverage=cov,rows=rows,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,
                scope="Two saved B841 roots only. Leads need full historical dedup, full job replay and same-deal GTO+NL2 native continuation. No unseen-root exhaustion.")
    dump(out/"rank80-screen.json",report)
    print(json.dumps(dict(rank=80,rows=[dict(flop=x["flop"],strict_bettors=x["strict_flop_bettors"],strict_callers=x["strict_flop_callers"],stage=x["stage"],unseen_turns=len(x["untested_turns"]),leads=len(x["leads"])) for x in rows],coverage=cov)))
if __name__=="__main__":
    {"archive":archive,"upload":upload,"rank80":rank80}[sys.argv[1]](Path(sys.argv[2]).resolve())
