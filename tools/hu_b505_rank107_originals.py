"""Replay rank107's two retained public boards against both original seat ranges."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b483_locked_medium import POOL, proof
from hu_board_reach_corrections import source_key
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

DATA = Path("data")
MODEL = "ln-ipfr-r_model-ujl14x"
LINE = "b33 c/x b50 c/x"
PINS = DATA / "nl2_hu_b505_rank107_artifacts.json"
REPORT = DATA / "nl2_hu_b505_locked_medium.json"
BOARDS = (
    ("7s5h3d", "3d5h7s6c9s", 14752561398, 14752473776),
    ("QsJh4d", "4dJhQs7s6c", 14755175780, 14754959467),
)


def original(archive, path, digest):
    name = "solver/postflop/" + path
    blob = archive.read(name)
    assert sha(blob) == digest
    return json.loads(blob), json.loads(archive.read(name[:-5] + ".job.json"))


def replay(folder, artifact, pin, flop, public, version, expected_digest):
    path = folder / f"{artifact}.zip"
    assert sha(path.read_bytes()) == pin["sha256"]
    with ZipFile(path) as archive:
        assert archive.read("evidence/poker-solver-pin.txt").decode().strip() == SOLVER
        assert archive.read("evidence/rust-pin.txt").decode().strip() == RUST
        m = json.loads(archive.read(f"evidence/BTN_BB-{flop}-{version}.json"))
        assert (m["spot"], m["pot_family"], m["version"], m["failures"]) == ("BTN_BB", "SRP", version, [])
        assert m["preflop_ranges"] == dict(source="PINNED_POKER_SOLVER_PREFLOP_CFR", spot="BTN_BB",
            full_sha256="787f719c752165262807f79b91daec81e1db86a83d557a4ea645ef2649f532c7")
        assert m["pool_source_sha256"] == POOL
        case, = m["cases"]
        assert (case["line"], case["turn"], case["source_sha256"]) == ("b33 c", public[6:8], expected_digest)
        root, root_job = original(archive, m["file_flop"], m["file_flop_sha256"])
        sub, sub_job = original(archive, case["source_path"], expected_digest)

    hero = 1 if version == "exp_ip" else None
    for game, job, pot, stack in ((root, root_job, 550, 9750), (sub, sub_job, 914, 9568)):
        assert game["flop"] == job["flop"] == flop
        assert (game["pot"], game["stack"]) == (job["pot"], job["stack"]) == (pot, stack)
        assert (job["rake_rate"], job["rake_cap"], job.get("hero")) == (.05, 1000, hero)
        assert [p["pat"] for p in job.get("locks", [])] == [p["pat"] for p in m["locks"]]
        assert 0 <= game["info"]["gto_expl_pct"] <= .5
        if hero is not None:
            assert 0 <= game["info"]["hero_gap_pct"] <= .5
    assert root_job["flop_oop"] == root_job["flop_ip"] == "33%,50%,75%,100%"
    assert (sub_job["line0"], sub_job["turn"], sub["line0"]) == (["b33", "c", "/"], public[6:8], "b33 c")
    assert sub_job["turn_oop"] == sub_job["turn_ip"] == "50%,100%"
    parent, = (n for n in root["nodes"] if n["line"] == "b33 c/" and n["board"] == public[:8])
    assert (parent["pot"], root["stack"] - max(parent["bets"])) == (sub_job["pot"], sub_job["stack"])
    for seat, key in enumerate(("oop_w", "ip_w")):
        assert sub_job[key] == [[h, w] for h, w in zip(root["hands"][seat], parent["wr"][seat], strict=True) if w > 1e-4]

    masks = game_reach(root, sub)[0]
    rows = {}
    root_locks, sub_locks = [sum(x["nodes"] for x in g["info"].get("lock_stats", {}).values()) for g in (root, sub)]
    scope = lock_scope(sub, m["locks"], version)
    if hero is not None:
        assert min(root_locks, sub_locks, scope["observed_marginal_source_nodes"]) > 0
    for n in sub["nodes"]:
        if (n["line"], n["player"]) != (LINE, 1):
            continue
        assert n["board"][:8] == public[:8] and len(n["board"]) == 10
        assert n["pot"] == 1828 and n["bets"] == [457, 457] and n["acts"] == ["x", "b50", "b100", "a"]
        child, = (v for v in sub["nodes"] if (v["board"], v["line"], v["player"]) == (n["board"], LINE + " b50", 0))
        assert (child["pot"], child["bets"]) == (2742, [457, 1371])
        observation = proof(root, sub, n, masks)
        rows[n["board"]] = dict(observation, version=version, source_run_id=pin["run"], source_sha256=expected_digest,
            spot="BTN_BB", family="SRP", flop=flop, turn=sub["turn"], root_sha256=m["file_flop_sha256"],
            archive_id=artifact, archive_sha256=pin["sha256"], source_archive=pin["name"],
            gto_gap_pct=sub["info"]["gto_expl_pct"], locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),
            root_applied_rust_lock_nodes=root_locks, subgame_applied_rust_lock_nodes=sub_locks,
            lock_scope={k: v for k, v in scope.items() if k not in ("caveat", "matching_examples")})
    assert len(rows) == 2 and public in rows
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("originals", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    pins = json.loads(PINS.read_bytes())
    historical = json.loads((DATA / "nl2_hu_multiboard_status_v48_b390_rank107.json").read_bytes())["records"][MODEL]
    assert (historical["frequency_rank"], historical["assumed_model_node_spr"]) == (107, 4.968)
    report = dict(schema="NL2_HU_B505_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={}, alternate_rivers=[])
    for flop, public, gto_id, lock_id in BOARDS:
        board, = (b for b in historical["certified_3_to_5_exact_flop_boards"] if (b["public_board"], b["actual_exact_action_line"]) == (public, LINE))
        lock, = board["nl2_locked_variants"]
        for version, artifact, expected, run, field in (
            ("gto", gto_id, board["source_sha256"], board["source_run_id"], "gto_references"),
            ("exp_ip", lock_id, lock["sha256"], lock["run_id"], "references"),
        ):
            pin = pins[str(artifact)]
            assert pin["run"] == run
            rows = replay(args.originals, artifact, pin, flop, public, version, expected)
            report[field][source_key(MODEL, rows[public])] = rows[public]
            report["alternate_rivers"].extend(row for key, row in rows.items() if key != public)
    data = compact(report) + b"\n"
    if args.verify:
        assert REPORT.read_bytes() == data
    else:
        REPORT.write_bytes(data)


if __name__ == "__main__":
    main()
