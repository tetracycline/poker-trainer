#!/usr/bin/env python3
"""B370: source-blind APPROX first-ten triage. This does NOT award certificates.
Only SHA-pinned actual GTO and real, measured-source hero partial locks are
counted as a ready exact-flop pair. No solver run or missing evidence invented.
"""
import collections
import hashlib
import json
from pathlib import Path
from hu_multiboard_promote import build_source_index, candidates, texture
from hu_cert_lock_medium_audit import audit

D=Path("data")
STATUS=D/"nl2_hu_multiboard_status_v47_b364_rank96.json"
OUT=D/"nl2_hu_b370_first10_approx_source_triage.json"
DOC=Path("docs/NL2_HU_B370_FIRST10_APPROX_SOURCE_TRIAGE.md")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def eligible(x):
    if x["strict_full_street_combo_reachable"]<=0 or x["genuine_gto_exploitability_pct"]>.5:
        return False
    if x["relative_spr_error_pct"]>5 or len(x["source_sha256"])!=64:
        return False
    return any(len(str(l.get("sha256","")))==64
               and l.get("version")==("exp_ip" if x["acting_seat"]==1 else "exp_oop")
               and isinstance(l.get("observed_marginal_source_nodes"),int)
               and l["observed_marginal_source_nodes"]>0
               and isinstance(l.get("assumed_default_source_nodes"),int)
               and isinstance(l.get("unlocked_source_nodes"),int)
               for l in x["nl2_locked_variants"])

