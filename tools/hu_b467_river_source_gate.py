"""Independently certify exact river decisions carried inside three pinned B453 source pairs."""
import argparse
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path

from hu_b453_rank32_three_original_source_gate import RUST_PIN, SOURCE_PIN, source_one
from hu_cert_lock_medium_audit import audit
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope, locked_model_gain, source_nodes


DATA = Path("data")
EVIDENCE = DATA / "solver_evidence"
BASE = DATA / "nl2_hu_multiboard_status_v51_b453_rank32.json"
PROOF = DATA / "nl2_hu_b467_rank97_147_verified_river_nodes.json"
PARENT = "ln-opfr-t_model-qx9t0u"
TARGETS = {
    "ln-opfr-r_model-1bkyftx": (97, "b100 c/b50 c/", 2.083),
    "ln-opfr-r_model-z20jim": (147, "b100 c/x x/", 4.667),
}
PINS = {
    "B447_R32_AS_KH_3D": "a319f06afc7a101191706fe92c1f7fc74d0233ab6aae797667175f0e46df9a45",
    "B449_R32_KS_7H_2D": "a35c186c7140f25f783a4c1fec6502372d179bae4112ecc69bd6aff759510c2c",
    "B452_R32_KS_QH_4D": "da8d43eb92b8915676f31f62cb48618a1a57d12eea5140906f4fece55f9c3094",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode()


def json_bytes(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode()


def publish_bytes(path, data, verify):
    if verify:
        assert path.read_bytes() == data, f"Stale derived source {path}"
    else:
        path.write_bytes(data)


def originals(pin):
    code = pin["archive_code"]
    archive = (EVIDENCE / f"NL2_{code}.json.gz").read_bytes()
    assert sha(archive) == PINS[code]
    pack = json.loads(gzip.decompress(archive))
    assert pack["schema"] == f"NL2_{code}_ORIGINAL_RUST_GTO_AND_NL2_OOP_V1"
    assert pack["pinned_solver"] == SOURCE_PIN and pack["pinned_rust"] == RUST_PIN
    flop, turn, run = pin["flop"], pin["turn"], pin["source_run_id"]
    assert (pack["flop"], pack["turn"], pack["run_id"], pack["source_run_id"]) == (flop, turn, run, run)
    batch = code.split("_")[0].lower()
    first = json.loads((DATA / f"nl2_hu_{batch}_rank32_first_source_proof.json").read_bytes())
    assert first["source_archive_sha256"] == PINS[code] and first["target_model"] == PARENT
    gto, exp = pack["source_arrays"]
    for s, version, prior, digest in (
        (gto, "gto", first["authentic_GTO"], pin["original_GTO_SHA256"]),
        (exp, "exp_oop", first["partially_NL2_pool_locked_EXP_OOP"], pin["actual_NL2_SHA256"]),
    ):
        assert sha(compact(s["root"])) == s["root_sha256"] == s["manifest"]["file_flop_sha256"]
        assert sha(compact(s["subgame"])) == s["source_sha256"] == digest
        source_one(s, version, flop, turn, prior, run)
    return (gto, exp)


def extract(source, line, model_spr, pin):
    root, sub = source["root"], source["subgame"]
    version = source["version"]
    # Pick a public river deterministically, before applying private-hand reach.
    matches = sorted((n for n in sub["nodes"] if len(n["board"]) == 10 and n["line"] == line and n["player"] == 0),
                     key=lambda n: n["board"])
    assert len({n["board"] for n in matches}) == len(matches) and matches
    node = matches[0]
    mask, _ = game_reach(root, sub)
    key = "|".join((node["board"], line, "0"))
    actual = compatible_node_reach(root, sub, node, mask[key])
    assert actual["count"] > 0 and actual["compatible_hole_card_pairs"] > 0
    result, = source_nodes(dict(sub, nodes=[node]), {"nodes": {key: actual}})
    assert abs(result["node_spr"] - model_spr) / model_spr <= .01
    assert result["strictly_reachable_combos"] == actual["count"]
    assert result["public_board"][6:8] == pin["turn"]
    scope = lock_scope(sub, source["manifest"]["locks"], version)
    if version == "exp_oop":
        assert scope["observed_marginal_source_nodes"] > 0 and sub["info"]["hero_gap_pct"] <= .5
    case = dict(spot="UTG_CO", pot_family="SRP", version=version, source_sha256=source["source_sha256"],
                flop=pin["flop"], turn=pin["turn"], flop_line="b100 c", hands_by_seat=sub["hands"],
                nodes=[result], gto_exploitability_pct=sub["info"]["gto_expl_pct"],
                locked_hero_gap_pct=sub["info"].get("hero_gap_pct"), villain_lock_scope=scope)
    cards = {cardkey(h) for h, bits in zip(sub["hands"][0], base64.b64decode(actual["mask"])) if bits}
    return case, actual["compatible_hole_card_pairs"], cards


def export_board(parent_pin, parent_board, sources, rank, line, model_spr, verify):
    gto, exp = sources
    g, gpairs, ghands = extract(gto, line, model_spr, parent_pin)
    e, epairs, ehands = extract(exp, line, model_spr, parent_pin)
    node, e_node = g["nodes"][0], e["nodes"][0]
    assert node["public_board"] == e_node["public_board"] and node["node_spr"] == e_node["node_spr"]
    assert node["public_board"].startswith(parent_board["public_board"])
    run, archive = parent_pin["source_run_id"], parent_pin["archive_code"]
    code = f"R{rank}_{run}"
    output = dict(schema="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1", source_run_id=run,
                  original_archive_sha256=PINS[archive], errors=[], no_generic_texture_certification=True,
                  artifacts=[dict(cases=[g, e])])
    path = EVIDENCE / f"NL2_MULTIBOARD_{code}.json.gz"
    if verify:
        encoded = path.read_bytes()
        assert gzip.decompress(encoded) == compact(output)
    else:
        encoded = gzip.compress(compact(output), mtime=0, compresslevel=9)
        path.write_bytes(encoded)
    scope = e["villain_lock_scope"]
    lock = dict(version="exp_oop", run_id=run, sha256=exp["source_sha256"], source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",
                source_not_real_per_combo_observation=True, villain_observed_pattern_node_share_pct=scope["coverage_pct"],
                unknown_history_frequency_filled_with_default=bool(scope["imputed_assumption_nodes"]),
                observed_marginal_source_nodes=scope["observed_marginal_source_nodes"],
                assumed_default_source_nodes=scope["imputed_assumption_nodes"], unlocked_source_nodes=scope["unmatched_nodes"],
                hero_model_gain_bb=locked_model_gain(exp["subgame"], "exp_oop"), true_hero_gap_pct=e["locked_hero_gap_pct"])
    b = dict(flop=parent_pin["flop"], turn=parent_pin["turn"], river=node["public_board"][-2:],
             public_board=node["public_board"], actual_exact_action_line=line, acting_seat=0, exact_flop_action="b100 c",
             actual_pot_bb=node["pot_bb"], actual_effective_stack_bb=node["remaining_bb"], actual_spr=node["node_spr"],
             model_assumed_spr=model_spr, relative_spr_error_pct=round(100*abs(node["node_spr"]-model_spr)/model_spr, 6),
             genuine_gto_exploitability_pct=g["gto_exploitability_pct"], source_run_id=run, source_sha256=gto["source_sha256"],
             source_kind="PINNED_PREFLOP_CFR", assumed_preflop_ranges=False, exact_combo_reachable=node["source_reachable_combos"],
             strict_full_street_combo_reachable=node["strictly_reachable_combos"], exact_node_actions=node["source_actions"],
             medium_50pct_eligible_combos=node["medium_50pct_eligible_combos"],
             b50_nonpolarized_relative_equity_research_candidate=node["b50_nonpolarized_relative_equity_research_candidate"],
             nl2_locked_variants=[lock], flop_texture=parent_board["flop_texture"])
    p = dict(flop=b["flop"], turn=b["turn"], river=b["river"], public_board=b["public_board"], source_run_id=run,
             archive_code=archive, archive_sha256=PINS[archive], viewer_archive_code=code, viewer_sha256=sha(encoded),
             original_GTO_SHA256=gto["source_sha256"], actual_NL2_SHA256=exp["source_sha256"], actual_spr=b["actual_spr"],
             GTO_strict_combos=node["strictly_reachable_combos"], NL2_strict_combos=e_node["strictly_reachable_combos"],
             GTO_compatible_hole_card_pairs=gpairs, NL2_compatible_hole_card_pairs=epairs, common_legal_hero_combos=len(ghands & ehands),
             pool_observed_marginal_lock_nodes=scope["observed_marginal_source_nodes"], pool_assumed_lock_nodes=scope["imputed_assumption_nodes"],
             pool_unlocked_nodes=scope["unmatched_nodes"], medium50_exact_research_candidate=b["b50_nonpolarized_relative_equity_research_candidate"])
    return b, p


def apply_to_registry(status, proof):
    """Apply the verified B467 records to a cumulative registry, retaining all other promotions."""
    for model_id, group in proof["models"].items():
        target = status["records"][model_id]
        boards = group["boards"]
        assert (target["frequency_rank"], target["solver_profile"], target["street"], target["source_model_id"]) == (group["rank"], "UTG_CO", 2, PARENT)
        assert len({b["flop"] for b in boards}) == len(boards) == 3
        if target["label"] == "CERT-MULTIBOARD":
            assert target["certified_3_to_5_exact_flop_boards"] == boards
            continue
        assert target["label"] == "APPROX"
        target.update(label="CERT-MULTIBOARD", proven_exact_board_count=3, certified_3_to_5_exact_flop_boards=boards, blocked_reason=None)
        status["CERT_MULTIBOARD"] += 1
        status["APPROX"] -= 1
    status["B467_rank97_147_river_sources"] = proof["models"]
    assert status["CERT_MULTIBOARD"] + status["APPROX"] == status["TOTAL"] == 392
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    data = json.loads(BASE.read_bytes())
    groups = {mid: dict(rank=r, actor="UTG_OOP", line=line, spot="UTG_CO", boards=[], pins=[])
              for mid, (r, line, _) in TARGETS.items()}
    parent = data["records"][PARENT]
    baseline_boards = {b["flop"]: b for b in parent["certified_3_to_5_exact_flop_boards"]}
    parent_pins = data["B453_rank32_three_true_original_GTO_NL2_OOP_flops"]["pins"]
    assert len(parent_pins) == 3 and {p["archive_code"] for p in parent_pins} == set(PINS)
    for pin in parent_pins:
        pair = originals(pin)
        for mid, (rank, line, spr) in TARGETS.items():
            m = data["records"][mid]
            assert (m["source_model_id"], m["assumed_model_node_spr"], m["label"]) == (PARENT, spr, "APPROX")
            board, sample = export_board(pin, baseline_boards[pin["flop"]], pair, rank, line, spr, args.verify)
            groups[mid]["boards"].append(board)
            groups[mid]["pins"].append(sample)
    proof = dict(schema="NL2_HU_B467_TWO_SEAT_RIVER_ORIGINAL_PAIRS_V1", models=groups,
                 river_selection="LEXICOGRAPHICALLY_FIRST_PUBLIC_RIVER_BEFORE_PRIVATE_MASK",
                 NL2_lock_scope="STREET_AND_SIZE_MARGINAL", exact_public_board_policy="NAMED_ONLY")
    publish_bytes(PROOF, json_bytes(proof), args.verify)
    extensions = EVIDENCE / "extensions"
    if not args.verify:
        extensions.mkdir(exist_ok=True)
    for model_id, group in groups.items():
        extension = dict(model_id=model_id, **group)
        publish_bytes(extensions / f'rank{group["rank"]}.json', json_bytes(extension), args.verify)
    before, after = audit(data), audit(apply_to_registry(copy.deepcopy(data), proof))
    assert (after["cert_multiboard"]-before["cert_multiboard"], before["approx"]-after["approx"]) == (2, 2)
    assert after["aggregate"]["named_board_proofs"]-before["aggregate"]["named_board_proofs"] == 6
    assert after["aggregate"]["paired_hero_locked_source_variants"]-before["aggregate"]["paired_hero_locked_source_variants"] == 6
    print(f'Confirmed ranks 97 and 147, {after["aggregate"]["named_board_proofs"]-before["aggregate"]["named_board_proofs"]} exact original pairs')


if __name__ == "__main__":
    main()
