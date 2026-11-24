"""Find repeats of saved two-seat-positive public boards on the actual current routes."""
import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from hu_trainer_route_gate import compatible, missing_visible_rows

DATA = Path("data")
EVIDENCE = DATA / "solver_evidence"
ASSIGNED = {29, 92, 93, 94, 104, 105, 255}


def read(path):
    return json.loads(path.read_bytes())


def board_key(board):
    return (board["public_board"], board["actual_exact_action_line"], board["acting_seat"], board["source_sha256"])


def collect(records):
    donors = {}
    counts = Counter()

    def add(board, spot, origin):
        donors.setdefault((spot, *board_key(board)), board)
        counts[origin] += 1

    for record in records.values():
        boards = record["certified_3_to_5_exact_flop_boards"] + record.get("remaining_exact_board_evidence", [])
        for board in boards:
            if board.get("compatible_hole_card_pairs", 0) and any(x.get("compatible_hole_card_pairs", 0) for x in board["nl2_locked_variants"]):
                add(board, record["solver_profile"], "current_positive_board_rows")

    old = read(DATA / "nl2_hu_multiboard_status_v53_b465_rank218.json")["records"]
    ext = read(DATA / "nl2_hu_verified_extensions.json")
    extra = defaultdict(list)
    for group in ext["models"] + ext["reverified_models"]:
        extra[group["model_id"]].extend(group["boards"])
    for mid, updates in ext["board_reach_updates"].items():
        model = old[mid]
        boards = model["certified_3_to_5_exact_flop_boards"] + model.get("remaining_exact_board_evidence", []) + extra[mid]
        indexed = {board_key(b): b for b in boards}
        for update in updates:
            if not (update.get("gto") or {}).get("compatible_hole_card_pairs", 0):
                continue
            if not any(lock and lock.get("compatible_hole_card_pairs", 0) for lock in update["locks"]):
                continue
            key = (update["public_board"], update["line"], update["seat"], update["gto_sha256"])
            board = indexed[key]
            assert update["gto"]["run_id"] == board["source_run_id"]
            add(board, model["solver_profile"], "historical_paired_board_rows")

    paths = set((EVIDENCE / "reverified").glob("rank*.json")) | set((EVIDENCE / "partial").glob("*rank*.json")) | set(DATA.glob("nl2_hu_b*_partial.json"))
    for path in sorted(paths):
        obj = read(path)
        group = obj.get("group", obj)
        if not {"model_id", "boards", "pins"} <= group.keys():
            continue
        for board, pin in zip(group["boards"], group["pins"], strict=True):
            if not all(pin.get(k, 0) > 0 for k in ("GTO_compatible_hole_card_pairs", "NL2_compatible_hole_card_pairs")):
                continue
            assert (board["flop"], board["public_board"], board["source_sha256"]) == (pin["flop"], pin["public_board"], pin["original_GTO_SHA256"])
            add(board, records[group["model_id"]]["solver_profile"], "paired_reverified_or_partial_rows")

    for model in read(DATA / "nl2_hu_b477_raw_river_pairs.json")["models"].values():
        for flop, pair in model["flops"].items():
            for public in pair["positive_paired_rivers"]:
                assert all(pair[v]["boards"][public]["compatible_hole_card_pairs"] > 0 for v in ("gto", "locked"))
                board = dict(flop=flop, public_board=public, actual_exact_action_line=model["exact_line"], acting_seat=model["acting_seat"],
                             actual_spr=model["effective_stack_bb"] / model["pot_bb"], source_sha256=pair["gto"]["source_sha256"], source_run_id=pair["gto"]["source_run_id"])
                add(board, records[model["model_id"]]["solver_profile"], "B477_original_pairs")
    return donors, counts


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    registry_file = DATA / "nl2_hu_multiboard_status_current.json"
    registry = read(registry_file)
    records = registry["records"]
    assert len(records) == 392
    routes = json.loads(subprocess.check_output(["node", "tools/hu_trainer_route_contract.cjs", *records],
                                               input=json.dumps(list(records)), text=True))["routes"]
    donors, counts = collect(records)
    survivors = {}
    for mid, model in records.items():
        rank = model["frequency_rank"]
        if model["label"] != "APPROX" or rank in ASSIGNED or model["assumed_model_node_spr"] <= 0:
            continue
        cases = defaultdict(list)
        for (spot, *_), board in donors.items():
            if spot != model["solver_profile"] or abs(board["actual_spr"] / model["assumed_model_node_spr"] - 1) > .05:
                continue
            if compatible(routes[mid], board) and not missing_visible_rows(routes[mid], board):
                cases[board["flop"]].append(board_key(board))
        if cases:
            survivors[rank] = dict(sorted(cases.items()))
    report = dict(schema="NL2_B718_SAVED_TWO_SEAT_SOURCE_SCAN_V1", registry_sha256=hashlib.sha256(registry_file.read_bytes()).hexdigest(),
                  CERT_MULTIBOARD=registry["CERT_MULTIBOARD"], APPROX=registry["APPROX"], total=392, excluded_assigned_ranks=sorted(ASSIGNED),
                  distinct_named_donor_nodes=len(donors), source_rows=counts,
                  single_flop_upper_bounds={k: sorted(v) for k, v in sorted(survivors.items()) if len(v)==1},
                  multiple_distinct_flop_upper_bounds={k: v for k, v in sorted(survivors.items()) if len(v)>=2},
                  scope="Named paired sources in current, original historical two-seat correction, reverified, published partial and B477 raw-source records. A possible donor still needs matching original private-hand masks at every displayed decision.")
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
