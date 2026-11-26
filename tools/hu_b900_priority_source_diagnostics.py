"""B900: authenticate B899 negative original roots, then diagnose prior rank57
source attrition. No native driver, no registry mutation, no branch movement.
"""
import io, json, os, subprocess, sys, zipfile
from pathlib import Path, PurePosixPath
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
import hu_b898_archive_boundaries as archive
import hu_b703_rank29_highcards as r29
import hu_b637_rank57 as r57
from hu_b467_river_source_gate import compact
from hu_b582_rank29_reach import cards

BASE="7684ad121c891dc4880d58203af9fc5d6c2c4a39"
PREFIX="data/solver_evidence/b900_rank29_negative/"
RUNS={
    45901243318:BASE,45901243266:BASE,
    45527191880:"c97ab1e6decb8b4dd1484421fab8534de8be2cc8",
    45527191595:"c97ab1e6decb8b4dd1484421fab8534de8be2cc8",
    45721198494:"c17a0d254cfad9da8ee1b53b098baf7f941be0de",
    45721198403:"c17a0d254cfad9da8ee1b53b098baf7f941be0de",
}
R29={
    "Ac3c2h":(15155657968,45901243318,"a5c830369c8eb402190948ddc97866f6823e3684d8ec7a75408f24813c678cb7",["2c","4c","5c","6c"]),
    "Ac3h2c":(15155528132,45901243318,"1245490c17177abdf1de25f6e2b160abeadfe03f9213c88cf534ffa2354180ae",["3c","4c","5c","6c"]),
}
R57={
    "Ad6h6s":(14982203888,45527191880,"561fd6f22168b686e8e24f4cb2cf50674a65b8b4341aaccde273771a61016929",["2c","3d","4h","9s","Qc"]),
    "Kh8d8s":(14983660946,45527191880,"92fb7deadf389f051f0f304b4d94fafceca3ac0de01f7537953321ef9ce7a9c5",["2c","3h","5d","Ts","Ac"]),
    "Kh5s5d":(15072163235,45721198494,"1a3f8bc004187ceb1e4ea83b358510ef96c1732fba27ff33c8ee91322181e642",["2c","3h","7s"]),
    "Ts6h6d":(15072352695,45721198494,"118d0d14fd4aa244901745e65b64c9aa40f065da39cb516ab700cd84cb1f7e0a",["3c","4s","8h"]),
}
def dump(path,obj):
    path.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
def guard():
    archive.BASE=BASE
    archive.PREFIX=PREFIX
    return archive.guard()
def completed(ids):
    out={}
    for rid in ids:
        r=api("/actions/runs/"+str(rid))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(RUNS[rid],BRANCH,"completed","success")
        out[str(rid)]=r
    return out
def artifact(spec):
    aid,rid,h,turns=spec
    a=api("/actions/artifacts/"+str(aid))
    assert not a["expired"] and a["digest"]=="sha256:"+h
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==(rid,RUNS[rid])
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
    assert sha(raw)==h
    return raw,a
def unique(z,suffix):
    names=[n for n in z.namelist() if n==suffix or n.endswith("/"+suffix)]
    assert len(names)==1,(suffix,names)
    return names[0]
def read(z,suffix):
    return json.loads(z.read(unique(z,suffix)))
def rank29(out):
    parent=guard(); cov=coverage()
    assert not git("status","--porcelain")
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    out.mkdir(parents=True,exist_ok=False)
    runs=completed((45901243318,45901243266))
    meta={}; rows=[]
    route=json.loads(subprocess.check_output(["node","tools/hu_b703_rank29_routes.cjs"]))
    assert (route["model_id"],route["actor"],route["line"],route["spr"])==(r29.MODEL,0,r29.LINE,7.52)
    for flop,spec in R29.items():
        raw,a=artifact(spec)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            proofname=unique(z,"proof.json")
            pf=json.loads(z.read(proofname))
            pre= z.read(unique(z,"b899-preflight.json"))
            rec=json.loads(pre)
            assert sha(pre)==pf["historical_preflight_sha256"]
            assert (rec["head"],rec["flop"],rec["turns"])==(BASE,flop,spec[3])
            assert rec["coverage"]==cov and not rec["dedup"]["history_matches"] and not rec["dedup"]["artifact_name_matches"]
            assert pf["rank"]==29 and pf["flop"]==flop and pf["actor"]==0 and pf["line"]==r29.LINE
            assert pf["not_a_certification"] and pf["independent_same_two_physical_hands_gate_pending"]
            assert all(pf[k]==0 for k in ("positive_distinct_flops","gto_turn_subgames","actor_locked_turn_subgames","gto_half_pot_river_nodes","nl2_half_pot_river_nodes"))
            prefix=str(PurePosixPath(proofname).parent)
            prefix="" if prefix=="." else prefix+"/"
            for name,h in pf["native_file_sha256"].items():
                assert sha(z.read(prefix+name))==h,(flop,name)
            rootbytes=z.read(prefix+"flop/result.json")
            assert sha(rootbytes)==pf["root_sha256"]
            native=json.loads(rootbytes)
            job=json.loads(z.read(prefix+"flop/job.json"))
            assert sha(compact(job))==pf["root_job_sha256"]
            assert cards(native["flop"])==cards(flop)
            assert (native["pot"],native["stack"],job["pot"],job["stack"])==(250,9900,250,9900)
            assert 0<=native["info"]["gto_expl_pct"]<=.5 and not native["info"].get("lock_stats")
            assert [r["turn"] for r in pf["turns"]]==spec[3]
            verified=[]
            for tr in pf["turns"]:
                _,legal,diagnostic=r29.root_gate(native,tr["turn"],route)
                assert diagnostic==tr["root_gate"] and not legal
                assert tr["negative_stage"]=="ROOT_TWO_SEAT_UI_INTERSECTION_ZERO"
                assert not tr["gto_solved"] and not tr["actor_locked"] and not tr["checks"]
                verified.append(dict(turn=tr["turn"],stage=tr["negative_stage"],diagnostic=diagnostic))
            rows.append(dict(flop=flop,root_sha256=pf["root_sha256"],root_gap_pct=native["info"]["gto_expl_pct"],turns=verified,
                classification="BLOCKED_NATIVE_ROOT_TWO_SEAT_UI_INTERSECTION_ZERO",no_repeat_root=True,
                no_claim_about_untested_turns=True))
        name="b899-"+flop+".zip"
        (root/name).write_bytes(raw);meta[name]=a
    dump(root/"classification.json",dict(rank=29,coverage=cov,rows=rows,native_solves_this_batch=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
    dump(root/"receipts.json",dict(runs=runs,artifacts=meta))
    files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())}
    dump(out/"prepared.json",dict(parent=parent,files=files,coverage=cov,native_solves=0,cert_promotions=0))
    print(json.dumps({"rank":29,"verified_negative_flops":len(rows),"fixed_turns":sum(len(r["turns"]) for r in rows),"coverage":cov}))
