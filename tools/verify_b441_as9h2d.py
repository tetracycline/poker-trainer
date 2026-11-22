#!/usr/bin/env python3
"""Independent B441 EXP_OOP source audit and exact rank27/rank29 reachability check."""
import argparse, gzip, hashlib, json, pathlib, sys

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir",type=pathlib.Path,required=True)
    ap.add_argument("--downloads-root",type=pathlib.Path,required=True)
    ap.add_argument("--solver-root",type=pathlib.Path,required=True)
    ap.add_argument("--run-id",type=int,required=True)
    a=ap.parse_args()
    repo=pathlib.Path.cwd()
    D=repo/"data"
    A=a.artifact_dir
    sys.path.insert(0,str((repo/"tools").resolve()))
    from verify_hu_multiboard_100bb import verify
    from hu_sequential_cfr_reach import game_reach

    mf=A/"evidence/LMP_CO_BB-As9h2d-exp_oop.json"
    root=A/"solver/postflop/out/LMP_CO_BB/exp_oop/As9h2d_multiboard.json"
    assert all(p.is_file() for p in (mf,root,A/"evidence/poker-solver-pin.txt",A/"evidence/rust-pin.txt"))
    m=json.loads(mf.read_text())
    fr=json.loads(root.read_text())
    assert m["solved_cases"]==1 and len(m["cases"])==1 and not m["failures"] and not m["skipped"]
    assert (m["schema"],m["spot"],m["flop"],m["version"])==(
        "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB","As9h2d","exp_oop")
    assert m["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
    assert m["selected_lines"]==["b50 c"] and m["turns"]==["Kd"]
    assert "b33 c" in m["selected_turn_lines"] and "b75 c" in m["selected_turn_lines"]
    assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
    assert (fr["flop"],fr["pot"],fr["stack"])==("As9h2d",250,9900)
    assert m["file_flop_sha256"]==sha(root)
    c=m["cases"][0]
    sub=A/"solver/postflop"/c["source_path"]
    assert sub.is_file() and sha(sub)==c["source_sha256"]
    sd=json.loads(sub.read_text())
    assert (sd["flop"],sd["turn"],sd["line0"])==("As9h2d","Kd","b50 c")
    assert sd["info"]["gto_expl_pct"]<=0.5 and sd["info"]["hero_gap_pct"]<=0.5
    assert sum(len(n["board"])==10 for n in sd["nodes"])==c["true_river_nodes"]
    assert (A/"evidence/poker-solver-pin.txt").read_text().strip()=="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
    assert (A/"evidence/rust-pin.txt").read_text().strip()=="9d1509fe5077d019825f833eed04b16d342dfda1"

    independent=verify(a.downloads_root,a.solver_root,a.run_id)
    assert not independent["errors"],independent["errors"]
    assert len(independent["artifacts"])==1
    iv=independent["artifacts"][0]
    assert (iv["spot"],iv["version"],iv["flop"])==("LMP_CO_BB","exp_oop","As9h2d")
    assert not iv["errors"]
    assert len(iv["cases"])+len(iv["excludes"])==1
    assert independent["no_generic_texture_certification"] is True

    b440=json.loads((D/"nl2_hu_b440_r27_b439_gto_only_strict_zero_reach.json").read_text())
    gto_gz=D/"solver_evidence/NL2_B440_R27_B439_GTO_ONLY_AS9H2D.json.gz"
    assert sha(gto_gz)==b440["raw_source_archive_sha256"]
    ga=json.loads(gzip.decompress(gto_gz.read_bytes()))
    gm,gfr,gsub=ga["manifest"],ga["root_flop"],ga["turn_subgame"]
    assert (gm["spot"],gm["flop"],gm["version"])==("LMP_CO_BB","As9h2d","gto")
    assert gm["file_flop_sha256"]==b440["original_GTO_root_sha256"]
    assert gm["cases"][0]["source_sha256"]==b440["original_GTO_turn_source_sha256"]
    assert gm["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
    assert (gfr["flop"],gfr["pot"],gfr["stack"])==("As9h2d",250,9900)
    assert (gsub["flop"],gsub["turn"],gsub["line0"])==("As9h2d","Kd","b50 c")
    assert ga["poker_solver_commit"]=="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
    assert ga["rust_postflop_commit"]=="9d1509fe5077d019825f833eed04b16d342dfda1"
    gto_masks,gto_stats=game_reach(gfr,gsub)
    exp_masks,exp_stats=game_reach(fr,sd)

    rank27_gto={}
    for n in gsub["nodes"]:
        if n["player"]==0 and n["line"]=="b50 c/b33 c/" and len(n["board"])==10:
            key="|".join((n["board"],n["line"],"0"))
            rank27_gto[n["board"]]=gto_masks[key]["count"]
    expected27={x["public_board"]:x["strict_full_street_reachable_combos"]
                for x in b440["exact_named_river_nodes"]}
    assert rank27_gto==expected27 and len(rank27_gto)==2 and all(v==0 for v in rank27_gto.values())

    def collect(root_obj,sub_obj,masks,line,target_spr):
        out={}
        for n in sub_obj["nodes"]:
            if n["player"]!=0 or n["line"]!=line or len(n["board"])!=10:
                continue
            key="|".join((n["board"],n["line"],str(n["player"])))
            q=masks.get(key)
            assert q is not None,("missing strict mask",key)
            spr=(root_obj["stack"]-max(n["bets"]))/n["pot"]
            if abs(spr-target_spr)/target_spr>0.05:
                continue
            out[n["board"]]=dict(strict_combos=q["count"],spr=round(spr,6),
                source_actor_combos=sum(bool(x) for x in n["w"][0]))
        return out

    rank27_exp=collect(fr,sd,exp_masks,"b50 c/b33 c/",11.53)
    rank29_gto=collect(gfr,gsub,gto_masks,"b50 c/b75 c/",7.52)
    rank29_exp=collect(fr,sd,exp_masks,"b50 c/b75 c/",7.52)
    paired=sorted(set(k for k,v in rank29_gto.items() if v["strict_combos"]>0) &
                  set(k for k,v in rank29_exp.items() if v["strict_combos"]>0))
    rank29=dict(model_id="ln-iso-lmp_r_model-gifggm",frequency_rank=29,
        assumed_model_spr=7.52,exact_line="b50 c/b75 c/",acting_seat="BB_OOP",
        flop="As9h2d",turn="Kd",
        gto_positive_river_nodes=sum(v["strict_combos"]>0 for v in rank29_gto.values()),
        exp_oop_positive_river_nodes=sum(v["strict_combos"]>0 for v in rank29_exp.values()),
        paired_positive_river_nodes=len(paired),
        paired_riverboards=[dict(board=k,gto_strict_combos=rank29_gto[k]["strict_combos"],
            exp_oop_strict_combos=rank29_exp[k]["strict_combos"],
            spr_gto=rank29_gto[k]["spr"],spr_exp_oop=rank29_exp[k]["spr"]) for k in paired],
        exact_flop_pair_count=1 if paired else 0,
        certification="REMAINS_APPROX_NEEDS_3_TO_5_DISTINCT_EXACT_FLOP_PAIRS")

    status=json.loads((D/"nl2_hu_multiboard_status_v50_b417_rank166.json").read_text())
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["EST"],status["TOTAL"])==(163,229,0,392)
    r27=status["records"]["ln-iso-lmp_r_model-1aov4pd"]
    r29=status["records"]["ln-iso-lmp_r_model-gifggm"]
    assert (r27["frequency_rank"],r27["label"],r27["assumed_model_node_spr"])==(27,"APPROX",11.53)
    assert (r29["frequency_rank"],r29["label"],r29["assumed_model_node_spr"])==(29,"APPROX",7.52)

    payload=dict(schema="NL2_B441_AS9H2D_EXP_OOP_COMPLETION_AND_R29_EXACT_BOARD_PROOF_V1",
        run_id=a.run_id,artifact_name=A.name,
        exp_oop_manifest_sha256=sha(mf),exp_oop_root_sha256=sha(root),
        exp_oop_turn_source_sha256=sha(sub),exp_oop_root_job_sha256=sha(root.with_suffix(".job.json")),
        exp_oop_solver_commit=(A/"evidence/poker-solver-pin.txt").read_text().strip(),
        exp_oop_rust_commit=(A/"evidence/rust-pin.txt").read_text().strip(),
        exp_oop_gto_gap_pct=c["gto_gap_pct"],exp_oop_hero_gap_pct=c["hero_gap_pct"],
        exp_oop_verified_cases=len(iv["cases"]),exp_oop_strict_reach_exclusions=iv["excludes"],
        original_gto_source_run_id=45068014496,original_gto_artifact_id=14772553505,
        original_gto_archive_sha256=sha(gto_gz),
        original_gto_root_sha256=b440["original_GTO_root_sha256"],
        original_gto_turn_source_sha256=b440["original_GTO_turn_source_sha256"],
        rank27_negative=dict(model_id="ln-iso-lmp_r_model-1aov4pd",frequency_rank=27,
            exact_line="b50 c/b33 c/",gto_strict_river_nodes=rank27_gto,
            exp_oop_strict_river_nodes=rank27_exp,eligible_CERT=False,
            reason="ZERO_STRICT_GTO_REACH_AND_OUTSIDE_PREREGISTERED_TOP24"),
        rank29=rank29,preflop_range="ASSUMED_EXPLICIT_169CLASS_NOT_OBSERVED_NL2",
        pool_lock_scope="OBSERVED_NL2_MARGINAL_BY_SIZE_WHERE_AVAILABLE; IMPUTED_HISTORY_AND_ASSUMED_DEFAULTS_DISCLOSED",
        no_generic_texture_certification=True,CERT_MULTIBOARD=163,APPROX=229,EST=0,
        counts_unchanged=True,PR2_Draft_NEVER_MERGE=True)
    raw=dict(schema="NL2_B441_AUTHENTIC_EXP_OOP_SOURCE_ARCHIVE_V1",
        manifest=m,root_flop=fr,turn_subgame=sd,
        root_job=json.loads(root.with_suffix(".job.json").read_text()),
        poker_solver_commit=payload["exp_oop_solver_commit"],
        rust_postflop_commit=payload["exp_oop_rust_commit"])
    raw_bytes=json.dumps(raw,ensure_ascii=False,separators=(",",":")).encode()
    archive=D/"solver_evidence/NL2_B441_R27_R29_AS9H2D_EXPOOP.json.gz"
    archive.parent.mkdir(parents=True,exist_ok=True)
    archive.write_bytes(gzip.compress(raw_bytes,compresslevel=9,mtime=0))
    payload["raw_source_archive_sha256"]=sha(archive)
    proof=D/"nl2_hu_b441_as9h2d_exp_oop_source_proof.json"
    proof.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    index=dict(schema="NL2_B441_EXP_OOP_ARCHIVE_INDEX_V1",run_id=a.run_id,
        original_gto_run_id=45068014496,original_gto_artifact_id=14772553505,
        rank27_strict_zero_reach=True,rank29_model_id="ln-iso-lmp_r_model-gifggm",
        rank29_exact_flop_pair_count=rank29["exact_flop_pair_count"],
        exp_oop_root_sha256=payload["exp_oop_root_sha256"],
        exp_oop_turn_source_sha256=payload["exp_oop_turn_source_sha256"],
        raw_archive_sha256=payload["raw_source_archive_sha256"],
        strict_actor_combo_reach_stats=dict(exp_oop=exp_stats,gto=gto_stats),
        no_generic_texture_certification=True,counts_unchanged=True)
    (D/"solver_evidence/NL2_B441_R27_R29_AS9H2D_EXPOOP.index.json").write_text(
        json.dumps(index,ensure_ascii=False,indent=2)+"\n")
    doc=repo/"docs/NL2_HU_B441_AS9H2D_EXP_OOP_SOURCE_PROOF.md"
    doc.write_text(
        "# B441 As9h2d full EXP_OOP source completion; rank27 negative / rank29 b75 audit\n\n"
        "The previously cancelled B439 EXP_OOP job has now completed from the pinned original Rust CFR source. "
        "Its full 100bb LMP_CO_BB source uses an explicitly assumed 169-class limped preflop range; pool locks are "
        "marginal-by-size where measured and imputed/default elsewhere, never private-card observations.\n\n"
        f"- EXP_OOP source: run {a.run_id}; root SHA256 {payload['exp_oop_root_sha256']}; "
        f"turn source SHA256 {payload['exp_oop_turn_source_sha256']}\n"
        f"- Exploitability gaps: GTO {c['gto_gap_pct']}%; hero {c['hero_gap_pct']}%\n"
        f"- Rank27 b50-call / b33-call: GTO strict river combos {rank27_gto}; no CERT promotion\n"
        f"- Rank29 b50-call / b75-call: paired positive river nodes {len(paired)}; "
        f"exact flop pairs {rank29['exact_flop_pair_count']}/3 required; remains APPROX\n\n"
        "The GTO parent is the already completed B439 run 45068014496; it was not rerun. "
        "No generic texture certification; V50 counts remain 163 CERT / 229 APPROX / 0 EST. "
        "PR #2 remains Draft and is never merged.\n")
    print(json.dumps(dict(run_id=a.run_id,rank27="negative zero strict reach",
        rank29=rank29,cert=163,approx=229,est=0),ensure_ascii=False))

if __name__=="__main__":
    main()
