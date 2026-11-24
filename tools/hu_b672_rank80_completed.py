"""Authenticate four completed B671 workers without re-solving unreachable lines."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

from hu_sequential_cfr_reach import accepted

RUN = 45273794759
HEAD = "443e1d47385175a081b8c382b3e43b99ac9e9b18"
SOLVER = "abe310c3aad02dd4a7c77fb2831801fd490cf51b"
MODEL = "ln-iso-lmp_r_model-17pklmg"
LINE = "b33 c/x x/x"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def compact(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()


def verify(args):
    assert subprocess.check_output(["git", "-C", args.solver, "rev-parse", "HEAD"], text=True).strip() == SOLVER
    report = json.loads(args.report.read_bytes())
    assert (report["rank"], report["model_id"], report["status"], report["worker_run_id"], report["worker_head"]) == (
        80, MODEL, "APPROX", RUN, HEAD)
    assert (report["original_flop_solves"], report["checked_turn_boundaries"],
            report["valid_distinct_flops"], report["lock_solves"], report["medium_assessments"]) == (4, 24, 0, 0, 0)
    assert len(report["records"]) == 4
    assert {r["flop"] for r in report["records"]} == {"As9s4d", "Jh8h3d", "Qs7s2d", "AcTc5h"}
    template = Path("data/solver_evidence/NL2_B580_R27_LMP.zip").read_bytes()
    assert sha(template) == "d4b98b4351012d78aa62f3cd31b75228d4f7a35725584d86f633552fbf28369a"
    with ZipFile(io.BytesIO(template)) as archive:
        root_template = json.loads(archive.read("original-flop.job.json"))
    for spec in report["records"]:
        flop = spec["flop"]
        receipt = json.loads((args.originals / (str(spec["artifact_id"]) + ".json")).read_bytes())
        identity = receipt["workflow_run"]
        assert (receipt["id"], receipt["name"], identity["id"], identity["head_sha"], identity["repository_id"]) == (
            spec["artifact_id"], "B671-R80-" + flop, RUN, HEAD, 1438346845)
        raw = (args.originals / (str(spec["artifact_id"]) + ".zip")).read_bytes()
        assert receipt["digest"] == "sha256:" + sha(raw)
        assert sha(raw) == spec["artifact_sha256"]
        with ZipFile(io.BytesIO(raw)) as archive:
            expected = {"proof.json", "flop/job.json", "flop/result.json"}
            assert set(archive.namelist()) == expected and len(archive.namelist()) == len(expected)
            claim = json.loads(archive.read("proof.json"))
            root = json.loads(archive.read("flop/result.json"))
            job = dict(root_template, flop=flop, out="result.json", flop_oop="33%",
                       extract=[dict(prefix=[], street=True)] + [
                           dict(prefix=["b33", "c", turn], street=False, raw=True) for turn in spec["turns"]])
            assert json.loads(archive.read("flop/job.json")) == job
            assert (job["pot"], job["stack"], job["rake_rate"], job["rake_cap"]) == (250, 9900, .05, 1000)
            assert (root["flop"], root["pot"], root["stack"]) == (flop, 250, 9900)
            assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
            assert sha(compact(root)) == claim["root_sha256"] == spec["root_sha256"]
            assert (claim["rank"], claim["model_id"], claim["flop"], claim["line"]) == (80, MODEL, flop, LINE)
            assert (claim["actual_river_pot_bb"], claim["actual_river_effective_stack_bb"]) == (4.16, 98.17)
            lead, = [node for node in root["nodes"] if node["line"] == ""]
            call, = [node for node in root["nodes"] if node["line"] == "b33"]
            assert (lead["player"], lead["pot"], call["player"], call["pot"]) == (0, 250, 1, 333)
            bettors = accepted(lead, root["hands"], "b33")
            callers = accepted(call, root["hands"], "c")
            assert len(bettors) == spec["strict_flop_bettors"] == 0
            assert len(callers) == spec["strict_flop_callers"]
            assert [turn["turn"] for turn in claim["turns"]] == spec["turns"]
            assert len(spec["turns"]) == len(set(spec["turns"])) == 6
            for item in claim["turns"]:
                turn = item["turn"]
                parent, = [node for node in root["nodes"]
                           if node["line"] == "b33 c/" and node["board"].endswith(turn)]
                assert (parent["pot"], parent["bets"]) == (416, [83, 83])
                # No accepted bettor means no compatible two-seat deal,
                # independently of every subsequent displayed hand-class filter.
                assert item["eligible_turn_hands"] == item["legal_rivers"] == 0
                assert not item["paired_policies"] and not item["checks"]
    print(json.dumps(dict(rank=80, status="APPROX", original_flops=4,
                          checked_turn_boundaries=24, valid_flops=0, locks=0, medium=0)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--originals", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("data/nl2_hu_b672_rank80_completed.json"))
    verify(parser.parse_args())
