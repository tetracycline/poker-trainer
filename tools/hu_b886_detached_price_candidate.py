#!/usr/bin/env python3
"""B886: replay the completed B885 candidate and prepare a detached commit.
No solver calls, no ref update, no force push. Publication needs an external
expected_sha lease after this workflow and the full batch audit pass.
"""
import base64
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile
import io
from decimal import Decimal

REPO = "tetracycline/poker-trainer"
BRANCH = "fix/nl2-hu-lines-audit-20261118"
B885 = "716023f2732ebc9f109a5229f2c5d8a99dfb2e06"
RUN = 45779110492
AUDIT = 45779110405
ARTIFACT = 15098001087
ZIP_SHA = "6bf78f58bbf36e4a66da5b6bd3d41c5da8b826c6d1d07c2567bf7c84927d5244"
PIN = "data/solver_evidence/reverified/rank68.json"
PIN_SHA = "3ee6335964b565ef2ea3e4858eb73f3c6942fa59d85555c3e5c3e402d4c06e13"
STATUS = "data/nl2_hu_multiboard_status_current.json"
FILES = {
    "data/nl2_hu_model_history_crosswalk.json": "772f79273de1a7288bc71c6aca452f26353baa139753163471885eeacb7d8405",
    "data/nl2_hu_model_source_references.json": "44c1038d3b15682aeb7032c9cd21131cf978b5815f7c663a3f8b5f5d3c9185af",
    STATUS: "7c40158fdb39b2ae1bc698b364665045b17c07f2dacdc93c2bf39af28f1106d6",
    "data/nl2_hu_verified_extensions.json": "3f3c023f55153fc21ce9ef608a2d639859fb5d36552f943b6c9249c53ee79808",
    "nl2_cert_registry.js": "8e4a87d26d04e34232c0a1729f33849b18e80a976bc87d0f959a7c24277d4e85",
    "nl2_hu_model.js": "671c2160dabdcb9216534e17fe70ce17208010b105052eb87e48f4e81bf00c40",
    "tools/hu_apply_cert_extensions.py": "e4e48be36d168c060c248548827a57b25bb8a49cb5aef0bf34905edef65fe0ee",
}
TARGETS = {"ln-opfr-t_model-19umlco": (68, 7.25),
           "ln-opfr-r_model-1puypid": (157, 2.6),
           "ln-opfr-r_model-tl6ij8": (158, 4.151),
           "ln-opfr-r_model-8w3cpr": (205, 7.25)}

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def git(*args): return subprocess.check_output(["git", *args], text=True).strip()
def call(*args): subprocess.run(args, check=True)
def api(path, body=None, raw=False):
    url = "https://api.github.com/repos/" + REPO + path
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json", "User-Agent": "NL2-B886-candidate"})
    # Do not forward the repository token to the artifact storage host.
    class SafeRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            out = super().redirect_request(req, fp, code, msg, headers, newurl)
            if out is not None and not newurl.startswith("https://api.github.com/"):
                out.remove_header("Authorization")
            return out
    with urllib.request.build_opener(SafeRedirect()).open(req, timeout=120) as response:
        b = response.read()
    return b if raw else json.loads(b)

def guard():
    parent = os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"] == REPO
    assert os.environ["GITHUB_REF"] == "refs/heads/" + BRANCH
    assert git("rev-parse", "HEAD") == parent
    assert git("rev-parse", "HEAD^") == B885
    p = api("/pulls/2")
    assert p["state"] == "open" and p["draft"] and not p["merged"]
    assert p["head"]["repo"]["full_name"] == REPO
    assert p["head"]["ref"] == BRANCH and p["head"]["sha"] == parent
    return parent

