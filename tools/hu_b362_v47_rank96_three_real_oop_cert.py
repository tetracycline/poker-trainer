#!/usr/bin/env python3
"""B362 V47: promote only three different, SHA-authentic 100bb UTG_CO rank96
original Rust GTO plus actually reachable NL2 OOP partial-lock flops.
Frozen legacy Stage2 Ks7h2d + B359 As9h2d + B361 Qs8h2d.
Legacy Stage2 used 33/50/75 flop sizing, NOT the four-size menu of new jobs.
"""
import argparse
import copy
import gzip
import hashlib
import json
import pathlib
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import game_reach
from hu_cert_lock_medium_coverage_matrix import create
from hu_cert_lock_medium_audit import audit

D=pathlib.Path("data")
MID="ln-opfr-r_model-18g2rvt"
LINE="b33 c/b50 c/"
SPOT="UTG_CO"
SPR=4.15
HIST_RUN=44654973894
RUNS={359:44976462678,361:44977743690}
PARENT=D/"nl2_hu_multiboard_status_v46_b354_rank79.json"
STATUS=D/"nl2_hu_multiboard_status_v47_b362_rank96.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v47_b362.json"
PROOF=D/"nl2_hu_b362_v47_rank96_3_original_GTO_real_NL2_OOP_source_gate.json"
DOC=pathlib.Path("docs/NL2_HU_B362_V47_RANK96_THREE_REAL_GTO_NL2_OOP_CERT.md")
def read(p):
    return json.loads(p.read_text())
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(raw):
    return hashlib.sha256(raw).hexdigest()
def actor_nodes(case):
    return {n["public_board"]:n for n in case["nodes"]
        if n["acting_seat"]==0 and n["exact_node_line"]==LINE
        and len(n["public_board"])==10
        and n["strictly_reachable_combos"]>0
        and abs(n["node_spr"]-SPR)/SPR<=.05}
def make_lock(version,run,source_sha,scope,observed=None,assumed=None,unlocked=None,gain=None):
    assert version=="exp_oop" and run>0 and len(source_sha)==64
    assert (observed is None and assumed is None and unlocked is None) or all(
        isinstance(x,int) and x>=0 for x in (observed,assumed,unlocked))
    return dict(version=version,run_id=run,sha256=source_sha,source_scope=scope,
        villain_observed_pattern_node_share_pct=None,
        source_not_real_per_combo_observation=True,
        unknown_history_frequency_filled_with_default=True if observed is None
            else bool(assumed or unlocked),
        observed_marginal_source_nodes=observed,
        assumed_default_source_nodes=assumed,
        unlocked_source_nodes=unlocked,
        hero_model_gain_bb=gain)
def archive(batch):
    ixp=D/f"solver_evidence/NL2_MULTIBOARD_B{batch}_R96_VERIFIED.index.json"
    gz=D/f"solver_evidence/NL2_MULTIBOARD_B{batch}_R96_VERIFIED.json.gz"
    ix=read(ixp)
    raw=gzip.decompress(gz.read_bytes())
    assert ix["run_id"]==RUNS[batch] and ix["gzip_sha256"]==sha(gz)
    assert ix["raw_sha256"]==digest(raw)
    data=json.loads(raw)
    assert data["schema"]=="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1"
    assert data["source_run_id"]==RUNS[batch] and not data["errors"]
    assert data["source_poker_solver_pin"]=="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
    assert data["authentic_rust_engine_pin"]=="9d1509fe5077d019825f833eed04b16d342dfda1"
    return data,dict(batch=batch,run_id=RUNS[batch],
        archive_index_sha256=sha(ixp),archive_gzip_sha256=sha(gz))
def case_for(data,flop,turn,version):
    matches=[c for a in data["artifacts"]
        if (a["spot"],a["flop"],a["version"])==(SPOT,flop,version)
        for c in a["cases"] if (c["flop_line"],c["turn"])==("b33 c",turn)]
    assert len(matches)==1,("Source exact subgame missing",flop,turn,version)
    c=matches[0]
    assert (c["flop_root_pot_bb"],c["flop_root_stack_bb"])==(6.5,97.5)
    assert c["empirical_scope"]=="PINNED_PREFLOP_CFR"
    assert c["flop_size_menu"]==["33%","50%","75%","100%"]
    assert c["gto_exploitability_pct"]<=.5 and len(c["source_sha256"])==64
    if version=="exp_oop":
        assert c["locked_hero_gap_pct"] is not None and c["locked_hero_gap_pct"]<=.5
    return c
