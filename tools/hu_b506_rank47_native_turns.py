"""Reconstruct the checked-to CO turn decision from original B3 and B192 sources."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import EVIDENCE, json_bytes
from hu_b501_rank80_originals import load_limp_call
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board

DATA = Path("data")
MODEL = "ln-iso-lmp_t_model-1oaypnl"
FLOP_LINE = "x b33 c"
TURN_LINE = FLOP_LINE + "/x"
CASES = (
    ("KsQh4d", "4dQhKsTc", 14601426559, 14602013161),
    ("8s8h3d", "3d8h8s5s", 14600026283, 14695089375),
    ("9s6h3d", "3d6h9sTs", 14599037935, 14695243751),
)


def artifact_pins():
    history = json.loads((DATA / "nl2_hu_b490_original_artifacts.json").read_bytes())
    pins = {p["id"]: dict(p, head=p["commit"]) for p in history}
    b3 = json.loads((DATA / "nl2_hu_b501_rank80_artifacts.json").read_bytes())
    pins.update({int(k): v for k, v in b3.items()})
    return {aid: pins[aid] for _, _, gto, lock in CASES for aid in (gto, lock)}


def load(folder, pins, aid, version, flop, public):
    pin = pins[aid]
    m, case, root, sub, root_job, rj_sha, sj_sha, parent, _, _ = load_limp_call(
        folder, aid, pin, version, FLOP_LINE)
    assert (root["flop"], sub["turn"], case["turn"]) == (flop, public[-2:], public[-2:])
    source = dict(manifest=m, root=root, subgame=sub, version=version, run=pin["run"],
                  source_sha256=case["source_sha256"], archive_code=f"GHA_{aid}", archive_sha256=pin["sha256"])
    root_sha = m["file_flop_sha256"]
    row = audit_decision(source, public, TURN_LINE, 1, root_sha)
    assert row and row["status"] == "POSITIVE_JOINT_REACH"
    assert row["source_actions"] == ["x", "b50", "b100"]
    assert row["compatible_hole_card_pairs"] >= row["strict_legal_combos"] > 0
    origin = dict(artifact_id=aid, run=pin["run"], archive_sha256=pin["sha256"], head=pin["head"],
                  root_sha256=root_sha, root_job_sha256=rj_sha, subgame_job_sha256=sj_sha,
                  source_sha256=case["source_sha256"])
    return source, row, origin, (root_job["oop"], root_job["ip"]), parent


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--originals", type=Path)
    cli.add_argument("--pins", action="store_true")
    args = cli.parse_args()
    pins = artifact_pins()
    if args.pins:
        print(json.dumps(pins))
        return
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
    assert (model["frequency_rank"], model["solver_profile"], model["family"], model["street"]) == (47, "LMP_CO_BB", "LMP", 1)
    report = dict(schema="NL2_HU_B506_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
    group = dict(rank=47, model_id=MODEL, boards=[], pins=[])
    for flop, public, gid, lid in CASES:
        g, gr, gp, g_ranges, _ = load(args.originals, pins, gid, "gto", flop, public)
        lock, lr, lp, l_ranges, parent = load(args.originals, pins, lid, "exp_ip", flop, public)
        assert g_ranges == l_ranges
        if parent:
            assert (parent, lp["root_sha256"], lp["root_job_sha256"]) == (g["run"], gp["root_sha256"], gp["root_job_sha256"])
            lock["verified_gto_parent"] = dict(run=g["run"], sha256=gp["root_sha256"])
        board, pin = emit_board(model, g, lock, public, TURN_LINE, texture(flop))
        assert (pin["GTO_compatible_hole_card_pairs"], pin["NL2_compatible_hole_card_pairs"]) == (
            gr["compatible_hole_card_pairs"], lr["compatible_hole_card_pairs"])
        pin.update(original_gto_archive=gp, original_lock_archive=lp)
        if parent:
            board["nl2_locked_variants"][0].update(variant_label="原始 GTO 翻牌範圍，轉河牌 NL2 局部鎖頻",
                gto_parent_source_run_id=parent, gto_parent_source_sha256=gp["root_sha256"])
        group["boards"].append(board)
        group["pins"].append(pin)
        report["references"][source_key(MODEL, lr)] = lr
        report["gto_references"][source_key(MODEL, gr)] = gr
    (EVIDENCE / "reverified/rank47.json").write_bytes(json_bytes(group))
    (DATA / "nl2_hu_b506_locked_medium.json").write_bytes(json_bytes(report))


if __name__ == "__main__":
    main()