def prepare(out):
    parent = guard()
    assert not git("status", "--porcelain")
    for run in (RUN, AUDIT):
        j = api("/actions/runs/" + str(run))
        assert (j["head_sha"], j["status"], j["conclusion"]) == (B885, "completed", "success")
    a = api("/actions/artifacts/" + str(ARTIFACT))
    assert not a["expired"] and a["name"] == "B885-atomic-price-candidate"
    assert a["workflow_run"]["id"] == RUN and a["workflow_run"]["head_sha"] == B885
    assert a["digest"] == "sha256:" + ZIP_SHA
    raw = api("/actions/artifacts/" + str(ARTIFACT) + "/zip", raw=True)
    assert sha(raw) == ZIP_SHA
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        report = json.loads(z.read("report.json"))
        patch = z.read("candidate.patch")
    assert report["candidate_only"] and report["candidate_file_sha256"] == FILES
    assert report["source_pin_sha256"] == PIN_SHA
    assert report["unchanged_records"] == 388
    assert all(report[k] == 0 for k in ("native_solves","new_cert","new_locks","new_medium"))
    assert sha(Path(PIN).read_bytes()) == PIN_SHA
    before = read(STATUS)
    out.mkdir(parents=True, exist_ok=True)
    (out / "b885-candidate.patch").write_bytes(patch)
    (out / "b885-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    call("git","apply","--check",str(out/"b885-candidate.patch"))
    call("git","apply",str(out/"b885-candidate.patch"))
    after = read(STATUS)
    assert set(before["records"]) == set(after["records"])
    assert len(after["records"]) == 392
    assert collections.Counter(x["label"] for x in after["records"].values()) == {"CERT-MULTIBOARD":158,"APPROX":234}
    for key, old in before["records"].items():
        new = after["records"][key]
        if key not in TARGETS:
            assert old == new
        else:
            rank, spr = TARGETS[key]
            assert old["label"] == new["label"]
            assert (new["frequency_rank"],new["assumed_model_node_spr"]) == (rank,spr)
    assert before["all_cert_lock_medium"] == after["all_cert_lock_medium"]
    assert before["exact_source_extensions"] == after["exact_source_extensions"]
    weights = {x["model_id"]:Decimal(str(x["estimated_NL2_hand_opportunity_fraction"]))
               for x in read("data/nl2_hu_multiboard_prerank.json")["nodes"]}
    assert set(weights) == set(after["records"])
    coverage = round(100*sum(weights[k] for k,v in after["records"].items()
                     if v["label"]=="CERT-MULTIBOARD")/sum(weights.values()),6)
    high = sum(v["label"]=="APPROX" and weights[k]>=Decimal("0.002") for k,v in after["records"].items())
    assert coverage == Decimal("84.700987") and high == 30
    assert set(git("diff","--name-only").splitlines()) == set(FILES)
    for p, h in FILES.items(): assert sha(Path(p).read_bytes()) == h, p
    (out/"prepare.json").write_text(json.dumps({"parent":parent,"source_zip_sha256":ZIP_SHA,
        "cert":158,"approx":234,"coverage_pct":str(coverage),"high":high,
        "changed_files":FILES,"unchanged_records":388,"native_solves":0},indent=2)+"\n")

def upload(out):
    parent = guard()
    prepared = read(out/"prepare.json")
    assert prepared["parent"] == parent and prepared["changed_files"] == FILES
    assert sha(Path(PIN).read_bytes()) == PIN_SHA
    assert set(git("diff","--name-only").splitlines()) == set(FILES)
    entries = []
    for p,h in FILES.items():
        b = Path(p).read_bytes()
        assert sha(b) == h,p
        expected = hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        actual = api("/git/blobs",{"content":base64.b64encode(b).decode(),"encoding":"base64"})["sha"]
        assert actual == expected,p
        entries.append({"path":p,"mode":"100644","type":"blob","sha":actual})
    base = api("/git/commits/"+parent)["tree"]["sha"]
    tree = api("/git/trees",{"base_tree":base,"tree":entries})["sha"]
    c = api("/git/commits",{"message":"B886 publish audited exact UTG price reconciliation (zero new CERT)",
                            "tree":tree,"parents":[parent]})
    assert c["tree"]["sha"] == tree and [p["sha"] for p in c["parents"]] == [parent]
    # No refs API mutation. The external controller must verify this candidate
    # and workflow, then update the existing ref with expected_sha and force=false.
    receipt = dict(prepared, candidate_commit=c["sha"], candidate_tree=tree, blobs=entries,
                   expected_sha=parent, ref_updated=False, candidate_only=True,
                   full_audit_completed=True)
    (out/"detached-candidate.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))

if __name__ == "__main__":
    {"prepare":prepare,"upload":upload}[sys.argv[1]](Path(sys.argv[2]).resolve())
