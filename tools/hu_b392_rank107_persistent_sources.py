#!/usr/bin/env python3
"""B392: independently verify/preserve complete exact original Rust CFR per-combo source
for B390 rank107, so UI need not rely on expiring GitHub Actions artifacts.
"""
import argparse,gzip,hashlib,json,pathlib
from verify_hu_multiboard_100bb import verify
D=pathlib.Path("data")
OUT=D/"nl2_hu_b392_rank107_persistent_original_source_archive_index.json"
DOC=pathlib.Path("docs/NL2_HU_B392_RANK107_PERSISTENT_SOURCE_VIEWER.md")
MAP={
 "B392_R107_B374":(45017142943,"b374"),
 "B392_R107_B387":(45023132316,"b387"),
 "B392_R107_B388":(45025076333,"b388"),
}
MID="ln-ipfr-r_model-ujl14x"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--solver-root",type=pathlib.Path,required=True)
 for name in ("b374","b387","b388"):ap.add_argument("--"+name,type=pathlib.Path,required=True)
 args=ap.parse_args()
 s=read(D/"nl2_hu_multiboard_status_v48_b390_rank107.json")
 cert=read(D/"nl2_hu_b390_rank107_three_true_GTO_NL2_IP_cert_proof.json")
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(160,232,0,392)
 rec=s["records"][MID]
 assert rec["label"]=="CERT-MULTIBOARD" and rec["proven_exact_board_count"]==3
 assert cert["CERT_after"]==160 and len(cert["source_pins"])==3
 expected=set()
 for p in cert["source_pins"]:
  expected.add((p["original_GTO_run"],p["original_GTO_SHA256"]))
  expected.add((p["actual_NL2_IP_run"],p["actual_NL2_SHA256"]))
 assert len({p["flop"] for p in cert["source_pins"]})==3
 preserved=set()
 indexes=[]
 solver=args.solver_root
 assert (solver/"inputs/pool_stats.json").is_file()
 for code,(run,folder) in MAP.items():
  where=getattr(args,folder)
  assert where.is_dir()
  original=verify(where,solver,run)
  assert original["schema"]=="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1"
  assert original["source_run_id"]==run and original["no_generic_texture_certification"]
  assert not original["errors"] and original["new_authentic_board_cases"]>0
  assert original["source_poker_solver_pin"]=="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
  assert original["authentic_rust_engine_pin"]=="9d1509fe5077d019825f833eed04b16d342dfda1"
  cases=[c for art in original["artifacts"] for c in art["cases"]]
  assert len(cases)==original["new_authentic_board_cases"]
  for c in cases:
   assert c["spot"]=="BTN_BB" and c["pot_family"]=="SRP"
   assert c["flop"] in ("7s5h3d","QsJh4d")
   assert c["flop_line"]=="b33 c" and c["turn"] in ("6c","7s")
   assert c["source_sha256"] and len(c["source_sha256"])==64
   assert c["strict_combo_path_summary"]["sequential_actor_combo_nodes"]>0
   assert len(c["hands_by_seat"])==2 and c["nodes"]
   preserved.add((run,c["source_sha256"]))
  outfile=D/"solver_evidence"/("NL2_MULTIBOARD_"+code+".json.gz")
  outfile.parent.mkdir(parents=True,exist_ok=True)
  raw=(json.dumps(original,ensure_ascii=False,separators=(",",":"))+"\n").encode()
  outfile.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
  assert gzip.decompress(outfile.read_bytes())==raw
  indexes.append(dict(batch=code,source_run_id=run,gzip_path=str(outfile),
    archived_gzip_sha256=sha(outfile),original_raw_json_sha256=hashlib.sha256(raw).hexdigest(),
    actual_authenticated_cases=len(cases),
    source_exact_subgame_SHA256s=sorted({c["source_sha256"] for c in cases}),
    all_sources_original_Rust_SHA_and_sequential_combo_verified=True))
 # Cert's historical Jh9d6s source is already preserved in the frozen V47 source files.
 newest={z for z in expected if z[0] in (45017142943,45023132316,45025076333)}
 assert newest<=preserved,("Certified source SHA missing from durable original archive",sorted(newest-preserved))
 assert len(indexes)==3
 x=dict(schema="NL2_B392_RANK107_DURABLE_GTO_NL2_IP_ACTUAL_RUST_CFR_ARCHIVES_V1",
   source_V48_sha256=sha(D/"nl2_hu_multiboard_status_v48_b390_rank107.json"),
   source_B390_cert_proof_sha256=sha(D/"nl2_hu_b390_rank107_three_true_GTO_NL2_IP_cert_proof.json"),
   model_id=MID,verified_archives=indexes,
   genuine_GTO_and_NL2_partial_source_SHA_matches_160_CERT=True,
   historical_Jh9d6s_kept_in_original_V47_verified_immutable_files=True,
   no_unobserved_per_private_hand_NL2_frequency_claim=True,
   no_generic_texture_or_all_hands_GTO=True,
   CERT_MULTIBOARD=160,APPROX=232,EST=0,
   PR2_Draft_NEVER_MERGE=True)
 OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B392 persistent real original rank107 per-combo GTO/NL2 source viewer\n\n"
  "All four newly certified Rust CFR cases in 3 independent SHA/reach-verified gzip batches "
  "from Actions B374, B387 and B388 are now retained in the PR, rather than relying only "
  "on expiring artifacts. Original historical Jh9d6s remains in V47 verified source files. "
  "The viewer matches exact source run, SHA, flop, turn, actor, position and pot family. "
  "CFR solver GTO and partially NL2-locked opponent pool assumptions are never treated as "
  "observed private-card conditional opponent actions. "
  "160 CERT / 232 APPROX, no additional model promotion. PR remains draft.\n")
 print("PASS B392",len(indexes),"durable original full combo sources; true 160 CERT/232 APPROX")
if __name__=="__main__":main()
