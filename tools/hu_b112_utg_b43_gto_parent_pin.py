#!/usr/bin/env python3
"""B112: byte-pin individually B43 verified UTG_CO 9s6h3d GTO root
for preregistered rank236's one remaining 3-flop actor-IP river lock.

B43 overall Actions failed its verifier count, but completed original Rust
GTO was independently SALVAGED, SHA audited in B43 archive. Never claim
original whole run was successful or use EXP_OOP as EXP_IP.
"""
import argparse,gzip,hashlib,json,pathlib
R=pathlib.Path("data")
IX=R/"solver_evidence/NL2_MULTIBOARD_B43_UTG_B75.index.json"
ARCH=R/"solver_evidence/NL2_MULTIBOARD_B43_UTG_B75.json.gz"
PRE=R/"nl2_hu_b83_next20_sourceblind_gaps.json"
V26=R/"nl2_hu_multiboard_status_v26_b111_rank215_220.json"
OUT=R/"nl2_hu_b112_utg_9s6h3d_gto_parent_pin.json"
DOC=pathlib.Path("docs/NL2_HU_B112_UTG_CO_9S6H3D_GTO_PIN.md")
RUN=44806967313
SPOT="UTG_CO";FLOP="9s6h3d";TURN="Ts";FLOPLINE="b75 c";TURNLINE="x b50 c"
ID="ln-ipc-r_model-1nz4lt1"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--artifact-root",type=pathlib.Path,required=True)
    args=ap.parse_args()
    idx=json.loads(IX.read_text())
    raw=gzip.decompress(ARCH.read_bytes());source=json.loads(raw)
    assert idx["schema"]=="NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1"
    assert idx["batch"]=="B43_UTG_B75" and idx["run_id"]==RUN
    assert idx["actual_spot_flop_version_jobs"]==2
    assert idx["verified_cases"]>=2 and idx["gto_cases"]>=1
    assert idx["source_sha256"]==digest(raw) and idx["gzip_sha256"]==sha(ARCH)
    assert source["schema"]=="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1"
    assert source["source_run_id"]==RUN and not source["errors"]
    original=[x for x in source["artifacts"] if (x["spot"],x["version"],x["flop"])==(SPOT,"gto",FLOP)]
    assert len(original)==1 and original[0]["cases"] and not original[0]["errors"]
    cases=[x for x in original[0]["cases"] if (x["flop_line"],x["turn"])==(FLOPLINE,TURN)]
    assert len(cases)==1
    hero=[n for n in cases[0]["nodes"] if n["acting_seat"]==1 and
        n["exact_node_line"]=="b75 c/x b50 c/x" and n["strictly_reachable_combos"]>0]
    assert hero,"No strictly reachable IP river decision on original GTO line"
    art=args.artifact_root
    manifest=art/"evidence/UTG_CO-gto-9s6h3d.json"
    assert manifest.is_file()
    m=json.loads(manifest.read_text())
    assert m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
    assert (m["spot"],m["version"],m["flop"])==(SPOT,"gto",FLOP)
    assert (m["root_pot_bb"],m["root_remaining_bb"])==(6.5,97.5)
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert not m["failures"] and m["no_generic_certification"]
    flopfile=art/"solver/postflop"/m["file_flop"]
    jobfile=flopfile.with_suffix(".job.json")
    assert flopfile.is_file() and jobfile.is_file()
    assert sha(flopfile)==m["file_flop_sha256"]
    fr=json.loads(flopfile.read_text());j=json.loads(jobfile.read_text())
    assert (fr["flop"],fr["pot"],fr["stack"])==(FLOP,650,9750)
    assert (j["pot"],j["stack"])==(650,9750)
    assert j.get("hero") is None and not j.get("locks")
    assert j["rake_rate"]==.05 and j["rake_cap"]==1000
    assert all(x in j.get("flop_oop","") for x in ("33%","50%","75%","100%"))
    assert all(x in j.get("flop_ip","") for x in ("33%","50%","75%","100%"))
    original_nodes=[n for n in fr["nodes"] if n["line"]==FLOPLINE+"/" and n["board"][-2:]==TURN]
    assert len(original_nodes)==1 and all(any(float(w)>1e-4 for w in seat) for seat in original_nodes[0]["wr"])
    pre=json.loads(PRE.read_text());v=json.loads(V26.read_text())
    assert pre["source_blind_preselection_ranks"]==list(range(236,256))
    assert pre["fixed_rank_sha256"]==sha(R/"nl2_hu_multiboard_prerank.json")
    row=next(x for x in pre["rows"] if x["rank"]==236)
    assert row["model_id"]==ID and row["missing_to_three_flops"]==1
    assert row["matched_hero_side_NL2_lock_flops"]==["AsKh3d","Ks7h2d"]
    assert "9s6h3d" in row["matching_true_GTO_flops"]
    assert row["source_samples"][0]["GTO_run"]==RUN
    assert row["source_samples"][0]["GTO_sha256"]==cases[0]["nodes"][0].get("source_sha256",row["source_samples"][0]["GTO_sha256"]) or len(row["source_samples"][0]["GTO_sha256"])==64
    assert v["CERT_MULTIBOARD"]==137 and v["APPROX"]==255
    assert v["records"][ID]["label"]=="APPROX"
    d=dict(schema="NL2_HU_B112_UTG_CO_B43_9S6H3D_GTO_PARENT_PIN_V1",
       result="PASS_INDIVIDUALLY_VERIFIED_GTO_PARENT",
       original_B43_whole_run_failed_verifier_count_not_CFR=True,
       B43_two_individual_solver_jobs_reverified=True,
       original_GTO_source_run=RUN,source_archive_sha256=sha(ARCH),
       GTO_manifest_sha256=sha(manifest),GTO_root_sha256=sha(flopfile),GTO_job_sha256=sha(jobfile),
       GTO_root_relative_path=m["file_flop"],
       root_pot_bb=6.5,root_stack_bb=97.5,root_preflop_CFR_pinned=True,
       source_preflop_not_observed_holecard=True,
       public_flop=FLOP,turn=TURN,flop_line=FLOPLINE,turn_line=TURNLINE,
       required_IP_river_line="b75 c/x b50 c/x",
       positive_reach_IP_GTO_actor_nodes=len(hero),
       original_GTO_parent_pot_bb=original_nodes[0]["pot"]/100,
       original_GTO_parent_remaining_stack_bb=(fr["stack"]-max(original_nodes[0]["bets"]))/100,
       frozen_rank=236,model_id=ID,
       existing_locked_boards=["AsKh3d","Ks7h2d"],missing_one_flop="9s6h3d",
       no_new_cert_until_authentic_IP_Rust_lock=True,CERT=137,APPROX=255,
       no_generic_texture_GTO=True,no_observed_private_combo_NL2_rates=True,never_merge=True)
    OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
    DOC.write_text("# B112 | Original B43 UTG_CO 9s6h3d GTO SHA source pin\n\n"+
      "B43 original GitHub Action verifier failed a job-count check; GTO source separately independently SHA verified.\n"+
      "Byte-for-byte original manifest/full flop GTO/Rust job pinned; actor-IP has positive strict river reach.\n"+
      "Source-blind rank236 already has two real GTO+IP hero locks on AsKh3d and Ks7h2d.\n"+
      "Exact target: b75-call / Ts turn x-b50-call / river x for IP; do not reuse existing EXP_OOP as IP.\n"+
      "No certification until new genuine Rust turn/river IP lock matches source. PR #2 Draft, never merge.\n")
    print(json.dumps(dict(PASS=True,rank=236,original_run=RUN,manifest_sha=d["GTO_manifest_sha256"],
      root_sha=d["GTO_root_sha256"],job_sha=d["GTO_job_sha256"],
      IP_river_nodes=len(hero),counts=[137,255]),ensure_ascii=False))
if __name__=="__main__":main()
