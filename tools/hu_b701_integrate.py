"""Combine independently replayed B699/B700 groups in one protected registry update."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from hu_b580_rank27_rivers import suit_isomorphism_class

CENTRAL = (
    "data/nl2_hu_multiboard_status_current.json",
    "data/nl2_hu_verified_extensions.json",
    "data/nl2_hu_model_history_crosswalk.json",
    "data/nl2_hu_model_source_references.json",
)
MODELS = {84: "ln-3bp-3b_t_model-ciziut", 121: "ln-3bp-3b_t_model-yap927"}
EXTRA_ARCHIVES = {
    84: set(),
    121: {"data/solver_evidence/NL2_B698_R121_TD8D4S.zip",
          "data/solver_evidence/NL2_B698_R121_TS9S6H.zip"},
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def integrate(args):
    before_raw = args.before.read_bytes()
    assert Path(CENTRAL[0]).read_bytes() == before_raw
    before = json.loads(before_raw)
    assert before["TOTAL"] == 392 and len(before["records"]) == 392
    protected = {key: value for key, value in before["records"].items()
                 if value["label"] == "CERT-MULTIBOARD"}
    assert len(protected) == before["CERT_MULTIBOARD"] >= 148
    assert all(before["records"][mid]["label"] == "APPROX" for mid in MODELS.values())
    current_data = Path("data").resolve()
    payload = {}
    groups = {}
    for rank, folder in ((84, args.rank84), (121, args.rank121)):
        stage = folder.resolve()
        assert stage != current_data and current_data not in stage.parents
        assert stage.is_dir()
        path = stage / "solver_evidence" / "reverified" / ("rank" + str(rank) + ".json")
        group = json.loads(path.read_bytes())
        assert (group["rank"], group["model_id"]) == (rank, MODELS[rank])
        assert len(group["boards"]) == len(group["pins"]) == 3
        assert len({suit_isomorphism_class(board["flop"]) for board in group["boards"]}) == 3
        pinned_archives = {}
        for board, pin in zip(group["boards"], group["pins"], strict=True):
            assert all(board[key] == pin[key] for key in ("flop", "turn", "public_board"))
            public = board["public_board"]
            flop_cards = {board["flop"][i:i + 2] for i in (0, 2, 4)}
            assert len(public) == 8 and public[-2:] == board["turn"]
            assert len(flop_cards) == 3 and board["turn"] not in flop_cards
            assert {public[i:i + 2] for i in (0, 2, 4)} == flop_cards
            assert board["actual_spr"] == pin["actual_spr"]
            assert board["acting_seat"] == 0 and board["actual_exact_action_line"] == "x b33 c/"
            assert pin["GTO_compatible_hole_card_pairs"] >= pin["GTO_strict_combos"] > 0
            assert pin["NL2_compatible_hole_card_pairs"] >= pin["NL2_strict_combos"] > 0
            assert pin["rendered_decision_hands"] and board["nl2_locked_variants"]
            pinned_archives["data/solver_evidence/NL2_" + pin["archive_code"] + ".zip"] = pin["archive_sha256"]
        groups[rank] = group
        for source in sorted(stage.rglob("*")):
            assert not source.is_symlink(), source
            if not source.is_file():
                continue
            relative = source.relative_to(stage)
            assert ".." not in relative.parts
            target = Path("data") / relative
            key = target.as_posix()
            assert key not in CENTRAL
            raw = source.read_bytes()
            named = "b699" in key.lower() or "b700" in key.lower()
            promoted = key == "data/solver_evidence/reverified/rank" + str(rank) + ".json"
            original_archive = key in EXTRA_ARCHIVES[rank]
            if original_archive:
                assert digest(raw) == pinned_archives[key], (key, "original archive SHA mismatch")
            if not (named or promoted or original_archive):
                assert target.is_file() and target.read_bytes() == raw, key
            if key in payload:
                assert payload[key] == raw, (key, "conflicting staged sources")
            payload[key] = raw
    assert set(groups) == set(MODELS)
    for key, raw in payload.items():
        target = Path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    subprocess.run([sys.executable, "tools/hu_apply_cert_extensions.py", "--out", CENTRAL[0]], check=True)
    after = json.loads(Path(CENTRAL[0]).read_bytes())
    assert set(after["records"]) == set(before["records"])
    for key, record in before["records"].items():
        if key not in MODELS.values():
            assert after["records"][key] == record, key
    for key, record in protected.items():
        assert after["records"][key] == record, key
    for rank, mid in MODELS.items():
        row = after["records"][mid]
        assert row["label"] == "CERT-MULTIBOARD" and row["proven_exact_board_count"] == 3
        assert len(row["certified_3_to_5_exact_flop_boards"]) == 3
    assert (after["CERT_MULTIBOARD"], after["APPROX"], after["TOTAL"]) == (
        before["CERT_MULTIBOARD"] + 2, before["APPROX"] - 2, 392)
    report = dict(schema="NL2_HU_B701_TWO_MODEL_INTEGRATION_V1",
        before_registry_sha256=digest(before_raw),
        after_registry_sha256=digest(Path(CENTRAL[0]).read_bytes()),
        before_certified=before["CERT_MULTIBOARD"], after_certified=after["CERT_MULTIBOARD"],
        before_approx=before["APPROX"], after_approx=after["APPROX"],
        preserved_certified_records=len(protected), unchanged_other_records=390,
        promoted_ranks=sorted(MODELS), certified_named_boards=6,
        original_native_solves_repeated=0,
        source_stage_sha256={key: digest(raw) for key, raw in payload.items()},
        protected_record_sha256={key: digest(canonical(record)) for key, record in protected.items()})
    report_path = "data/nl2_hu_b701_two_model_integration.json"
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    paths = sorted(set(payload) | set(CENTRAL) | {report_path})
    args.paths.write_text("\n".join(paths) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ("source_stage_sha256", "protected_record_sha256")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("rank84", "rank121", "before", "paths"):
        parser.add_argument("--" + name, type=Path, required=True)
    integrate(parser.parse_args())
