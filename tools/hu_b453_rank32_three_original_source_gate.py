#!/usr/bin/env python3
"""B453 verify three original Rust GTO/NL2 OOP solves and certify ONLY exact rank32 boards.

Each binary-compressed original source is verified against its separate first-pass
proof and source-run SHA; sequential 40/70 action reach is independently recomputed.
One bad, missing, or zero-reach original case fails closed: no status change.
"""
import collections,gzip,hashlib,json,pathlib,sys

D=pathlib.Path("data")
MODEL="ln-opfr-t_model-qx9t0u"
SOURCE_PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST_PIN="9d1509fe5077d019825f833eed04b16d342dfda1"
SCHEMA="NL2_HU_392_MULTIBOARD_CERT_STATUS_V51_B453_R32"
SPEC=(
    (447,"AsKh3d","8s","AS_KH_3D"),
    (449,"Ks7h2d","9d","KS_7H_2D"),
    (452,"KsQh4d","Tc","KS_QH_4D"),
)
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def valid_sha(x):return isinstance(x,str) and len(x)==64 and all(c in "0123456789abcdef" for c in x)
def getnode(d):
    matches=[n for n in d["nodes"] if n["line"]=="b100 c/" and n["player"]==0 and len(n["board"])==8]
    if len(matches)!=1:raise ValueError("No unique original BB/UTG OOP b100 call actor node")
    return matches[0]

def source_one(source,expected_ver,flop,turn,proofnode,source_run):
    from hu_sequential_cfr_reach import game_reach
    from verify_hu_multiboard_100bb import source_nodes
    assert source["version"]==expected_ver
    m,r,sub=source["manifest"],source["root"],source["subgame"]
    j=source["subgame_job"]
    assert isinstance(m,dict) and isinstance(r,dict) and isinstance(sub,dict) and isinstance(j,dict)
    assert m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
    assert (m["spot"],m["version"],m["flop"])==("UTG_CO",expected_ver,flop)
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert (m["root_pot_bb"],m["root_remaining_bb"])==(6.5,97.5)
    assert m["flop_size_profile"]=="full" and m["restricted_tree_assumption"] is False
    assert m["flop_line_policy"]=="oop-b100only" and m["selected_lines"]==["b100 c"]
    assert m["turn_sizing_mode"]=="default" and m["turns"]==[turn]
    assert m["solved_cases"]==1 and len(m["cases"])==1 and not m["failures"] and not m["skipped"]
    assert m["solver_pin"]=="f0a173b3d9331c4ff8697359a838094f76babb35f16133e37bbd0bfb203b5253"
    assert m["solver_ranges_sha256"]=="f2a302b483c79995ed90031b62e65a202ae7a1fdc8695f8940fe3e8291fb2bba"
    assert m["file_flop_sha256"]==source["root_sha256"] and valid_sha(source["root_sha256"])
    c=m["cases"][0]
    assert (c["line"],c["turn"],c["source_sha256"])==("b100 c",turn,source["source_sha256"])
    assert valid_sha(c["source_sha256"])
    assert (r["flop"],r["pot"],r["stack"])==(flop,650,9750)
    assert r["info"]["gto_expl_pct"]<=0.5
    assert (sub["flop"],sub["turn"],sub["line0"])==(flop,turn,"b100 c")
    assert sub["info"]["gto_expl_pct"]<=0.5
    assert c["gto_gap_pct"]<=.5
    if expected_ver=="gto":
        assert j.get("hero") is None and not j.get("locks")
        assert c["hero_gap_pct"] is None
    else:
        assert j["hero"]==0 and j.get("locks")
        assert c["hero_gap_pct"] is not None and c["hero_gap_pct"]<=.5
        assert sub["info"]["hero_gap_pct"]<=.5
        assert m["locks"] and any((x.get("n") or 0)>=500 for x in m["locks"])
    assert abs(j["rake_rate"]-0.05)<1e-8 and j["rake_cap"]==1000
    assert j["turn_oop"]=="50%,100%" and j["turn_ip"]=="50%,100%"
    mask,stat=game_reach(r,sub)
    n=getnode(sub)
    assert n["board"][-2:]==turn
    key="|".join((n["board"],n["line"],"0"))
    q=mask[key]
    actual=(sub["stack"]-max(n["bets"]))/n["pot"]
    assert abs(actual-4.667)/4.667<=0.05
    raw=sum(float(x)>1e-4 for x in n["w"][0])
    assert raw>0
    assert n["acts"]==proofnode["source_actions"]
    assert (n["board"],0,int(q["count"]))==(proofnode["public_board"],proofnode["exact_actor"],proofnode["strict_full_street_combos"])
    assert raw==proofnode["source_combo_rows"]
    assert abs(actual-proofnode["actual_spr"])<0.00001
    assert source["source_sha256"]==proofnode["source_run_sha"]
    focus=dict(sub);focus["nodes"]=[n]
    evidence=source_nodes(focus,{"nodes":{key:q}}) if q["count"]>0 else []
    if q["count"]>0:
        assert len(evidence)==1
        assert evidence[0]["strictly_reachable_combos"]==q["count"]
        assert evidence[0]["medium_50pct_eligible_combos"]==proofnode["medium50_strict_eligible_combos"]
        assert (evidence[0]["b50_nonpolarized_relative_equity_research_candidate"] is
                proofnode["b50_nonpolarized_research_candidate"])
    assert source_run>0
    return dict(manifest=m,subgame=sub,source=source,node=n,strict=q["count"],
                source_actor_combos=raw,original_spr=actual,source_sha=c["source_sha256"],
                evidence=evidence[0] if evidence else None)