def build_fresh(batch,flop):
    original=D/f"nl2_hu_b{batch}_rank96_two_new_true_source_proofs.json"
    p=read(original);data,pin=archive(batch)
    assert p["source_run_id"]==RUNS[batch] and p["rank96_remains_APPROX_pending_independent_3_board_gate"]
    pair=next(z for z in p["candidate_pairs"] if z["flop"]==flop)
    assert pair["strict_authenticated_pair"] and pair["new_exact_matched_GTO_NL2_OOP_river_boards"]
    rows={x["version"]:x for x in p["source_proofs"] if x["flop"]==flop}
    assert set(rows)=={"gto","exp_oop"}
    assert rows["gto"]["turn"]==rows["exp_oop"]["turn"]
    turn=rows["gto"]["turn"]
    cg=case_for(data,flop,turn,"gto")
    ce=case_for(data,flop,turn,"exp_oop")
    assert cg["source_sha256"]==rows["gto"]["turn_river_sha256"]
    assert ce["source_sha256"]==rows["exp_oop"]["turn_river_sha256"]
    orig,lock=actor_nodes(cg),actor_nodes(ce)
    shared=sorted(set(orig)&set(lock)&set(pair["new_exact_matched_GTO_NL2_OOP_river_boards"]),
        key=lambda b:(-orig[b]["strictly_reachable_combos"],b))
    assert shared,("No genuine two-actor exact public river",flop)
    board=shared[0];n=orig[board];e=lock[board]
    for v,nodes in (("gto",orig),("exp_oop",lock)):
        r=rows[v]["strict_UTG_OOP_exact_river_public_nodes"]
        assert board in r and nodes[board]["strictly_reachable_combos"]==r[board]["combos"]
        assert abs(nodes[board]["node_spr"]-r[board]["SPR"])<.00001
    assert n["source_actions"]==e["source_actions"]
    assert abs(n["node_spr"]-e["node_spr"])<=.01
    sc=ce["villain_lock_scope"]
    observed=sc["observed_marginal_source_nodes"]
    assumed=sc["imputed_assumption_nodes"]
    unmatched=sc["unmatched_nodes"]
    assert all(isinstance(x,int) and x>=0 for x in (observed,assumed,unmatched))
    medium=int(n.get("medium_50pct_eligible_combos") or 0)
    research=bool(n.get("b50_nonpolarized_relative_equity_research_candidate"))
    if research:assert medium>0
    b=dict(flop=flop,turn=turn,public_board=board,
      actual_exact_action_line=LINE,acting_seat=0,exact_flop_action="b33 c",
      actual_pot_bb=n["pot_bb"],actual_effective_stack_bb=n["remaining_bb"],
      actual_spr=n["node_spr"],model_assumed_spr=SPR,
      relative_spr_error_pct=round(100*abs(n["node_spr"]-SPR)/SPR,5),
      genuine_gto_exploitability_pct=cg["gto_exploitability_pct"],
      source_run_id=RUNS[batch],source_sha256=cg["source_sha256"],
      source_kind="PINNED_PREFLOP_CFR_AUTHENTIC_FULL_FOUR_SIZE_100BB_RUST",
      assumed_preflop_ranges=False,
      exact_combo_reachable=n["source_reachable_combos"],
      strict_full_street_combo_reachable=n["strictly_reachable_combos"],
      exact_node_actions=n["source_actions"],
      medium_50pct_eligible_combos=medium,
      b50_nonpolarized_relative_equity_research_candidate=research,
      flop_texture=texture(flop),
      nl2_locked_variants=[make_lock("exp_oop",RUNS[batch],ce["source_sha256"],
        "TRUE_ORIGINAL_100BB_UTGCO_NL2_OOP_PARTIAL_RUST_MEASURED_POOL_MARGINAL_VS_ASSUMED_SOURCE_NODES",
        observed=observed,assumed=assumed,unlocked=unmatched,
        gain=ce.get("hero_model_gain_bb"))])
    return b,dict(flop=flop,turn=turn,board=board,run_id=RUNS[batch],
        original_GTO_turn_sha256=cg["source_sha256"],
        true_NL2_OOP_turn_sha256=ce["source_sha256"],
        strictly_reachable_GTO_actor_combos=n["strictly_reachable_combos"],
        strictly_reachable_NL2_actor_combos=e["strictly_reachable_combos"],
        pin=pin,proof_sha256=sha(original),flop_source_menu=cg["flop_size_menu"],
        no_per_private_card_empirical_NL2_rates=True)
