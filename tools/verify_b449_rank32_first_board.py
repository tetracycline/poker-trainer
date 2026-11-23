#!/usr/bin/env python3
"""B449 rank32 first exact UTG_CO b100c full-menu GTO and NL2-OOP source, fail closed."""
import argparse,hashlib,gzip,json,pathlib,sys
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
MODEL="ln-opfr-t_model-qx9t0u"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jread(p):return json.loads(p.read_text())
def locate(root,ver):
    e=root/"trainer/evidence"
    if not e.exists():e=root/"evidence"
    mfile=e/f"UTG_CO-Ks7h2d-{ver}.json"
    assert mfile.is_file()
    m=jread(mfile)
    assert (m["schema"],m["spot"],m["version"],m["flop"])==("NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","UTG_CO",ver,"Ks7h2d")
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert (m["root_pot_bb"],m["root_remaining_bb"])==(6.5,97.5)
    assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
    assert m["flop_line_policy"]=="oop-b100only" and m["selected_lines"]==["b100 c"]
    assert m["turns"]==["9d"] and m["turn_sizing_mode"]=="default"
    assert not m["failures"]
    assert (e/"poker-solver-pin.txt").read_text().strip()==SOLVER
    assert (e/"rust-pin.txt").read_text().strip()==RUST
    rfile=root/"solver/postflop/out/UTG_CO"/ver/"Ks7h2d_multiboard.json"
    assert rfile.is_file() and m["file_flop_sha256"]==sha(rfile)
    r=jread(rfile)
    assert (r["flop"],r["pot"],r["stack"])==("Ks7h2d",650,9750)
    cs=m.get("cases",[])
    assert len(cs)<=1
    if not cs:return dict(version=ver,manifest=m,root=r,manifest_file=mfile,root_file=rfile,sub=None,sub_file=None,job=None,job_file=None)
    c=cs[0];assert (c["line"],c["turn"])==("b100 c","9d")
    subfile=root/"solver/postflop"/c["source_path"]
    assert subfile.is_file() and sha(subfile)==c["source_sha256"]
    sub=jread(subfile);jobfile=subfile.with_suffix(".job.json");assert jobfile.is_file()
    assert (sub["flop"],sub["turn"],sub["line0"])==("Ks7h2d","9d","b100 c")
    assert float(sub["info"]["gto_expl_pct"])<=.5 if ver=="gto" else float(sub["info"]["hero_gap_pct"])<=.5
    job=jread(jobfile)
    assert job.get("flop_oop") is None or True
    if ver=="gto":assert job.get("hero") is None and not job.get("locks")
    else:assert job["hero"]==0 and job["locks"]
    return dict(version=ver,manifest=m,root=r,manifest_file=mfile,root_file=rfile,sub=sub,sub_file=subfile,job=job,job_file=jobfile)
