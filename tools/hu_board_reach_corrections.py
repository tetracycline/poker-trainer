"""Apply original two-seat action-path evidence to exact board and locked-source records."""
import base64
import hashlib
import json
import re
from pathlib import Path

REPORT_NAME = re.compile(r"nl2_hu_b([1-9][0-9]*)_locked_medium\.json")
NODE = ("spot", "family", "flop", "turn", "public_board", "line", "acting_seat")
RESULT = ("version", "source_run_id", "source_sha256", *NODE, "status", "source_hand_count",
          "source_hand_order_sha256", "source_actions", "compatible_action_mask_b64",
          "strict_legal_combos", "compatible_opponent_combos", "compatible_hole_card_pairs",
          "gto_gap_pct", "locked_hero_gap_pct", "b50")
APPLIED = ("root_applied_rust_lock_nodes", "subgame_applied_rust_lock_nodes")
UNRESOLVED = "UNRESOLVED_JOINT_REACH"
REASON = "FEWER_THAN_THREE_FLOPS_AFTER_TWO_SEAT_REPLAY"


def summarize(observation):
    """Check action masks and extract just the fields needed to reconstruct the live registry."""
    if observation.get("status") == UNRESOLVED:
        return dict(sha256=observation["source_sha256"], run_id=observation["source_run_id"],
                    unresolved_reason=observation["reason"])
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
    assert observation["status"] == ("POSITIVE_JOINT_REACH" if combos else "ZERO_JOINT_REACH")
    counts = {k: observation[k] for k in APPLIED if k in observation}
    if counts:
        assert len(counts) == 2 and all(type(n) is int and n >= 0 for n in counts.values())
        assert (sum(counts.values()) > 0) == (observation["version"] != "gto")
    return dict(**(counts if observation["version"] != "gto" else {}),
                sha256=observation["source_sha256"], run_id=observation["source_run_id"],
                strictly_reachable_combos=combos, compatible_hole_card_pairs=pairs,
                medium_50pct_eligible_combos=medium,
                b50_nonpolarized_relative_equity_research_candidate=candidate)


def source_key(mid, row):
    return json.dumps([mid, row["public_board"], row["line"], row["acting_seat"],
                       row["source_run_id"], row["source_sha256"]], separators=(",", ":"), ensure_ascii=False)


