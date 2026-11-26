"""B899: source-blind first two B898 static-positive rank29 flops.
Original solves only after historical source/dispatch dedup. Candidate only.
"""
import argparse, io, itertools, json, os, re, subprocess, zipfile
from pathlib import Path
import hu_b703_rank29_highcards as base
import hu_b898_rank29_static_cohort as cohort
from hu_b895_archive_r158 import coverage
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b467_river_source_gate import json_bytes

PARENT="2923d7bbb2da193f6f3b39fdd2543f48cd797a39"
B898="07cf79e6df3336a3f65c36638d578e63a68308b7"
RUN=45894207896
AUDIT=45894207828
ART=15153306263
DIGEST="f210b8147f0b3ee93430ad32bb1422910ce477f3a24ea6415273d75d762284a5"
FLOPS=("Ac3c2h","Ac3h2c")
APP=cohort.APP
SELF={"tools/hu_b899_rank29_cohort_native.py",".github/workflows/nl2-hu-b899-rank29-cohort-native.yml","docs/NL2_HU_B899_RANK29_COHORT_NATIVE.md"}

def guard():
    assert os.environ["GITHUB_REPOSITORY"]==REPO
    assert os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    head=os.environ["GITHUB_SHA"]
    assert git("rev-parse","HEAD")==head and git("rev-parse","HEAD^")==PARENT
    assert set(git("diff","--name-only",PARENT,head).splitlines())==SELF
    p=api("/pulls/2")
    assert p["state"]=="open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==(REPO,BRANCH,head)
    return head

def frozen_cohort():
    for rid in (RUN,AUDIT):
        r=api("/actions/runs/"+str(rid))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(B898,BRANCH,"completed","success")
    a=api("/actions/artifacts/"+str(ART))
    assert not a["expired"] and a["digest"]=="sha256:"+DIGEST
    assert a["workflow_run"]["id"]==RUN and a["workflow_run"]["head_sha"]==B898
    raw=api("/actions/artifacts/"+str(ART)+"/zip",raw=True)
    assert sha(raw)==DIGEST
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        names=[n for n in z.namelist() if n.endswith("report.json")]
        assert len(names)==1
        report=json.loads(z.read(names[0]))
    assert report["rank"]==29 and report["native_solves"]==report["cert_promotions"]==0
    assert report["coverage"]==coverage()
    assert tuple(report["selected_before_evaluation"][:2])==FLOPS
    assert len({cohort.iso(f) for f in FLOPS})==2
    return report

def variants(flop):
    cs=[flop[i:i+2] for i in (0,2,4)]
    ss=sorted({c[1] for c in cs})
    out=set()
    for suits in itertools.permutations("cdhs",len(ss)):
        m=dict(zip(ss,suits))
        for cards in itertools.permutations([c[0]+m[c[1]] for c in cs]):
            out.add("".join(cards).lower())
    return sorted(out)

def historical_dispatch(flop):
    # All ancestors of the exact authorized parent, including removed/changed
    # workflows and code. Do not search other branches or rerun any old jobs.
    vs=variants(flop)
    pattern="|".join(v for v in vs)
    history=git("log","--format=%H","--regexp-ignore-case","-G",pattern,PARENT,"--",".github/workflows","tools")
    assert not history,("historical dispatch lead: do not solve",history)
    # Check names of historical workflow artifacts (including expired entries
    # still listed); fail closed if the listing cannot be completed.
    count=0; ids=set(); hits=[]; first_total=None
    for page in range(1,101):
        a=api("/actions/artifacts?per_page=100&page="+str(page))
        if first_total is None:first_total=a["total_count"]
        rows=a["artifacts"]
        for row in rows:
            assert row["id"] not in ids, "artifact listing shifted; do not dispatch"
            ids.add(row["id"])
            n=re.sub(r"[^a-z0-9]","",row["name"].lower())
            if any(v in n for v in vs):hits.append({"id":row["id"],"name":row["name"]})
        count+=len(rows)
        if len(rows)<100:break
    else:raise RuntimeError("artifact inventory not exhausted")
    assert count>=first_total,("incomplete artifact inventory",count,first_total)
    assert not hits,("historical artifact lead: do not solve",hits)
    return dict(history_matches=[],artifact_name_matches=[],artifact_metadata_rows=count,
                historical_ref=PARENT,limitations="Expired unlisted sources or unrecorded dispatches cannot be excluded.")

def preflight(a):
    head=guard()
    report=frozen_cohort()
    row,=[r for r in report["rows"] if r["flop"]==a.flop]
    assert row["status"]=="STATIC_POSITIVE_REQUIRES_FULL_HISTORICAL_DISPATCH_REVIEW"
    assert not row["can_dispatch_native"]
    w=row["witness"]
    # Source-blind fixed maximum four suited turns; first the authenticated
    # static witness turn, then the original cohort enumeration order.
    turns=[w["turn"]]+[t for t in row["all_suited_turns"] if t!=w["turn"]][:3]
    assert len(turns)==len(set(turns))==4
    dedup=historical_dispatch(a.flop)
    # The original cohort checked retained source bytes at B898. Since then
    # only the five B898 receipt files and the three new dispatch files exist.
    delta=set(git("diff","--name-only",B898,PARENT).splitlines())
    assert len(delta)==5 and all(p.startswith("data/solver_evidence/b898_boundary_receipts/") for p in delta)
    for p in delta:
        raw=Path(p).read_bytes()
        if p.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                raw=b"".join(z.read(n) for n in z.namelist() if not n.endswith("/"))
        assert not any(v.encode() in raw.lower() for v in variants(a.flop)),p
    receipt=dict(head=head,flop=a.flop,turns=turns,witness=w,cohort_artifact=ART,
                 cohort_sha256=DIGEST,dedup=dedup,coverage=report["coverage"],candidate_only=True)
    a.receipt.write_bytes(json_bytes(receipt))
    print(json.dumps(receipt,sort_keys=True))
    return receipt

def main(a):
    if a.preflight:
        r=preflight(a)
    else:
        r=json.loads(a.receipt.read_bytes())
        assert r["head"]==os.environ["GITHUB_SHA"] and r["flop"]==a.flop
        assert r["cohort_sha256"]==DIGEST and r["candidate_only"]
        if a.driver:guard()
    w=r["witness"]
    old=(base.CASES,base.RANGE_WITNESSES,base.APP_PINS)
    try:
        base.CASES={a.flop:r["turns"]}
        base.RANGE_WITNESSES={a.flop:(w["turn"],w["river"],w["hero"],w["villain"])}
        base.APP_PINS=APP
        base.run(a)
    finally:
        base.CASES,base.RANGE_WITNESSES,base.APP_PINS=old
    if not a.preflight:
        p=a.output/"proof.json"
        proof=json.loads(p.read_bytes())
        proof.update(schema="NL2_B899_R29_COHORT_NATIVE_CANDIDATE_V1",
                     historical_preflight_sha256=sha(a.receipt.read_bytes()),
                     cohort_artifact_sha256=DIGEST,not_a_certification=True,
                     independent_same_two_physical_hands_gate_pending=True)
        p.write_bytes(json_bytes(proof))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("solver","output","receipt"):p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--flop",choices=FLOPS,required=True)
    p.add_argument("--driver",type=Path)
    p.add_argument("--preflight",action="store_true")
    main(p.parse_args())
