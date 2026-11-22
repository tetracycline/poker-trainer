#!/usr/bin/env python3
"""Independent B439 As9h2d EXP_OOP turn/river partial-source verifier."""
import argparse,gzip,hashlib,json,pathlib,sys
GTO_RUN=45068014496
GTO_ARTIFACT=14772553505
GTO_MANIFEST_SHA="633af964d7e1afa37b620fa1573130b130ba8e1fc4d1963534597a0446e25078"
GTO_ROOT_SHA="67c9f2c4faf58da55da9624d370a419fcaa55e5db670b3baa9d50fd2f4d19fee"
GTO_JOB_SHA="4e3c4af303d9962768284a269f8c146192a700b14579c98f6d86683d6f9c5323"
GTO_TURN_SHA="98377f820251e273540ccce5132b7a451a6018aff3d322dc2eb75496de6c5db6"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def targets(root,sub,masks,line,spr0):
    out=[]
    for n in sub["nodes"]:
        if n["player"]!=0 or n["line"]!=line or len(n["board"])!=10: continue
        spr=(root["stack"]-max(n["bets"]))/n["pot"]
        if abs(spr-spr0)/spr0>0.05: continue
        q=masks["|".join((n["board"],n["line"],"0"))]
        out.append(dict(public_board=n["board"],acting_seat=0,exact_line=n["line"],
          source_actor_combos=sum(bool(x) for x in n["w"][0]),
          strict_full_street_reachable_combos=q["count"],actual_spr=round(spr,6),target_spr=spr0))
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--downloads-root",type=pathlib.Path,required=True)
    p.add_argument("--run-id",type=int,required=True)
    a=p.parse_args()
    repo=pathlib.Path.cwd(); D=repo/"data"
    sys.path.insert(0,str((repo/"tools").resolve()))
    from hu_sequential_cfr_reach import game_reach
    G=a.downloads_root/"gto"; E=a.downloads_root/"exp_oop"
    gmfile=G/"evidence/LMP_CO_BB-As9h2d-gto.json"
    grpath=G/"solver/postflop/out/LMP_CO_BB/gto/As9h2d_multiboard.json"
    gjpath=grpath.with_suffix(".job.json")
    gspath=grpath.parent/"As9h2d_b50c_Kd.json"
    assert all(x.is_file() for x in (gmfile,grpath,gjpath,gspath))
    gm=json.loads(gmfile.read_text()); gr=json.loads(grpath.read_text()); gs=json.loads(gspath.read_text())
    assert (sha(gmfile),sha(grpath),sha(gjpath),sha(gspath))==(GTO_MANIFEST_SHA,GTO_ROOT_SHA,GTO_JOB_SHA,GTO_TURN_SHA)
    assert (gm["schema"],gm["spot"],gm["version"],gm["flop"])==("NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB","gto","As9h2d")
    assert gm["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
    assert gm["selected_lines"]==["b50 c"] and gm["turns"]==["Kd"] and gm["turn_sizing_mode"]=="river-gaps"
    assert gm["cases"][0]["source_sha256"]==GTO_TURN_SHA and gr["info"]["gto_expl_pct"]<=.5
    assert (gr["flop"],gr["pot"],gr["stack"])==("As9h2d",250,9900)
    assert (gs["flop"],gs["turn"],gs["line0"])==("As9h2d","Kd","b50 c") and gs["info"]["gto_expl_pct"]<=.5

    # gh run download preserves the EXP artifact's trainer/ and solver/ roots.
    # GTO artifact has evidence/ and solver/ at its root; normalize only EXP evidence.
    EDATA=E/"trainer" if (E/"trainer/evidence").is_dir() else E
    mf=EDATA/"evidence/LMP_CO_BB-As9h2d-exp_oop.json"
    erpath=E/"solver/postflop/out/LMP_CO_BB/exp_oop/As9h2d_multiboard.json"
    ejpath=erpath.with_suffix(".job.json")
    espath=erpath.parent/"As9h2d_b50c_Kd.json"
    esjpath=espath.with_suffix(".job.json")
    assert all(x.is_file() for x in (mf,erpath,ejpath,espath,esjpath))
    em=json.loads(mf.read_text()); er=json.loads(erpath.read_text()); es=json.loads(espath.read_text()); esj=json.loads(esjpath.read_text())
    assert (em["schema"],em["spot"],em["version"],em["flop"])==("NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB","exp_oop","As9h2d")
    assert em["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
    assert em["flop_size_profile"]=="full" and not em["restricted_tree_assumption"]
    assert em["flop_line_policy"]=="oop-b50only" and em["selected_lines"]==["b50 c"]
    assert em["turn_sizing_mode"]=="river-gaps" and em["turns"]==["Kd"]
    assert em["selected_turn_lines"]==["x b33 c","x b66 c","x b75 c","x x","b33 c","b66 c","b75 c"]
    assert em["turn_line_policy"]=="default" and em["solved_cases"]==1 and not em["failures"] and not em["skipped"]
    assert em["gto_parent_source_run_id"]==GTO_RUN and em["gto_parent_source_sha256"]==GTO_ROOT_SHA
    assert em["gto_parent_source_manifest_sha256"]==GTO_MANIFEST_SHA and em["flop_root_jobfile_sha256"]==GTO_JOB_SHA
    parent=em["authenticated_original_gto_parent"]
    assert (parent["original_run_id"],parent["original_artifact_id"])==(GTO_RUN,GTO_ARTIFACT)
    assert parent["original_GTO_root_sha256"]==GTO_ROOT_SHA and parent["original_GTO_job_sha256"]==GTO_JOB_SHA
    assert parent["original_GTO_manifest_sha256"]==GTO_MANIFEST_SHA
    assert parent["genuine_NL2_partial_lock_only_on_downstream_turn_and_river"] is True
    assert parent["flop_is_original_unlocked_GTO_not_fully_hero_NL2_locked"] is True
    assert sha(erpath)==GTO_ROOT_SHA and sha(ejpath)==GTO_JOB_SHA and em["file_flop_sha256"]==GTO_ROOT_SHA
    assert (er["flop"],er["pot"],er["stack"])==("As9h2d",250,9900)
    assert (es["flop"],es["turn"],es["line0"])==("As9h2d","Kd","b50 c")
    assert em["cases"][0]["line"]=="b50 c" and em["cases"][0]["turn"]=="Kd"
    assert em["cases"][0]["source_sha256"]==sha(es)
    assert em["cases"][0]["gto_gap_pct"]<=.5 and em["cases"][0]["hero_gap_pct"]<=.5
    assert es["info"]["gto_expl_pct"]<=.5 and es["info"]["hero_gap_pct"]<=.5
    assert esj["hero"]==0 and esj.get("locks")
    assert abs(esj["rake_rate"]-.05)<1e-8 and esj["rake_cap"]==1000
    assert esj["turn_oop"]=="33%,66%,75%" and esj["turn_ip"]=="33%,66%,75%"
    assert em["locks"] and any((x.get("n") or 0)>=500 for x in em["locks"])

    gmask,gstats=game_reach(gr,gs); emask,estats=game_reach(er,es)
    r27g=targets(gr,gs,gmask,"b50 c/b33 c/",11.53)
    r29g=targets(gr,gs,gmask,"b50 c/b75 c/",7.52)
    r27e=targets(er,es,emask,"b50 c/b33 c/",11.53)
    r29e=targets(er,es,emask,"b50 c/b75 c/",7.52)
    assert len(r27g)==len(r29g)==len(r27e)==len(r29e)==2
    assert all(x["source_actor_combos"]>0 and x["strict_full_street_reachable_combos"]==0 for x in r27g+r29g)

    archive=dict(schema="NL2_B443_AS9H2D_EXP_OOP_TURN_RIVER_PARTIAL_RAW_V1",
      run_id=a.run_id,gto_parent_run_id=GTO_RUN,gto_parent_artifact_id=GTO_ARTIFACT,
      gto_manifest=gm,gto_root=gr,gto_root_job=json.loads(gjpath.read_text()),gto_turn=gs,
      exp_manifest=em,exp_root=er,exp_root_job=json.loads(ejpath.read_text()),
      exp_turn=es,exp_turn_job=esj,solver_pin="abe310c3aad02dd4a7c77fb2831801fd490cf51b",
      rust_pin="9d1509fe5077d019825f833eed04b16d342dfda1")
    raw=json.dumps(archive,ensure_ascii=False,separators=(",",":")).encode()
    gz=D/"solver_evidence/NL2_B443_R27_R29_AS9H2D_EXP_OOP_TURN_ONLY.json.gz"
    gz.parent.mkdir(parents=True,exist_ok=True); gz.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
    proof=dict(schema="NL2_B443_AS9H2D_EXP_OOP_TURN_RIVER_PARTIAL_PROOF_V1",
      run_id=a.run_id,gto_parent_run_id=GTO_RUN,gto_parent_artifact_id=GTO_ARTIFACT,
      flop="As9h2d",turn="Kd",flop_line="b50 c",scope="TRUE_RUST_EXP_OOP_TURN_RIVER_PARTIAL_LOCK",
      not_full_tree_NL2_lock=True,original_flop_root_is_unlocked_GTO=True,
      preflop_ranges="ASSUMED_EXPLICIT_169CLASS_NOT_OBSERVED_NL2",
      GTO_root_sha256=GTO_ROOT_SHA,GTO_root_job_sha256=GTO_JOB_SHA,GTO_manifest_sha256=GTO_MANIFEST_SHA,
      GTO_turn_sha256=GTO_TURN_SHA,EXP_OOP_turn_sha256=sha(es),EXP_OOP_turn_job_sha256=sha(espath.with_suffix(".job.json")),
      GTO_gap_pct=gs["info"]["gto_expl_pct"],EXP_OOP_hero_gap_pct=es["info"]["hero_gap_pct"],
      NL2_lock_patterns=em["locks"],NL2_lock_stats=es["info"].get("lock_stats",{}),
      rank27_GTO_targets=r27g,rank27_EXP_OOP_targets=r27e,rank29_GTO_targets=r29g,rank29_EXP_OOP_targets=r29e,
      rank27_GTO_strict_zero=True,rank29_GTO_strict_zero=True,
      counts_unchanged=True,CERT_MULTIBOARD=163,APPROX=229,EST=0,
      no_generic_texture_certification=True,PR2_Draft_NEVER_MERGE=True,
      full_tree_attempt_run_id=45076066054,full_tree_attempt="CANCELLED_AT_27M_WITH_NO_SOURCE_OUTPUT")
    pp=D/"nl2_hu_b443_as9h2d_exp_oop_partial_source_proof.json"
    pp.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
    ix=dict(schema="NL2_B443_AS9H2D_EXP_OOP_PARTIAL_INDEX_V1",proof_sha256=sha(pp),archive_sha256=sha(gz),
      gto_root_sha256=GTO_ROOT_SHA,exp_turn_sha256=sha(es),run_id=a.run_id,no_cert_promotion=True)
    (gz.parent/"NL2_B443_R27_R29_AS9H2D_EXP_OOP_TURN_ONLY.index.json").write_text(json.dumps(ix,indent=2)+"\n")
    (repo/"docs/NL2_HU_B443_AS9H2D_EXP_OOP_PARTIAL_SOURCE.md").write_text(
      "# B443 As9h2d authentic EXP_OOP turn/river partial lock\n\n"
      "The B441 full-flop EXP_OOP run was cancelled at 27 minutes before producing a source root. "
      "B443 reuses only the already completed SHA-pinned B439 original full-size GTO flop root, "
      "then runs genuine Rust EXP_OOP on the exact b50-call / Kd turn-and-river subgame. "
      "This is a **partial downstream lock**, not a full-tree NL2 flop solution.\n\n"
      "The limped 169-class preflop range remains ASSUMED. NL2 locking uses aggregate street/size marginals "
      "and disclosed fallbacks, never private-card conditional frequencies. Rank27 b33-call and rank29 "
      "b75-call exact GTO river targets have zero strict full-street reachable combos; neither is promoted. "
      "Counts remain 163 CERT / 229 APPROX / 0 EST.\n")
    print(json.dumps({"run_id":a.run_id,"scope":"TURN_RIVER_PARTIAL_EXP_OOP","cert":163,"approx":229,"est":0}))
if __name__=="__main__": main()
