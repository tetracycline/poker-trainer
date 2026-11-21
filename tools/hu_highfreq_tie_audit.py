#!/usr/bin/env python3
"""B39: source-blind frequency-tie cohort; original frozen top24 CERT labels untouched.

Select only nodes whose preregistered NL2 opportunity proxy is numerically
identical to frozen rank-24 threshold, BEFORE querying CFR evidence. Never
inflate CERT automatically or treat approximate class abstractions as GTO.
"""
import collections
import hashlib
import json
import pathlib

from hu_multiboard_promote import candidates, build_source_index, texture

ROOT = pathlib.Path("data")
OUT = ROOT / "nl2_hu_b39_frequency_tie_prereg.json"
DOC = pathlib.Path("docs/NL2_HU_B39_TIE_PREREG.md")


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for part in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def main():
    rank_path = ROOT / "nl2_hu_multiboard_prerank.json"
    status_path = ROOT / "nl2_hu_multiboard_status.json"
    queue_path = ROOT / "nl2_hu_stage2_queue.json"
    rank = json.loads(rank_path.read_text())
    status = json.loads(status_path.read_text())
    queue = json.loads(queue_path.read_text())
    n = rank["cutoff"]["N"]
    assert n == 24 and rank["cutoff"]["method"] == "TOP_N_BY_NL2_EMPIRICAL_ANCHORED_OPPORTUNITY_PROXY"
    assert rank["summary"]["models"] == 392
    ordered = sorted(rank["nodes"], key=lambda x: x["rank_by_empirically_grounded_frequency_proxy"])
    assert len(ordered) == status["TOTAL"] == 392
    threshold = ordered[n-1]["estimated_NL2_hand_opportunity_fraction"]
    assert threshold > 0
    # Cohort selection happens BEFORE reading any solver evidence, by exact
    # locked frequency-proxy score; the historical top24 is not re-optimized.
    ties = [dict(x) for x in ordered[n:]
            if abs(x["estimated_NL2_hand_opportunity_fraction"]-threshold) <= 1e-12]
    tie_ranks = [x["rank_by_empirically_grounded_frequency_proxy"] for x in ties]
    assert tie_ranks == [25, 26], "Source-blind tie policy must be reviewed if ranking changes"
    assert all(not x["high_frequency_priority"] for x in ties)
    by_id = {x["model_id"]: x for x in queue["records"]}
    assert all(status["records"][x["model_id"]]["label"] == "APPROX" for x in ties)
    # Only after fixing the tie population may existing real CFR data be read.
    paths = [pathlib.Path(x) for x in status["source_evidence"]["source_files"]]
    assert paths and all(x.is_file() for x in paths)
    exact, locked, source_summary = build_source_index(ROOT, paths)
    rows = []
    for r in ties:
        original = by_id[r["model_id"]]
        r["preflop_text"] = original["preflop_text"]
        r["abstract_action_history"] = original["abstract_action_history"]
        refs, reason = candidates(r, exact, locked, None)
        by_flop = collections.defaultdict(list)
        for ref in refs:
            by_flop[ref["flop"]].append(ref)
        with_lock = {f: a for f,a in by_flop.items()
                     if any(b["nl2_locked_variants"] for b in a)}
        lock_textures = sorted({texture(f) for f in with_lock})
        examples = []
        for flop, a in sorted(by_flop.items()):
            best = sorted(a, key=lambda x: (-len(x["nl2_locked_variants"]),
                 -x["strict_full_street_combo_reachable"], x["relative_spr_error_pct"]))[0]
            examples.append(dict(
                flop=flop, turn=best["turn"], full_board=best["public_board"],
                action_line=best["actual_exact_action_line"],
                source_run_id=best["source_run_id"],
                gto_source_sha256=best["source_sha256"],
                strict_combo_reach=best["strict_full_street_combo_reachable"],
                gto_gap_pct=best["genuine_gto_exploitability_pct"],
                actual_spr=best["actual_spr"],
                hero_lock_versions=sorted({v["version"] for v in best["nl2_locked_variants"]}),
                lock_run_ids=sorted({v["run_id"] for v in best["nl2_locked_variants"]})))
        rows.append(dict(
            rank=r["rank_by_empirically_grounded_frequency_proxy"],
            model_id=r["model_id"],spot=r["spot"],family=r["family"],
            street=r["street"],action_history=r["abstract_action_history"],
            model_spr=r["approx_spr"],opportunity_proxy=threshold,
            current_official_label="APPROX",
            exact_gto_flops=sorted(by_flop),
            hero_locked_flops=sorted(with_lock),
            distinct_hero_locked_flop_count=len(with_lock),
            required_distinct_flops=3,
            missing_hero_locked_flops=max(0,3-len(with_lock)),
            verified_lock_texture_count=len(lock_textures),
            verified_lock_textures=lock_textures,
            source_matches=examples,
            no_matching_source_reason=reason,
            preregistered_research_candidate_only=True))
    result = dict(
        schema="NL2_HU_B39_SOURCE_BLIND_EQUAL_SCORE_TIE_PREREG_V1",
        frozen_top24_original_sha256=file_sha(rank_path),
        frozen_status_before_tie_audit_sha256=file_sha(status_path),
        original_preregistered_N=n,
        original_cutoff_score=threshold,
        source_blind_selection="ALL_RANKS_AFTER_24_WITH_SCORE_EQUAL_TO_FROZEN_RANK24",
        tie_ranks=tie_ranks,
        tie_node_ids=[x["model_id"] for x in ties],
        no_change_to_original_cutoff=True,
        no_auto_upgrade_to_cert=True,
        no_claim_of_observed_per_combo_NL2_frequencies=True,
        source_files_verified=len(paths),
        source_summary=source_summary,
        official_counts=dict(CERT_MULTIBOARD=status["CERT_MULTIBOARD"],
                             APPROX=status["APPROX"],TOTAL=status["TOTAL"]),
        rows=rows)
    assert result["official_counts"] == {"CERT_MULTIBOARD":24,"APPROX":368,"TOTAL":392}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    lines = [
      "# B39 | Source-blind NL2 tied-frequency expansion research",
      "",
      "PR #2 Draft only. Original frozen top24 threshold and all published labels are unchanged.",
      "The two immediately below-cutoff nodes have the identical frozen NL2 opportunity score as rank24.",
      "They are a separate *preregistered research cohort*, not automatic CERT nodes.",
      "No value of source EV, win rate, or CFR result influenced which ranks entered this cohort.",
      "",
      "| Rank | Model | Spot | Model SPR | Matching exact GTO flops | With matching hero lock | Missing to 3 | Lock textures |",
      "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in rows:
        lines.append("| "+str(r["rank"])+" | "+r["model_id"]+" | "+r["spot"]+" | "+str(r["model_spr"])+" | "+str(len(r["exact_gto_flops"]))+" | "+str(r["distinct_hero_locked_flop_count"])+" | "+str(r["missing_hero_locked_flops"])+" | "+", ".join(r["verified_lock_textures"])+" |")
        for ex in r["source_matches"]:
            lines.append("")
            lines.append("- Rank "+str(r["rank"])+": "+ex["flop"]+" "+ex["turn"]+
                ", line `"+ex["action_line"]+"`, GTO run "+str(ex["source_run_id"])+
                ", lock runs "+str(ex["lock_run_ids"])+", strict combos "+str(ex["strict_combo_reach"]))
    lines.extend(["",
      "## Classification and evidence constraints",
      "",
      "- Selection uses only the *previously frozen*, source-independent frequency proxy; its exact tie score is "+str(threshold)+".",
      "- No cutoff modifications, no historical status modifications and no implied CERT promotion.",
      "- Actual later-street actor, action-line, public board, pot/SPR, GTO SHA, reach and independent hero-side lock are mandatory.",
      "- One node needs at least 3 distinctive real flop boards, at least two distinct textures, and a hero-side NL2 source with known observed/default scope.",
      "- Observed pool-wide marginal frequencies must **never** be represented as observed private-combo action probabilities.",
      "- Any new eligibility/cohort version must retain the original top24 immutable audit and be approved separately from source-driven upgrades.",
      ""])
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(lines))
    print(json.dumps({"B39_tie_ranks":tie_ranks,
          "missing_by_rank":{str(x["rank"]):x["missing_hero_locked_flops"] for x in rows},
          "official_CERT":24,"official_APPROX":368},ensure_ascii=False))


if __name__ == "__main__":
    main()
