#!/usr/bin/env python3
"""B444: certify rank62 only after three exact GTO + measured NL2-IP locked boards."""
import argparse,gzip,hashlib,json,pathlib,sys,collections
MODEL="ln-ipfr-t_model-snfiz2"
SOLVER_PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST_PIN="9d1509fe5077d019825f833eed04b16d342dfda1"
PIPE_SHA="f0a173b3d9331c4ff8697359a838094f76babb35f16133e37bbd0bfb203b5253"
RANGES_SHA="f2a302b483c79995ed90031b62e65a202ae7a1fdc8695f8940fe3e8291fb2bba"
PREFLOP_SHA="d4ca8e0c7d53deb6af337bfef8ff0c125205c1d3ef912267d8b40efc2fe7c100"
CURRENT_PINNED_PREFLOP_SHA="58e91ec080c8adaef762b49590ebbf245873861b54e3618a1716316aadd35caf"
# Original legacy manifests use d4ca..., current pinned checkout uses distinct 58e... tree.

MODEL_SPR=6.791
SPECS=[
 dict(flop="As9h2d",turn="Kd",run_id=44522421850,dir_gto="as9h2d_gto",
      dir_ip="as9h2d_exp_ip",code="B444_R62_AS9H2D",legacy=True,
      manifest_gto="CO_BB-gto.json",manifest_ip="CO_BB-exp_ip.json"),
 dict(flop="8s8h3d",turn="5s",run_id=44653774402,dir_gto="8s8h3d_gto",
      dir_ip="8s8h3d_exp_ip",code="B444_R62_8S8H3D",legacy=True,
      manifest_gto="CO_BB-gto-8s8h3d.json",manifest_ip="CO_BB-exp_ip-8s8h3d.json"),
 dict(flop="KsQh4d",turn="Tc",run_id=None,dir_gto="new_gto",
      dir_ip="new_exp_ip",code="B444_R62_KSQH4D",legacy=False,
      manifest_gto="CO_BB-KsQh4d-gto.json",manifest_ip="CO_BB-KsQh4d-exp_ip.json"),
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def evidence_dir(base):
    p=base/"trainer/evidence"
    return p if p.is_dir() else base/"evidence"
def check_pin(base,solver_root):
    e=evidence_dir(base)
    p1=e/"poker-solver-commit.txt"; p2=e/"upstream-engine-commit.txt"
    if not p1.exists(): p1=e/"poker-solver-pin.txt"
    if not p2.exists(): p2=e/"rust-pin.txt"
    assert p1.read_text().strip()==SOLVER_PIN
    assert p2.read_text().strip()==RUST_PIN
    assert sha(solver_root/"postflop/py/pipeline.py")==PIPE_SHA
    assert sha(solver_root/"postflop/py/ranges.py")==RANGES_SHA
    assert sha(solver_root/"preflop/gto_norake.json")==CURRENT_PINNED_PREFLOP_SHA
def paths(base,version,flop,turn,legacy,manifest_name,solver_root):
    ev=evidence_dir(base); m=read(ev/manifest_name)
    rootdir=base/"solver/postflop/out/CO_BB"/version
    root=rootdir/(f"{flop}_extra_branch.json" if legacy else f"{flop}_multiboard.json")
    sub=rootdir/f"{flop}_xb75c_{turn}.json"; job=sub.with_suffix(".job.json")
    rootjob=root.with_suffix(".job.json")
    assert all(x.is_file() for x in (root,rootjob,sub,job)),(root,rootjob,sub,job)
    case=next((x for x in m["cases"] if x.get("line")=="x b75 c" and x.get("turn")==turn),None)
    assert case is not None,(manifest_name,[(x.get("line"),x.get("turn")) for x in m.get("cases",[])])
    if legacy:
        assert m["schema"]=="HU_MISSING_ACTION_HISTORY_CFR_V1"
        assert (m["spot"],m["version"])==("CO_BB",version)
        assert flop in m["selected_flops"]
        assert m["source_pipeline_sha256"]==PIPE_SHA
        assert m["source_ranges_sha256"]==RANGES_SHA
        assert m["source_preflop_tree_sha256"]==PREFLOP_SHA
        expected=case["sub_sha256"]
    else:
        assert m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
        assert (m["spot"],m["version"],m["flop"])==("CO_BB",version,flop)
        assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
        assert "x b75 c" in m["selected_lines"] and turn in m["turns"]
        assert m["file_flop_sha256"]==sha(root)
        assert m["solver_pin"]==sha(solver_root/"postflop/py/pipeline.py")
        assert m["solver_ranges_sha256"]==sha(solver_root/"postflop/py/ranges.py")
        expected=case.get("source_sha256") or case.get("sub_sha256")
    assert sha(sub)==expected,(sub,sha(sub),expected)
    return m,root,rootjob,sub,job,case
def node_for(sub,turn):
    a=[n for n in sub["nodes"] if n["line"]=="x b75 c/x" and n["player"]==1 and n["board"][-2:]==turn]
    assert len(a)==1,("target node count",turn,len(a))
    return a[0]
def texture(flop):
    ranks=[int("23456789TJQKA".index(flop[i]))+2 for i in (0,2,4)]
    if len(set(ranks))<3:return "PAIRED"
    if max(ranks)<=9:return "LOW"
    if max(ranks)>=12:return "HIGH"
    return "MID"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--downloads",required=True,type=pathlib.Path)
    ap.add_argument("--solver-root",required=True,type=pathlib.Path)
    ap.add_argument("--run-id",required=True,type=int)
    a=ap.parse_args()
    repo=pathlib.Path.cwd(); D=repo/"data"; solver_root=a.solver_root.resolve()
    sys.path.insert(0,str((repo/"tools").resolve()))
    sys.path.insert(0,str((solver_root/"postflop/py").resolve()))
    from hu_sequential_cfr_reach import game_reach
    from verify_hu_multiboard_100bb import source_nodes,lock_scope,locked_model_gain
    import locks as LK
    assert sha(solver_root/"postflop/py/pipeline.py")==PIPE_SHA
    assert sha(solver_root/"postflop/py/ranges.py")==RANGES_SHA
    assert sha(solver_root/"preflop/gto_norake.json")==CURRENT_PINNED_PREFLOP_SHA
    all_boards=[]; archive_by_run={}; archive_codes={}
    for spec in SPECS:
        run_id=spec["run_id"] if spec["legacy"] else a.run_id
        gb=a.downloads/spec["dir_gto"]; ib=a.downloads/spec["dir_ip"]
        check_pin(gb,solver_root); check_pin(ib,solver_root)
        gm,grpath,grjob,gspath,gsjob,gcase=paths(gb,"gto",spec["flop"],spec["turn"],spec["legacy"],spec["manifest_gto"],solver_root)
        im,irpath,irjob,ispath,isjob,icase=paths(ib,"exp_ip",spec["flop"],spec["turn"],spec["legacy"],spec["manifest_ip"],solver_root)
        gr=read(grpath); grj=read(grjob); gs=read(gspath); gj=read(gsjob)
        ir=read(irpath); irj=read(irjob); ins=read(ispath); ij=read(isjob)
        assert (gr["flop"],gs["flop"],gs["turn"])==(spec["flop"],spec["flop"],spec["turn"])
        assert (ir["flop"],ins["flop"],ins["turn"])==(spec["flop"],spec["flop"],spec["turn"])
        assert abs(float(gj.get("rake_rate",0.05))-.05)<1e-8 and gj.get("rake_cap",1000)==1000
        assert abs(float(ij["rake_rate"])-.05)<1e-8 and ij["rake_cap"]==1000
        assert ij["hero"]==1 and ij.get("locks")
        assert gj.get("hero") in (None,0) and not gj.get("locks")
        ggap=float(gs["info"]["gto_expl_pct"])
        hgap=float(ins["info"]["hero_gap_pct"])
        assert ggap<=.5,(spec["flop"],"GTO gap",ggap)
        assert hgap<=.5,(spec["flop"],"EXP_IP hero gap",hgap)
        if spec["legacy"]:
            assert float(gcase["sub_gto_expl_pct"])<=.5
            assert abs(float(icase["sub_hero_gap_pct"])-hgap)<1e-6
        else:
            assert float(gcase.get("gto_gap_pct",ggap))<=.5
            assert float(icase.get("hero_gap_pct",hgap))<=.5
        L=LK.build("SRP","ip",False,spec["flop"])
        assert LK.driver_locks(L)==ij["locks"],(spec["flop"],"job locks differ from pinned measured pool")
        gmask,gstats=game_reach(gr,gs); imask,istats=game_reach(ir,ins)
        gn=node_for(gs,spec["turn"]); inn=node_for(ins,spec["turn"])
        key="|".join((gn["board"],gn["line"],"1"))
        ikey="|".join((inn["board"],inn["line"],"1"))
        gq=gmask[key]; iq=imask[ikey]
        gstrict=int(gq["count"]); istrict=int(iq["count"])
        graw=sum(float(x)>1e-4 for x in gn["w"][1])
        iraw=sum(float(x)>1e-4 for x in inn["w"][1])
        assert gstrict>=40,(spec["flop"],"GTO strict reach",gstrict)
        assert istrict>0,(spec["flop"],"NL2-IP strict reach",istrict)
        actual_spr=(float(gs["stack"])-max(gn["bets"]))/float(gn["pot"])
        spr_err=100*abs(actual_spr-MODEL_SPR)/MODEL_SPR
        assert spr_err<=5,(spec["flop"],actual_spr,spr_err)
        lock=lock_scope(ins,L,"exp_ip")
        assert lock["observed_marginal_source_nodes"]>0 and lock["pattern_matched_nodes"]>0,(spec["flop"],lock)
        one=dict(gs); one["nodes"]=[gn]
        gnodes=source_nodes(one,{"nodes":{key:gq}})
        assert len(gnodes)==1
        medium_eligible=int(gnodes[0]["medium_50pct_eligible_combos"])
        medium_candidate=bool(gnodes[0]["b50_nonpolarized_relative_equity_research_candidate"])
        ip_one=dict(ins); ip_one["nodes"]=[inn]
        inodes=source_nodes(ip_one,{"nodes":{ikey:iq}})
        assert len(inodes)==1
        lock_variant=dict(
            version="exp_ip",run_id=run_id,sha256=sha(ispath),
            source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",
            villain_observed_pattern_node_share_pct=lock["coverage_pct"],
            source_not_real_per_combo_observation=True,
            unknown_history_frequency_filled_with_default=bool(lock["imputed_assumption_nodes"]),
            observed_marginal_source_nodes=int(lock["observed_marginal_source_nodes"]),
            assumed_default_source_nodes=int(lock["imputed_assumption_nodes"]),
            unlocked_source_nodes=int(lock["unmatched_nodes"]),
            hero_model_gain_bb=locked_model_gain(ins,"exp_ip"),
            hero_gap_pct=hgap,strict_full_street_combo_reachable=istrict)
        board=dict(
            flop=spec["flop"],turn=spec["turn"],public_board=gn["board"],
            actual_exact_action_line="x b75 c/x",acting_seat=1,exact_flop_action="x b75 c",
            actual_pot_bb=round(float(gn["pot"])/100,5),
            actual_effective_stack_bb=round((float(gs["stack"])-max(gn["bets"]))/100,5),
            actual_spr=round(actual_spr,6),model_assumed_spr=MODEL_SPR,
            relative_spr_error_pct=round(spr_err,6),
            genuine_gto_exploitability_pct=ggap,source_run_id=run_id,
            source_sha256=sha(gspath),source_kind="PINNED_PREFLOP_CFR",
            assumed_preflop_ranges=False,exact_combo_reachable=int(graw),
            strict_full_street_combo_reachable=gstrict,
            exact_node_actions=list(gn["acts"]),
            medium_50pct_eligible_combos=medium_eligible,
            b50_nonpolarized_relative_equity_research_candidate=medium_candidate,
            nl2_locked_variants=[lock_variant],flop_texture=texture(spec["flop"]))
        all_boards.append(board)
        def make_case(ver,sub,subpath,stats,node,mask_entry,raw_count,expl,hero_gap=None,lockmeta=None):
            one_sub=dict(sub);one_sub["nodes"]=[node]
            k="|".join((node["board"],node["line"],str(node["player"])))
            nodes=source_nodes(one_sub,{"nodes":{k:mask_entry}})
            return dict(
                run_id=run_id,spot="CO_BB",pot_family="SRP",version=ver,
                flop=spec["flop"],turn=spec["turn"],flop_line="x b75 c",
                source_sha256=sha(subpath),gto_exploitability_pct=expl,
                locked_hero_gap_pct=hero_gap,
                certified_scope=("EXACT_BOARD_ONLY_GTO" if ver=="gto" else "PARTIALLY_LOCKED_NL2_MARGINAL_PROXY"),
                empirical_scope="PINNED_POKER_SOLVER_PREFLOP_CFR",
                source_kind="PINNED_PREFLOP_CFR",source_reachable_combos=int(raw_count),
                strict_combo_path_summary=stats,hands_by_seat=sub["hands"],nodes=nodes,
                paired_NL2_hero_lock=lockmeta,no_generic_texture_certification=True)
        gcaseproof=make_case("gto",gs,gspath,gstats,gn,gq,graw,ggap)
        icaseproof=make_case("exp_ip",ins,ispath,istats,inn,iq,iraw,
                             float(ins["info"].get("gto_expl_pct",ggap)),hgap,lock_variant)
        archive_by_run[run_id]=dict(
            schema="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1",
            source_run_id=run_id,actual_NL2_stake_hands=2334487,
            source_poker_solver_pin=SOLVER_PIN,authentic_rust_engine_pin=RUST_PIN,
            no_generic_texture_certification=True,errors=[],
            new_authentic_board_cases=2,exact_board_gto_sources=1,
            imputed_pool_locked_sources=1,verified_source_nodes=1,
            strictly_reachable_combo_nodes=gstrict,
            medium50_strict_eligible_combo_nodes=medium_eligible,
            medium50_strict_research_candidate_nodes=int(medium_candidate),
            artifacts=[dict(artifact=spec["code"],cases=[gcaseproof,icaseproof])],
            raw_source=dict(gto_manifest=gm,gto_root=gr,gto_root_job=grj,
                gto_turn_subgame=gs,gto_turn_job=gj,exp_ip_manifest=im,
                exp_ip_root=ir,exp_ip_root_job=irj,exp_ip_turn_subgame=ins,
                exp_ip_turn_job=ij,gto_root_sha256=sha(grpath),
                gto_sub_sha256=sha(gspath),exp_ip_root_sha256=sha(irpath),
                exp_ip_sub_sha256=sha(ispath)))
        print(json.dumps(dict(flop=spec["flop"],turn=spec["turn"],run_id=run_id,
            gto_strict=gstrict,nl2_ip_strict=istrict,gto_gap=round(ggap,4),
            hero_gap=round(hgap,4),observed_lock_nodes=lock["observed_marginal_source_nodes"],
            assumed_lock_nodes=lock["imputed_assumption_nodes"],unlocked=lock["unmatched_nodes"],
            medium50=medium_eligible,medium_candidate=medium_candidate),ensure_ascii=False))
    archive_codes={}
    for spec in SPECS:
        rid=spec["run_id"] if spec["legacy"] else a.run_id
        code=spec["code"]; archive=archive_by_run[rid]
        raw=json.dumps(archive,ensure_ascii=False,separators=(",",":")).encode()
        path=D/"solver_evidence"/f"NL2_MULTIBOARD_{code}.json.gz"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
        idx=dict(schema="NL2_B444_R62_ARCHIVE_INDEX_V1",source_run_id=rid,
            archive_code=code,archive_sha256=sha(path),
            gto_sha256=archive["raw_source"]["gto_sub_sha256"],
            exp_ip_sha256=archive["raw_source"]["exp_ip_sub_sha256"],
            flop=spec["flop"],turn=spec["turn"],no_generic_texture_certification=True)
        (D/"solver_evidence"/f"NL2_MULTIBOARD_{code}.index.json").write_text(
            json.dumps(idx,ensure_ascii=False,indent=2)+"\n")
        archive_codes[(spec["flop"],spec["turn"])]=code
    old=D/"nl2_hu_multiboard_status_v50_b417_rank166.json"
    st=read(old)
    assert (st["CERT_MULTIBOARD"],st["APPROX"],st["EST"],st["TOTAL"])==(163,229,0,392)
    r=st["records"][MODEL]
    assert r["label"]=="APPROX" and r["frequency_rank"]==62
    r["label"]="CERT-MULTIBOARD";r["proven_exact_board_count"]=3
    r["certified_3_to_5_exact_flop_boards"]=all_boards
    r["blocked_reason"]=None
    r["source_credibility"]="GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH"
    st["CERT_MULTIBOARD"]=164;st["APPROX"]=228
    st["schema"]="NL2_HU_392_MULTIBOARD_CERT_STATUS_V51_B444_R62"
    st["parent_v50_sha256"]=sha(old)
    st["B444_rank62_three_true_original_GTO_NL2_IP_flops"]=dict(
        rank=62,spot="CO_BB",actor="CO_IP",line="x b75 c/x",
        flops=[x["flop"] for x in all_boards],pins=[
            dict(flop=b["flop"],turn=b["turn"],source_run_id=b["source_run_id"],
                 GTO_strict_combos=b["strict_full_street_combo_reachable"],
                 NL2_strict_combos=b["nl2_locked_variants"][0]["strict_full_street_combo_reachable"],
                 original_GTO_SHA256=b["source_sha256"],
                 actual_NL2_SHA256=b["nl2_locked_variants"][0]["sha256"],
                 archive_code=archive_codes[(b["flop"],b["turn"])],
                 GTO_gap_pct=b["genuine_gto_exploitability_pct"],
                 NL2_hero_gap_pct=b["nl2_locked_variants"][0]["hero_gap_pct"])
            for b in all_boards],
        preflop_source="PINNED_POKER_SOLVER_PREFLOP_CFR",
        solver_pin=SOLVER_PIN,rust_pin=RUST_PIN,
        measured_NL2_aggregate_marginals=True,
        private_card_conditional_rates_not_claimed=True,
        no_generic_texture_certification=True)
    st["no_generic_texture_GTO"]=True;st["PR2_remains_draft_never_merge"]=True
    v51=D/"nl2_hu_multiboard_status_v51_b444_rank62.json"
    v51.write_text(json.dumps(st,ensure_ascii=False,indent=2)+"\n")
    cw=read(D/"nl2_hu_model_history_crosswalk.json")
    x=cw["records"][MODEL]
    x["same_history_within_1pct_spr_count"]=3
    x["candidate_status"]="MATCHED_ABSTRACT_HISTORY_AND_1PCT_SPR_ONLY"
    x["best_exact_board_examples"]=[
        dict(source_run_id=b["source_run_id"],source_sha256=b["source_sha256"],
             spot="CO_BB",family="SRP",version="gto",flop=b["flop"],turn=b["turn"],
             actual_public_board=b["public_board"],exact_flop_actions="x b75 c",
             exact_solver_node_line="x b75 c/x",acting_seat=1,
             actual_node_spr=b["actual_spr"],model_assumed_spr=MODEL_SPR,
             relative_spr_difference=round(b["relative_spr_error_pct"]/100,6),
             reached_combos=b["exact_combo_reachable"],
             strict_full_street_reachable_combos=b["strict_full_street_combo_reachable"],
             board_exact_match_to_model=False,
             available_for="EXACT_SOURCE_EXAMPLE_ONLY_NOT_GENERIC_CERT")
        for b in all_boards]
    x["generic_model_status"]="MODEL_UNCERTIFIED"
    x["upgraded_to_cert"]=False;x["upgraded_to_est"]=False
    x["board_specific_certification_status"]="CERT_MULTIBOARD"
    (D/"nl2_hu_model_history_crosswalk.json").write_text(json.dumps(cw,ensure_ascii=False,indent=2)+"\n")
    refs=read(D/"nl2_hu_model_source_references.json")
    q=refs["items"][MODEL];q["reference_count"]=3
    q["references"]=[
        dict(source_run_id=b["source_run_id"],spot="CO_BB",family="SRP",version="gto",
             flop=b["flop"],turn=b["turn"],flop_line="x b75 c",
             exact_solver_node_line="x b75 c/x",turn_spr=b["actual_spr"],
             source_sha256=b["source_sha256"],reference_status="CERT_EXACT_BOARD_GTO_ONLY")
        for b in all_boards]
    q["status"]="REFERENCE_ONLY_NOT_CERTIFIED"
    q["note"]="Exact GTO references only; paired measured-marginal EXP_IP locks and strict reach are in V51."
    refs["items"][MODEL]=q
    (D/"nl2_hu_model_source_references.json").write_text(json.dumps(refs,ensure_ascii=False,indent=2)+"\n")
    proof=dict(schema="NL2_B444_R62_THREE_BOARD_GTO_NL2_IP_CERT_PROOF_V1",
        model_id=MODEL,frequency_rank=62,profile="CO_BB",actor="CO_IP",
        exact_action_line="x b75 c/x",target_spr=MODEL_SPR,boards=all_boards,
        boards_tested=3,
        total_GTO_strict_combos=sum(x["strict_full_street_combo_reachable"] for x in all_boards),
        total_NL2_IP_strict_combos=sum(x["nl2_locked_variants"][0]["strict_full_street_combo_reachable"] for x in all_boards),
        measured_NL2_marginal_lock=True,not_private_card_conditional_frequencies=True,
        no_generic_texture_certification=True,CERT_MULTIBOARD=164,APPROX=228,EST=0,
        total=392,top24_cutoff_unchanged=True,PR2_Draft_NEVER_MERGE=True)
    (D/"nl2_hu_b444_rank62_three_board_cert.json").write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
    (repo/"docs/NL2_HU_B444_R62_THREE_BOARD_CERT.md").write_text(
        "# B444 rank62: three exact GTO and measured NL2-IP boards\n\n"
        "Rank62 (ln-ipfr-t_model-snfiz2) is certified only on three named CO_BB boards at the exact "
        "x b75 c/x turn-barrel node, actor CO/IP, target SPR 6.791. Each board has an authentic pinned "
        "GTO source, a paired Rust EXP_IP source using measured aggregate NL2 marginal locks, and strict "
        "full-street combo reach. The two prior source pairs are reused by SHA; the third board KsQh4d/Tc "
        "is newly solved in B444. The generic texture model remains uncertified and must not be extrapolated.\n\n"
        "Counts: 164 CERT-MULTIBOARD / 228 APPROX / 0 EST. NL2 frequencies are aggregate marginal proxies, "
        "not private-card conditional observations. Non-polarized 50% evidence is reported per board and "
        "is not promoted where the exact-board relative-equity test fails.\n")
    print(json.dumps(dict(commit_ready=True,cert=164,approx=228,est=0,
        board_count=3,gto_strict_total=proof["total_GTO_strict_combos"],
        nl2_ip_strict_total=proof["total_NL2_IP_strict_combos"]),ensure_ascii=False))
if __name__=="__main__":main()
