"""Assemble the exact-board registry from the latest base and independently verified source pairs."""
import argparse
import base64
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re

from hu_cert_lock_medium_audit import audit
from hu_b483_locked_medium import proof as original_reach
from hu_sequential_cfr_reach import game_reach
from hu_board_reach_corrections import apply_updates, read_replays, replay_updates, source_key
from hu_trainer_route_gate import active_pins, apply_routes, rendered_contract
from copy import deepcopy

DATA = Path("data")
SOURCE = DATA / "solver_evidence"
EXTENSIONS = SOURCE / "extensions"
BASES = (
    "nl2_hu_multiboard_status_v53_b465_rank218.json",
    "nl2_hu_multiboard_status_v52_b463_rank45.json",
    "nl2_hu_multiboard_status_v51_b453_rank32.json",
)


def read(path):
    return json.loads(path.read_bytes())


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def verify_case(code, archive_sha, run, model, board, version, sha, count):
    assert re.fullmatch(r"[0-9a-f]{64}", sha) and run > 0 and count > 0
    assert re.fullmatch(r"[A-Za-z0-9_]+", code)
    encoded = (SOURCE / f"NL2_MULTIBOARD_{code}.json.gz").read_bytes()
    assert hashlib.sha256(encoded).hexdigest() == archive_sha
    proof = json.loads(gzip.decompress(encoded))
    assert proof["schema"] == "NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1"
    assert proof["source_run_id"] == run and proof["no_generic_texture_certification"] and not proof["errors"]
    case, = (c for item in proof["artifacts"] for c in item["cases"]
             if (c["version"], c["source_sha256"], c["flop"], c["turn"]) ==
                (version, sha, board["flop"], board["turn"]))
    assert (case["spot"], case["pot_family"], case["flop_line"]) == (
        model["solver_profile"], model["family"], board["exact_flop_action"])
    node, = (n for n in case["nodes"] if (n["public_board"], n["exact_node_line"], n["acting_seat"]) ==
            (board["public_board"], board["actual_exact_action_line"], board["acting_seat"]))
    mask = base64.b64decode(node["strictly_reachable_masks_b64"], validate=True)
    assert len(mask) == len(case["hands_by_seat"][board["acting_seat"]])
    assert sum(bool(val) for val in mask) == node["strictly_reachable_combos"] == count
    assert abs(node["node_spr"]/board["actual_spr"] - 1) < .001
    assert 0 <= case["gto_exploitability_pct"] <= .5
    if version == "gto":
        assert node["source_actions"] == board["exact_node_actions"]
        assert node["medium_50pct_eligible_combos"] == board["medium_50pct_eligible_combos"]
        assert node["b50_nonpolarized_relative_equity_research_candidate"] is board["b50_nonpolarized_relative_equity_research_candidate"]
    else:
        assert 0 <= case["locked_hero_gap_pct"] <= .5

    return case, node