def main():
    sys.path.insert(0,str(pathlib.Path("tools").resolve()))
    from verify_hu_multiboard_100bb import lock_scope,locked_model_gain
    base=D/"nl2_hu_multiboard_status_v50_b417_rank166.json"
    st=load(base)
    assert st["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166"
    assert (st["CERT_MULTIBOARD"],st["APPROX"],st["TOTAL"])==(163,229,392)
    model=st["records"][MODEL]
    assert (model["frequency_rank"],model["solver_profile"],model["label"],model["assumed_model_node_spr"])==(
        32,"UTG_CO","APPROX",4.667)
    output=[];pins=[];negatives=[]
    for batch,flop,turn,code in SPEC:
        proof_path=D/f"nl2_hu_b{batch}_rank32_first_source_proof.json"
        archive_path=D/"solver_evidence"/f"NL2_B{batch}_R32_{code}.json.gz"
        assert proof_path.is_file() and archive_path.is_file(),(proof_path,archive_path)
        proof=load(proof_path)
        assert proof["schema"]==f"NL2_B{batch}_R32_ONE_OF_THREE_EXACT_FLOPS_V1"
        assert (proof["target_model"],proof["frequency_rank"],proof["root_profile"])==(MODEL,32,"UTG_CO")
        assert (proof["flop"],proof["turn"],proof["target_exact_line"],proof["actor"])==(flop,turn,"b100 c/","UTG_OOP")
        assert proof["source_archive_sha256"]==sha(archive_path)
        assert proof["original_solver_pin"]==SOURCE_PIN and proof["original_rust_pin"]==RUST_PIN
        assert proof["original_full_menu_rust_CFR"] and proof["no_generic_model_CERT"]
        assert proof["NL2_frequencies_are_pool_street_size_marginals_not_private_hand_rates"]
        raw=json.loads(gzip.decompress(archive_path.read_bytes()))
        assert raw["schema"]==f"NL2_B{batch}_R32_AS_KH_3D_ORIGINAL_RUST_GTO_AND_NL2_OOP_V1" or raw["schema"].startswith(f"NL2_B{batch}_R32_")
        assert raw["run_id"]>0 and raw["source_run_id"]==raw["run_id"]
        assert (raw["flop"],raw["turn"])==(flop,turn)
        assert raw["pinned_solver"]==SOURCE_PIN and raw["pinned_rust"]==RUST_PIN
        assert len(raw["source_arrays"])==2
        src={z["version"]:z for z in raw["source_arrays"]}
        assert set(src)=={"gto","exp_oop"}
        g=source_one(src["gto"],"gto",flop,turn,proof["authentic_GTO"],raw["run_id"])
        e=source_one(src["exp_oop"],"exp_oop",flop,turn,
              proof["partially_NL2_pool_locked_EXP_OOP"],raw["run_id"])
        valid=bool(g["strict"]>0 and e["strict"]>0)
        assert proof["authentic_paired_positive"] is valid
        if not valid:
            negatives.append(dict(flop=flop,turn=turn,GTO_strict=g["strict"],EXP_OOP_strict=e["strict"],run_id=raw["run_id"]))
            continue
        lock=lock_scope(e["subgame"],e["manifest"]["locks"],"exp_oop")
        assert lock["observed_marginal_source_nodes"]>0 and lock["pattern_matched_nodes"]>0
        board_e=g["evidence"]
        assert board_e is not None
        assert board_e["source_actions"]==g["node"]["acts"]
        obs=lock["observed_marginal_source_nodes"]
        assumed=lock["imputed_assumption_nodes"]
        unmatch=lock["unmatched_nodes"]
        variant=dict(version="exp_oop",run_id=raw["run_id"],sha256=e["source_sha"],
             source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",
             villain_observed_pattern_node_share_pct=lock["coverage_pct"],
             source_not_real_per_combo_observation=True,
             unknown_history_frequency_filled_with_default=bool(assumed),
             observed_marginal_source_nodes=obs,assumed_default_source_nodes=assumed,
             unlocked_source_nodes=unmatch,
             hero_model_gain_bb=locked_model_gain(e["subgame"],"exp_oop"),
             true_hero_gap_pct=e["subgame"]["info"]["hero_gap_pct"])
        texture= (lambda ranks:
            "PAIRED" if len(set(ranks))<3 else "LOW" if max(ranks)<=9 else "HIGH" if max(ranks)>=12 else "MID")(
            ["23456789TJQKA".index(flop[i])+2 for i in (0,2,4)])
        board=dict(flop=flop,turn=turn,public_board=g["node"]["board"],
             actual_exact_action_line="b100 c/",acting_seat=0,exact_flop_action="b100 c",
             actual_pot_bb=round(g["node"]["pot"]/100,5),
             actual_effective_stack_bb=round((g["subgame"]["stack"]-max(g["node"]["bets"]))/100,5),
             actual_spr=round(g["original_spr"],6),model_assumed_spr=4.667,
             relative_spr_error_pct=round(100*abs(g["original_spr"]-4.667)/4.667,6),
             genuine_gto_exploitability_pct=g["subgame"]["info"]["gto_expl_pct"],
             source_run_id=raw["run_id"],source_sha256=g["source_sha"],source_kind="PINNED_PREFLOP_CFR",
             assumed_preflop_ranges=False,exact_combo_reachable=g["source_actor_combos"],
             strict_full_street_combo_reachable=g["strict"],exact_node_actions=list(g["node"]["acts"]),
             medium_50pct_eligible_combos=board_e["medium_50pct_eligible_combos"],
             b50_nonpolarized_relative_equity_research_candidate=board_e["b50_nonpolarized_relative_equity_research_candidate"],
             nl2_locked_variants=[variant],flop_texture=texture)
        assert board["strict_full_street_combo_reachable"]>0 and board["relative_spr_error_pct"]<=5
        output.append(board)
        pins.append(dict(flop=flop,turn=turn,source_run_id=raw["run_id"],
             original_GTO_SHA256=g["source_sha"],actual_NL2_SHA256=e["source_sha"],
             GTO_strict_combos=g["strict"],NL2_strict_combos=e["strict"],
             actual_spr=board["actual_spr"],archive_code=f"B{batch}_R32_{code}",
             pool_observed_marginal_lock_nodes=obs,pool_assumed_lock_nodes=assumed,
             pool_unlocked_nodes=unmatch,medium50_exact_research_candidate=board["b50_nonpolarized_relative_equity_research_candidate"]))
    assert len(output)+len(negatives)==3
    result=dict(schema="NL2_B453_R32_THREE_ORIGINAL_GTO_NL2_OOP_SOURCE_GATE_V1",
         model_id=MODEL,rank=32,flops=[z[1] for z in SPEC],positive_exact_boards=output,
         negative_exact_boards=negatives,three_flops_original_source_complete=True,
         three_distinct_positive_gto_and_hero_locked_source_pairs=len(output)==3,
         not_private_card_NL2_conditional_frequency=True,
         no_generic_texture_CERT=True,PR2_Draft_NEVER_MERGE=True)
    gate_path=D/"nl2_hu_b453_rank32_three_board_gate.json"
    if len(output)!=3:
        result.update(CERT_MULTIBOARD=163,APPROX=229,EST=0,
            classification="APPROX_FAIL_CLOSED_INSUFFICIENT_STRICT_REACH")
        gate_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        (pathlib.Path("docs")/"NL2_HU_B453_R32_THREE_BOARD_GATE.md").write_text(
           "# B453 rank32 original three-board strict reach gate\n\n"
           "At least one of the three preregistered original GTO + real NL2 OOP lock "
           "flop pairs has no strict max/near-action legal combo. This is authentic negative evidence: "
           "rank32 remains APPROX, no fabricated CERT or medium-size recommendation. "
           "The previous V50 counts remain 163 CERT / 229 APPROX / 0 EST.\n")
        print(json.dumps(dict(cert=163,approx=229,classification=result["classification"],bad=negatives)))
        return
    assert len({b["flop"] for b in output})==3
    model["label"]="CERT-MULTIBOARD"
    model["proven_exact_board_count"]=3
    model["certified_3_to_5_exact_flop_boards"]=output
    model["blocked_reason"]=None
    model["source_credibility"]="GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH"
    st.update(schema=SCHEMA,CERT_MULTIBOARD=164,APPROX=228,EST=0,
        parent_V50_sha256=sha(base),no_generic_texture_GTO=True,
        PR2_remains_draft_never_merge=True)
    st["B453_rank32_three_true_original_GTO_NL2_OOP_flops"]=dict(
        rank=32,spot="UTG_CO",actor="UTG_OOP",line="b100 c/",
        flops=[b["flop"] for b in output],pins=pins,
        preflop_source="PINNED_POKER_SOLVER_PREFLOP_CFR",
        NL2_lock_scope="MEASURED_STREET_SIZE_POOL_MARGINALS_PLUS_DISCLOSED_ASSUMPTIONS",
        per_private_hand_action_frequency_observed=False,
        generic_handclass_texture_actions_still_approx=True,
        source_blind_first10_preregistered=True,
        no_generic_texture_certification=True)
    target=D/"nl2_hu_multiboard_status_v51_b453_rank32.json"
    target.write_text(json.dumps(st,ensure_ascii=False,indent=2)+"\n")
    # Report only named, exact GTO board references; generic handclass models stay uncertain.
    cwpath=D/"nl2_hu_model_history_crosswalk.json";cw=load(cwpath)
    row=cw["records"][MODEL]
    row["same_history_within_1pct_spr_count"]=3
    row["candidate_status"]="MATCHED_ABSTRACT_HISTORY_AND_1PCT_SPR_ONLY"
    row["generic_model_status"]="MODEL_UNCERTIFIED"
    row["upgraded_to_cert"]=False
    row["upgraded_to_est"]=False
    row["board_specific_certification_status"]="CERT_MULTIBOARD"
    row["best_exact_board_examples"]=[dict(
      source_run_id=b["source_run_id"],source_sha256=b["source_sha256"],
      spot="UTG_CO",family="SRP",version="gto",flop=b["flop"],turn=b["turn"],
      actual_public_board=b["public_board"],exact_flop_actions="b100 c",
      exact_solver_node_line="b100 c/",acting_seat=0,
      actual_node_spr=b["actual_spr"],model_assumed_node_spr=4.667,
      relative_spr_difference=round(b["relative_spr_error_pct"]/100,7),
      reached_combos=b["exact_combo_reachable"],
      strict_full_street_reachable_combos=b["strict_full_street_combo_reachable"],
      board_exact_match_to_model=False,available_for="EXACT_SOURCE_EXAMPLE_ONLY_NOT_GENERIC_CERT")
      for b in output]
    cwpath.write_text(json.dumps(cw,ensure_ascii=False,indent=2)+"\n")
    refpath=D/"nl2_hu_model_source_references.json";refs=load(refpath)
    item=refs["items"][MODEL]
    item["reference_count"]=3
    item["references"]=[dict(source_run_id=b["source_run_id"],spot="UTG_CO",family="SRP",
        version="gto",flop=b["flop"],turn=b["turn"],flop_line="b100 c",
        exact_solver_node_line="b100 c/",turn_spr=b["actual_spr"],
        source_sha256=b["source_sha256"],reference_status="CERT_EXACT_BOARD_GTO_ONLY")
      for b in output]
    item["status"]="REFERENCE_ONLY_NOT_CERTIFIED"
    item["note"]="Exactly 3 GTO sources; each paired EXP_OOP strict and measured-marginal lock in V51. No generalized texture strategy."
    refpath.write_text(json.dumps(refs,ensure_ascii=False,indent=2)+"\n")
    result.update(CERT_MULTIBOARD=164,APPROX=228,EST=0,
       classification="CERT_MULTIBOARD_EXACT_NAMED_ONLY")
    gate_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    (pathlib.Path("docs")/"NL2_HU_B453_R32_THREE_BOARD_GATE.md").write_text(
      "# B453 rank32: three authentic exact GTO / partially NL2 OOP locked boards\n\n"
      "Three preregistered UTG_CO (OOP) boards were independently verified: "
      "AsKh3d/8s, Ks7h2d/9d, KsQh4d/Tc. Every real pinned Rust GTO source has "
      "strict max/near-action full-street legal combos and a separately "
      "computed real Rust partially locked EXP_OOP on the same exact board, actor, "
      "b100-call betting history, and SPR ~4.667. No gross FME, texture, or "
      "private-card conditional NL2 claim is inferred. The 50% nonpolarized "
      "flag is retained only on boards passing true relative-equity gates. "
      "Counts are **164 CERT / 228 APPROX / 0 EST**; PR #2 remains Draft.\n")
    print(json.dumps(dict(CERT=164,APPROX=228,EST=0,
        flops=[(x["flop"],x["strict_full_street_combo_reachable"]) for x in output])))
if __name__=="__main__":main()
