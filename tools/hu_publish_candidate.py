"""Create a verified-data commit object, optionally with the frozen B674 prices.

The branch is never moved here. The caller must inspect the successful Actions
run and candidate commit, then publish it with a fast-forward lease.
"""
import argparse
import base64
import glob
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

REPOSITORY = "tetracycline/poker-trainer"
BRANCH = "fix/nl2-hu-lines-audit-20261118"


def git(*arguments):
    return subprocess.check_output(["git", *arguments])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", required=True)
    parser.add_argument("--paths", nargs="+", required=True)
    parser.add_argument("--priced-model", action="store_true")
    args = parser.parse_args()
    assert os.environ["GITHUB_REPOSITORY"] == REPOSITORY
    head = os.environ["GITHUB_SHA"]
    assert re.fullmatch(r"[0-9a-f]{40}", head)
    assert git("rev-parse", "HEAD").decode().strip() == head
    token = os.environ["GH_TOKEN"]

    def api(method, resource, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            "https://api.github.com/repos/" + REPOSITORY + "/" + resource,
            data=body, method=method,
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28",
                     "Content-Type": "application/json",
                     "User-Agent": "nl2-verified-candidate"})
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)

    def check_head():
        pull = api("GET", "pulls/2")
        assert pull["draft"] and pull["state"] == "open" and not pull["merged"]
        assert pull["head"]["repo"]["full_name"] == REPOSITORY
        assert (pull["head"]["ref"], pull["head"]["sha"]) == (BRANCH, head)

    check_head()
    selected = []
    for pattern in args.paths:
        matches = sorted(glob.glob(pattern))
        assert matches, "No verified output matches " + pattern
        selected.extend(matches)
    selected = sorted(set(selected))
    root = Path.cwd().resolve()
    pinned_code = {
        "nl2_hu_model.js": "a98cb80d7762b464064874de39dcff6f4bf5707d",
        "nl2.js": "15aee97e53a156fe073c96a120638a8a3679958f",
    }
    if args.priced_model:
        assert set(pinned_code) <= set(selected), "Both frozen price files are required"
        for name, expected in pinned_code.items():
            assert git("hash-object", name).decode().strip() == expected
    for name in selected:
        path = Path(name)
        assert (name.startswith("data/") or (args.priced_model and name in pinned_code))
        assert ".." not in path.parts
        assert path.is_file() and not path.is_symlink()
        assert path.resolve().is_relative_to(root)
    assert not git("diff", "--cached", "--name-only").strip(), "Index was not clean"
    subprocess.run(["git", "add", "--", *selected], check=True)
    changed = git("diff", "--cached", "--name-status").decode().splitlines()
    assert changed, "No new verified evidence to publish"
    assert all(line.split("\t", 1)[0] in {"A", "M"} for line in changed)
    assert all(line.split("\t", 1)[1] in selected for line in changed)

    elements = []
    for row in git("diff", "--cached", "--raw", "--no-abbrev").decode().splitlines():
        metadata, path = row.split("\t")
        oldmode, mode, oldsha, sha, status = metadata.split()
        assert mode == "100644" and status in {"A", "M"}
        raw = git("cat-file", "blob", sha)
        blob = api("POST", "git/blobs",
                   {"encoding": "base64", "content": base64.b64encode(raw).decode()})
        assert blob["sha"] == sha
        elements.append({"path": path, "mode": mode, "type": "blob", "sha": sha})
    parent = api("GET", "git/commits/" + head)
    tree = api("POST", "git/trees", {"base_tree": parent["tree"]["sha"], "tree": elements})
    assert tree["sha"] == git("write-tree").decode().strip()
    check_head()
    commit = api("POST", "git/commits",
                 {"message": args.message, "tree": tree["sha"], "parents": [head]})
    assert len(commit["parents"]) == 1 and commit["parents"][0]["sha"] == head
    print("CANDIDATE_COMMIT=" + commit["sha"], flush=True)
    print("CANDIDATE_PARENT=" + head, flush=True)
    print("CANDIDATE_TREE=" + tree["sha"], flush=True)
    print("CANDIDATE_PATHS=" + json.dumps([item["path"] for item in elements]), flush=True)


if __name__ == "__main__":
    main()
