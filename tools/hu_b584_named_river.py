"""Expose one additional river from the same native rank64 subgames and source flop."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b568_caller_rivers import (
    DATA,
    LINE,
    MID,
    POOL,
    RUST,
    SOLVER,
    conditional_source,
    observations,
    root_job,
    street_rates,
    turn_job,
)
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board

FLOP, TURN, RIVER = "8s5d3c", "2h", "4c"
CODE = "B584_R64_8S5D3C_2H_4C"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path, required=True)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert (
        subprocess.check_output(["git", "-C", solver, "rev-parse", "HEAD"], text=True).strip() == SOLVER
    )
    poolbytes = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(poolbytes) == POOL
    pool = json.loads(poolbytes)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges

    group_path = EVIDENCE / "reverified/rank64.json"
    group = json.loads(group_path.read_bytes())
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())["records"][MID]
    assert model["label"] == "CERT-MULTIBOARD" and group["model_id"] == MID and group["rank"] == 64
    assert len({b["flop"] for b in group["boards"]}) == len(group["boards"]) == 3
    assert {b["public_board"] for b in group["boards"]} == {
        b["public_board"] for b in model["certified_3_to_5_exact_flop_boards"]
    }
    (canonical,) = (b for b in group["boards"] if b["flop"] == FLOP and b["turn"] == TURN)
    (pin,) = (p for p in group["pins"] if p["public_board"] == canonical["public_board"])
    run = canonical["source_run_id"]
    code = "B568_R64_8S5D3C_2H"
    assert canonical["actual_exact_action_line"] == LINE and canonical["acting_seat"] == 1
    assert pin["archive_code"] == pin["locked_original_archive_code"] == code
    archive = EVIDENCE / ("NL2_" + code + ".zip")
    digest = sha(archive.read_bytes())
    assert digest == pin["archive_sha256"] == pin["locked_original_archive_sha256"]
    rootjob = root_job(FLOP, pipeline)
    assert tuple(rootjob[k] for k in ("oop", "ip")) == tuple(
        ranges.to_str(w) for w in ranges.ranges("SB_BB", "gto")
    )
    pair = []
    route = json.loads(subprocess.check_output(["node", "tools/hu_b568_caller_routes.cjs"]))
    with ZipFile(archive) as z:
        provenance = json.loads(z.read("provenance.json"))
        assert set(z.namelist()) == set(provenance["sha256"]) | {"provenance.json"}
        assert all(sha(z.read(name)) == value for name, value in provenance["sha256"].items())
        assert (
            provenance["solver"],
            provenance["rust"],
            provenance["pool_sha256"],
            provenance["run"],
            provenance["flop"],
            provenance["turn"],
        ) == (SOLVER, RUST, POOL, run, FLOP, TURN)
        assert z.read("flop.job.json") == compact(rootjob)
        root = json.loads(z.read("flop.json"))
        assert (root["flop"], root["pot"], root["stack"]) == (FLOP, 600, 9700)
        assert 0 <= root["info"]["gto_expl_pct"] <= 0.5 and not root["info"].get("lock_stats")
        for version, expected in (
            ("gto", pin["original_GTO_SHA256"]),
            ("exp_ip", pin["actual_NL2_SHA256"]),
        ):
            job, meta, public, rivers = turn_job(root, FLOP, TURN, version, pool, pipeline)
            assert (
                RIVER in rivers
                and z.read(version + "/job.json") == compact(job)
                and z.read(version + "/locks.json") == compact(meta)
            )
            raw = z.read(version + "/native.json")
            assert sha(raw) == expected
            source = conditional_source(root, raw, job, meta, version, run, pool, rivers)
            source.update(archive_code=code, archive_sha256=digest)
            pair.append(source)
            if version == "exp_ip":
                measured = street_rates(source, job, pool)
    alternate = public + RIVER
    assert alternate != canonical["public_board"] and alternate[:8] == canonical["public_board"][:8]
    (gr, gh), (er, eh) = [observations(source, route)[alternate] for source in pair]
    shared = []
    for hand in sorted(gh.keys() & eh.keys()):
        common = {k: v for k, v in gh[hand].items() if k != "native"}
        assert all(eh[hand][k] == v for k, v in common.items())
        shared.append(dict(common, gto=gh[hand]["native"], nl2=eh[hand]["native"]))
    assert shared and er["b50"]["candidate"] and gr["b50"]["eligible"] > 0
    assert er["b50"]["eligible"] >= 20 and er["b50"]["middle_count"] >= 10
    board, witness = emit_board(model, *pair, alternate, LINE, texture(FLOP), viewer_code=CODE)
    for key in (
        "frozen_gto_flop",
        "trainer_assumed_river_pot_bb",
        "trainer_assumed_river_effective_stack_bb",
        "native_opponent_bet_pct",
        "restricted_flop_bet_sizes_pct",
        "flop_sizing_assumption",
    ):
        board[key] = canonical[key]
    assert (
        board["actual_pot_bb"] == canonical["actual_pot_bb"] == 24
        and board["actual_effective_stack_bb"] == canonical["actual_effective_stack_bb"] == 88
    )
    board["nl2_locked_variants"][0].update(
        variant_label="相同翻牌及轉牌的另一個河牌決策",
        pool_sha256=POOL,
        gto_parent_source_sha256=sha(compact(root)),
        gto_parent_source_run_id=run,
        first_matching_barrel_rates=measured,
        applied_street_rates=rates(pair[1]),
        viewer_archive_code=CODE,
        viewer_sha256=witness["viewer_sha256"],
    )
    labels = {"過": "x", "下注 ½": "b50", "下注 ¾": "b75"}
    witness.update(
        rendered_decision_hands=shared,
        hands_accepting_displayed_suggestion=sum(
            all(labels[h["displayed_suggestion"]] in h[v]["accepted_actions"] for v in ("gto", "nl2"))
            for h in shared
        ),
    )
    branch = dict(
        board=board,
        pin=witness,
        reach_report=dict(
            references={source_key(MID, er): er}, gto_references={source_key(MID, gr): gr}
        ),
    )
    previous = canonical.get("optional_named_rivers", [])
    assert not previous or previous == [branch]
    canonical["optional_named_rivers"] = [branch]
    group_path.write_bytes(json_bytes(group))
    print("Rank64 named alternative", alternate, len(shared), "shared hands, NL2 half pot", er["b50"])


if __name__ == "__main__":
    main()
