"""Apply original two-seat action-path evidence to exact board and locked-source records."""
import base64
import json
import re
from pathlib import Path

REPORTS = (Path("data/nl2_hu_b483_locked_medium.json"), Path("data/nl2_hu_b485_locked_medium.json"))
REASON = "FEWER_THAN_THREE_FLOPS_AFTER_TWO_SEAT_REPLAY"


def summarize(observation):
    """Check action masks and extract just the fields needed to reconstruct the live registry."""
    mask = base64.b64decode(observation["compatible_action_mask_b64"], validate=True)
    actions = observation["source_actions"]
    assert len(mask) == observation["source_hand_count"] and len(set(actions)) == len(actions)
    assert re.fullmatch("[0-9a-f]{64}", observation["source_hand_order_sha256"])
    assert (observation["version"] == "gto" or observation["version"] ==
            ("exp_ip" if observation["acting_seat"] else "exp_oop"))
    assert observation["gto_gap_pct"] >= 0
    if observation["version"] == "gto":
        assert observation["gto_gap_pct"] <= .5
    else:
        assert 0 <= observation["locked_hero_gap_pct"] <= .5
    combos = observation["strict_legal_combos"]
    pairs = observation["compatible_hole_card_pairs"]
    assert type(combos) is int and type(pairs) is int and pairs >= combos >= 0
    assert bool(pairs) == bool(combos) and sum(bool(bits) for bits in mask) == combos
    assert all(bits < 1 << len(actions) for bits in mask)
    assert re.fullmatch("[0-9a-f]{64}", observation["archive_sha256"])
    proof = observation["b50"]
    medium = 0
    candidate = False
    if combos:
        if "b50" in actions:
            flag = 1 << actions.index("b50")
            medium = sum(bool(bits & flag) for bits in mask)
        assert proof["eligible"] == medium and type(proof["candidate"]) is bool
        candidate = proof["candidate"]
        assert not candidate or medium >= 20
    else:
        assert proof is None
    return dict(sha256=observation["source_sha256"], run_id=observation["source_run_id"],
                strictly_reachable_combos=combos, compatible_hole_card_pairs=pairs,
                medium_50pct_eligible_combos=medium,
                b50_nonpolarized_relative_equity_research_candidate=candidate)


def replay_updates(registry):
    refs = {}
    gto_refs = {}
    for path in REPORTS:
        if not path.exists():
            if path == REPORTS[0]:
                raise FileNotFoundError(path)
            continue
        report = json.loads(path.read_bytes())
        for k, v in report.get("gto_references", {}).items():
            if k in gto_refs and v != gto_refs[k]:
                raise ValueError(f"Disagreement between original GTO replays: {k}")
            gto_refs[k] = v
        for k, v in report["references"].items():
            if k in refs and v != refs[k]:
                raise ValueError(f"Disagreement between two original-source audits: {k}")
            refs[k] = v
    updates = {}
    seen = set()
    seen_gto = set()
    for model in registry["records"].values():
        if model["label"] != "CERT-MULTIBOARD":
            continue
        mid = model["model_id"]
        for board in model["certified_3_to_5_exact_flop_boards"]:
            public, line, seat = (board[k] for k in ("public_board", "actual_exact_action_line", "acting_seat"))
            locks = []
            gto = None
            for lock in board["nl2_locked_variants"]:
                key = json.dumps([mid, public, line, seat, lock["run_id"], lock["sha256"]],
                                 ensure_ascii=False, separators=(",", ":"))
                if key not in refs:
                    continue
                observed = refs[key]
                assert (observed["spot"], observed["family"], observed["flop"], observed["turn"],
                        observed["public_board"], observed["line"], observed["acting_seat"]) == (
                    model["solver_profile"], model["family"], board["flop"], board["turn"], public, line, seat)
                row = summarize(observed)
                assert (row["sha256"], row["run_id"]) == (lock["sha256"], lock["run_id"])
                assert observed["status"] == ("POSITIVE_JOINT_REACH" if row["strictly_reachable_combos"] else "ZERO_JOINT_REACH")
                locks.append(row)
                seen.add(key)
                if observed["gto"] is not None:
                    original_source = observed["gto"]
                    assert original_source["version"] == "gto" and all(
                        observed[f] == original_source[f] for f in ("spot", "family", "flop", "turn", "public_board", "line", "acting_seat"))
                    original = summarize(original_source)
                    assert (original["sha256"], original["run_id"]) == (board["source_sha256"], board["source_run_id"])
                    assert gto is None or gto == original
                    gto = original
            gto_key = json.dumps([mid, public, line, seat, board["source_run_id"], board["source_sha256"]],
                                 ensure_ascii=False, separators=(",", ":"))
            if gto_key in gto_refs:
                original_source = gto_refs[gto_key]
                assert (original_source["version"], original_source["spot"], original_source["family"],
                        original_source["flop"], original_source["turn"], original_source["public_board"],
                        original_source["line"], original_source["acting_seat"]) == (
                    "gto", model["solver_profile"], model["family"], board["flop"], board["turn"], public, line, seat)
                original = summarize(original_source)
                assert (original["run_id"], original["sha256"]) == (board["source_run_id"], board["source_sha256"])
                assert gto is None or gto == original
                gto = original
                seen_gto.add(gto_key)
            if locks or gto is not None:
                updates.setdefault(mid, []).append(dict(public_board=public, line=line, seat=seat,
                    gto_run=board["source_run_id"], gto_sha256=board["source_sha256"], gto=gto, locks=locks))
    assert seen == set(refs), "An audited original is missing from the pre-correction registry"
    assert seen_gto == set(gto_refs)
    return updates


def apply_updates(registry, updates):
    for mid, entries in updates.items():
        model = registry["records"][mid]
        assert model["label"] == "CERT-MULTIBOARD"
        by_board = {(r["public_board"], r["line"], r["seat"]): r for r in entries}
        kept = []
        for board in model["certified_3_to_5_exact_flop_boards"]:
            key = (board["public_board"], board["actual_exact_action_line"], board["acting_seat"])
            row = by_board.pop(key, None)
            if row is None:
                kept.append(board)
                continue
            assert (row["gto_run"], row["gto_sha256"]) == (board["source_run_id"], board["source_sha256"])
            if row["gto"] is not None:
                gto = row["gto"]
                if gto["strictly_reachable_combos"] == 0:
                    continue
                board.update(strict_full_street_combo_reachable=gto["strictly_reachable_combos"],
                    compatible_hole_card_pairs=gto["compatible_hole_card_pairs"],
                    medium_50pct_eligible_combos=gto["medium_50pct_eligible_combos"],
                    b50_nonpolarized_relative_equity_research_candidate=gto["b50_nonpolarized_relative_equity_research_candidate"])
            by_lock = {(v["run_id"], v["sha256"]): v for v in row["locks"]}
            surviving_locks = []
            for lock in board["nl2_locked_variants"]:
                test = by_lock.pop((lock["run_id"], lock["sha256"]), None)
                if test is None:
                    surviving_locks.append(lock)
                elif test["strictly_reachable_combos"] > 0:
                    surviving_locks.append(dict(lock, **test))
            assert not by_lock
            if surviving_locks:
                board["nl2_locked_variants"] = surviving_locks
                kept.append(board)
        assert not by_board and len({b["flop"] for b in kept}) == len(kept)
        model["proven_exact_board_count"] = len(kept)
        if len(kept) >= 3:
            model["certified_3_to_5_exact_flop_boards"] = kept
        else:
            model.update(label="APPROX", blocked_reason=REASON, certified_3_to_5_exact_flop_boards=[],
                         remaining_exact_board_evidence=kept)
