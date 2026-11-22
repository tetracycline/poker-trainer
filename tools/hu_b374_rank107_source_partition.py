#!/usr/bin/env python3
"""B374 source-only verify new rank107 BTN-IP exact GTO + partially NL2-locked Rust solves.
Never upgrade any 392 model until 3 distinct flops & full-street combo reach are proven.
"""
import argparse,collections,hashlib,json,pathlib
D=pathlib.Path("data")
FLOPS=("KsQh4d","7s5h3d")
VERSIONS=("gto","exp_ip")
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
TARGET="b33 c/x b50 c/x"
OUT=D/"nl2_hu_b374_r107_two_new_fresh_true_gto_nl2_ip_source_manifest.json"
DOC=pathlib.Path("docs/NL2_HU_B374_RANK107_TWO_NEW_FLOP_SOURCE_BATCH.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 a=argparse.ArgumentParser();a.add_argument("--download-dir",type=pathlib.Path,required=True)
 args=a.parse_args();folders=args.download_dir
 source=[];valid={}
 for flop in FLOPS:
  for version in VERSIONS:
   tag=f"nl2-multiboard-B374_R107-BTN_BB-{flop}-{version}"
   root=folders/tag
   manifest=root/"evidence"/f"BTN_BB-{flop}-{version}.json"
   item=dict(flop=flop,version=version,original_artifact_tag=tag,job_manifest_present=manifest.is_file())
   if manifest.is_file():
    m=load(manifest)
    assert (m["schema"],m["spot"],m["version"],m["flop"],m["pot_family"])==(
     "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","BTN_BB",version,flop,"SRP")
    assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
    assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
    assert m["selected_lines"]==["b33 c"] and len(m["turns"])==1
    assert len(m["pool_source_sha256"])==64 and len(m["solver_pin"])==64
    assert m["solved_cases"]==len(m["cases"])
    assert not m["failures"],(tag,m["failures"])
    assert (root/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
    assert (root/"evidence/rust-pin.txt").read_text().strip()==RUST
    f=root/"solver/postflop"/m["file_flop"]
    assert f.is_file() and sha(f)==m["file_flop_sha256"]
    item.update(manifest_sha256=sha(manifest),root_sha256=sha(f),
      original_turns=m["turns"],actual_solved_cases=m["solved_cases"],
      documented_zero_case_negatives=m["skipped"],source_cases=[])
    for c in m["cases"]:
     cp=root/"solver/postflop"/c["source_path"]
     assert cp.is_file() and sha(cp)==c["source_sha256"]
     assert c["line"]=="b33 c" and c["turn"] in m["turns"]
     assert c["gto_gap_pct"] is not None and c["gto_gap_pct"]<=0.5
     if version=="exp_ip":
      assert c["hero_gap_pct"] is not None and c["hero_gap_pct"]<=.5
      assert any(int(z.get("n",0))>0 and "ASSUMED" not in z.get("scope","") for z in m["locks"])
      assert any(z.get("nodes",0)>0 for z in c["lock_stats"].values())
     tree=load(cp)
     assert tree["flop"]==flop and tree["turn"]==c["turn"]
     found=[x for x in tree["nodes"] if x["line"]==TARGET and x["player"]==1 and len(x["board"])==10]
     item["source_cases"].append(dict(turn=c["turn"],file_sha256=sha(cp),
       exact_true_actor_IP_river_public_boards=sorted({z["board"] for z in found}),
       actual_actor_IP_original_runout_nodes=len(found),
       real_gto_gap_pct=c["gto_gap_pct"],real_hero_gap_pct=c["hero_gap_pct"],
       observed_pooled_marginals_not_private_card_rates=True,
       exact_full_street_strict_combo_count_still_unverified=True))
    valid[(flop,version)]=item
   else:
    item["explicit_negative_reason"]="MISSING_AUTHENTIC_MANIFEST_OR_JOB_NOT_COMPLETED"
   source.append(item)
 paired=[]
 for flop in FLOPS:
  g,e=valid.get((flop,"gto")),valid.get((flop,"exp_ip"))
  if g and e:
   a=next((c for c in g["source_cases"] if c["actual_actor_IP_original_runout_nodes"]>0),None)
   b=next((c for c in e["source_cases"] if c["actual_actor_IP_original_runout_nodes"]>0),None)
   if a and b and a["turn"]==b["turn"]:
    boards=sorted(set(a["exact_true_actor_IP_river_public_boards"]) & set(b["exact_true_actor_IP_river_public_boards"]))
    if boards:
     paired.append(dict(flop=flop,turn=a["turn"],exact_actor_IP_line=TARGET,
       genuine_same_exact_public_runouts=boards,original_GTO_sha=a["file_sha256"],
       authentic_NL2_partial_hero_lock_sha=b["file_sha256"],
       strictly_legal_full_street_combo_overlay_PENDING=True))
 s=load(D/"nl2_hu_multiboard_status_v47_b364_rank96.json")
 mid="ln-ipfr-r_model-ujl14x"
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(159,233,0,392)
 assert s["records"][mid]["frequency_rank"]==107 and s["records"][mid]["label"]=="APPROX"
 out=dict(schema="NL2_HU_B374_RANK107_TWO_FRESH_FLOP_SHA_AUTHENTIC_SOURCE_TRIAGE_V1",
  model_id=mid,frequency_rank=107,flops_predeclared=list(FLOPS),spot="BTN_BB",
  actor="BTN_IP",exact_river_line=TARGET,source_solver_commit=PIN,original_rust_commit=RUST,
  raw_artifacts=source,actual_paired_orig_GTO_partial_NL2_flops=paired,
  previous_one_existing_verified_genuine_flop_is_separate=True,
  independent_full_street_strict_combo_reach_still_required=True,
  never_generalize_to_abstract_texture=True,
  original_preflop_solver_data_not_observed_NL2_hole_cards=True,
  no_generic_GTO_certification_awarded=True,CERT_MULTIBOARD=159,APPROX=233,EST=0,
  PR2_remains_draft_unmerged=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B374 rank107 authentic source-only two new flop batch\n\n"
    f"Authenticated genuine paired new flop sources: **{len(paired)}/2**. "
    "Exact original GTO and NL2 partial hero locks are kept distinct from pooled marginal input assumptions. "
    "Before any CERT the full-street per-combo strict reach, exact actor, SPR and 3 distinct flops must independently pass. "
    "**159 CERT / 233 APPROX / 0 EST unchanged.**\n")
 print(f'B374 source-check: {len(paired)}/2 exact GTO + partial NL2 IP source pairs; 159 CERT / 233 APPROX')
if __name__=="__main__":main()