def rank57(out):
    guard();cov=coverage()
    runs=completed((45527191880,45527191595,45721198494,45721198403))
    route=json.loads(subprocess.check_output(["node","tools/hu_b617_sb_routes.cjs"]))["57"]
    assert route["paired"]["turn"]==["TPG"] and route["paired"]["river"]=={"TPG":"下注 ¾"}
    rows=[];meta={}
    for flop,spec in R57.items():
        raw,a=artifact(spec);meta[flop]=a
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            pf=read(z,"proof.json")
            assert (pf["rank"],pf["model_id"],pf["flop"],pf["line"])==(57,r57.MODEL,flop,r57.LINE)
            assert (pf["actual_river_pot_bb"],pf["actual_river_effective_stack_bb"])==(30,85)
            assert [r["turn"] for r in pf["turns"]]==spec[3]
            native=read(z,"flop/result.json")
            job=read(z,"flop/job.json")
            assert sha(compact(native))==pf["root_sha256"]
            assert (native["flop"],native["pot"],native["stack"],job["pot"],job["stack"])==(flop,600,9700,600,9700)
            assert 0<=native["info"]["gto_expl_pct"]<=.5 and not native["info"].get("lock_stats")
            details=[]
            for tr in pf["turns"]:
                t=tr["turn"]
                g=read(z,t+"-gto/result.json")
                gj=read(z,t+"-gto/job.json")
                assert (g["flop"],g["pot"],g["stack"],gj["pot"],gj["stack"])==(flop,1200,9400,1200,9400)
                assert 0<=g["info"]["gto_expl_pct"]<=.5 and not g["info"].get("lock_stats")
                rivers=[n["board"][-2:] for n in g["nodes"] if (n["line"],n["player"])==(r57.LINE,0)]
                gm=r57.hands_for(native,g,t,rivers,route)
                common={};lm={}
                if gm:
                    e=read(z,t+"-exp_oop/result.json");ej=read(z,t+"-exp_oop/job.json")
                    assert (e["flop"],e["pot"],e["stack"],ej["pot"],ej["stack"])==(flop,1200,9400,1200,9400)
                    assert 0<=e["info"]["gto_expl_pct"]<=.5 and 0<=e["info"]["hero_gap_pct"]<=.5 and e["info"]["lock_stats"]
                    lm=r57.hands_for(native,e,t,rivers,route)
                    common={b:sorted(gm[b][0]&lm[b][0]) for b in gm.keys()&lm.keys() if gm[b][0]&lm[b][0]}
                    assert tr["paired_policies"]
                else:
                    assert not tr["paired_policies"]
                assert not common and not tr["checks"]
                details.append(dict(turn=t,gto_displayed_boards=len(gm),nl2_displayed_boards=len(lm),
                    gto_displayed_hero_combos=sum(len(v[0]) for v in gm.values()),
                    nl2_displayed_hero_combos=sum(len(v[0]) for v in lm.values()),
                    failure_stage="GTO_DISPLAYED_ACTION_ZERO" if not gm else ("NL2_DISPLAYED_ACTION_ZERO" if not lm else "GTO_NL2_HERO_INTERSECTION_ZERO"),
                    shared_hero_boards=0))
            rows.append(dict(flop=flop,root_sha256=pf["root_sha256"],source_artifact_sha256=spec[2],turns=details))
    out.mkdir(parents=True,exist_ok=False)
    report=dict(rank=57,coverage=cov,rows=rows,runs=runs,artifacts=meta,native_solves=0,cert_promotions=0,
        scope="Existing B840/B877 fixed boundaries only; no declaration of exhaustion, no same-deal positives, no native redispatch.")
    dump(out/"rank57-diagnostic.json",report)
    print(json.dumps({"rank":57,"flops":len(rows),"fixed_turns":sum(len(r["turns"]) for r in rows),
        "stages":[{"flop":r["flop"],"stages":[t["failure_stage"] for t in r["turns"]]} for r in rows]}))
if __name__=="__main__":
    mode=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if mode=="upload":
        archive.BASE=BASE;archive.PREFIX=PREFIX;archive.upload(out)
    else:
        {"rank29":rank29,"rank57":rank57}[mode](out)
