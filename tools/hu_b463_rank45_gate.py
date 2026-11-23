#!/usr/bin/env python3
"""Certify the ISO check/check turn decision from the three preregistered full-tree solves."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope, locked_model_gain, source_nodes


DATA = Path("data")
PACKS = DATA / "solver_evidence"
MODEL = "ln-iso-iso_t_model-1x553s3"
PROFILE = "ISO_BTN_CO"
LINE = "x x/"
SPR = 10.105
SOLVER = "abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST = "9d1509fe5077d019825f833eed04b16d342dfda1"
SCHEMA = "NL2_HU_392_MULTIBOARD_CERT_STATUS_V52_B463_R45"
BASE = DATA / "nl2_hu_multiboard_status_v51_b453_rank32.json"
TARGET = DATA / "nl2_hu_multiboard_status_v52_b463_rank45.json"
GATE = DATA / "nl2_hu_b463_rank45_three_board_gate.json"
VERSIONS = ("gto", "exp_oop")
PRIOR = (
    ("B457_R45_AS_KH_3D", "AsKh3d", "8s", 45091643550, "c967875bc8ecaf3a4c07fd363eac0b2ebe64e845679675839a6ac69091d25548"),
    ("B458_R45_8S_8H_3D", "8s8h3d", "5s", 45091753191, "371d06fc37c70c7ba779d49c4e61de39972b9f682fcb3542793dd28bf1020e40"),
)
THIRD = ("B463_R45_7S_5H_3D", "7s5h3d", "6c")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()


def archive_path(code):
    return PACKS / f"NL2_{code}.json.gz"


def load_new(downloads, run_id):
    code, flop, turn = THIRD
    arrays = []
    for version in VERSIONS:
        root = downloads / version
        evidence = root / "trainer/evidence"
        assert (evidence / "poker-solver-pin.txt").read_text().strip() == SOLVER
        assert (evidence / "rust-pin.txt").read_text().strip() == RUST
        m = read(evidence / f"{PROFILE}-{flop}-{version}.json")
        outdir = root / "solver/postflop/out" / PROFILE / version
        flopfile = outdir / f"{flop}_multiboard.json"
        assert digest(flopfile.read_bytes()) == m["file_flop_sha256"]
        s = dict(version=version, manifest=m, root=read(flopfile),
                 root_sha256=m["file_flop_sha256"], subgame=None, subgame_job=None, source_sha256=None)
        if m["cases"]:
            case, = m["cases"]
            subfile = outdir / f"{flop}_xx_{turn}.json"
            assert case["source_path"] == str(subfile.relative_to(root / "solver/postflop"))
            assert digest(subfile.read_bytes()) == case["source_sha256"]
            s.update(subgame=read(subfile), subgame_job=read(subfile.with_suffix(".job.json")),
                     source_sha256=case["source_sha256"])
        arrays.append(s)
    return dict(schema=f"NL2_{code}_ORIGINAL_RUST_GTO_AND_NL2_OOP_V1",
                run_id=run_id, source_run_id=run_id, flop=flop, turn=turn,
                pinned_solver=SOLVER, pinned_rust=RUST, source_arrays=arrays)


def validate_source(source, version, flop, turn):
    m, root = source["manifest"], source["root"]
    assert source["version"] == version
    assert m["schema"] == "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
    assert (m["spot"], m["version"], m["flop"]) == (PROFILE, version, flop)
    assert m["solver_pin"] == "f0a173b3d9331c4ff8697359a838094f76babb35f16133e37bbd0bfb203b5253"
    assert m["solver_ranges_sha256"] == "f2a302b483c79995ed90031b62e65a202ae7a1fdc8695f8940fe3e8291fb2bba"
    ranges = m["preflop_ranges"]
    assert ranges["source"] == "ASSUMED_EXPLICIT_169CLASS"
    assert (ranges["profile"]["oop"], ranges["profile"]["ip"]) == ("CO", "BTN")
    assert len(ranges["oop_169"]) == len(ranges["ip_169"]) == 169
    assert (m["root_pot_bb"], m["root_remaining_bb"]) == (9.5, 96)
    assert m["flop_size_profile"] == "full" and not m["restricted_tree_assumption"]
    assert m["flop_line_policy"] == "checkcheck" and m["selected_lines"] == ["x x"]
    assert m["turn_sizing_mode"] == "default" and m["turns"] == [turn]
    assert m["solved_cases"] == len(m["cases"]) <= 1 and not m["failures"]
    assert digest(compact(root)) == source["root_sha256"] == m["file_flop_sha256"]
    assert (root["flop"], root["pot"], root["stack"]) == (flop, 950, 9600)
    assert root["info"]["gto_expl_pct"] <= .5
    if not m["cases"]:
        skipped, = m["skipped"]
        assert (skipped["line"], skipped["turn"]) == ("x x", turn)
        assert skipped["reason"] in ("NO_BOTH_PLAYER_REACH", "ZERO_LEGAL_PLAYER_RANGE_AFTER_TURN_CARD_BLOCKERS",
                                     "RUST_ENGINE_EXCLUDED_EMPTY_REACH_RANGE")
        assert source["subgame"] is None and source["source_sha256"] is None
        return None
    case, = m["cases"]
    sub, job = source["subgame"], source["subgame_job"]
    assert not m["skipped"] and (case["line"], case["turn"]) == ("x x", turn)
    assert digest(compact(sub)) == case["source_sha256"] == source["source_sha256"]
    assert (sub["flop"], sub["turn"], sub["line0"]) == (flop, turn, "x x")
    assert sub["info"]["gto_expl_pct"] == case["gto_gap_pct"] <= .5
    assert job["rake_rate"] == .05 and job["rake_cap"] == 1000
    assert job["turn_oop"] == job["turn_ip"] == "50%,100%"
    if version == "gto":
        assert job.get("hero") is None and not job.get("locks") and case["hero_gap_pct"] is None
    else:
        assert job["hero"] == 0 and job["locks"] and m["locks"] and sub["info"]["lock_stats"]
        assert sub["info"]["hero_gap_pct"] == case["hero_gap_pct"] <= .5
    node, = (n for n in sub["nodes"] if len(n["board"]) == 8 and n["line"] == LINE and n["player"] == 0)
    assert node["board"][-2:] == turn
    assert {node["board"][i:i+2] for i in (0, 2, 4)} == {flop[i:i+2] for i in (0, 2, 4)}
    spr = (sub["stack"] - max(node["bets"])) / node["pot"]
    assert abs(spr - SPR) / SPR <= .01
    masks, _ = game_reach(root, sub)
    key = "|".join((node["board"], LINE, "0"))
    masks[key] = compatible_node_reach(root, sub, node, masks[key])
    if masks[key]["count"] == 0:
        return None
    result, = source_nodes(dict(sub, nodes=[node]), {"nodes": {key: masks[key]}})
    assert result["strictly_reachable_combos"] == masks[key]["count"]
    result["compatible_hole_card_pairs"] = masks[key]["compatible_hole_card_pairs"]
    result["compatible_opponent_combos"] = masks[key]["compatible_opponent_combos"]
    return result


def exact_pair(pack, code, flop, turn, run_id, archive_sha):
    assert (pack["run_id"], pack["source_run_id"], pack["flop"], pack["turn"]) == (run_id, run_id, flop, turn)
    assert pack["schema"] == f"NL2_{code}_ORIGINAL_RUST_GTO_AND_NL2_OOP_V1"
    assert (pack["pinned_solver"], pack["pinned_rust"]) == (SOLVER, RUST)
    gto, exp = pack["source_arrays"]
    g = validate_source(gto, "gto", flop, turn)
    e = validate_source(exp, "exp_oop", flop, turn)
    assert gto["manifest"]["preflop_ranges"] == exp["manifest"]["preflop_ranges"]
    pin = dict(flop=flop, turn=turn, source_run_id=run_id, archive_code=code, archive_sha256=archive_sha,
               original_GTO_SHA256=gto["source_sha256"], actual_NL2_SHA256=exp["source_sha256"],
               GTO_strict_combos=g["strictly_reachable_combos"] if g else 0,
               NL2_strict_combos=e["strictly_reachable_combos"] if e else 0)
    if g is None or e is None:
        return None, pin
    assert g["public_board"] == e["public_board"] and g["node_spr"] == e["node_spr"]
    scope = lock_scope(exp["subgame"], exp["manifest"]["locks"], "exp_oop")
    observed, assumed, unlocked = (scope[k] for k in ("observed_marginal_source_nodes", "imputed_assumption_nodes", "unmatched_nodes"))
    assert observed > 0
    variant = dict(version="exp_oop", run_id=run_id, sha256=pin["actual_NL2_SHA256"],
                   source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY", source_not_real_per_combo_observation=True,
                   villain_observed_pattern_node_share_pct=scope["coverage_pct"],
                   unknown_history_frequency_filled_with_default=bool(assumed), observed_marginal_source_nodes=observed,
                   assumed_default_source_nodes=assumed, unlocked_source_nodes=unlocked,
                   hero_model_gain_bb=locked_model_gain(exp["subgame"], "exp_oop"),
                   true_hero_gap_pct=exp["subgame"]["info"]["hero_gap_pct"])
    candidate = g["b50_nonpolarized_relative_equity_research_candidate"]
    board = dict(flop=flop, turn=turn, public_board=g["public_board"], actual_exact_action_line=LINE,
                 acting_seat=0, exact_flop_action="x x", actual_pot_bb=g["pot_bb"], actual_effective_stack_bb=g["remaining_bb"],
                 actual_spr=g["node_spr"], model_assumed_spr=SPR, relative_spr_error_pct=round(100*abs(g["node_spr"]-SPR)/SPR, 6),
                 genuine_gto_exploitability_pct=gto["subgame"]["info"]["gto_expl_pct"], source_run_id=run_id,
                 source_sha256=pin["original_GTO_SHA256"], source_kind="ASSUMED_EXPLICIT_169CLASS", assumed_preflop_ranges=True,
                 exact_combo_reachable=g["source_reachable_combos"], strict_full_street_combo_reachable=pin["GTO_strict_combos"],
                 exact_node_actions=g["source_actions"], medium_50pct_eligible_combos=g["medium_50pct_eligible_combos"],
                 b50_nonpolarized_relative_equity_research_candidate=candidate, nl2_locked_variants=[variant],
                 flop_texture={"AsKh3d":"HIGH", "8s8h3d":"PAIRED", "7s5h3d":"LOW"}[flop])
    pin.update(GTO_compatible_hole_card_pairs=g["compatible_hole_card_pairs"],
               NL2_compatible_hole_card_pairs=e["compatible_hole_card_pairs"],
               GTO_compatible_opponent_combos=g["compatible_opponent_combos"],
               NL2_compatible_opponent_combos=e["compatible_opponent_combos"], actual_spr=g["node_spr"], pool_observed_marginal_lock_nodes=observed,
               pool_assumed_lock_nodes=assumed, pool_unlocked_nodes=unlocked, medium50_exact_research_candidate=candidate)
    return board, pin


def update_references(boards):
    cw_path = DATA / "nl2_hu_model_history_crosswalk.json"
    cw = read(cw_path)
    row = cw["records"][MODEL]
    examples, refs = [], []
    for b in boards:
        source = dict(source_run_id=b["source_run_id"], source_sha256=b["source_sha256"],
                      spot=PROFILE, family="ISO", version="gto", flop=b["flop"], turn=b["turn"], exact_solver_node_line=LINE)
        refs.append(dict(source, flop_line="x x", turn_spr=b["actual_spr"], reference_status="CERT_EXACT_BOARD_GTO_ONLY"))
        examples.append(dict(source, actual_public_board=b["public_board"], exact_flop_actions="x x", acting_seat=0,
                             actual_node_spr=b["actual_spr"], model_assumed_node_spr=SPR,
                             relative_spr_difference=b["relative_spr_error_pct"]/100, reached_combos=b["exact_combo_reachable"],
                             strict_full_street_reachable_combos=b["strict_full_street_combo_reachable"],
                             board_exact_match_to_model=False, available_for="EXACT_SOURCE_EXAMPLE_ONLY_NOT_GENERIC_CERT"))
    row.update(source_line_match_count=len(boards), same_history_within_1pct_spr_count=len(boards),
               candidate_status="MATCHED_ABSTRACT_HISTORY_AND_1PCT_SPR_ONLY",
               board_specific_certification_status="CERT_MULTIBOARD", best_exact_board_examples=examples)
    write(cw_path, cw)
    refs_path = DATA / "nl2_hu_model_source_references.json"
    idx = read(refs_path)
    idx["items"][MODEL].update(reference_count=len(refs), references=refs,
                               note="Three named ISO boards with exact GTO and separately locked CO-OOP sources. Preflop ranges assumed.")
    write(refs_path, idx)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    assert args.run_id > 0
    status = read(BASE)
    model = status["records"][MODEL]
    assert (model["frequency_rank"], model["family"], model["solver_profile"], model["label"], model["assumed_model_node_spr"]) == (45, "ISO", PROFILE, "APPROX", SPR)
    assert (status["CERT_MULTIBOARD"], status["APPROX"], status["EST"]) == (164, 228, 0)
    boards, pins = [], []
    for code, flop, turn, run_id, sha in PRIOR:
        raw = archive_path(code).read_bytes()
        assert digest(raw) == sha
        # Historical first-pass prose mislabeled rank 32. The archive and live model identify the exact node.
        board, pin = exact_pair(json.loads(gzip.decompress(raw)), code, flop, turn, run_id, sha)
        assert board
        boards.append(board)
        pins.append(pin)
    new_pack = load_new(args.downloads, args.run_id)
    raw = gzip.compress(compact(new_pack), mtime=0, compresslevel=9)
    new_board, new_pin = exact_pair(new_pack, *THIRD, args.run_id, digest(raw))
    archive_path(THIRD[0]).write_bytes(raw)
    pins.append(new_pin)
    if new_board:
        boards.append(new_board)
        assert len({b["flop"] for b in boards}) == 3 and len({p["source_run_id"] for p in pins}) == 3
        model.update(label="CERT-MULTIBOARD", proven_exact_board_count=3, certified_3_to_5_exact_flop_boards=boards, blocked_reason=None)
        status.update(schema=SCHEMA, CERT_MULTIBOARD=165, APPROX=227, parent_V51_sha256=digest(BASE.read_bytes()))
        status["B463_rank45_three_true_original_GTO_NL2_OOP_flops"] = dict(rank=45, spot=PROFILE, actor="CO_OOP", line=LINE,
                 flops=[b["flop"] for b in boards], pins=pins, preflop_source="ASSUMED_EXPLICIT_169CLASS",
                 per_private_hand_action_frequency_observed=False, no_generic_texture_certification=True)
        write(TARGET, status)
        update_references(boards)
    result = dict(model_id=MODEL, rank=45, classification=model["label"], positive_exact_boards=boards, pins=pins,
                  CERT_MULTIBOARD=status["CERT_MULTIBOARD"], APPROX=status["APPROX"], EST=status["EST"])
    write(GATE, result)
    print(f'Rank 45: {model["label"]} ({len(boards)} positive paired flops), {status["CERT_MULTIBOARD"]}/{status["APPROX"]}')


if __name__ == "__main__":
    main()