def read_replays(directory=Path("data")):
    paths = []
    for path in directory.glob("nl2_hu_b*_locked_medium.json"):
        match = REPORT_NAME.fullmatch(path.name)
        if match is None or path.is_symlink():
            raise ValueError(f"Invalid raw reach report path: {path}")
        paths.append((int(match[1]), path))
    paths.sort()
    if not any(path.name == "nl2_hu_b483_locked_medium.json" for _, path in paths):
        raise FileNotFoundError("Missing original B483 reach evidence")
    sources, verified, refs, gto_refs, links, pending = [], {}, {}, {}, {}, {}

    def register(key, row, gto):
        mid = json.loads(key)[0]
        assert isinstance(mid, str) and mid and key == source_key(mid, row)
        assert type(row["acting_seat"]) is int and row["acting_seat"] in (0, 1)
        assert type(row["source_run_id"]) is int and row["source_run_id"] > 0
        assert re.fullmatch("[0-9a-f]{64}", row["source_sha256"])
        assert row["version"] == ("gto" if gto else ("exp_ip" if row["acting_seat"] else "exp_oop"))
        assert row["status"] in ("POSITIVE_JOINT_REACH", "ZERO_JOINT_REACH")
        summarize(row)
        identity = (row["source_run_id"], row["source_sha256"], row["version"], row["spot"], row["public_board"], row["line"], row["acting_seat"])
        before = verified.get(identity)
        if before is None:
            before = verified[identity] = {k: v for k, v in row.items() if k != "gto"}
        else:
            for field in (*RESULT, *APPLIED, "root_sha256", "root_gto_stage_gap_pct", "root_locked_hero_gap_pct"):
                if field in row and field in before and row[field] != before[field]:
                    raise ValueError(f"Conflicting replay of {key}: {field}")
                if field in row:
                    before[field] = row[field]
        target = gto_refs if gto else refs
        assert key not in target or target[key] is before
        target[key] = before
        return mid

    for number, path in paths:
        schema = f"NL2_HU_B{number}_ORIGINAL_LOCKED_MEDIUM_V1"
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report["schema"] == schema, f"Wrong raw reach schema: {path}"
        sources.append(dict(path="data/"+path.name, schema=schema, sha256=hashlib.sha256(raw).hexdigest()))
        assert isinstance(report["references"], dict) and isinstance(report.get("gto_references", {}), dict)
        for key, row in report["references"].items():
            mid = register(key, row, False)
            original = row.get("gto")
            if original is not None:
                assert all(original[field] == row[field] for field in NODE)
                original_key = source_key(mid, original)
                register(original_key, original, True)
                assert links.setdefault(key, original_key) == original_key
        for key, row in report.get("gto_references", {}).items():
            register(key, row, True)
        assert isinstance(report.get("unresolved", {}), dict)
        for key, item in report.get("unresolved", {}).items():
            mid, public, line, seat, run, sha = json.loads(key)
            assert isinstance(mid, str) and mid and isinstance(public, str) and isinstance(line, str)
            assert type(seat) is int and seat in (0, 1) and type(run) is int and run > 0
            assert re.fullmatch("[0-9a-f]{64}", sha)
            assert item["version"] in ("gto", "exp_ip" if seat else "exp_oop")
            assert isinstance(item["reason"], str) and item["reason"].strip()
            exact = dict(public_board=public, line=line, acting_seat=seat, source_run_id=run, source_sha256=sha)
            assert all(item[f] == v for f, v in exact.items() if f in item) and key == source_key(mid, exact)
            assert not any(k in item for k in ("strict_legal_combos", "compatible_action_mask_b64", "b50"))
            value = {**item, **exact}
            value["status"] = UNRESOLVED
            if key in pending:
                assert pending[key]["version"] == value["version"]
            pending[key] = value
    for key, row in pending.items():
        target = gto_refs if row["version"] == "gto" else refs
        identity = (row["source_run_id"], row["source_sha256"], row["version"], row.get("spot"),
                    row["public_board"], row["line"], row["acting_seat"])
        target.setdefault(key, verified.get(identity, row))
    return sources, refs, gto_refs, links


def match_board(row, model, board):
    actual = dict(spot=model["solver_profile"], family=model["family"], flop=board["flop"], turn=board["turn"],
                  public_board=board["public_board"], line=board["actual_exact_action_line"], acting_seat=board["acting_seat"])
    for k, expected in actual.items():
        if row["status"] != UNRESOLVED or k in row:
            assert row[k] == expected


def replay_updates(registry, refs, gto_refs, links, seen, seen_gto, model_ids=None):
    updates = {}
    for model in registry["records"].values():
        if model["label"] != "CERT-MULTIBOARD" or (model_ids is not None and model["model_id"] not in model_ids):
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
                match_board(observed, model, board)
                row = summarize(observed)
                assert (row["sha256"], row["run_id"]) == (lock["sha256"], lock["run_id"])
                locks.append(row)
                seen.add(key)
                assert observed["version"] == lock["version"]
                if key in links:
                    assert json.loads(links[key])[-2:] == [board["source_run_id"], board["source_sha256"]]
            gto_key = json.dumps([mid, public, line, seat, board["source_run_id"], board["source_sha256"]],
                                 ensure_ascii=False, separators=(",", ":"))
            if gto_key in gto_refs:
                original_source = gto_refs[gto_key]
                match_board(original_source, model, board)
                if original_source["status"] != UNRESOLVED:
                    assert original_source["source_actions"] == board["exact_node_actions"]
                original = summarize(original_source)
                assert (original["run_id"], original["sha256"]) == (board["source_run_id"], board["source_sha256"])
                gto = original
                seen_gto.add(gto_key)
            if locks or gto is not None:
                updates.setdefault(mid, []).append(dict(public_board=public, line=line, seat=seat,
                    gto_run=board["source_run_id"], gto_sha256=board["source_sha256"], gto=gto, locks=locks))
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
                if "unresolved_reason" in gto or gto["strictly_reachable_combos"] == 0:
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
                elif "unresolved_reason" not in test and test["strictly_reachable_combos"] > 0:
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