def verify_native_lock(model, board, item, case, node, locked, originals, package):
    lock = item["lock"]
    key = dict(public_board=board["public_board"], line=board["actual_exact_action_line"], acting_seat=board["acting_seat"])
    def observation(refs, run, sha):
        identity = dict(key, source_run_id=run, source_sha256=sha)
        row = refs.get(source_key(model["model_id"], identity))
        assert row and row["status"] == "POSITIVE_JOINT_REACH", "Native-menu variant needs both exact positive original replays"
        assert row["compatible_hole_card_pairs"] >= row["strict_legal_combos"] > 0
        assert row["source_actions"] == board["exact_node_actions"]
        if "b50" not in row["source_actions"]:
            assert row["source_actions"] == ["x"] and row["b50"]["eligible"] == 0 and not row["b50"]["candidate"]
        return row
    observation(originals, board["source_run_id"], board["source_sha256"])
    row = observation(locked, lock["run_id"], lock["sha256"])
    assert row["archive_sha256"] == hashlib.sha256(package).hexdigest()
    packed = json.loads(gzip.decompress(package))
    raw = base64.b64decode(packed["source_file_b64"], validate=True)
    root = base64.b64decode(packed["conditional_root_file_b64"], validate=True)
    assert hashlib.sha256(raw).hexdigest() == packed["source_sha256"] == lock["sha256"]
    assert hashlib.sha256(root).hexdigest() == packed["conditional_root_sha256"] and packed["run"] == lock["run_id"]
    parent_key = source_key(model["model_id"], dict(key, source_run_id=item["parent_lock_run"], source_sha256=item["parent_lock_sha256"]))
    parent = locked[parent_key]
    assert packed["conditional_root_sha256"] == (parent.get("original_root_sha256") or parent.get("root_sha256"))
    root, game = json.loads(root), json.loads(raw)
    job = packed["job"]
    assert (job["flop"], job["turn"], job["line0"]) == (
        board["flop"], board["turn"], [*board["exact_flop_action"].split(), "/"])
    assert game["flop"] == job["flop"] and (game["pot"], game["stack"]) == (job["pot"], job["stack"])
    game.update(turn=job["turn"], line0=board["exact_flop_action"])
    exact, = (n for n in game["nodes"] if (n["board"], n["line"], n["player"]) ==
              (key["public_board"], key["line"], key["acting_seat"]))
    assert (exact["pot"]/100, (game["stack"]-max(exact["bets"]))/100) == (board["actual_pot_bb"], board["actual_effective_stack_bb"])
    replay = original_reach(root, game, exact, game_reach(root, game)[0])
    assert all(row[field] == value for field, value in replay.items())
    assert sum(v["nodes"] for v in game["info"]["lock_stats"].values()) == row["subgame_applied_rust_lock_nodes"] > 0
    assert (game["info"]["gto_expl_pct"], game["info"]["hero_gap_pct"]) == (row["gto_gap_pct"], row["locked_hero_gap_pct"])
    hands = case["hands_by_seat"][board["acting_seat"]]
    order = json.dumps(hands, ensure_ascii=False, separators=(",", ":")).encode()
    assert row["source_hand_order_sha256"] == hashlib.sha256(order).hexdigest()
    assert (row["source_hand_count"], row["source_actions"], row["strict_legal_combos"], row["compatible_action_mask_b64"]) == (
        len(hands), node["source_actions"], node["strictly_reachable_combos"], node["strictly_reachable_masks_b64"])
    assert row["b50"] == node["medium_50pct_strict_evidence"]
    assert row["locked_hero_gap_pct"] == case["locked_hero_gap_pct"] and row["gto_gap_pct"] == case["gto_exploitability_pct"]


def append_lock(registry, item, locked, originals):
    model=registry["records"][item["model_id"]]
    assert model["label"]=="CERT-MULTIBOARD"
    board,=(b for b in model["certified_3_to_5_exact_flop_boards"]
            if (b["flop"],b["turn"],b["public_board"],b["actual_exact_action_line"],b["acting_seat"])==
               (item["flop"],item["turn"],item["public_board"],item["line"],item["acting_seat"]))
    assert (board["source_run_id"],board["source_sha256"])==(item["gto_run"],item["gto_sha256"])
    locks=board["nl2_locked_variants"]
    assert any((v["run_id"],v["sha256"])==(item["parent_lock_run"],item["parent_lock_sha256"]) for v in locks)
    lock=item["lock"]
    assert lock["version"]==("exp_ip" if board["acting_seat"] else "exp_oop")
    assert lock["sha256"] not in {v["sha256"] for v in locks}
    assert re.fullmatch(r"[A-Za-z0-9_]+\.json\.gz",item["original_package"])
    package=(SOURCE/item["original_package"]).read_bytes()
    assert hashlib.sha256(package).hexdigest()==item["original_package_sha256"]
    case,node=verify_case(lock["viewer_archive_code"],lock["viewer_sha256"],lock["run_id"],model,board,
                          lock["version"],lock["sha256"],lock["strictly_reachable_combos"])
    assert lock["true_hero_gap_pct"]==case["locked_hero_gap_pct"]
    stats=case["villain_lock_scope"]
    assert (lock["observed_marginal_source_nodes"],lock["assumed_default_source_nodes"],lock["unlocked_source_nodes"])==(
        stats["observed_marginal_source_nodes"],stats["imputed_assumption_nodes"],stats["unmatched_nodes"])
    assert (lock["medium_50pct_eligible_combos"],lock["b50_nonpolarized_relative_equity_research_candidate"])==(
        node["medium_50pct_eligible_combos"],node["b50_nonpolarized_relative_equity_research_candidate"])
    if lock.get("requires_native_joint_replay"):
        verify_native_lock(model, board, item, case, node, locked, originals, package)
    locks.append(lock)