def build_historic(gto_folder,exp_folder):
    hfile=D/"nl2_hu_b175_v32_248_exact_GTO_source_provenance.json"
    history=read(hfile)
    row=next(z for z in history["rows"] if z["rank"]==96)
    assert row["model_id"]==MID and row["model_SPR"]==SPR and row["hero_seat"]==0
    assert row["distinct_GTO_plus_NL2_hero_flops"]==["Ks7h2d"]
    old_proofs=[p for p in row["exact_authentic_gto_source_proofs"]
        if (p["flop"],p["turn"],p["actor"],p["exact_line"],p["source_run"])==
           ("Ks7h2d","9d",0,LINE,HIST_RUN)]
    assert len(old_proofs)>=2 and all(p["true_NL2_actor_locked"] and
        p["paired_lock_runs"]==[HIST_RUN] and p["strict_legal_combos"]>0
        and p["SPR_error_pct"]<=5 for p in old_proofs)
    original_sha=old_proofs[0]["source_sha"]
    assert all(p["source_sha"]==original_sha for p in old_proofs)
    sources={}
    for version,folder in (("gto",gto_folder),("exp_oop",exp_folder)):
        manifest=folder/f"evidence/UTG_CO-{version}-Ks7h2d.json"
        assert manifest.is_file()
        m=read(manifest)
        assert (m["spot"],m["version"])==(SPOT,version)
        c=[x for x in m["cases"] if (x["flop"],x["turn"],x["line"])==("Ks7h2d","9d","b33 c")]
        assert len(c)==1
        item=c[0]
        flop_path=folder/"solver/postflop"/item["flop_json"]
        sub_path=folder/"solver/postflop"/item["sub_json"]
        assert flop_path.is_file() and sub_path.is_file()
        assert sha(flop_path)==item["flop_sha256"] and sha(sub_path)==item["sub_sha256"]
        root=read(flop_path);child=read(sub_path)
        assert (root["flop"],root["pot"],root["stack"])==("Ks7h2d",650,9750)
        assert (child["flop"],child["turn"],child["line0"])==("Ks7h2d","9d","b33 c")
        assert child["info"]["gto_expl_pct"]<=.5
        if version=="exp_oop":assert child["info"]["hero_gap_pct"]<=.5
        seq,stats=game_reach(root,child)
        candidates={}
        for n in child["nodes"]:
            if (n["player"],n["line"],len(n["board"]))!=(0,LINE,10):continue
            q=seq.get("|".join((n["board"],n["line"],"0")))
            assert q is not None
            spr=(child["stack"]-max(n["bets"]))/n["pot"]
            if q["count"]<=0 or abs(spr-SPR)/SPR>.05:continue
            candidates[n["board"]]=dict(node=n,strict=q["count"],
                source=sum(float(z)>1e-4 for z in n["w"][0]),
                spr=spr)
        sources[version]=dict(manifest_sha256=sha(manifest),turn_sha256=sha(sub_path),
            root_sha256=sha(flop_path),item=item,root=root,child=child,candidates=candidates)
    assert sources["gto"]["turn_sha256"]==original_sha
    a=sources["gto"];z=sources["exp_oop"]
    shared=sorted(set(a["candidates"])&set(z["candidates"]),
        key=lambda b:(-a["candidates"][b]["strict"],b))
    assert shared,("Historic B175 original case did not reproduce actor 40/70",a["candidates"],z["candidates"])
    board=shared[0]
    cg=a["candidates"][board];ce=z["candidates"][board]
    n=cg["node"];e=ce["node"]
    assert n["acts"]==e["acts"]
    medium=0 # No speculative legacy medium50 claim: historical current-action figures do not guarantee full sequential threshold
    b=dict(flop="Ks7h2d",turn="9d",public_board=board,
      actual_exact_action_line=LINE,acting_seat=0,exact_flop_action="b33 c",
      actual_pot_bb=n["pot"]/100,
      actual_effective_stack_bb=(a["child"]["stack"]-max(n["bets"]))/100,
      actual_spr=round(cg["spr"],6),model_assumed_spr=SPR,
      relative_spr_error_pct=round(100*abs(cg["spr"]-SPR)/SPR,5),
      genuine_gto_exploitability_pct=a["child"]["info"]["gto_expl_pct"],
      source_run_id=HIST_RUN,source_sha256=a["turn_sha256"],
      source_kind="PINNED_PREFLOP_CFR_LEGACY_100BB_33_50_75_FLOP_MENU_NO_100",
      assumed_preflop_ranges=False,exact_combo_reachable=cg["source"],
      strict_full_street_combo_reachable=cg["strict"],
      exact_node_actions=n["acts"],
      medium_50pct_eligible_combos=medium,
      b50_nonpolarized_relative_equity_research_candidate=False,
      flop_texture=texture("Ks7h2d"),
      nl2_locked_variants=[make_lock("exp_oop",HIST_RUN,z["turn_sha256"],
        "HISTORIC_ORIGINAL_STAGE2_AUTHENTIC_UTGCO_NL2_OOP_PARTIAL_RUST_UNKNOWN_NODE_DENOMINATORS")])
    return b,dict(flop="Ks7h2d",turn="9d",board=board,run_id=HIST_RUN,
        original_GTO_turn_sha256=a["turn_sha256"],
        true_NL2_OOP_turn_sha256=z["turn_sha256"],
        original_GTO_root_sha256=a["root_sha256"],
        original_NL2_root_sha256=z["root_sha256"],
        original_GTO_manifest_sha256=a["manifest_sha256"],
        original_NL2_manifest_sha256=z["manifest_sha256"],
        source_B175_sha256=sha(hfile),source_GTO_B175_strict_rows=[p["strict_legal_combos"] for p in old_proofs],
        reproduced_sequential_GTO_combos=cg["strict"],
        reproduced_sequential_NL2_actor_combos=ce["strict"],
        source_flop_size_menu="LEGACY_33_50_75_NOT_FULL_33_50_75_100",
        no_per_private_card_empirical_NL2_rates=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--historic-gto",required=True,type=pathlib.Path)
    p.add_argument("--historic-exp-oop",required=True,type=pathlib.Path)
    args=p.parse_args()
    old=read(PARENT)
    assert old["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79"
    assert (old["CERT_MULTIBOARD"],old["APPROX"],old["EST"],old["TOTAL"])==(158,234,0,392)
    target=old["records"][MID]
    assert (target["label"],target["frequency_rank"],target["solver_profile"],
        target["assumed_model_node_spr"])==("APPROX",96,SPOT,SPR)
    before_legacy=sha(PARENT)
    boards=[];pins=[]
    b,pin=build_historic(args.historic_gto,args.historic_exp_oop)
    boards.append(b);pins.append(pin)
    for batch,flop in ((359,"As9h2d"),(361,"Qs8h2d")):
        b,pin=build_fresh(batch,flop)
        boards.append(b);pins.append(pin)
    assert [b["flop"] for b in boards]==["Ks7h2d","As9h2d","Qs8h2d"]
    assert len({b["flop"] for b in boards})==3
    textures={b["flop_texture"] for b in boards}
    assert len(textures)>=2
    assert all(b["acting_seat"]==0 and b["actual_exact_action_line"]==LINE and
        b["strict_full_street_combo_reachable"]>0 and b["relative_spr_error_pct"]<=5 and
        b["nl2_locked_variants"][0]["version"]=="exp_oop" and
        not b["assumed_preflop_ranges"] for b in boards)
    new=copy.deepcopy(old)
    new["records"][MID].update(
      label="CERT-MULTIBOARD",high_frequency_preregistered=True,
      original_top24_high_frequency_preregistered=False,
      source_blind_expansion_rank=96,
      prereg_cohort="HISTORIC_STAGE2_KS7H2D_ACTUAL_GTO_NL2_OOP_PLUS_B359_AS9H2D_AND_B361_QS8H2D_TRUE_ORIGINAL_RUST_SHA_40_70",
      certified_3_to_5_exact_flop_boards=boards,
      proven_exact_board_count=3,blocked_reason=None,
      source_credibility="3_DIFFERENT_AUTHENTIC_100BB_UTGCO_GTO_AND_REAL_NL2_OOP_HERO_SHA_TWO_PLUS_TEXTURES_LEGACY_TREE_DISCLOSED")
    assert {k for k in old["records"] if old["records"][k]!=new["records"][k]}=={MID}
    new.update(schema="NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B362_RANK96",
      CERT_MULTIBOARD=159,APPROX=233,EST=0,TOTAL=392,parent_v46_sha256=before_legacy,
      source_blind_expansion_ranks=sorted(set(old["source_blind_expansion_ranks"])|{96}),
      supplementary_cert_count=old["supplementary_cert_count"]+1,
      B362_rank96_three_authentic_GTO_NL2_OOP_flops=dict(
          rank=96,model_id=MID,spot=SPOT,actor="UTG_OOP",exact_line=LINE,
          model_spr=SPR,flops=[b["flop"] for b in boards],
          textures=sorted(textures),source_verification=pins,
          legacy_stage2_33_50_75_menu_explicit=True,
          newer_B359_B361_true_full_four_size_menu=True,
          only_named_board_no_unseen_texture_extrapolation=True,
          no_per_private_card_observed_NL2_frequency=True))
    assert sum(z["label"]=="CERT-MULTIBOARD" for z in new["records"].values())==159
    assert sum(z["label"]=="APPROX" for z in new["records"].values())==233
    # This version must be added deliberately to the independent source auditor and committed atomically after PASS.
    auditor=pathlib.Path("tools/hu_cert_lock_medium_audit.py")
    source=auditor.read_text()
    needle="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79')"
    replacement="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79',\n                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B362_RANK96')"
    assert source.count(needle)==1 and "V47_B362_RANK96" not in source
    auditor.write_text(source.replace(needle,replacement))
    import importlib,hu_cert_lock_medium_audit
    importlib.reload(hu_cert_lock_medium_audit)
    # Rebind create's audit so this rerun validates the actual new schema.
    import hu_cert_lock_medium_coverage_matrix
    hu_cert_lock_medium_coverage_matrix.audit=hu_cert_lock_medium_audit.audit
    assert hu_cert_lock_medium_audit.audit(new)["cert_multiboard"]==159
    matrix=hu_cert_lock_medium_coverage_matrix.create(new)
    assert (len(matrix["boards"]),len(matrix["models"]))==(606,159)
    assert matrix["strict_aggregate"]["named_board_proofs"]==606
    assert matrix["strict_aggregate"]["hero_lock_variants"]==698
    STATUS.write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n")
    matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V47_B362",
      parent_v47_status_sha256=sha(STATUS),
      partial_NL2_locks_are_not_whole_flop_GTO=True,
      NL2_private_combo_conditional_rates_not_observed=True,
      only_exact_board_b50_nonpolarized_research=True,
      unknown_source_denominators_are_not_zero_or_empirical=True,
      legacy_original_stage2_source_menu_is_disclosed=True,
      PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(matrix,indent=2,ensure_ascii=False)+"\n")
    proof=dict(schema="NL2_HU_B362_V47_RANK96_3_GENUINE_UTGCO_GTO_NL2_OOP_SOURCE_CERT_V1",
      parent_V46_status_sha256=before_legacy,V47_status_sha256=sha(STATUS),
      V47_matrix_sha256=sha(MATRIX),source_Auditor_sha256=sha(auditor),
      three_distinct_flops=[x["flop"] for x in boards],
      two_plus_textures=sorted(textures),true_original_source_provenance=pins,
      preflop_100bb_CFR_pinned=True,
      historical_source_flop_menu_33_50_75_not_full_four=True,
      GTO_and_NL2_are_not_universal_texture_recommendations=True,
      no_observed_NL2_private_card_action_conditionals=True,
      CERT=159,APPROX=233,EST=0,TOTAL=392,
      named_GTO_NL2_actor_boards=606,real_NL2_actor_lock_variants=698,
      full_HU2475_and_independent_audit_required_before_commit=True,
      PR2_Draft_NEVER_MERGE=True)
    PROOF.write_text(json.dumps(proof,indent=2,ensure_ascii=False)+"\n")
    DOC.write_text("# B362 V47 rank96: three authentic exact-board UTG_CO OOP GTO + NL2 partial-lock sources\n\n"
       "Certified exact original 100bb public flops: "
       +", ".join(b["flop"]+"/"+b["turn"]+" ("+b["public_board"]+")" for b in boards)
       +". Actor UTG OOP, exact b33 c/b50 c/, SPR4.15 ±5%, source SHA verified, full sequential 40/70 prior actor actions, both GTO and real NL2 partially locked hero sources, >=2 flop textures.\n\n"
       "Caveat: historical Stage2 Ks7h2d was solved with 33/50/75 FLOP sizing, NOT the full newer 33/50/75/100 menu; B359/B361 are original full four-size 100bb CFR. This changes the abstract game and is transparently retained per source, never relabeled as identical. NL2 locks rely on pooled street/size marginals and stated defaults, not observed opponent private-card-conditional rates. No GTO generalization to other textures or public boards. \n\n"
       "V47 159 CERT /233 APPROX /0 EST, 606 true named source boards and 698 real actor NL2 partial lock variants. Current deployed UI remains V46 until separately updated; full Actions HU2475 before commit. PR #2 draft, NEVER MERGE.\n")
    print("PASS B362 V47 source-gated 3 original flops",[(b["flop"],b["strict_full_street_combo_reachable"]) for b in boards],
        "159 CERT/233 APPROX, 606 named/698 actor locks")
if __name__=="__main__":
    main()
