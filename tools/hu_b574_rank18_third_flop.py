"""Combine two authenticated B565 positive river sources with a new independent paired flop."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b545_sb_half_pot import register
from hu_b565_paired_barrels import MID, assess, read_zip

DATA = Path("data")
OLD_RUN = 45128951555
OLD_HEAD = "83ced7faefb331870e620ad19b627b31cdc2f5d5"
OLD_REPORT_SHA = "0b40af1ec779e07ee2b03afe929e65cf55fb625aa78b6862f4003faa8bdc9c37"
ARCHIVES = {
    "TdTs4h": (
        14796508645,
        "9e62cd3b4dea4209f7dfe5f2e4da8170d48764f9db938f793d79469badd689bd",
        "b46753b38c693b952771f79db076130ec2c296100d69c4045b77af3d3776a099",
    ),
    "JdJh3c": (
        14796882649,
        "3213daf7c4bebb703d3fd630b80a588d05e392dc0c5ee31e0d34214aeaccfb18",
        "7a8d37dcb8c915eea9eb9d885c9e1c2243da30baa75e17872de269f7801cd67d",
    ),
}
PINS = DATA / "nl2_hu_b574_fresh_source.json"
REPORT = DATA / "nl2_hu_b574_rank18_checkpoint.json"


def authenticate(flop, path, folder):
    aid, archive_digest, inner = ARCHIVES[flop]
    assert sha(path.read_bytes()) == inner
    if folder:
        meta = json.loads((folder / f"{aid}.json").read_bytes())
        raw = (folder / f"{aid}.zip").read_bytes()
        assert (meta["id"], meta["digest"], meta["name"]) == (
            aid,
            "sha256:" + archive_digest,
            "B565-native-" + flop,
        )
        run = meta["workflow_run"]
        assert (run["id"], run["head_sha"], run["repository_id"]) == (
            OLD_RUN,
            OLD_HEAD,
            1438346845,
        )
        assert sha(raw) == archive_digest
        with ZipFile(folder / f"{aid}.zip") as z:
            assert (
                z.namelist() == [path.name] and z.read(path.name) == path.read_bytes()
            )


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver", type=Path, required=True)
    cli.add_argument("--receipts", type=Path)
    cli.add_argument("--run", type=int)
    cli.add_argument("--out", type=Path, default=REPORT)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert (
        subprocess.check_output(
            ["git", "-C", solver, "rev-parse", "HEAD"], text=True
        ).strip()
        == SOLVER
    )
    assert (
        sha((solver / "postflop/py/ranges.py").read_bytes()) == RANGES
        and sha((solver / "postflop/py/pipeline.py").read_bytes()) == PIPELINE
    )
    raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges

    old = (DATA / "nl2_hu_b565_rank18_checkpoints.json").read_bytes()
    assert sha(old) == OLD_REPORT_SHA
    old = json.loads(old)
    assert old["run"] == OLD_RUN and not old["attempts"]["QcQd4s"]["selected"]
    route = json.loads(
        subprocess.check_output(["node", "tools/hu_b545_sb_routes.cjs"])
    )["18"]
    actions = json.loads(
        subprocess.check_output(["node", "tools/hu_b557_sb_river_actions.cjs"])
    )["18"]
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())[
        "records"
    ][MID]
    assert (model["frequency_rank"], model["solver_profile"]) == (18, "SB_BB")
    group = {"rank": 18, "model_id": MID, "boards": [], "pins": []}
    refs = {
        "schema": "NL2_HU_B574_ORIGINAL_LOCKED_MEDIUM_V1",
        "references": {},
        "gto_references": {},
    }
    new = json.loads(PINS.read_bytes())
    f = new["flop"]
    assert f not in ARCHIVES and (f[0], f[2], f[4]) not in {
        (p[0], p[2], p[4]) for p in ARCHIVES
    }
    reports = {}
    for flop in [*ARCHIVES, f]:
        code = ("B565" if flop in ARCHIVES else "B574") + "_R18_" + flop.upper()
        path = EVIDENCE / ("NL2_" + code + ".zip")
        if flop in ARCHIVES:
            authenticate(flop, path, args.receipts)
        else:
            assert (
                sha(path.read_bytes()) == new["archive_sha256"]
                and path.name == new["file"]
            )
        files = read_zip(path)
        checks, pair, hands = assess(
            files, flop, route, actions, pool, pipeline, ranges
        )
        record = {
            "flop": flop,
            "checked": checks,
            "selected": pair[2]["public_board"] if pair else None,
            "hands": hands,
        }
        assert files["outcome.json"] == compact(record)
        reports[flop] = record
        if flop in ARCHIVES:
            assert record == old["attempts"][flop] and pair
        if not pair or not args.run:
            continue
        run = OLD_RUN if flop in ARCHIVES else args.run
        register(model, group, refs, run, code, sha(path.read_bytes()), pair)
        b, p = group["boards"][-1], group["pins"][-1]
        b["conditional_turn_oop_bet_sizes_pct"] = [75]
        counts = {"gto": 0, "nl2": 0, "both": 0}
        for h in hands:
            token = {"過": "x", "下注 ¾": "b75"}[h["displayed_suggestion"]]
            for k in ("gto", "nl2"):
                counts[k] += token in h[k]["accepted_actions"]
            counts["both"] += all(
                token in h[k]["accepted_actions"] for k in ("gto", "nl2")
            )
        p.update(
            rendered_decision_hands=hands, hands_accepting_displayed_suggestion=counts
        )
        if flop in ARCHIVES:
            (prior,) = (x for x in old["group"]["boards"] if x["flop"] == flop)
            (pin,) = (x for x in old["group"]["pins"] if x["flop"] == flop)
            if "original_b545_flop_archive_sha256" in pin:
                p["original_b545_flop_archive_sha256"] = pin[
                    "original_b545_flop_archive_sha256"
                ]
            assert b == prior and p == pin
            assert (
                sha(
                    (
                        EVIDENCE
                        / f"NL2_MULTIBOARD_{pin['viewer_archive_code']}.json.gz"
                    ).read_bytes()
                )
                == pin["viewer_sha256"]
            )
    if len(group["boards"]) == 3:
        assert len({b["flop"] for b in group["boards"]}) == 3
        (EVIDENCE / "reverified/rank18.json").write_bytes(json_bytes(group))
        (DATA / "nl2_hu_b574_locked_medium.json").write_bytes(json_bytes(refs))
    args.out.write_bytes(
        json_bytes(
            {
                "schema": "NL2_HU_B574_PAIRED_BARREL_SOURCES_V1",
                "run": args.run,
                "original_run": OLD_RUN,
                "original_report_sha256": OLD_REPORT_SHA,
                "attempts": reports,
                "distinct_flops": sum(bool(r["selected"]) for r in reports.values()),
            }
        )
    )
    print("Verified", [(f, r["selected"]) for f, r in reports.items()])


if __name__ == "__main__":
    main()
