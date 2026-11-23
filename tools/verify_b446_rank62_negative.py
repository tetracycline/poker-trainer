#!/usr/bin/env python3
"""B446: independently preserve rank62 strict GTO non-reachability, never promote zero-reach nodes."""
import argparse,hashlib,json,pathlib,sys
SPEC=[
 ("As9h2d","Kd",44522421850,14529315586,14529030791,"as9h2d_gto","as9h2d_exp_ip","CO_BB-gto.json","CO_BB-exp_ip.json",True),
 ("8s8h3d","5s",44653774402,14593700327,14593317327,"8s8h3d_gto","8s8h3d_exp_ip","CO_BB-gto-8s8h3d.json","CO_BB-exp_ip-8s8h3d.json",True),
 ("KsQh4d","Tc",45085489935,14778983309,14779277183,"new_gto","new_exp_ip","CO_BB-KsQh4d-gto.json","CO_BB-KsQh4d-exp_ip.json",False)
]
OLD_PREFLOP="d4ca8e0c7d53deb6af337bfef8ff0c125205c1d3ef912267d8b40efc2fe7c100"
SOLVER_SHA="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST_SHA="9d1509fe5077d019825f833eed04b16d342dfda1"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def locate(base,manifest,flop,turn,version,legacy):
    evid=base/"trainer/evidence"
    if not evid.is_dir():evid=base/"evidence"
    mf=evid/manifest
    assert mf.is_file(),mf
    m=load(mf)
    assert (m["spot"],m["version"])==("CO_BB",version)
    if legacy:
        assert m["schema"]=="HU_MISSING_ACTION_HISTORY_CFR_V1"
        assert m["source_preflop_tree_sha256"]==OLD_PREFLOP
        assert flop in m["selected_flops"]
    else:
        assert m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
        assert m["flop"]==flop and m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    rootdir=base/"solver/postflop/out/CO_BB"/version
    root=rootdir/(flop+("_extra_branch.json" if legacy else "_multiboard.json"))
    child=rootdir/(flop+"_xb75c_"+turn+".json")
    assert root.is_file() and child.is_file(),(root,child)
    case=next((v for v in m["cases"] if v.get("line")=="x b75 c" and v.get("turn")==turn),None)
    assert case is not None,(mf,flop,turn)
    expected=case["sub_sha256"] if legacy else case["source_sha256"]
    assert sha(child)==expected
    if not legacy:assert m["file_flop_sha256"]==sha(root)
    p1=evid/"poker-solver-commit.txt";p2=evid/"upstream-engine-commit.txt"
    assert p1.read_text().strip()==SOLVER_SHA and p2.read_text().strip()==RUST_SHA
    return m,load(root),load(child),root,child
