#!/usr/bin/env python3
"""B454 investigate frozen rank35 LMP OOP b33-call/check-check river with 3 original GTO sources."""
import argparse,hashlib,json,pathlib,sys
SOURCE_RUN=44666294821
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
SPEC=(
 dict(flop="8s8h3d",turn="5s",artifact_id=14600026283,
      manifest_sha="f6922cc27956249d6d69e1c4a184956dc356f67ba8b577194a88a2eccebd3bb7",
      root_sha="c5861d2bbcc0361f095b13a8ed3e393785c48ec2a517cee1cafb7c52567ed61c",
      sub_sha="bbfc9d8eeb36e39c27271e8fb3810458cdc4592a0584da23702f8dfe48803568"),
 dict(flop="9s6h3d",turn="Ts",artifact_id=14599037935,
      manifest_sha="e1928c60767bd27371029f56f3d53f0f3471f74d955108cf808ff3090bc85d13",
      root_sha="2856dcd71a0d8b4f2f2597ffb5e62cc8b31aeefa3017cbf6f263bcc733716909",
      sub_sha="9b712c7e60081b08041c48139edf8bf7e9d3d36bdd839e6031e9038b2ac3b167"),
 dict(flop="KsQh4d",turn="Tc",artifact_id=14601426559,
      manifest_sha="26ee0877e730fb2326dc5a151c2004d0b41153f6a2a10a48ddc7898d00e64190",
      root_sha="fd64ea26856897b8f8a01a5e3be00cbccce36daa78d664a38be082470b7af354",
      sub_sha="c9f3c0b7b4887a9f244871b43f3632e0ec877ef508f207da36aea88a5a70af16"),
)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def main():
  a=argparse.ArgumentParser()
  a.add_argument("--downloads",required=True,type=pathlib.Path)
  a.add_argument("--run-id",required=True,type=int)
  p=a.parse_args()
  sys.path.insert(0,str(pathlib.Path("tools").resolve()))
  from hu_sequential_cfr_reach import game_reach,accepted
  D=pathlib.Path("data")
  st=load(D/"nl2_hu_multiboard_status_v51_b453_rank32.json")
  r=st["records"]["ln-iso-lmp_r_model-pjewx6"]
  assert st["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V51_B453_R32"
  assert (st["CERT_MULTIBOARD"],st["APPROX"],st["EST"])==(164,228,0)
  assert (r["frequency_rank"],r["label"],r["solver_profile"],r["assumed_model_node_spr"])==(35,"APPROX","LMP_CO_BB",23.558)
  data=[]
  for x in SPEC:
    flop=x["flop"];turn=x["turn"]
    base=p.downloads/flop
    rootdir=base/"solver/postflop/out/LMP_CO_BB/gto"
    mf=base/"evidence"/f"LMP_CO_BB-gto-{flop}.json"
    rp=rootdir/f"{flop}_multiboard.json"
    sp=rootdir/f"{flop}_b33c_{turn}.json"
    job=sp.with_suffix(".job.json")
    assert all(f.is_file() for f in (mf,rp,sp,job))
    assert (sha(mf),sha(rp),sha(sp))==(x["manifest_sha"],x["root_sha"],x["sub_sha"])
    assert (base/"evidence/poker-solver-pinned-SHA.txt").read_text().strip()==PIN
    assert (base/"evidence/rust-engine-pin-SHA.txt").read_text().strip()==RUST
    m,fr,sub=map(load,(mf,rp,sp))
    assert (m["schema"],m["spot"],m["version"],m["flop"])==(
      "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB","gto",flop)
    assert m["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
    assert (m["root_pot_bb"],m["root_remaining_bb"])==(2.5,99.0)
    root_job=load(rp.with_suffix(".job.json"))
    assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
    assert m["allow_OOP_flop_leads"] is True
    assert root_job["flop_oop"]=="33%,50%,75%,100%" and root_job["flop_ip"]=="33%,50%,75%,100%"
    assert root_job["flop_raise"]=="3x,a" and root_job.get("hero") is None
    assert (root_job["pot"],root_job["stack"])==(250,9900)
    assert abs(root_job["rake_rate"]-0.05)<1e-8 and root_job["rake_cap"]==1000
    # Historical B3 predates the manifest field flop_size_profile; check the actual Rust job, never invent metadata.
    assert "b33 c" in m["selected_lines"] and m["turns"]==[turn]
    assert m["solved_cases"]>=1 and not m["failures"]
    assert m["file_flop_sha256"]==sha(rp)
    c=next(z for z in m["cases"] if (z["line"],z["turn"])==("b33 c",turn))
    assert c["source_sha256"]==sha(sp)
    assert c["gto_gap_pct"]<=.5 and fr["info"]["gto_expl_pct"]<=.5 and sub["info"]["gto_expl_pct"]<=.5
    assert (sub["line0"],sub["turn"],sub["flop"])==("b33 c",turn,flop)
    assert (fr["pot"],fr["stack"])==(250,9900)
    assert c["real_flop_parent_spr"]>0
    srcnode=next(n for n in fr["nodes"] if n["line"]=="" and n["player"]==0 and len(n["board"])==6)
    assert "b33" in srcnode["acts"]
    legal_b33=accepted(srcnode,fr["hands"],"b33")
    seq,stats=game_reach(fr,sub)
    targets=[]
    for n in sub["nodes"]:
      if n["player"]!=0 or n["line"]!="b33 c/x x/" or len(n["board"])!=10:continue
      actual=(sub["stack"]-max(n["bets"]))/n["pot"]
      if abs(actual-23.558)/23.558>.05:continue
      key="|".join((n["board"],n["line"],"0"))
      q=seq[key]
      raw=sum(w>1e-4 for w in n["w"][0])
      assert raw>0
      targets.append(dict(public_board=n["board"],actor_seat=0,exact_node_line=n["line"],
           source_actor_combos=raw,strict_full_street_combos=q["count"],
           actual_spr=round(actual,6)))
    assert len(targets)==2 and all(z["strict_full_street_combos"]==0 for z in targets)
    assert len(legal_b33)==0
    data.append(dict(flop=flop,turn=turn,
        original_run_id=SOURCE_RUN,original_gto_artifact_id=x["artifact_id"],
        original_manifest_sha256=sha(mf),original_root_sha256=sha(rp),
        original_b33c_turn_sha256=sha(sp),gto_gap_pct=c["gto_gap_pct"],
        root_b33_strict_action_eligible_combos=len(legal_b33),
        river_targets=targets,river_node_count=len(targets),
        positive_river_GTO_reachable_combos=0,
        source_has_nonzero_raw_actor_combos=True,
        original_full_size_rust_CFR=True))
  assert len(data)==3 and len({x["flop"] for x in data})==3
  assert sum(x["river_node_count"] for x in data)==6
  proof=dict(schema="NL2_B454_R35_THREE_ORIGINAL_LMP_B33_XX_STRICT_ZERO_NEGATIVE_V1",
    source_run_id=SOURCE_RUN,verification_run_id=p.run_id,
    model_id="ln-iso-lmp_r_model-pjewx6",frequency_rank=35,
    spot="LMP_CO_BB",acting_seat=0,target_exact_river_line="b33 c/x x/",
    target_model_spr=23.558,
    three_distinct_true_original_GTO_flops=data,
    strict_positive_source_flops=0,
    original_source_authoritative_sha_pin=True,
    original_sources_reused_only_no_solver_rerun=True,
    rank35_remains_APPROX=True,
    strict_zero_reason="PREFLOP_FROZEN_LMP_B33_ROOT_BET_ACTION_DISALLOWED_FOR_ALL_THREE_AT_40_70",
    old_preflop_169_class_ranges_assumed_not_observed=True,
    no_generic_texture_CERT=True,no_unearned_50pct_nonpolarized_claim=True,
    CERT_MULTIBOARD=164,APPROX=228,EST=0,PR2_Draft_NEVER_MERGE=True)
  out=D/"nl2_hu_b454_rank35_authentic_strict_zero_negative.json"
  out.write_text(json.dumps(proof,indent=2,ensure_ascii=False)+"\n")
  (pathlib.Path("docs")/"NL2_HU_B454_R35_B33XX_STRICT_ZERO_NEGATIVE.md").write_text(
    "# B454 rank35 LMP OOP b33-call / check-check river: authentic negative\n\n"
    "The original successful B3 100bb full-size Rust GTO source run 44666294821 "
    "was independently checked on three distinct flops 8s8h3d/5s, 9s6h3d/Ts and KsQh4d/Tc. "
    "All six exact river decision nodes have nonzero raw actor combos but "
    "**zero strict multi-street combos**, because the original GTO flop b33 "
    "action is never max/near-frequency under the frozen 40%/70% rule. "
    "No old failed EXP was rerun. The LMP 169-class preflop remains an assumption, "
    "not measured private hands. Rank35 stays APPROX. V51 still 164 CERT / 228 APPROX.\n")
  print(json.dumps(dict(batch="B454",model_rank=35,flops=3,river_nodes=6,positive=0,cert=164,approx=228)))
if __name__=="__main__": main()
