"""B853: all active CERT named-board partial NL2 lock and 50%-pot gap scorecard.

Never infer private-card NL2 frequencies from observed pooled marginals.
Do not change certified status, solve new game trees, or relabel APPROX.
"""
import argparse,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from hu_current_medium_coverage import coverage

def read(p):return json.loads(p.read_bytes())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--md",type=Path,required=True)
    a=p.parse_args()
    statusp=Path("data/nl2_hu_multiboard_status_current.json")
    rankp=Path("data/nl2_hu_multiboard_prerank.json")
    before=statusp.read_bytes()
    registry=json.loads(before)
    assert (registry["CERT_MULTIBOARD"],registry["APPROX"],registry["TOTAL"])==(158,234,392)
    frozen=read(rankp)
    assert frozen["source_hands"]==2334487
    nodes={n["model_id"]:n for n in frozen["nodes"]}
    assert len(nodes)==392 and set(nodes)==set(registry["records"])
    report=coverage(registry) # independently walks GTO, valid combo masks and lock-source provenance
    assert report["certified_models"]==158
    assert len(report["boards"])==registry["all_cert_lock_medium"]["named_board_proofs"]
    registered={mid for mid,v in registry["records"].items() if v["label"]=="CERT-MULTIBOARD"}
    assert len(registered)==158
    rows=[];each=Counter();half=Counter();measured_total=assumed_total=unmatched_total=0
    for board in report["boards"]:
        mid=board["model_id"];assert mid in registered
        record=registry["records"][mid];n=nodes[mid]
        assert n["rank_by_empirically_grounded_frequency_proxy"]==board["rank"]==record["frequency_rank"]
        assert (board["pot_bb"],board["stack_bb"])==(board["pot_bb"],board["stack_bb"])
        assert board["gto"]["legal_combos"]>0 and board["gto"]["compatible_pairs"]>=board["gto"]["legal_combos"]
        assert board["opponent_locks"]
        assert "medium_policy_usage" in board
        each[mid]+=1;half[board["half_pot_status"]]+=1
        locks=[];counts=[0,0,0]
        for p in board["opponent_locks"]:
            o,im,u=[int(p[x]) for x in ("measured_nodes","assumed_nodes","unmatched_nodes")]
            assert o>0 and im>=0 and u>=0
            counts=[counts[i]+x for i,x in enumerate((o,im,u))]
            assert p["legal_combos"]>0 and p["compatible_pairs"]>=p["legal_combos"]
            locks.append(dict(version=p["version"],source_run_id=p["run"],source_sha256=p["sha256"],observed_pool_marginal_nodes=o,assumed_default_nodes=im,unmatched_nodes=u,legal_combos=p["legal_combos"],nonpolarized_candidate=bool(p["nonpolarized_candidate"]),halfpot_eligible_combos=p["half_pot_eligible_combos"]))
        o,im,u=counts;observed_share=round(o/(o+im+u),6)
        measured_total+=o;assumed_total+=im;unmatched_total+=u
        frequency=100*float(n["estimated_NL2_hand_opportunity_fraction"])
        assert frequency>0
        # Prioritization proxy only: not a measured exact board probability.
        priority_score=round(frequency*(1-observed_share),7)
        rows.append(dict(rank=record["frequency_rank"],model_id=mid,board=board["public_board"],line=board["line"],actor=board["seat"],solver_profile=record["solver_profile"],estimated_model_node_opportunity_pct=round(frequency,6),priority_score_proxy=priority_score,half_pot_status=board["half_pot_status"],gto_source_actions=board["gto"]["actions"],gto_strict_legal_combos=board["gto"]["legal_combos"],gto_halfpot_eligible_combos=board["gto"]["half_pot_eligible_combos"],gto_nonpolarized_candidate=bool(board["gto"]["nonpolarized_candidate"]),total_observed_marginal_nodes=o,total_assumed_default_nodes=im,total_unmatched_nodes=u,observed_node_fraction=observed_share,locks=locks))
    assert len(each)==158 and all(3<=v<=5 for v in each.values()),dict(each)
    assert len(rows)==sum(each.values())==len(report["boards"])
    assert statusp.read_bytes()==before
    rows.sort(key=lambda x:(-x["priority_score_proxy"],x["rank"],x["board"],x["line"]))
    score=dict(schema="NL2_B853_ALL_CERT_PARTIAL_LOCK_NONPOLAR_GAP_V1",status_sha256=digest(statusp),frozen_rank_sha256=digest(rankp),cert_models=158,approx_models=234,qualified_named_board_examples=len(rows),observed_pool_marginal_nodes=measured_total,assumed_default_nodes=assumed_total,unmatched_nodes=unmatched_total,half_pot_status_by_named_board=dict(sorted(half.items())),comparison_eligibility_summary=report["medium_action_eligible"],nonpolarized_research_summary=report["nonpolarized_candidate"],ranked_named_board_gap_rows=rows,no_new_native_solves=True,no_new_cert_promotions=True,no_unobserved_private_card_conditional_data=True,model_node_frequency_is_not_exact_board_arrival_rate=True,not_a_global_half_pot_recommendation=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.md.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(score,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    lines=["# B853 — 158 existing CERT models: original lock & 50%-pot gap audit","",
        f"Audited {len(rows)} authenticated named public boards across 158 CERT models. The 234 other models stay APPROX.",
        "The pooled NL2 counts are observed *marginal* statistics; no per-private-combo conditional observation exists.",
        "50%-pot depolarization is a named-board research candidate only where verified; never extrapolate to every texture.",
        "The opportunity priority is the *model-node* proxy times unmatched/assumed source share; it is NOT a measured exact-board arrival rate.",
        "No GTO solve, CERT upgrade, status downgrade, or merge is performed.","",
        f"Original actor-locked marginal nodes: {measured_total}; assumed/default: {assumed_total}; unmatched: {unmatched_total}.",
        f"Frozen registry SHA256: \`{digest(statusp)}\`","",
        "| Rank | Exact board | Model | Measured | Assumed | Unmatched | Half-pot evidence |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |"]
    for x in rows[:30]:
        lines.append(f"| {x['rank']} | {x['board']} | \`{x['model_id']}\` | {x['total_observed_marginal_nodes']} | {x['total_assumed_default_nodes']} | {x['total_unmatched_nodes']} | {x['half_pot_status']} |")
    lines+=["","Only exact-board original GTO plus true actor-matched partially locked NL2 sources and strictly reachable combos can support CERT.","PR #2 stays draft; never merge or force push.",""]
    a.md.write_text("\n".join(lines))
    print(json.dumps({k:score[k] for k in ("cert_models","approx_models","qualified_named_board_examples","observed_pool_marginal_nodes","assumed_default_nodes","unmatched_nodes")}))
if __name__=="__main__":main()