def target(root,sub,mask,turn):
    rows=[]
    for n in sub["nodes"]:
        if n.get("line")!="x b75 c/x" or n.get("player")!=1 or len(n["board"])!=8 or n["board"][-2:]!=turn:continue
        key="|".join((n["board"],n["line"],"1"))
        q=mask[key]
        spr=(sub["stack"]-max(n["bets"]))/n["pot"]
        assert abs(spr-6.791)/6.791<=.05
        assert "b50" in n["acts"] and "b100" in n["acts"]
        rows.append(dict(board=n["board"],line=n["line"],actor=1,
          source_actor_combos=sum(float(x)>1e-4 for x in n["w"][1]),
          strict_full_street_combos=int(q["count"]),node_spr=round(spr,6)))
    assert len(rows)==1,(turn,rows)
    assert rows[0]["source_actor_combos"]>0
    return rows[0]
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--downloads",required=True,type=pathlib.Path)
    a.add_argument("--run-id",required=True,type=int)
    p=a.parse_args()
    root=pathlib.Path.cwd()
    sys.path.insert(0,str((root/"tools").resolve()))
    from hu_sequential_cfr_reach import game_reach
    status=load(root/"data/nl2_hu_multiboard_status_v50_b417_rank166.json")
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["TOTAL"])==(163,229,392)
    rec=status["records"]["ln-ipfr-t_model-snfiz2"]
    assert (rec["frequency_rank"],rec["label"],rec["assumed_model_node_spr"])==(62,"APPROX",6.791)
    results=[]
    for flop,turn,rid,gid,eid,gd,ed,gman,eman,legacy in SPEC:
        gm,gr,gs,groot,gchild=locate(p.downloads/gd,gman,flop,turn,"gto",legacy)
        em,er,es,eroot,echild=locate(p.downloads/ed,eman,flop,turn,"exp_ip",legacy)
        assert (gr["flop"],gs["flop"],gs["turn"])==(flop,flop,turn)
        assert (er["flop"],es["flop"],es["turn"])==(flop,flop,turn)
        assert float(gs["info"]["gto_expl_pct"])<=.5
        assert float(es["info"]["hero_gap_pct"])<=.5
        gmask,gstats=game_reach(gr,gs)
        emask,estats=game_reach(er,es)
        g=target(gr,gs,gmask,turn)
        e=target(er,es,emask,turn)
        ej=echild.with_suffix(".job.json")
        assert ej.is_file() and load(ej)["hero"]==1 and load(ej).get("locks")
        results.append(dict(flop=flop,turn=turn,original_run=rid,
          gto_artifact_id=gid,exp_ip_artifact_id=eid,
          gto_root_sha256=sha(groot),gto_turn_sha256=sha(gchild),
          exp_ip_root_sha256=sha(eroot),exp_ip_turn_sha256=sha(echild),
          GTO=g,EXP_IP=e,gto_gap_pct=gs["info"]["gto_expl_pct"],
          exp_ip_hero_gap_pct=es["info"]["hero_gap_pct"],
          original_preflop_sha256=gm.get("source_preflop_tree_sha256"),
          source_type="HISTORICAL_PINNED" if legacy else "CURRENT_PINNED",
          prior_sources_reused_only=True,not_an_empirical_per_private_hand_frequency=True))
        print(json.dumps({"flop":flop,"GTO_strict":g["strict_full_street_combos"],
          "EXP_IP_strict":e["strict_full_street_combos"]}))
    assert len(results)==3 and results[0]["GTO"]["strict_full_street_combos"]==0
    positives=[x for x in results if x["GTO"]["strict_full_street_combos"]>0
               and x["EXP_IP"]["strict_full_street_combos"]>0]
    assert len(positives)<3
    out=dict(schema="NL2_B446_R62_AUTHENTIC_GTO_FAIL_CLOSED_V1",
      model_id="ln-ipfr-t_model-snfiz2",frequency_rank=62,
      exact_line="x b75 c/x",acting_seat=1,target_spr=6.791,
      source_experiments=results,paired_positive_flops=len(positives),
      verified_board_candidate_count=3,
      strict_zero_GTO_flops=[x["flop"] for x in results if x["GTO"]["strict_full_street_combos"]==0],
      classification="APPROX_NO_CERT_UNDER_MAX_NEAR_MULTI_STREET_RULE",
      reason="PREREGISTERED_GTO_STRICT_FULL_STREET_COMBO_REACH_IS_ZERO_FOR_AS9H2D",
      historical_preflop_SHA=OLD_PREFLOP,
      pinned_solver_sha=SOLVER_SHA,pinned_rust_sha=RUST_SHA,
      original_source_pot_and_board_only=True,
      NL2_lock_is_street_size_marginal_not_private_hand_observation=True,
      no_unearned_medium_nonpolarized_50pct_bet_claim=True,
      no_generic_texture_certification=True,
      CERT_MULTIBOARD=163,APPROX=229,EST=0,TOTAL=392,
      old_failed_B433_not_promoted=True,PR2_Draft_NEVER_MERGE=True)
    d=root/"data/nl2_hu_b446_rank62_strict_zero_negative_proof.json"
    d.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    doc=root/"docs/NL2_HU_B446_R62_GTO_STRICT_ZERO_NEGATIVE.md"
    doc.write_text("# B446 rank62 authentic strict-reach negative evidence\n\n"
      "Three complete original GTO+NL2-IP solver sources were retrieved and SHA-checked, not rerun. "
      "At the exact CO IP turn node x b75 c/x, As9h2d/Kd has **zero strict full-street GTO reachable combos** "
      "under the frozen max/near-frequency rule, even though raw actor source combos exist. "
      "Therefore rank62 cannot be certified using these three flops. The failed B445 promotion is not reused; "
      "V50 remains 163 CERT / 229 APPROX / 0 EST. \n\n"
      "Historical source input preflop SHA and current pinned preflop SHA are distinct; both are labeled. "
      "No invention of private-card NL2 frequencies or generic non-polarized 50% decision rules.\n")
    print(json.dumps({"B446":"FAIL_CLOSED_VERIFIED","cert":163,"approx":229,
      "positive_flops":len(positives),"total":3}))
if __name__=="__main__":main()