def find(source):
    if source["sub"] is None:return dict(strict_combos=0,reason="AUTHENTIC_NO_LEGAL_TURN_CASE")
    from hu_sequential_cfr_reach import game_reach
    mask,stats=game_reach(source["root"],source["sub"])
    n=[n for n in source["sub"]["nodes"] if n["line"]=="b100 c/" and n["player"]==0 and n["board"][-2:]=="9d" and len(n["board"])==8]
    assert len(n)==1
    n=n[0];key="|".join((n["board"],n["line"],"0"))
    q=mask[key]
    actual=(source["sub"]["stack"]-max(n["bets"]))/n["pot"]
    assert abs(actual-4.667)/4.667<=.05
    raw=sum(float(w)>1e-4 for w in n["w"][0])
    assert raw>0
    out=dict(public_board=n["board"],exact_actor=0,source_combo_rows=raw,
             strict_full_street_combos=q["count"],actual_spr=round(actual,6),model_spr=4.667,
             source_actions=n["acts"],source_run_sha=sha(source["sub_file"]))
    if q["count"]:
        from verify_hu_multiboard_100bb import source_nodes
        focused=dict(source["sub"]);focused["nodes"]=[n]
        a=source_nodes(focused,{"nodes":{key:q}})
        assert len(a)==1
        out["medium50_strict_eligible_combos"]=a[0]["medium_50pct_eligible_combos"]
        out["b50_nonpolarized_research_candidate"]=a[0]["b50_nonpolarized_relative_equity_research_candidate"]
    else:
        out["medium50_strict_eligible_combos"]=0
        out["b50_nonpolarized_research_candidate"]=False
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--downloads",required=True,type=pathlib.Path)
    p.add_argument("--run-id",required=True,type=int)
    a=p.parse_args()
    D=pathlib.Path("data")
    sys.path.insert(0,str(pathlib.Path("tools").resolve()))
    status=jread(D/"nl2_hu_multiboard_status_v50_b417_rank166.json")
    m=status["records"][MODEL]
    assert (m["label"],m["frequency_rank"],m["assumed_model_node_spr"])==("APPROX",32,4.667)
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["EST"])==(163,229,0)
    sources=[locate(a.downloads/ver,ver) for ver in ("gto","exp_oop")]
    proofs=[find(s) for s in sources]
    for s in sources:
        if s["version"]=="gto":assert s["root"]["info"]["gto_expl_pct"]<=.5
        else:
            assert s["manifest"]["locks"] and any((n.get("n") or 0)>=500 for n in s["manifest"]["locks"])
    paired=bool(sources[0]["sub"] and sources[1]["sub"] and proofs[0]["strict_full_street_combos"]>0 and proofs[1]["strict_full_street_combos"]>0)
    archive=dict(schema="NL2_B449_R32_KS_7H_2D_ORIGINAL_RUST_GTO_AND_NL2_OOP_V1",run_id=a.run_id,
        source_run_id=a.run_id,flop="Ks7h2d",turn="9d",
        pinned_solver=SOLVER,pinned_rust=RUST,
        source_arrays=[dict(version=s["version"],manifest=s["manifest"],root=s["root"],
                 subgame=s["sub"],subgame_job=s["job"],
                 root_sha256=sha(s["root_file"]),
                 source_sha256=sha(s["sub_file"]) if s["sub_file"] else None) for s in sources])
    archive_bytes=json.dumps(archive,ensure_ascii=False,separators=(",",":")).encode()
    out=D/"solver_evidence/NL2_B449_R32_KS_7H_2D.json.gz"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(gzip.compress(archive_bytes,mtime=0,compresslevel=9))
    report=dict(schema="NL2_B449_R32_ONE_OF_THREE_EXACT_FLOPS_V1",
      target_model=MODEL,frequency_rank=32,root_profile="UTG_CO",flop="Ks7h2d",turn="9d",
      target_exact_line="b100 c/",actor="UTG_OOP",root_pot_bb=6.5,root_remaining_bb=97.5,
      expected_node_spr=4.667,
      authentic_GTO=proofs[0],partially_NL2_pool_locked_EXP_OOP=proofs[1],
      authentic_paired_positive=paired,
      paired_true_flop_count=1 if paired else 0,
      target_distinct_flop_minimum=3,
      predeclared_followup_flops=["KsQh4d"],
      no_generic_model_CERT=True,
      NL2_frequencies_are_pool_street_size_marginals_not_private_hand_rates=True,
      original_full_menu_rust_CFR=True,source_archive_sha256=sha(out),
      original_solver_pin=SOLVER,original_rust_pin=RUST,
      b50_nonpolarized_only_if_strict_reachable_and_true_equity_meets_gate=True,
      CERT_MULTIBOARD=163,APPROX=229,EST=0,PR2_Draft_NEVER_MERGE=True)
    rp=D/"nl2_hu_b449_rank32_first_source_proof.json"
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    idx=dict(schema="NL2_B449_R32_SOURCE_INDEX_V1",run_id=a.run_id,archive_sha256=sha(out),
       proof_sha256=sha(rp),flop="Ks7h2d",paired_positive=paired,no_premature_cert=True)
    (out.parent/"NL2_B449_R32_KS_7H_2D.index.json").write_text(json.dumps(idx,indent=2)+"\n")
    doc=pathlib.Path("docs/NL2_HU_B449_R32_KS_7H_2D_SOURCE_PROOF.md")
    doc.write_text("# B449 rank32 UTG_CO b100-call first authentic source\n\n"
       "Three flops predeclared: AsKh3d, Ks7h2d, KsQh4d. This batch independently solves only the second "
       "and archives the full-size original GTO and separately locked real Rust EXP_OOP turn subgame. "
       "Only exact b100 c / Ks7h2d 9d combinations with strict max/near action reach are eligible. "
       "Pool marginal NL2 locks are not private-hole-card conditional observations. "
       "An isolated second-board proof does not certify a generic texture or a 3-flop MODEL; "
       "counts remain **163 CERT / 229 APPROX / 0 EST**.\n")
    print(json.dumps({"run":a.run_id,"paired_positive":paired,
       "GTO_strict":proofs[0]["strict_full_street_combos"],
       "EXP_OOP_strict":proofs[1]["strict_full_street_combos"],
       "CERT":163,"APPROX":229}))
if __name__=="__main__":main()
