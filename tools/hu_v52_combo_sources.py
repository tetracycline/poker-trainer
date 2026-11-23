"""Make the exact rank32 and rank45 GTO/EXP target combos available in the trainer."""
import gzip
import hashlib
import json
from pathlib import Path

from hu_b463_rank45_gate import validate_source
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope, source_nodes

DATA = Path("data")
ARCHIVES = DATA / "solver_evidence"
REGISTRY = DATA / "nl2_hu_multiboard_status_v52_b463_rank45.json"
GROUPS = (
    ("ln-opfr-t_model-qx9t0u", "B453_rank32_three_true_original_GTO_NL2_OOP_flops"),
    ("ln-iso-iso_t_model-1x553s3", "B463_rank45_three_true_original_GTO_NL2_OOP_flops"),
)


def export_board(rank, model, board, pin):
    code = pin["archive_code"]
    path = ARCHIVES / f"NL2_{code}.json.gz"
    packed = path.read_bytes()
    digest = hashlib.sha256(packed).hexdigest()
    run = pin["source_run_id"]
    if "archive_sha256" in pin:
        assert digest == pin["archive_sha256"]
    else:
        index = json.loads(path.with_suffix("").with_suffix(".index.json").read_text())
        assert digest == index["archive_sha256"] and index["run_id"] == run and index["paired_positive"]
    raw = json.loads(gzip.decompress(packed))
    assert raw["source_run_id"] == run
    assert raw["flop"] == board["flop"] == pin["flop"]
    assert raw["turn"] == board["turn"] == pin["turn"]
    assert sorted(s["version"] for s in raw["source_arrays"]) == ["exp_oop", "gto"]
    cases = []
    for source in raw["source_arrays"]:
        version = source["version"]
        gto = version == "gto"
        baseline = pin["original_GTO_SHA256" if gto else "actual_NL2_SHA256"]
        assert source["source_sha256"] == baseline
        assert source["manifest"]["spot"] == model["solver_profile"]
        assert source["manifest"]["pot_family"] == model["family"]
        assert source["manifest"]["version"] == version
        target = source["subgame"]
        if rank == 45:
            node = validate_source(source, version, board["flop"], board["turn"])
            assert node is not None
        else:
            mask, _ = game_reach(source["root"], target)
            matching = [n for n in target["nodes"]
                        if (n["board"], n["player"], n["line"]) ==
                        (board["public_board"], board["acting_seat"], board["actual_exact_action_line"])]
            assert len(matching) == 1
            node, = source_nodes(dict(target, nodes=matching), {"nodes": mask})
        assert node["strictly_reachable_combos"] == pin["GTO_strict_combos" if gto else "NL2_strict_combos"] > 0
        if gto:
            assert baseline == board["source_sha256"]
            assert node["medium_50pct_eligible_combos"] == board["medium_50pct_eligible_combos"]
            assert node["b50_nonpolarized_relative_equity_research_candidate"] == board["b50_nonpolarized_relative_equity_research_candidate"]
        else:
            assert any(v["version"] == version and v["sha256"] == baseline and v["run_id"] == run
                       for v in board["nl2_locked_variants"])
        cases.append(dict(version=version, spot=model["solver_profile"], pot_family=model["family"],
                          source_sha256=baseline, flop=board["flop"], turn=board["turn"],
                          flop_line=target["line0"], hands_by_seat=target["hands"], nodes=[node],
                          gto_exploitability_pct=target["info"]["gto_expl_pct"],
                          locked_hero_gap_pct=target["info"].get("hero_gap_pct"),
                          villain_lock_scope=lock_scope(target, source["manifest"]["locks"], version)))
    report = dict(schema="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1",
                  source_run_id=run, original_archive_sha256=digest,
                  no_generic_texture_certification=True, errors=[], artifacts=[dict(cases=cases)])
    content = json.dumps(report, separators=(",", ":"), ensure_ascii=False).encode()
    path = ARCHIVES / f"NL2_MULTIBOARD_R{rank}_{run}.json.gz"
    path.write_bytes(gzip.compress(content, mtime=0))


def main():
    data = json.loads(REGISTRY.read_text())
    for model_id, key in GROUPS:
        model, group = data["records"][model_id], data[key]
        assert model["label"] == "CERT-MULTIBOARD" and group["rank"] == model["frequency_rank"]
        boards = model["certified_3_to_5_exact_flop_boards"]
        pins = {p["flop"]: p for p in group["pins"]}
        assert len(boards) == len(pins) == 3
        for board in boards:
            export_board(group["rank"], model, board, pins[board["flop"]])


if __name__ == "__main__":
    main()
