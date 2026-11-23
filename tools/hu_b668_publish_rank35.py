"""Authenticate and replay the four original B642 workers before publishing rank35."""
import argparse
import io
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import hu_b642_rank35 as batch
from hu_b467_river_source_gate import json_bytes, sha
from hu_b483_locked_medium import POOL

RUN = 45270338275
HEAD = "45363db528f858e831b22e39b36054be22351727"
REPO = 1438346845


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--solver", type=Path, required=True)
    args = parser.parse_args()
    pins = json.loads(Path("data/nl2_hu_b668_rank35_workers.json").read_bytes())
    assert pins["run"] == RUN and pins["head"] == HEAD
    pool_bytes = (args.solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_bytes) == POOL
    pool = json.loads(pool_bytes)["NL2"]
    run = json.loads((args.receipts / "run.json").read_bytes())
    assert (run["id"], run["head_sha"], run["repository"]["id"], run["event"], run["path"]) == (
        RUN, HEAD, REPO, "push", ".github/workflows/nl2-hu-b642-rank35.yml")
    assert run["status"] == "completed" and run["conclusion"] == "success"
    jobs = json.loads((args.receipts / "jobs.json").read_bytes())["jobs"]
    for flop in batch.CASES:
        job, = [j for j in jobs if j["name"] == "solve (" + flop + ")"]
        assert job["conclusion"] == "success"
    evidence = []
    with tempfile.TemporaryDirectory() as tempdir:
        work = Path(tempdir)
        for frozen in pins["workers"]:
            flop, aid = frozen["flop"], frozen["id"]
            receipt = json.loads((args.receipts / f"{aid}.json").read_bytes())
            workflow = receipt["workflow_run"]
            assert (receipt["id"], receipt["name"], receipt["digest"]) == (
                aid, "B642-" + flop, "sha256:" + frozen["sha256"])
            assert (workflow["id"], workflow["head_sha"], workflow["repository_id"]) == (RUN, HEAD, REPO)
            raw = (args.receipts / f"{aid}.zip").read_bytes()
            assert sha(raw) == frozen["sha256"] and len(raw) == receipt["size_in_bytes"]
            target = work / ("B642-" + flop)
            target.mkdir()
            with ZipFile(io.BytesIO(raw)) as worker:
                expected = json.loads(worker.read("summary.json"))
                assert expected["flop"] == flop and expected["source_run"] == RUN
                code = "B642_R35_" + flop.upper()
                archive = "NL2_" + code + ".zip"
                viewer = "NL2_MULTIBOARD_" + code + ".json.gz"
                assert expected["paired_rivers"] > 0
                assert set(worker.namelist()) == {"summary.json", archive, viewer}
                original = worker.read(archive)
                assert sha(original) == expected["pin"]["archive_sha256"]
                with ZipFile(io.BytesIO(original)) as native:
                    def replay(driver, folder, job):
                        key = {"flop": "root", "gto": "gto", "locked": "native"}[folder.name]
                        assert json.loads(native.read(key + ".job.json")) == job
                        return native.read(key + ".json")

                    # Repeat the complete two-seat policy, original SHA, measured-lock
                    # and rendered-hand checks over the immutable native worker bytes.
                    with patch.object(batch, "native", replay):
                        batch.solve(flop, pool, RUN, None, work / "replay", target)
                assert json.loads((target / "summary.json").read_bytes()) == expected
                assert (target / archive).read_bytes() == original
                assert (target / viewer).read_bytes() == worker.read(viewer)
            evidence.append(dict(flop=flop, artifact_id=aid, worker_sha256=sha(raw),
                                 shared_checks=expected["pin"]["shared_rendered_checks"]))
        batch.collect(work)
    report = dict(run=RUN, head=HEAD, rank=35, workers=evidence)
    Path("data/nl2_hu_b668_rank35_replay.json").write_bytes(json_bytes(report))


if __name__ == "__main__":
    main()
