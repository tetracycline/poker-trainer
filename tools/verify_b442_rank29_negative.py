#!/usr/bin/env python3
"""B442: preserve completed GTO artifacts and prove rank29 b75 branch has zero strict reach."""
import argparse,gzip,hashlib,json,pathlib,sys

ARTIFACTS=[
 dict(flop="4s4h2d",turn="8s",run_id=45065684467,artifact_id=14771462173,
      name="nl2-multiboard-B434_R29_LMPCOBB_B50_B75-LMP_CO_BB-4s4h2d-gto"),
 dict(flop="8s8h3d",turn="5s",run_id=45066400126,artifact_id=14771824149,
      name="nl2-multiboard-B437_R29_LMPCOBB_B50_B75-LMP_CO_BB-8s8h3d-gto"),
 dict(flop="9s6h3d",turn="Ts",run_id=45066455212,artifact_id=14772216694,
      name="nl2-multiboard-B438_R29_LMPCOBB_B50_B75-LMP_CO_BB-9s6h3d-gto"),
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--downloads-root",type=pathlib.Path,required=True)
    a=ap.parse_args()
    repo=pathlib.Path.cwd(); D=repo/"data"
    sys.path.insert(0,str((repo/"tools").resolve()))
    from hu_sequential_cfr_reach import game_reach

    results=[];archives=[]
    for item in ARTIFACTS:
        A=a.downloads_root/item["name"]
        mf=next((A/"evidence").glob("*.json"))
        m=json.loads(mf.read_text())
        assert (m["schema"],m["spot"],m["flop"],m["version"])==(
            "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB",item["flop"],"gto")
        assert m["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
        assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
        assert m["selected_lines"]==["b50 c"] and "b75 c" in m["selected_turn_lines"]
        assert m["turns"]==[item["turn"]] and m["solved_cases"]==1
        assert not m["failures"] and not m["skipped"]
        c=m["cases"][0]
        assert c["line"]=="b50 c" and c["turn"]==item["turn"]
        assert c["gto_gap_pct"]<=0.5
        root=next((A/"solver/postflop/out/LMP_CO_BB/gto").glob(item["flop"]+"_multiboard.json"))
        sub=A/"solver/postflop"/c["source_path"]
        assert root.is_file() and sub.is_file()
        fr=json.loads(root.read_text()); sd=json.loads(sub.read_text())
        assert m["file_flop_sha256"]==sha(root) and c["source_sha256"]==sha(sub)
        assert (fr["flop"],fr["pot"],fr["stack"])==(item["flop"],250,9900)
        assert (sd["flop"],sd["turn"],sd["line0"])==(item["flop"],item["turn"],"b50 c")
        assert sd["info"]["gto_expl_pct"]<=0.5
        assert sum(len(n["board"])==10 for n in sd["nodes"])==c["true_river_nodes"]
        assert (A/"evidence/poker-solver-pin.txt").read_text().strip()=="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
        assert (A/"evidence/rust-pin.txt").read_text().strip()=="9d1509fe5077d019825f833eed04b16d342dfda1"
        masks,stats=game_reach(fr,sd)
        nodes=[]
        for n in sd["nodes"]:
            if n["player"]!=0 or n["line"]!="b50 c/b75 c/" or len(n["board"])!=10: continue
            spr=(fr["stack"]-max(n["bets"]))/n["pot"]
            if abs(spr-7.52)/7.52>0.05: continue
            key="|".join((n["board"],n["line"],"0"))
            q=masks[key]
            nodes.append(dict(public_board=n["board"],source_actor_combos=sum(bool(x) for x in n["w"][0]),
                strict_full_street_reachable_combos=q["count"],actual_spr=round(spr,6)))
        assert len(nodes)==2,(item["flop"],nodes)
        assert all(n["source_actor_combos"]>0 for n in nodes)
        assert all(n["strict_full_street_reachable_combos"]==0 for n in nodes)
        root_job=root.with_suffix(".job.json")
        sub_job=sub.with_suffix(".job.json")
        raw=dict(schema="NL2_B442_R29_GTO_ONLY_RAW_SOURCE_V1",run_id=item["run_id"],
            artifact_id=item["artifact_id"],artifact_name=item["name"],manifest=m,
            root_flop=fr,turn_subgame=sd,
            root_job=json.loads(root_job.read_text()) if root_job.exists() else None,
            sub_job=json.loads(sub_job.read_text()) if sub_job.exists() else None,
            poker_solver_commit="abe310c3aad02dd4a7c77fb2831801fd490cf51b",
            rust_postflop_commit="9d1509fe5077d019825f833eed04b16d342dfda1")
        raw_bytes=json.dumps(raw,ensure_ascii=False,separators=(",",":")).encode()
        out=D/"solver_evidence"/f"NL2_B442_R29_{item['flop']}_GTO_ONLY.json.gz"
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(gzip.compress(raw_bytes,compresslevel=9,mtime=0))
        results.append(dict(flop=item["flop"],turn=item["turn"],run_id=item["run_id"],
            artifact_id=item["artifact_id"],gto_gap_pct=c["gto_gap_pct"],
            root_sha256=sha(root),turn_source_sha256=sha(sub),
            target_line="b50 c/b75 c/",target_spr=7.52,strict_zero_river_nodes=nodes,
            source_actor_combos=sum(n["source_actor_combos"] for n in nodes),
            strict_reachable_combos=0,raw_archive_sha256=sha(out)))
        archives.append(out)

    # Include the already preserved B439 As9h2d GTO source without re-running it.
    b440=json.loads((D/"nl2_hu_b440_r27_b439_gto_only_strict_zero_reach.json").read_text())
    gto_gz=D/"solver_evidence/NL2_B440_R27_B439_GTO_ONLY_AS9H2D.json.gz"
    assert sha(gto_gz)==b440["raw_source_archive_sha256"]
    ga=json.loads(gzip.decompress(gto_gz.read_bytes()))
    gm,gfr,gsub=ga["manifest"],ga["root_flop"],ga["turn_subgame"]
    assert (gm["spot"],gm["flop"],gm["version"])==("LMP_CO_BB","As9h2d","gto")
    assert gm["cases"][0]["source_sha256"]==b440["original_GTO_turn_source_sha256"]
    masks,stats=game_reach(gfr,gsub)
    nodes=[]
    for n in gsub["nodes"]:
        if n["player"]!=0 or n["line"]!="b50 c/b75 c/" or len(n["board"])!=10: continue
        spr=(gfr["stack"]-max(n["bets"]))/n["pot"]
        if abs(spr-7.52)/7.52>0.05: continue
        key="|".join((n["board"],n["line"],"0"))
        nodes.append(dict(public_board=n["board"],source_actor_combos=sum(bool(x) for x in n["w"][0]),
            strict_full_street_reachable_combos=masks[key]["count"],actual_spr=round(spr,6)))
    assert len(nodes)==2 and all(n["strict_full_street_reachable_combos"]==0 for n in nodes)
    results.append(dict(flop="As9h2d",turn="Kd",run_id=45068014496,artifact_id=14772553505,
        gto_gap_pct=gm["cases"][0]["gto_gap_pct"],root_sha256=b440["original_GTO_root_sha256"],
        turn_source_sha256=b440["original_GTO_turn_source_sha256"],target_line="b50 c/b75 c/",
        target_spr=7.52,strict_zero_river_nodes=nodes,
        source_actor_combos=sum(n["source_actor_combos"] for n in nodes),strict_reachable_combos=0,
        raw_archive_sha256=sha(gto_gz),archive_already_preserved=True))

    status=json.loads((D/"nl2_hu_multiboard_status_v50_b417_rank166.json").read_text())
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["EST"],status["TOTAL"])==(163,229,0,392)
    r=status["records"]["ln-iso-lmp_r_model-gifggm"]
    assert (r["frequency_rank"],r["label"],r["assumed_model_node_spr"])==(29,"APPROX",7.52)
    payload=dict(schema="NL2_B442_R29_STRICT_GTO_ZERO_REACH_NEGATIVE_PROOF_V1",
        model_id="ln-iso-lmp_r_model-gifggm",frequency_rank=29,profile="LMP_CO_BB",
        target_line="b50 c/b75 c/",target_spr=7.52,acting_seat="BB_OOP",
        boards=results,boards_tested=len(results),river_nodes_tested=sum(len(x["strict_zero_river_nodes"]) for x in results),
        strict_positive_river_nodes=0,strict_reachable_combos=0,
        prior_GTO_sources_reused_only=True,old_EXP_OOP_jobs_not_rerun=True,
        rank29_remains_APPROX=True,reason="ZERO_STRICT_FULL_STREET_GTO_REACH_ON_ALL_FOUR_AUTHENTIC_FLOP_SOURCES",
        preflop_range="ASSUMED_EXPLICIT_169CLASS_NOT_OBSERVED_NL2",
        no_generic_texture_certification=True,CERT_MULTIBOARD=163,APPROX=229,EST=0,
        counts_unchanged=True,PR2_Draft_NEVER_MERGE=True)
    proof=D/"nl2_hu_b442_rank29_strict_gto_zero_reach.json"
    proof.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    index=dict(schema="NL2_B442_R29_NEGATIVE_ARCHIVE_INDEX_V1",proof_sha256=sha(proof),
        source_archives=[dict(path=str(p.relative_to(D)),sha256=sha(p)) for p in archives],
        preserved_B439_GTO_archive_sha256=sha(gto_gz),strict_zero_river_nodes=8,
        no_generic_texture_certification=True,counts_unchanged=True)
    (D/"solver_evidence/NL2_B442_R29_NEGATIVE.index.json").write_text(
        json.dumps(index,ensure_ascii=False,indent=2)+"\n")
    doc=repo/"docs/NL2_HU_B442_R29_STRICT_GTO_ZERO_REACH.md"
    doc.write_text(
        "# B442 rank29 strict GTO reach negative audit\n\n"
        "Four completed authentic GTO sources were inspected; no GTO solve was repeated. "
        "Across 4 distinct flop boards and 8 exact river nodes on the b50-call / b75-call BB-OOP line, "
        "the strict full-street action-policy intersection contains zero reachable combos. "
        "Source actor combos were nonzero, so this is not an empty-source artifact.\n\n"
        "The three older incomplete batches had GTO sources only; their missing EXP_OOP legs were not rerun. "
        "B439 As9h2d GTO is reused from the already committed B440 archive. "
        "Rank29 remains APPROX and is not promoted. V50 counts remain 163 CERT / 229 APPROX / 0 EST.\n")
    print(json.dumps(dict(rank=29,boards_tested=4,river_nodes_tested=8,
        strict_reachable_combos=0,cert=163,approx=229,est=0),ensure_ascii=False))

if __name__=="__main__": main()
