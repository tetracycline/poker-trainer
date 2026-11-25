#!/usr/bin/env python3
"""B871: re-audit current 234 APPROX source gaps directly from authenticated CFR index.

This is an old-index *prefilter*, never a new CERT. Only strict independent
GTO+actor-matched hero lock + exact physical two-seat action/SPR verification
can promote an eligible named flop. Keep all frozen frequency orders unchanged.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,texture

D=Path("data")
def load(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out",type=Path,required=True)
    ap.add_argument("--csv-out",type=Path,required=True)
    a=ap.parse_args()
    regp=D/"nl2_hu_multiboard_status_current.json"
    rankp=D/"nl2_hu_multiboard_prerank.json"
    queuep=D/"nl2_hu_stage2_queue.json"
    priorityp=D/"nl2_hu_b838_234_approx_frequency_priority.json"
    before=regp.read_bytes()
    status,rank,queue,priority=map(load,(regp,rankp,queuep,priorityp))
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["EST"],status["TOTAL"])==(158,234,0,392)
    assert (priority["baseline_CERT_MULTIBOARD"],priority["baseline_APPROX"],priority["baseline_EST"])==(158,234,0)
    assert priority["current_certified_opportunity_share_pct"]==84.700987
    assert priority["original_pool_hands"]==rank["source_hands"]==2334487
    assert len(priority["rows"])==234 and len(rank["nodes"])==len(queue["records"])==len(status["records"])==392
    nodes={n["model_id"]:n for n in rank["nodes"]}
    models={m["model_id"]:m for m in queue["records"]}
    assert len(nodes)==len(models)==392
    assert len({v["rank"] for v in priority["rows"]})==234
    sources=status["source_evidence"]["source_files"]
    extra=[]
    for name in sources:
        path=Path(name)
        assert path.is_file() and "solver_evidence" in path.parts and path.parts[0]=="data" and ".." not in path.parts,name
        extra.append(path)
    assert len(extra)>=20
    # Exactly the GitHub-Actions-authenticated compact source index already used for
    # the repository's historic certification prefilter; no new solver execution.
    gto,locks,index_info=build_source_index(D,extra)
    counts=Counter();rows=[]
    for priority_row in priority["rows"]:
        mid=priority_row["model_id"];current=status["records"][mid]
        m=models[mid];n=dict(nodes[mid])
        r=priority_row["rank"]
        assert (current["label"],current["frequency_rank"],m["model_id"],n["rank_by_empirically_grounded_frequency_proxy"])==("APPROX",r,mid,r)
        assert n["spot"]==m["solver_profile"]==current["solver_profile"]
        assert n["family"]==m["family"]
        n["preflop_text"]=m["preflop_text"]
        n["abstract_action_history"]=m["abstract_action_history"]
        refs,error=candidates(n,gto,locks,None)
        byflop=defaultdict(list)
        for ref in refs:
            assert ref["strict_full_street_combo_reachable"]>0 and ref["source_sha256"]
            byflop[ref["flop"]].append(ref)
        matched=sorted(f for f,items in byflop.items() if any(p["nl2_locked_variants"] for p in items))
        named_all=sorted(byflop)
        needs=max(0,3-len(matched))
        proof,reason=choose_3_5(refs) if error is None else ([],error)
        # Index matching alone is insufficient to certify a current abstract model.
        # In particular masks must be independently checked against *both* policies
        # and the rendered actual previous-street trajectory, not merely textures.
        classifier="PREFILTER_3PLUS_NEEDS_INDEPENDENT_CURRENT_STRICT_GATE" if len(matched)>=3 else (
            "PREFILTER_ONE_AUTHENTIC_FLOP_SHORT" if needs==1 else (
            "PREFILTER_TWO_AUTHENTIC_FLOPS_SHORT" if needs==2 else
            "PREFILTER_THREE_AUTHENTIC_FLOPS_SHORT"))
        counts[classifier]+=1
        suggested_source_proof=[dict(flop=z["flop"],run_id=z["source_run_id"],sha256=z["source_sha256"],line=z["actual_exact_action_line"],strict_reach=z["strict_full_street_combo_reachable"],acting_seat=z["acting_seat"],nl2_actor_locks=len(z["nl2_locked_variants"])) for z in proof]
        rows.append(dict(rank=r,model_id=mid,spot=m["spot"],family=m["family"],street=m["street"],estimated_per_hand_opportunity_pct=priority_row["estimated_per_hand_frequency_pct"],is_above_research_threshold=priority_row["passes_min_0_2_pct_frequency"],original_index_gto_flops=named_all,original_index_actor_matched_locked_flops=matched,preliminary_flop_count=len(matched),preliminary_new_flops_needed=needs,source_parse_error=error,source_diversity_gate_reason=reason,preregistered_priority_class=classifier,preliminary_3to5_named_proofs=suggested_source_proof,current_status_label="APPROX",can_auto_certify=False))
    assert len(rows)==234 and {x["model_id"] for x in rows}=={z["model_id"] for z in priority["rows"]}
    assert sum(counts.values())==234
    assert status["CERT_MULTIBOARD"]==158 and regp.read_bytes()==before
    # HW 2026-11-25: opportunity frequency ONLY, never missing-flop count.
    weight=lambda z:nodes[z["model_id"]]["estimated_NL2_hand_opportunity_fraction"]
    ordered=sorted(rows,key=lambda z:(-weight(z),z["rank"]))
    assert [x["rank"] for x in ordered]==[x["rank"] for x in priority["rows"]]
    total_weight=math.fsum(n["estimated_NL2_hand_opportunity_fraction"] for n in nodes.values())
    cert_weight=math.fsum(n["estimated_NL2_hand_opportunity_fraction"] for mid,n in nodes.items() if status["records"][mid]["label"]=="CERT-MULTIBOARD")
    actual_coverage=100*cert_weight/total_weight
    assert abs(total_weight-priority["total_unnormalized_estimated_node_opportunities_per_hand"])<1e-10
    assert round(actual_coverage,6)==priority["current_certified_opportunity_share_pct"]
    assert all(x["is_above_research_threshold"]==(weight(x)>=0.002) for x in ordered)
    first_actionable=[x for x in ordered if weight(x)>=0.002]
    assert len(first_actionable)==priority["number_remaining_above_or_equal_min_per_hand_frequency"]==30
    data=dict(schema="NL2_B871_CURRENT_234_SOURCE_INDEX_RESCREEN_V1",current_status_sha256=sha(regp),frozen_priority_sha256=sha(priorityp),original_queue_sha256=sha(queuep),frozen_ranks_sha256=sha(rankp),source_index_files=[dict(path=str(p),sha256=sha(p)) for p in extra],source_index_summary=index_info,official_locked_flop_prefilter_counts=dict(counts),eligible_above_0_2pct=30,models=rows,preliminary_one_flop_short_ranks=[x["rank"] for x in rows if x["preliminary_new_flops_needed"]==1],preliminary_three_plus_but_STILL_APPROX=[x["rank"] for x in rows if x["preliminary_new_flops_needed"]==0],first_actionable_queue=[dict(rank=x["rank"],model_id=x["model_id"],freq_pct=x["estimated_per_hand_opportunity_pct"],preliminary_missing=x["preliminary_new_flops_needed"]) for x in first_actionable],CERT_MULTIBOARD=158,APPROX=234,NL2_weighted_opportunity_coverage_pct=round(actual_coverage,6),total_model_opportunity_weight=total_weight,certified_model_opportunity_weight=cert_weight,priority_order='frozen per-hand opportunity descending, then frozen rank; missing-flop counts are descriptive only',certification_count_change=0,actual_native_solves_this_batch=0,current_state_unchanged=True,any_old_source_index_candidate_is_not_a_current_certification=True,never_infer_private_hand_NL2_conditional_frequencies=True,no_generic_texture_extrapolation=True,PR2_DRAFT_NEVER_MERGE=True)
    a.json_out.parent.mkdir(parents=True,exist_ok=True)
    a.csv_out.parent.mkdir(parents=True,exist_ok=True)
    a.json_out.write_text(json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    with a.csv_out.open("w",newline="",encoding="utf8") as fp:
        fields=["rank","model_id","spot","street","estimated_per_hand_opportunity_pct","is_above_research_threshold","preliminary_flop_count","preliminary_new_flops_needed","source_parse_error","source_diversity_gate_reason","preregistered_priority_class","current_status_label"]
        out=csv.DictWriter(fp,fieldnames=fields,extrasaction="ignore");out.writeheader();out.writerows(ordered)
    print(json.dumps(dict(CERT=158,APPROX=234,coverage_pct=round(actual_coverage,6),indexed_sources=len(extra),prefilter_counts=dict(counts),one_short=data["preliminary_one_flop_short_ranks"],unverified_three_plus=data["preliminary_three_plus_but_STILL_APPROX"],first_actionable=data["first_actionable_queue"][:12])))
if __name__=="__main__":main()
