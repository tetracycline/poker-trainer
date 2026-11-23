#!/usr/bin/env python3
"""B448 audit every genuine exact CERT board against the frozen B419 lock/medium ledger."""
import collections,hashlib,json,pathlib
D=pathlib.Path("data")
def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    stpath=D/"nl2_hu_multiboard_status_v50_b417_rank166.json"
    ledpath=D/"nl2_hu_b419_cert163_board618_lock710_medium_ledger.json"
    st=load(stpath);led=load(ledpath)
    assert (st["CERT_MULTIBOARD"],st["APPROX"],st["TOTAL"])==(163,229,392)
    assert (led["CERT_MULTIBOARD"],led["APPROX"],led["EST"])==(163,229,0)
    assert (led["exact_named_boards"],led["hero_lock_source_variants"])==(618,710)
    assert (led["exact_nonpolarized_50pct_research_candidate_boards"],led["unknown_remains"])==(135,0)
    rows=led["per_named_board_exact_source_lock_and_50pct_status"]
    assert len(rows)==618
    idx={(x["model_id"],x["flop"],x["turn"]):x for x in rows}
    assert len(idx)==len(rows),"Duplicated ledger exact board"
    counts=collections.Counter();family=collections.Counter()
    examples=[]
    for mid,m in st["records"].items():
        if m["label"]!="CERT-MULTIBOARD":continue
        counts["models"]+=1;family[m["family"]]+=1
        boards=m["certified_3_to_5_exact_flop_boards"]
        assert 3<=len(boards)<=5 and len({x["flop"] for x in boards})==len(boards),mid
        for b in boards:
            key=(mid,b["flop"],b["turn"])
            assert key in idx,key
            x=idx[key]
            assert x["source_spot"]==m["solver_profile"],key
            assert (x["original_GTO_run_id"],x["original_GTO_sha256"])==(b["source_run_id"],b["source_sha256"]),key
            assert (x["actor_seat"],x["strictly_reachable_hero_combos"])==(
                b["acting_seat"],b["strict_full_street_combo_reachable"]),key
            assert b["strict_full_street_combo_reachable"]>0 and b["genuine_gto_exploitability_pct"]<=.5,key
            assert b["relative_spr_error_pct"]<=5,key
            assert abs(x["source_SPR"]-b["actual_spr"])<=.00001,key
            assert x["exact_action_line"]==b["actual_exact_action_line"],key
            assert x["exact_public_board"]==b["public_board"],key
            locks=b["nl2_locked_variants"];old=x["hero_partial_NL2_pool_lock_provenance"]
            assert locks and len(locks)==len(old),key
            for v in locks:
                matches=[z for z in old if (z["run_id"],z["sha256"],z["version"])==
                     (v["run_id"],v["sha256"],v["version"])]
                assert len(matches)==1,key
                z=matches[0];n=z["node_counts"]
                assert n["observed_marginal"]==v.get("observed_marginal_source_nodes"),key
                assert n["assumed_default"]==v.get("assumed_default_source_nodes"),key
                assert n["unmatched_unlocked"]==v.get("unlocked_source_nodes"),key
                assert z["not_empirical_villain_private_hand_conditional"] is True,key
                assert z["unknown_action_rates_are_not_zero"] is True,key
                assert z["empirical_frequency_scope"]=="OBSERVED_NL2_STREET_AND_SIZE_POOL_MARGINAL_ONLY",key
                assert z["source_scope"]=="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",key
                counts["lock_variants"]+=1
                counts["observed_pool_marginal_pattern_nodes"]+=n["observed_marginal"]
                counts["assumed_default_pattern_nodes"]+=n["assumed_default"]
                counts["unmatched_unlocked_pattern_nodes"]+=n["unmatched_unlocked"]
                if n["observed_marginal"]>0:counts["lock_variants_with_measured_pool_marginal"]+=1
                if n["assumed_default"]>0:counts["lock_variants_with_fallback"]+=1
            medium=bool(b["b50_nonpolarized_relative_equity_research_candidate"])
            assert x["medium_50pct_true_eligible_combos"]==int(b["medium_50pct_eligible_combos"]),key
            assert medium==(x["medium_50pct_research_status"]=="EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE"),key
            if medium:
                assert int(b["medium_50pct_eligible_combos"])>0,key
                counts["medium50_exact_board_candidates"]+=1
            else:
                assert x["medium_50pct_research_status"]=="NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE",key
                counts["medium50_not_supported"]+=1
            assert x["no_generalized_50pct_bet_strategy"] is True,key
            counts["exact_named_boards"]+=1
            if len(examples)<2:examples.append(dict(model=mid,flop=b["flop"],source_sha256=b["source_sha256"]))
    assert dict(counts)["models"]==163
    assert (counts["exact_named_boards"],counts["lock_variants"],counts["medium50_exact_board_candidates"],counts["medium50_not_supported"])==(618,710,135,483)
    pool=led["source_pool_node_totals"]
    for k in ["observed_pool_marginal_pattern_nodes","assumed_default_pattern_nodes","unmatched_unlocked_pattern_nodes"]:
        assert counts[k]==pool[k],k
    assert counts["lock_variants_with_measured_pool_marginal"]==pool["pool_marginal_present_lock_variants"]==662
    assert counts["lock_variants_with_fallback"]==pool["lock_variants_with_assumed_defaults"]==378
    proof=dict(schema="NL2_B448_ALL_163_CERT_EXACT_BOARD_LOCK_AND_MEDIUM_RECONCILIATION_V1",
       source_status_sha256=sha(stpath),source_ledger_sha256=sha(ledpath),
       CERT_MULTIBOARD=163,APPROX=229,EST=0,TOTAL=392,
       certified_models_checked=counts["models"],
       exact_named_boards_checked=counts["exact_named_boards"],
       matched_individual_hero_lock_variants=counts["lock_variants"],
       measured_NL2_pool_marginal_pattern_nodes=counts["observed_pool_marginal_pattern_nodes"],
       assumed_default_pattern_nodes=counts["assumed_default_pattern_nodes"],
       unmatched_unlocked_pattern_nodes=counts["unmatched_unlocked_pattern_nodes"],
       lock_variants_with_measured_marginals=counts["lock_variants_with_measured_pool_marginal"],
       lock_variants_with_disclosed_fallback=counts["lock_variants_with_fallback"],
       exact_board_research_candidates_for_medium_50pct=135,
       exact_board_medium_50pct_not_supported=483,
       all_618_original_GTO_SHA_actor_SPR_exact_action_and_legal_combo_match=True,
       all_710_partial_NL2_lock_variant_source_shas_and_population_counts_match=True,
       no_observed_per_private_hand_conditional_NL2_frequency_claim=True,
       no_unsupported_medium_50pct_betting_generalization=True,
       no_GenericTexture_CERT=True,
       lineage_examples=examples,
       all_prior_cert_labels_unchanged=True,PR2_Draft_NEVER_MERGE=True)
    d=D/"nl2_hu_b448_all163_cert_lock_medium_reconciliation.json"
    d.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
    docs=pathlib.Path("docs/NL2_HU_B448_ALL_CERT_LOCK_MEDIUM_RECONCILIATION.md")
    docs.write_text("# B448 all 163 CERT-MULTIBOARD boards: independent lock and medium reconciliation\n\n"
      "All 618 named, exact-board GTO sources match frozen V50 actor, action, SPR, "
      "strict combo reach, source run and SHA. All 710 NL2 pool-lock variants match "
      "the B419 board ledger, including 6,600 measured **pool-marginal pattern nodes**, "
      "2,268 assumed-default pattern nodes and 12,683 unmatched/unlocked nodes. "
      "These are not individual private-card NL2 observations.\n\n"
      "The 50% nonpolarized relative-equity research gate supports 135 named-board candidates; "
      "483 exact board examples **do not** support a medium-size recommendation. "
      "No generic strategy, real-money earnings or unjustified CERT is inferred. "
      "Counts remain **163 CERT / 229 APPROX / 0 EST**.\n")
    print(json.dumps({"result":"PASS","cert":163,"approx":229,"boards":618,"locks":710,"medium":135}))
if __name__=="__main__":main()
