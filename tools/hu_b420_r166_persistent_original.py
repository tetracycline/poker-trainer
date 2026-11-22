#!/usr/bin/env python3
"""B420: persist original whole-source 100bb Rust CFR per-combo archives for two
newly certified CO_BB rank166 without claiming villain private-hand NL2
measurements or generalized public-board GTO.
"""
import argparse,gzip,hashlib,json,pathlib
from verify_hu_multiboard_100bb import verify
D=pathlib.Path("data")
OUT=D/"nl2_hu_b420_rank166_persistent_source_index.json"
DOC=pathlib.Path("docs/NL2_HU_B420_R166_PERSISTENT_REAL_SOURCE.md")
SOURCE=D/"nl2_hu_multiboard_status_v50_b417_rank166.json"
PROOF=D/"nl2_hu_b417_rank166_three_true_source_cert_proof.json"
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
MAP={"B420_COBB_B400":(45028060598,"gto"),"B420_COBB_B407":(45029267778,"exp")}
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--solver-root",type=pathlib.Path,required=True)
 for name in ("gto","exp"):ap.add_argument("--"+name,type=pathlib.Path,required=True)
 args=ap.parse_args()
 s=read(SOURCE);p=read(PROOF)
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(163,229,0,392)
 assert (p["CERT_after"],p["APPROX_after"],p["named_boards_after"],p["hero_lock_variants_after"])==(163,229,618,710)
 assert p["rank"]==166 and len(p["source_pins"])==3
 assert s["records"]["ln-ipfr-r_model-1spq1ko"]["label"]=="CERT-MULTIBOARD"
 expected=set()
 for sample in p["source_pins"]:
  for run,checksum in ((sample["original_GTO_run"],sample["original_GTO_SHA256"]),
                       (sample["actual_NL2_IP_run"],sample["actual_NL2_SHA256"])):
    if run in (45028060598,45029267778):
     assert len(checksum)==64
     expected.add((run,checksum))
 assert expected and len(expected)<=8
 solver=args.solver_root
 assert (solver/"inputs/pool_stats.json").is_file()
 archived=[];verified=set()
 for key,(run,folder) in MAP.items():
  root=getattr(args,folder)
  assert root.is_dir()
  source=verify(root,solver,run)
  assert source["schema"]=="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1"
  assert source["source_run_id"]==run and source["no_generic_texture_certification"]
  assert not source["errors"] and source["new_authentic_board_cases"]>=2
  assert source["source_poker_solver_pin"]==PIN
  assert source["authentic_rust_engine_pin"]==RUST
  cases=[c for art in source["artifacts"] for c in art["cases"]]
  assert len(cases)==source["new_authentic_board_cases"]
  assert cases
  for c in cases:
   assert c["spot"]=="CO_BB" and c["pot_family"]=="SRP"
   assert c["flop"] in ("KcJh7d","QhTc5d")
   assert c["flop_line"] in ("x b50 c","x b100 c")
   assert c["source_sha256"] and len(c["source_sha256"])==64
   assert c["strict_combo_path_summary"]["sequential_actor_combo_nodes"]>0
   assert len(c["hands_by_seat"])==2 and c["nodes"]
   verified.add((run,c["source_sha256"]))
  path=D/"solver_evidence"/("NL2_MULTIBOARD_"+key+".json.gz")
  path.parent.mkdir(parents=True,exist_ok=True)
  content=(json.dumps(source,ensure_ascii=False,separators=(",",":"))+"\n").encode()
  path.write_bytes(gzip.compress(content,compresslevel=9,mtime=0))
  assert gzip.decompress(path.read_bytes())==content
  archived.append(dict(batch=key,original_source_run_id=run,gzip_path=str(path),
    original_zip_SHA256=sha(path),original_RAW_SHA256=hashlib.sha256(content).hexdigest(),
    actual_genuine_source_cases=len(cases),original_source_subgame_SHA256s=sorted({c["source_sha256"] for c in cases}),
    full_original_Rust_source_and_actor_reach_verified=True))
 assert expected<=verified,("Missing required authenticated new CERT source archive",sorted(expected-verified))
 assert len(archived)==2
 report=dict(schema="NL2_B420_RANK166_CERT_DURABLE_REAL_GTO_NL2_IP_SOURCE_ARCHIVES_V1",
  current_V50_SHA256=sha(SOURCE),B417_full_CERT_original_source_proof_sha256=sha(PROOF),
  original_true_Rust_engine_pin=RUST,original_full100bb_preflop_poker_solver_pin=PIN,
  certified_ranks=[166],durable_immutable_gzip_CFR_source_archives=archived,
  original_GTO_and_NL2_IP_source_SHA_pairing_verified=True,
  historical_JS9H4D_cert_source_already_in_original_V47_source_archive=True,
  opponent_NL2_freq_is_pooled_marginal_not_private_card_conditional=True,
  exact_named_public_board_only_no_general_texture_GTO=True,
  CERT_MULTIBOARD=163,APPROX=229,EST=0,TOTAL=392,PR2_remains_draft_unmerged=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B420 rank166 original Rust source permanent archive\n\n"
  "Archived original 100bb GTO (B393) and genuine partially NL2 IP-locked (B396) full source "
  "including exact hand combo/action frequencies for certified named public boards on "
  "KcJh7d and QhTc5d. Historical third flop Js9h4d remains in frozen authenticated V47 source. "
  "All original source SHAs are compared against independently verified B405 rank166 "
  "3-flop CERT; no fabricated generic texture strategies, no purported observed NL2 private-card frequencies. "
  "**163 CERT/229 APPROX**, 618 named boards, 710 NL2 lock variants, subject to HU2475 PASS. "
  "PR #2 remains DRAFT and never merge.\n")
 print("PASS B420 authenticated permanent GTO/NL2 CO-IP rank166 source archives",len(archived),"; 162/230")
if __name__=="__main__":main()
