"""B898: retain completed B896 static screens and B897 blocked original.
No native driver, no registry mutation, and no ref update in Actions.
"""
import base64, hashlib, io, json, os, sys, zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage

BASE = "a5a9ec9b5ee15a5c73734011ad5a083686731a11"
B896 = "058555083b0473acfbfca621fc28968375bae6fd"
PREFIX = "data/solver_evidence/b898_boundary_receipts/"
RUNS = {
    45879893776: (B896, "success"),
    45879893560: (B896, "success"),
    45886968636: (BASE, "failure"),
    45886968547: (BASE, "success"),
}
ARTS = {
    "b896-boundaries.zip": (15145804448, 45879893776, "707a79f3c6e9181cbaa0dbdb9b4b45852b41a80c15e6a1642a894fc15c369c49"),
    "b897-blocked-receipt.zip": (15149093754, 45886968636, "d668aa597a5b8d51f2ff59e71db7011376c33c2e3ba95db9f4623b0e50c2ecd8"),
}
JOB = 140139967714

def dump(p, obj):
    p.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n")

def guard():
    parent = os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"] == REPO
    assert os.environ["GITHUB_REF"] == "refs/heads/" + BRANCH
    assert git("rev-parse", "HEAD") == parent
    assert git("rev-parse", "HEAD^") == BASE
    p = api("/pulls/2")
    assert p["state"] == "open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"], p["head"]["ref"], p["head"]["sha"]) == (REPO, BRANCH, parent)
    return parent

def prepare(out):
    parent = guard()
    cov = coverage()
    assert not git("status", "--porcelain")
    root = Path(PREFIX)
    root.mkdir(parents=True, exist_ok=False)
    out.mkdir(parents=True, exist_ok=False)
    runs, meta = {}, {}
    for rid, (head, conclusion) in RUNS.items():
        r = api("/actions/runs/" + str(rid))
        assert (r["head_sha"], r["head_branch"], r["status"], r["conclusion"]) == (head, BRANCH, "completed", conclusion)
        runs[str(rid)] = r
    for name, (aid, rid, digest) in ARTS.items():
        a = api("/actions/artifacts/" + str(aid))
        assert not a["expired"] and a["digest"] == "sha256:" + digest
        assert a["workflow_run"]["id"] == rid
        assert a["workflow_run"]["head_sha"] == RUNS[rid][0]
        raw = api("/actions/artifacts/" + str(aid) + "/zip", raw=True)
        assert sha(raw) == digest
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
        (root / name).write_bytes(raw)
        meta[name] = a
    with zipfile.ZipFile(root / "b896-boundaries.zip") as z:
        reports = sorted(n for n in z.namelist() if n.endswith("/report.json"))
        assert len(reports) == 2, reports
        one, two = (z.read(n) for n in reports)
        assert one == two
        report = json.loads(one)
        assert report["native_solves"] == report["original_flop_solves_repeated"] == report["CERT_promotions"] == 0
        assert report["CERT"] == 158 and report["APPROX"] == 234
        assert {(r["rank"], r["turn"]) for r in report["rows"]} == {(157,"4h"),(157,"Kd"),(158,"4h"),(158,"Kd")}
        for r in report["rows"]:
            assert r["flop"] == "Jh9s4c" and r["status"] == "NO_STATIC_CHECK_WITNESS"
            assert not r["static_check_river_candidates"] and not r["raw_exact_hits"]
            assert not r["can_dispatch_native"]
        (root / "b896-report.json").write_bytes(one)
    j = api("/actions/jobs/" + str(JOB))
    assert (j["id"], j["run_id"], j["head_sha"], j["conclusion"]) == (JOB,45886968636,BASE,"failure")
    steps = {s["name"]:s["conclusion"] for s in j["steps"]}
    assert steps["Authenticate skipped original job and preflight fixed legal physical witness and dedup"] == "failure"
    assert steps["Build pinned driver after preflight"] == steps["Solve only the never-executed original and replay without driver"] == "skipped"
    with zipfile.ZipFile(root / "b897-blocked-receipt.zip") as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        assert len(names) == 1 and names[0].endswith("b897-job.json"), names
        prior = json.loads(z.read(names[0]))
        assert (prior["id"],prior["run_id"],prior["conclusion"]) == (139691797892,45755111223,"failure")
        old_steps = {s["name"]:s["conclusion"] for s in prior["steps"]}
        assert old_steps["Solve original GTO and authentic matched NL2 partial lock, independent file replay"] == "skipped"
    dump(root / "receipts.json", dict(runs=runs,artifacts=meta,blocked_job=j))
    dump(root / "classification.json", dict(
        rank=29, flop="Jd9d3c", fixed_turns=["2d","4d","5d","7d"],
        classification="BLOCKED_STATIC_RANGE_UI_WITNESS",
        logged_error="NO_STATIC_RANGE_UI_WITNESS: no native dispatch",
        native_solves=0, source_not_a_native_negative=True, no_repeat_fixed_boundary=True,
        prior_rank157_158_static_only_rows=4, cert_promotions=0, formal_lock_additions=0,
        formal_nonpolarized_additions=0, coverage=cov))
    files = {str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())}
    dump(out / "prepared.json", dict(parent=parent, files=files, coverage=cov, native_solves=0, cert_promotions=0))

def upload(out):
    parent=guard()
    coverage()
    p=json.loads((out/"prepared.json").read_bytes())
    assert p["parent"]==parent and p["native_solves"]==p["cert_promotions"]==0
    assert not git("diff","--name-only")
    entries=[]
    for path,h in p["files"].items():
        assert path.startswith(PREFIX)
        b=Path(path).read_bytes()
        assert sha(b)==h
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        actual=api("/git/blobs",{"content":base64.b64encode(b).decode(),"encoding":"base64"})["sha"]
        assert actual==expected
        entries.append({"path":path,"mode":"100644","type":"blob","sha":actual})
    tree=api("/git/trees",{"base_tree":api("/git/commits/"+parent)["tree"]["sha"],"tree":entries})["sha"]
    c=api("/git/commits",{"message":"B898 archive authenticated B896 boundaries and B897 blocked preflight; no CERT promotion","tree":tree,"parents":[parent]})
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[parent]
    receipt=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=parent,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",receipt)
    print(json.dumps(receipt,indent=2))

if __name__=="__main__":
    {"prepare":prepare,"upload":upload}[sys.argv[1]](Path(sys.argv[2]).resolve())
