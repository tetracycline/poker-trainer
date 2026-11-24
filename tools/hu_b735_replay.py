"""Verify the archived rank 128 lock against the original SB/BB GTO root and turn."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b734_rank128 import (
    AID, MODEL, PIN, POOL, RANGES, PIPELINE, ROUTES, SOLVER, audit_patterns,
    inspect, json_bytes, original, prepare_job, sha,
)


def replay(folder, solver):
    assert sys.version_info[:2] == (3, 11)
    assert subprocess.check_output(["git", "-C", solver, "rev-parse", "HEAD"], text=True).strip() == SOLVER
    native = solver / "postflop/py"
    assert sha((native / "pipeline.py").read_bytes()) == PIPELINE
    assert sha((native / "ranges.py").read_bytes()) == RANGES
    sys.path.insert(0, str(native))
    import pipeline
    import ranges

    inputs = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(inputs) == POOL
    pool = json.loads(inputs)["NL2"]
    receipt = json.loads((folder / "receipts.json").read_bytes())
    expected = {
        "old": (AID, PIN["run"], 136288829082, PIN["head"], PIN["sha256"]),
        "new": (14890829716, 45330359823, 138229827192, "64469a63c1fb524b16a5d5ccf2e0093f293fe072",
                "4847b5b8c0caf6c377dfbd9e4a243182615324700071f4ee7f3475ac5ac1936a"),
    }
    for key, (aid, rid, jid, head, digest) in expected.items():
        artifact, run, job = (receipt[f"{key}_{part}"] for part in ("artifact", "run", "job"))
        assert (run["id"], job["run_id"], job["id"], job["head_sha"], job["conclusion"]) == (rid, rid, jid, head, "success")
        assert artifact["workflow_run"]["id"] == rid and artifact["workflow_run"]["repository_id"] == 1438346845
        assert (artifact["id"], artifact["workflow_run"]["head_sha"], run["head_sha"], artifact["digest"]) == (aid, head, head, "sha256:" + digest)
        raw = (folder / f"{aid}.zip").read_bytes()
        assert len(raw) == artifact["size_in_bytes"] and sha(raw) == digest
    assert receipt["new_run"]["conclusion"] == "success"
    with TemporaryDirectory() as work:
        temp = Path(work)
        (temp / f"{AID}.zip").symlink_to((folder / f"{AID}.zip").resolve())
        (temp / f"{AID}.json").write_bytes(json_bytes(receipt["old_artifact"]))
        source = original(temp, ranges)
    with ZipFile(folder / "14890829716.zip") as archive:
        assert set(archive.namelist()) == {"exp_ip/job.json", "exp_ip/result.json", "proof.json", "rendered-routes.json"}
        job_raw, result_raw = (archive.read("exp_ip/" + f + ".json") for f in ("job", "result"))
        route_raw = archive.read("rendered-routes.json")
        assert subprocess.check_output(["node", ROUTES]) == route_raw
        actual = json.loads(archive.read("proof.json"))
    route = json.loads(route_raw)
    assert route["model"] == MODEL
    root = source["source"]["root"]
    locked = json.loads(result_raw)
    job, rules = prepare_job(source, "exp_ip", pool, pipeline)
    job["out"] = "result.json"
    assert json.loads(job_raw) == job and job["hero"] == 1 and job["locks"]
    assert locked["hands"] == source["source"]["subgame"]["hands"]
    assert 0 <= locked["info"]["hero_gap_pct"] <= .5 and 0 <= locked["info"]["gto_expl_pct"] <= .5
    applied = audit_patterns(locked, job, dict(locks=rules), pool, 1)
    assert applied == actual["applied_measured_lock"] and locked["info"]["lock_stats"]
    assert any(v > 0 for k, v in applied["driver_tree_nodes"].items() if k in applied["marginal_targets"])
    before = inspect(root, source["source"]["subgame"], route)
    after = inspect(root, locked, route)
    assert before == actual["gto"] and after == actual["nl2"] and source["identity"] == actual["existing_gto"]
    assert (sha(job_raw), sha(result_raw), sha(route_raw)) == (actual["nl2_job_sha256"], actual["nl2_source_sha256"], actual["rendered_route_sha256"])
    boards = []
    for board in sorted(before):
        gto, nl2 = before[board], after[board]
        common = sorted(set(gto["displayed_check_hands"]) & set(nl2["displayed_check_hands"]))
        assert common == actual["same_displayed_hands_by_public_board"][board]
        reach = nl2["reach"]
        assert reach["compatible_hole_card_pairs"] >= reach["strict_legal_combos"] > 0 and reach["b50"] is not None
        boards.append(dict(board=board, gto_displayed_check_hands=gto["displayed_check_hands"],
                           nl2_displayed_check_hands=nl2["displayed_check_hands"], shared_hands=common,
                           nl2_compatible_pairs=reach["compatible_hole_card_pairs"], nl2_nonpolarized_candidate=bool(reach["b50"]["candidate"])))
    counts = dict(positive_distinct_flops=int(any(b["shared_hands"] for b in boards)), native_locked_public_boards=len(boards),
                  joint_halfpot_assessed=len(boards), nonpolarized_candidates=sum(b["nl2_nonpolarized_candidate"] for b in boards))
    assert all(actual[k] == v for k, v in counts.items())
    assert list(counts.values()) == [0, 2, 2, 1]
    return dict(rank=128, model=MODEL, flop="KsQh4d", turn="Tc", boards=boards, **counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", required=True, type=Path)
    parser.add_argument("--folder", type=Path, default=Path("data/solver_evidence/partial/b735"))
    parser.add_argument("--write-summary", action="store_true")
    args = parser.parse_args()
    result = json_bytes(replay(args.folder, args.solver.resolve()))
    target = args.folder / "summary.json"
    if args.write_summary:
        target.write_bytes(result)
    else:
        assert target.read_bytes() == result
    print("rank 128: 2 locked, 2 joint half-pot assessments, 1 candidate, 0 paired original flops")
