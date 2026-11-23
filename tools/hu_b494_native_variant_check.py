"""Check rank5's original five boards and the optional independently verified native-menu lock."""
import json
import sys
from copy import deepcopy
from pathlib import Path

from hu_apply_cert_extensions import append_lock, read, verify_native_lock
from hu_board_reach_corrections import read_replays

MODEL = "ln-opfr-t_model-id38uf"
PUBLIC = "3d7hAsKd"
PARENT = "39833178b55b3f268c4a3f9795d2b7cce7acae336b6aea701e940a2393d7326f"


def rejected(call):
    try:
        call()
    except (ValueError, AssertionError):
        return
    raise AssertionError("Unverified native-menu variant passed")


def main():
    registry = read(Path(sys.argv[1] if len(sys.argv)>1 else "data/nl2_hu_multiboard_status_current.json"))
    model = registry["records"][MODEL]
    boards = model["certified_3_to_5_exact_flop_boards"]
    assert model["frequency_rank"] == 5 and model["label"] == "CERT-MULTIBOARD"
    assert model["proven_exact_board_count"] == len({b["flop"] for b in boards}) == len(boards) == 5
    board, = (b for b in boards if b["public_board"] == PUBLIC)
    variants = board["nl2_locked_variants"]
    parent, = (v for v in variants if v["sha256"] == PARENT)
    _, locked, originals, _ = read_replays()
    def key(run, sha):
        return json.dumps([MODEL, PUBLIC, board["actual_exact_action_line"], 0, run, sha], separators=(",", ":"))
    assert originals[key(board["source_run_id"], board["source_sha256"])]["source_actions"] == board["exact_node_actions"] == ["x","b50","b100"]
    assert locked[key(parent["run_id"], PARENT)]["source_actions"] == ["x","b66"]
    rejected(lambda: verify_native_lock(model, board, {"lock":parent}, {}, {}, locked, originals, b""))
    rejected(lambda: verify_native_lock(model, board, {"lock":parent}, {}, {}, {}, originals, b""))
    overlay = Path("data/solver_evidence/lock_variants/rank5_b494_As7h3d.json")
    active = [v for v in variants if v.get("requires_native_joint_replay")]
    assert len(active) == int(overlay.exists())
    if overlay.exists():
        item = read(overlay)
        row = item["lock"]
        assert row["requires_native_joint_replay"] is True and active[0]["sha256"] == row["sha256"]
        test = deepcopy(registry)
        b, = (b for b in test["records"][MODEL]["certified_3_to_5_exact_flop_boards"] if b["public_board"] == PUBLIC)
        b["nl2_locked_variants"] = [v for v in b["nl2_locked_variants"] if v["sha256"] != row["sha256"]]
        ref = key(row["run_id"],row["sha256"])
        rejected(lambda: append_lock(test,item,{},originals))
        for patch in [{"status":"ZERO_JOINT_REACH"}, {"source_actions":["x","b66"]}, {"compatible_action_mask_b64":""}]:
            rejected(lambda: append_lock(test,item,{**locked,ref:{**locked[ref],**patch}},originals))
        assert all(v["sha256"]!=row["sha256"] for v in b["nl2_locked_variants"])
        append_lock(test,item,locked,originals)
        assert b["nl2_locked_variants"][-1]["sha256"] == row["sha256"]
    print(f"Rank5 retains all five boards and its alternate lock; {len(active)} verified supplementary native-menu source.")


if __name__ == "__main__":
    main()