def promote(registry, extension):
    mid, rank = extension["model_id"], extension["rank"]
    model = registry["records"][mid]
    assert model["frequency_rank"] == rank and model["label"] == "APPROX"
    boards, pins = extension["boards"], extension["pins"]
    assert 3 <= len(boards) <= 5 and len({b["flop"] for b in boards}) == len(boards) == len(pins)
    for b in boards:
        p, = (p for p in pins if (p["flop"], p["turn"], p["public_board"]) == (b["flop"], b["turn"], b["public_board"]))
        code = p["viewer_archive_code"]
        assert b["source_sha256"] == p["original_GTO_SHA256"]
        assert b["strict_full_street_combo_reachable"] == p["GTO_strict_combos"] > 0
        assert b["model_assumed_spr"] == model["assumed_model_node_spr"]
        assert abs(b["actual_spr"]/b["model_assumed_spr"] - 1) <= .05
        verify_case(code, p["viewer_sha256"], b["source_run_id"], model, b, "gto", b["source_sha256"], p["GTO_strict_combos"])
        lock, = b["nl2_locked_variants"]
        assert lock["sha256"] == p["actual_NL2_SHA256"] and lock["version"] == ("exp_ip" if b["acting_seat"] else "exp_oop")
        assert lock["observed_marginal_source_nodes"] > 0
        if lock["run_id"] == b["source_run_id"]:
            locked_code, locked_sha = code, p["viewer_sha256"]
        else:
            locked_code, locked_sha = p["locked_viewer_archive_code"], p["locked_viewer_sha256"]
        verify_case(locked_code, locked_sha, lock["run_id"], model, b, lock["version"], lock["sha256"], p["NL2_strict_combos"])
    model.update(label="CERT-MULTIBOARD", proven_exact_board_count=len(boards),
                 certified_3_to_5_exact_flop_boards=boards, blocked_reason=None)
    return model