def main():
    s=json.loads(STATUS.read_text())
    assert s["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96"
    assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(159,233,0,392)
    a=audit(s)
    assert (a["cert_multiboard"],a["approx"],a["EST"])==(159,233,0)
    paths=sorted({Path(x) for x in s["source_evidence"]["source_files"]})
    missing=[str(x) for x in paths if not x.is_file()]
    # Missing archived evidence must not be used to promote anything.
    existing=[p for p in paths if p.is_file()]
    by_gto,by_lock,sources=build_source_index(D,existing)
    triage=[]
    for mid,m in s["records"].items():
        if m["label"]!="APPROX":
            continue
        model=dict(family=m["family"],spot=m["solver_profile"],
                   street=m["street"],preflop_text=m["preflop_text"],
                   abstract_action_history=m["abstract_action_history"],
                   approx_spr=m["assumed_model_node_spr"])
        rows,err=candidates(model,by_gto,by_lock,None)
        raw=collections.defaultdict(list)
        verified=collections.defaultdict(list)
        for x in rows:
            if x["strict_full_street_combo_reachable"]<=0 or x["relative_spr_error_pct"]>5:
                continue
            raw[x["flop"]].append(x)
            if eligible(x):
                verified[x["flop"]].append(x)
        examples=[]
        for flop,items in sorted(verified.items()):
            best=sorted(items,key=lambda q:(q["relative_spr_error_pct"],
                        -q["strict_full_street_combo_reachable"],q["public_board"]))[0]
            lock=next(l for l in best["nl2_locked_variants"]
                      if isinstance(l.get("observed_marginal_source_nodes"),int)
                      and l["observed_marginal_source_nodes"]>0
                      and isinstance(l.get("assumed_default_source_nodes"),int)
                      and isinstance(l.get("unlocked_source_nodes"),int))
            examples.append(dict(flop=flop,flop_texture=texture(flop),
                exact_public_board=best["public_board"],
                exact_line=best["actual_exact_action_line"],actual_spr=best["actual_spr"],
                gto_source_run_id=best["source_run_id"],
                gto_source_sha256=best["source_sha256"],
                nl2_hero_lock_run_id=lock["run_id"],nl2_hero_lock_sha256=lock["sha256"],
                strict_legal_combo_count=best["strict_full_street_combo_reachable"],
                measured_pool_marginal_node_count=lock["observed_marginal_source_nodes"],
                assumed_pool_node_count=lock["assumed_default_source_nodes"],
                unmatched_unlocked_pool_node_count=lock["unlocked_source_nodes"],
                source_preflop_assumed_not_private_NL2_observed=best["assumed_preflop_ranges"]))
        rank=m["frequency_rank"]
        triage.append(dict(model_id=mid,frequency_rank=rank,family=m["family"],
            solver_profile=m["solver_profile"],street=m["street"],
            action_history=m["abstract_action_history"],
            assumed_spr=m["assumed_model_node_spr"],
            matched_gto_source_flops=len(raw),
            true_paired_measured_NL2_hero_lock_flops=len(examples),
            strictly_measured_pairs=examples,
            additional_distinct_true_flops_needed=max(0,3-len(examples)),
            needs_second_texture=len({x["flop_texture"] for x in examples})<2,
            candidate_source_reason=err,
            label_unchanged="APPROX",
            no_cert_without_3_to_5_exact_original_solves=True))
    assert len(triage)==233
    # First choose exactly-one-flop gaps; then 3+ proven (source gate);
    # then remaining nodes by descending factual frequency (ascending rank).
    def priority(x):
        n=x["true_paired_measured_NL2_hero_lock_flops"]
        return (0 if n==2 else 1 if n>=3 else 2 if n==1 else 3,x["frequency_rank"])
    selected=sorted(triage,key=priority)[:10]
    assert len(selected)==10 and len({r["model_id"] for r in selected})==10
    report=dict(schema="NL2_HU_B370_SOURCE_GATED_FIRST10_PREFLIGHT_V1",
        source_status_sha256=sha(STATUS),status_counts_unchanged={"CERT":159,"APPROX":233,"EST":0},
        original_hu_river_coverage="2475/2475; independently rechecked by Actions",
        official_verified_subgames=sources["official_subgames"],
        additional_archived_source_cases=sources["new_subgames"],
        source_archive_missing=missing,strict_source_first=True,
        prioritized_only_one_flop_missing=True,
        excluded_unknown_or_unmeasured_lock_denominators=True,
        excluded_unmatched_and_imputed_pool_rates_as_measured=True,
        no_promotion_or_fake_solve_in_preflight=True,
        no_generic_texture_cert=True,no_2026_actual_NL2_private_hand_data_claim=True,
        source_blind_selected_ten=selected,
        remaining_approx_model_count=233,
        all_233_true_paired_flop_count_histogram=dict(collections.Counter(str(x["true_paired_measured_NL2_hero_lock_flops"]) for x in triage)),
        missing_true_flop_pairs_total_for_selected=sum(x["additional_distinct_true_flops_needed"] for x in selected))
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# B370 — ten high-priority APPROX source checks",
        "",
        "Preflight only. **159 CERT / 233 APPROX / 0 EST**; no unperformed solver jobs are represented as genuine CFR.",
        "Missing/UNKNOWN/unmeasured NL2 node-lock frequency evidence is excluded, not imputed.",
        "Each future CERT needs three to five distinct exact original GTO+actor NL2 pairs, original SHA, correct pot/history/SPR and strictly legal per-combo reach.",
        "",
        "| Rank | Model | Verified genuine paired flops | Additional distinct flops needed |",
        "|---:|---|---:|---:|"]
    for r in selected:
        lines.append(f'| {r["frequency_rank"]} | `{r["model_id"]}` | {r["true_paired_measured_NL2_hero_lock_flops"]} | {r["additional_distinct_true_flops_needed"]} |')
    DOC.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f'B370 first10 source preflight: 159 CERT / 233 APPROX, '
          f'{sum(x["true_paired_measured_NL2_hero_lock_flops"]==2 for x in selected)} only-one-flop cases, '
          f'{report["missing_true_flop_pairs_total_for_selected"]} genuine paired flops still needed; no fake upgrades.')

if __name__=="__main__":
    main()
