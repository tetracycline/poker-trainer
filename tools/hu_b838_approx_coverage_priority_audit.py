#!/usr/bin/env python3
"""B838: audit source-frozen 234 APPROX priority and hypothetical 90% coverage.

No certification can be granted by a ranking or by a model-node frequency.
This snapshot is against the explicitly pinned 158/234 status; regenerate
from a new registry version rather than silently changing its baseline.
"""
import csv
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DATA = Path("data")
BASE = "nl2_hu_b838_234_approx_frequency_priority"
D6 = Decimal("0.000001")


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def git_blob(p):
    b = p.read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + bytes([0]) + b).hexdigest()


def d(x):
    return Decimal(str(x))


def round6(x):
    return x.quantize(D6, rounding=ROUND_HALF_UP)


def main():
    status_path = DATA / "nl2_hu_multiboard_status_current.json"
    frozen_path = DATA / "nl2_hu_multiboard_prerank.json"
    meta = read(DATA / (BASE + ".json"))
    assert meta["schema"] == "NL2_HU_B838_234_APPROX_FREQUENCY_90PCT_PRIORITY_V1"
    assert git_blob(status_path) == meta["source_status_git_blob_sha"] == "996fc513406c8a1207d50bc300453858909493d9"
    assert git_blob(frozen_path) == meta["source_frozen_rank_git_blob_sha"] == "7519db4affc935040f07d455e090ce9d3bc07138"

    status, frozen = read(status_path), read(frozen_path)
    assert (status["CERT_MULTIBOARD"], status["APPROX"], status["TOTAL"]) == (158, 234, 392)
    assert frozen["source_hands"] == meta["original_pool_hands"] == 2334487
    assert frozen["source_sha256"] == meta["original_pool_stats_sha256"]
    assert len(status["records"]) == len(frozen["nodes"]) == 392
    nodes = sorted(frozen["nodes"], key=lambda n: n["rank_by_empirically_grounded_frequency_proxy"])
    assert [n["rank_by_empirically_grounded_frequency_proxy"] for n in nodes] == list(range(1, 393))
    assert len({n["model_id"] for n in nodes}) == 392
    for n in nodes:
        r = status["records"][n["model_id"]]
        assert r["frequency_rank"] == n["rank_by_empirically_grounded_frequency_proxy"]
        assert d(r["estimated_nl2_occurrence_opportunity_frac"]) == d(n["estimated_NL2_hand_opportunity_fraction"])
        assert r["solver_profile"] == n["spot"]

    total = sum((d(n["estimated_NL2_hand_opportunity_fraction"]) for n in nodes), Decimal(0))
    cert = sum((d(n["estimated_NL2_hand_opportunity_fraction"]) for n in nodes
                if status["records"][n["model_id"]]["label"] == "CERT-MULTIBOARD"), Decimal(0))
    approx = [n for n in nodes if status["records"][n["model_id"]]["label"] == "APPROX"]
    assert len(approx) == len(meta["rows"]) == 234
    assert total == Decimal("1.5293188403") == d(meta["total_unnormalized_estimated_node_opportunities_per_hand"])
    assert cert == d(meta["baseline_certified_unnormalized_opportunities_per_hand"])
    assert round6(100 * cert / total) == d(meta["baseline_certified_opportunity_share_pct"])
    assert [n["rank_by_empirically_grounded_frequency_proxy"] for n in approx] == sorted(n["rank_by_empirically_grounded_frequency_proxy"] for n in approx)

    with (DATA / (BASE + ".csv")).open(encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 234
    numeric_columns = (
        "estimated_per_hand_frequency_pct",
        "model_opportunity_share_pct",
        "cumulative_approx_share_of_all_opportunities_pct",
        "cumulative_total_coverage_if_all_above_certified_pct",
    )
    eligible = 0
    first90 = None
    cum = Decimal(0)
    for i, (source, row, cr) in enumerate(zip(approx, meta["rows"], csv_rows, strict=True), 1):
        r = status["records"][source["model_id"]]
        w = d(source["estimated_NL2_hand_opportunity_fraction"])
        cum += w
        assert (row["priority"], row["rank"], row["model_id"], row["solver_profile"], row["existing_label"]) == (
            i, r["frequency_rank"], source["model_id"], source["spot"], "APPROX")
        assert (cr["priority"], cr["rank"], cr["model_id"], cr["existing_label"]) == (
            str(i), str(row["rank"]), row["model_id"], "APPROX")
        assert row["preflop_text"] == r["preflop_text"] == cr["preflop_text"]
        assert row["action_history"] == r["abstract_action_history"] == cr["action_history"]
        expected = (100 * w, 100 * w / total, 100 * cum / total, 100 * (cert + cum) / total)
        for key, value in zip(numeric_columns, expected, strict=True):
            assert d(row[key]) == d(cr[key]) == round6(value), (i, key, row[key], cr[key], round6(value))
        e = w >= Decimal("0.002")
        eligible += int(e)
        assert row["passes_min_0_2_pct_frequency"] == e
        assert cr["passes_min_0_2_pct_frequency"] == str(e).lower()
        if first90 is None and 100 * (cert + cum) / total >= 90:
            first90 = i
    assert eligible == 30 == meta["number_remaining_above_or_equal_min_per_hand_frequency"]
    assert 234 - eligible == 204 == meta["number_remaining_below_min_per_hand_frequency"]
    assert first90 == 16 == meta["theoretical_count_of_all_successful_prioritized_promotions_to_reach_90pct"]
    assert round6(100 * (cert + sum((d(n["estimated_NL2_hand_opportunity_fraction"])
                for n in approx[:first90]), Decimal(0))) / total) == d(meta["theoretical_coverage_at_first_90pct_pct"])
    assert meta["current_certified_opportunity_share_pct"] == meta["baseline_certified_opportunity_share_pct"]
    assert meta["observed_certification_improvement_this_batch"] == 0
    assert meta["pr2_draft_do_not_merge"] is True
    doc = (Path("docs") / "NL2_HU_B838_APPROX_90PCT_COVERAGE.md").read_text(encoding="utf-8")
    assert "所有 234 格排序表" in doc and "不是不重複的實戰手牌覆蓋率" in doc
    table_rows = [line for line in doc.splitlines() if line.startswith("| ") and "ln-" in line]
    assert len(table_rows) == 234
    print(json.dumps({
        "PASS": True, "CERT": 158, "APPROX": 234,
        "actual_model_opportunity_coverage_pct": str(round6(100 * cert / total)),
        "relevant_above_0_2_percent": eligible,
        "hypothetical_first_90_percent_n": first90,
        "newly_certified_this_batch": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