def update_references(model, crosswalk, refs):
    rank_boards = model["certified_3_to_5_exact_flop_boards"]
    common = []
    examples = []
    for b in rank_boards:
        src = dict(source_run_id=b["source_run_id"], source_sha256=b["source_sha256"], spot=model["solver_profile"],
                   family=model["family"], version="gto", flop=b["flop"], turn=b["turn"], exact_solver_node_line=b["actual_exact_action_line"])
        common.append(dict(src, flop_line=b["exact_flop_action"], turn_spr=b["actual_spr"],
                           reference_status="CERT_EXACT_BOARD_GTO_ONLY"))
        examples.append(dict(src, actual_public_board=b["public_board"], exact_flop_actions=b["exact_flop_action"],
                             acting_seat=b["acting_seat"], actual_node_spr=b["actual_spr"],
                             model_assumed_node_spr=b["model_assumed_spr"], relative_spr_difference=b["relative_spr_error_pct"]/100,
                             reached_combos=b["exact_combo_reachable"], strict_full_street_reachable_combos=b["strict_full_street_combo_reachable"],
                             board_exact_match_to_model=False, available_for="EXACT_SOURCE_EXAMPLE_ONLY_NOT_GENERIC_CERT"))
    mid = model["model_id"]
    crosswalk["records"][mid].update(board_specific_certification_status="CERT_MULTIBOARD", best_exact_board_examples=examples,
                                     source_line_match_count=len(examples), same_history_within_1pct_spr_count=sum(e["relative_spr_difference"] <= .01 for e in examples))
    refs["items"][mid].update(reference_count=len(common), references=common,
                              note="Exact GTO and separately solved hero lock on each named board. Generic texture rows remain approximate.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    base = next(DATA / p for p in BASES if (DATA/p).is_file())
    registry = read(base)
    loaded = [read(p) for p in EXTENSIONS.glob("rank*.json")]
    assert loaded, "No verified extensions to apply"
    x_path, r_path = DATA/"nl2_hu_model_history_crosswalk.json", DATA/"nl2_hu_model_source_references.json"
    xwalk, refs = read(x_path), read(r_path)
    ordered = sorted(loaded, key=lambda x: x["rank"])
    for ext in ordered:
        update_references(promote(registry, deepcopy(ext)), xwalk, refs)
    variants = [read(p) for p in sorted((SOURCE/"lock_variants").glob("*.json"))]
    sources, locked, originals, links = read_replays()
    for item in variants:
        if not item.get("after_reverification"):
            append_lock(registry, item, locked, originals)
    seen, seen_gto = set(), set()

    def apply_replays(model_ids=None):
        changes = replay_updates(registry, locked, originals, links, seen, seen_gto, model_ids)
        apply_updates(registry, changes)
        for mid in changes:
            m = registry["records"][mid]
            update_references(m, xwalk, refs)
            if m["label"] == "APPROX":
                xwalk["records"][mid]["board_specific_certification_status"] = "APPROX"
                refs["items"][mid]["note"] = "Fewer than three named flops survive the original two-seat action-path replay."
        return changes

    contract = rendered_contract(registry["records"])
    excluded = {}

    def reconcile_routes():
        for mid in apply_routes(registry["records"], contract, excluded):
            model = registry["records"][mid]
            update_references(model, xwalk, refs)
            if model["label"] == "APPROX":
                xwalk["records"][mid]["board_specific_certification_status"] = "APPROX"
                refs["items"][mid]["note"] = "Fewer than three named flops match the rendered trainer action order and bet sizes."

    changes = apply_replays()
    reconcile_routes()
    repairs = sorted((read(p) for p in (SOURCE/"reverified").glob("rank*.json")), key=lambda e:e["rank"])
    for repair in repairs:
        for pin in repair["pins"]:
            assert pin["GTO_compatible_hole_card_pairs"] >= pin["GTO_strict_combos"] > 0
            assert pin["NL2_compatible_hole_card_pairs"] >= pin["NL2_strict_combos"] > 0
        restored = promote(registry, deepcopy(repair))
        restored.pop("remaining_exact_board_evidence", None)
        update_references(restored, xwalk, refs)
    repaired_ids = {r["model_id"] for r in repairs}
    for item in variants:
        if item.get("after_reverification"):
            assert item["model_id"] in repaired_ids
            append_lock(registry, item, locked, originals)
    repair_changes = apply_replays(repaired_ids)
    reconcile_routes()
    assert seen == set(locked) and seen_gto == set(originals), "Raw source missing from the named registry boards"
    labels = collections.Counter(r["label"] for r in registry["records"].values())
    registry.update(CERT_MULTIBOARD=labels["CERT-MULTIBOARD"], APPROX=labels["APPROX"])
    view = dict(schema="NL2_EXACT_VERIFIED_EXTENSIONS_V1", models=ordered, lock_variants=variants, board_reach_updates=changes,
                reverified_models=repairs, reverified_board_reach_updates=repair_changes, locked_medium_reports=sources,
                trainer_route_contract=contract, trainer_route_exclusions=list(excluded.values()))
    registry["trainer_route_contract_schema"] = contract["schema"]
    registry["exact_source_extensions"] = {}
    for e in ordered + repairs:
        mid = e["model_id"]
        selected = active_pins(registry["records"][mid], e["pins"])
        if selected:
            registry["exact_source_extensions"][mid] = selected
    registry["base_registry_schema"] = registry["schema"]
    registry["schema"] = "NL2_HU_392_MULTIBOARD_CERT_STATUS_VERIFIED_EXTENSIONS_V1"
    registry["base_registry"] = base.name
    registry["base_registry_sha256"] = hashlib.sha256(base.read_bytes()).hexdigest()
    summary = audit(registry)
    assert summary["cert_multiboard"] + summary["approx"] == registry["TOTAL"] == 392
    registry["all_cert_lock_medium"] = summary["aggregate"]
    dump(x_path, xwalk)
    dump(r_path, refs)
    dump(DATA/"nl2_hu_verified_extensions.json", view)
    dump(args.out, registry)
    print(f'{summary["cert_multiboard"]} CERT / {summary["approx"]} APPROX')


if __name__ == "__main__":
    main()
