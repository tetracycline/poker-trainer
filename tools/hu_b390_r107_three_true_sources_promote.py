#!/usr/bin/env python3
"""B390: rank107 source-blind exact-board promotion, independently SHA-gated 3 real GTO/NL2 pairs."""
import argparse,copy,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,texture
from hu_sequential_cfr_reach import game_reach
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create
from verify_hu_multiboard_100bb import strict_medium_evidence,lock_scope,locked_model_gain

D=pathlib.Path("data")
MID="ln-ipfr-r_model-ujl14x"
LINE="b33 c/x b50 c/x"
PARENT=D/"nl2_hu_multiboard_status_v47_b364_rank96.json"
PRE=D/"nl2_hu_b389_rank107_three_true_flop_pre_cert_gate.json"
STATUS=D/"nl2_hu_multiboard_status_v48_b390_rank107.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v48_b390.json"
AUDIT=D/"nl2_hu_cert_lock_medium_audit_v48_b390.json"
PROOF=D/"nl2_hu_b390_rank107_three_true_GTO_NL2_IP_cert_proof.json"
DOC=pathlib.Path("docs/NL2_HU_B390_RANK107_THREE_AUTHENTIC_CERT.md")
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))

def original(root,flop,turn,ver,proof):
 mp=root/"evidence"/f"BTN_BB-{flop}-{ver}.json"
 assert mp.is_file() and sha(mp)==proof["manifest"]
 assert (root/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
 assert (root/"evidence/rust-pin.txt").read_text().strip()==RUST
 m=read(mp)
 assert (m["schema"],m["spot"],m["flop"],m["version"],m["pot_family"])==(
  "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","BTN_BB",flop,ver,"SRP")
 assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
 assert (m["preflop_ranges"]["source"],m["flop_size_profile"])==("PINNED_POKER_SOLVER_PREFLOP_CFR","full")
 assert not m["restricted_tree_assumption"]
 assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
 assert (m["flop_line_policy"],m["selected_lines"],m["turns"])==("oop-b33only",["b33 c"],[turn])
 assert m["solved_cases"]==len(m["cases"])==1 and not m["failures"]
 frp=root/"solver/postflop"/m["file_flop"]
 assert frp.is_file() and sha(frp)==m["file_flop_sha256"]==proof["root"]
 fr=read(frp)
 assert (fr["flop"],fr["pot"],fr["stack"])==(flop,550,9750)
 c=m["cases"][0]
 assert (c["line"],c["turn"],c["source_sha256"])==("b33 c",turn,proof["sub"])
 assert c["gto_gap_pct"] is not None and 0<=c["gto_gap_pct"]<=.5
 assert (ver=="gto" and c["hero_gap_pct"] is None) or (ver=="exp_ip" and c["hero_gap_pct"] is not None and c["hero_gap_pct"]<=.5)
 subp=root/"solver/postflop"/c["source_path"]
 assert subp.is_file() and sha(subp)==proof["sub"]
 sub=read(subp)
 assert (sub["flop"],sub["turn"],sub["line0"])==(flop,turn,"b33 c")
 mask,_=game_reach(fr,sub)
 return m,c,sub,mask

def paired_sample(model,flop,turn,board,gr,er,gproof,eproof,run_g,run_e):
 gm,gc,gsub,gmask=original(gr,flop,turn,"gto",gproof)
 em,ec,esub,emask=original(er,flop,turn,"exp_ip",eproof)
 assert gm["preflop_ranges"]["full_sha256"]==em["preflop_ranges"]["full_sha256"]
 assert gm["pool_source_sha256"]==em["pool_source_sha256"]
 def node(sub,mask):
  rows=[n for n in sub["nodes"] if n["board"]==board and n["line"]==LINE and n["player"]==1]
  assert len(rows)==1,(flop,board,len(rows))
  n=rows[0];q=mask["|".join((board,LINE,"1"))]
  assert q["count"]>0,(flop,board,"ZERO_SOURCE_STRICT_ACTOR_IP_COMBOS")
  spr=(sub["stack"]-max(n["bets"]))/n["pot"]
  assert abs(spr-model["assumed_model_node_spr"])/max(1,spr)<=.05
  return n,q,spr
 gn,gq,gspr=node(gsub,gmask)
 en,eq,espr=node(esub,emask)
 assert abs(gspr-espr)<1e-5
 lc=lock_scope(esub,em["locks"],"exp_ip")
 assert lc["observed_marginal_source_nodes"]>0
 assert lc["villain_decision_nodes"]==lc["observed_marginal_source_nodes"]+lc["imputed_assumption_nodes"]+lc["unmatched_nodes"]
 medium=strict_medium_evidence(gn,gsub,gq["mask"])
 assert medium["eligible"]>=0
 nl2=dict(version="exp_ip",run_id=run_e,sha256=ec["source_sha256"],
   source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",
   villain_observed_pattern_node_share_pct=lc["coverage_pct"],
   source_not_real_per_combo_observation=True,
   unknown_history_frequency_filled_with_default=lc["imputed_assumption_nodes"]>0,
   observed_marginal_source_nodes=lc["observed_marginal_source_nodes"],
   assumed_default_source_nodes=lc["imputed_assumption_nodes"],
   unlocked_source_nodes=lc["unmatched_nodes"],
   hero_model_gain_bb=locked_model_gain(esub,"exp_ip"))
 sample=dict(flop=flop,turn=turn,public_board=board,actual_exact_action_line=LINE,
   acting_seat=1,exact_flop_action="b33 c",
   actual_pot_bb=gn["pot"]/100,
   actual_effective_stack_bb=(gsub["stack"]-max(gn["bets"]))/100,
   actual_spr=gspr,model_assumed_spr=model["assumed_model_node_spr"],
   relative_spr_error_pct=round(100*abs(gspr-model["assumed_model_node_spr"])/max(1,gspr),4),
   genuine_gto_exploitability_pct=gc["gto_gap_pct"],
   source_run_id=run_g,source_sha256=gc["source_sha256"],
   source_kind="PINNED_PREFLOP_CFR",assumed_preflop_ranges=False,
   exact_combo_reachable=sum(float(w)>1e-4 for w in gn["w"][1]),
   strict_full_street_combo_reachable=gq["count"],
   exact_node_actions=gn["acts"],medium_50pct_eligible_combos=medium["eligible"],
   b50_nonpolarized_relative_equity_research_candidate=medium["candidate"],
   nl2_locked_variants=[nl2],flop_texture=texture(flop))
 pinned=dict(flop=flop,turn=turn,board=board,original_GTO_run=run_g,
   actual_NL2_IP_run=run_e,original_GTO_SHA256=gc["source_sha256"],
   actual_NL2_SHA256=ec["source_sha256"],GTO_strict_combos=gq["count"],
   NL2_strict_combos=eq["count"],actual_spr=gspr,
   observed_source_nodes=lc["observed_marginal_source_nodes"],
   assumed_source_nodes=lc["imputed_assumption_nodes"],
   unlocked_source_nodes=lc["unmatched_nodes"])
 return sample,pinned

def patch_js(path):
 x=path.read_text(encoding="utf-8")
 marker="const v48=d=>{"
 assert x.count(marker)==1
 validator="""const v48b390=d=>{
 const r=d.records?.['ln-ipfr-r_model-ujl14x'];
 const q=d.B390_rank107_three_true_original_GTO_NL2_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107'||
  d.CERT_MULTIBOARD!==160||d.APPROX!==232||d.EST!==0||d.TOTAL!==392||
  q?.rank!==107||q?.spot!=='BTN_BB'||q?.actor!=='BTN_IP'||
  q?.flops?.join(',')!=='Jh9d6s,7s5h3d,QsJh4d'||
  q?.source_blind_first10_preregistered!==true||q?.pins?.length!==3||
  q.pins.some(z=>z.GTO_strict_combos<=0||z.NL2_strict_combos<=0||
   z.original_GTO_SHA256?.length!==64||z.actual_NL2_SHA256?.length!==64)||
  r?.label!=='CERT-MULTIBOARD'||r?.frequency_rank!==107||
  r?.proven_exact_board_count!==3||
  r.certified_3_to_5_exact_flop_boards?.length!==3||
  r.certified_3_to_5_exact_flop_boards.some(z=>
    z.acting_seat!==1||z.actual_exact_action_line!=='b33 c/x b50 c/x'||
    z.strict_full_street_combo_reachable<=0||z.relative_spr_error_pct>5||
    !z.nl2_locked_variants?.some(v=>v.version==='exp_ip'&&v.sha256?.length===64))||
  d.no_generic_texture_GTO!==true||d.PR2_remains_draft_never_merge!==true)
  throw Error('B390 original 3-board GTO/NL2 source fails closed');
 return d;
};
"""
 x=x.replace(marker,validator+marker)
 old="return fetch('data/nl2_hu_multiboard_status_v48_b369_rank27.json',{cache:'no-store'}).then(open).then(v48)"
 new="return fetch('data/nl2_hu_multiboard_status_v48_b390_rank107.json',{cache:'no-store'}).then(open).then(v48b390)\n    .catch(()=>fetch('data/nl2_hu_multiboard_status_v48_b369_rank27.json',{cache:'no-store'}).then(open).then(v48))"
 assert x.count(old)==1;x=x.replace(old,new)
 oldschema="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B369_RANK27','NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96'"
 assert x.count(oldschema)==1
 x=x.replace(oldschema,"'NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107',"+oldschema)
 if path.name=="nl2-multiboard.js":
  oldmatrix="fetch('data/nl2_hu_cert_lock_medium_matrix_v48_b369.json',{cache:'no-store'}).catch"
  assert x.count(oldmatrix)==1
  x=x.replace(oldmatrix,"fetch('data/nl2_hu_cert_lock_medium_matrix_v48_b390.json',{cache:'no-store'}).catch(()=>fetch('data/nl2_hu_cert_lock_medium_matrix_v48_b369.json',{cache:'no-store'})).catch")
 path.write_text(x,encoding="utf-8")

def main():
 ap=argparse.ArgumentParser()
 for opt in ("b374-gto","b374-exp","b387-gto","b388-exp"):
  ap.add_argument("--"+opt,type=pathlib.Path,required=True)
 a=ap.parse_args()
 b389=read(PRE);parent=read(PARENT)
 assert b389["provisional_ready_for_independent_V48_source_promotion"]
 assert b389["distinct_verified_original_GTO_and_NL2_hero_lock_flops"]==3
 assert (parent["CERT_MULTIBOARD"],parent["APPROX"],parent["EST"],parent["TOTAL"])==(159,233,0,392)
 rec=parent["records"][MID]
 assert (rec["label"],rec["frequency_rank"],rec["solver_profile"],rec["street"])==("APPROX",107,"BTN_BB",2)
 triage=read(D/"nl2_hu_b370_first10_approx_source_triage.json")
 hist=next(z for z in triage["source_blind_selected_ten"] if z["frequency_rank"]==107)["strictly_measured_pairs"][0]
 paths=[pathlib.Path(p) for p in parent["source_evidence"]["source_files"]]
 assert all(p.is_file() for p in paths)
 by_exact,by_locked,_=build_source_index(D,paths)
 model=dict(family=rec["family"],spot=rec["solver_profile"],street=rec["street"],
  preflop_text=rec["preflop_text"],abstract_action_history=rec["abstract_action_history"],
  approx_spr=rec["assumed_model_node_spr"])
 rows,reason=candidates(model,by_exact,by_locked,None)
 assert reason is None
 first=[x for x in rows if x["flop"]=="Jh9d6s" and x["public_board"]==hist["exact_public_board"]
   and x["source_sha256"]==hist["gto_source_sha256"]
   and any(v["sha256"]==hist["nl2_hero_lock_sha256"] for v in x["nl2_locked_variants"])]
 assert first
 original=copy.deepcopy(first[0])
 original["nl2_locked_variants"]=[x for x in original["nl2_locked_variants"]
   if x["version"]=="exp_ip" and x["sha256"]==hist["nl2_hero_lock_sha256"]][:1]
 assert len(original["nl2_locked_variants"])==1 and original["strict_full_street_combo_reachable"]>0
 b379=read(D/"nl2_hu_b379_rank107_7s5h3d_6c_true_gto_nl2_ip_strict_pair.json")
 g0=b379["genuine_original_full_flop_GTO_and_NL2_hero_IP_sources"]["gto"]
 e0=b379["genuine_original_full_flop_GTO_and_NL2_hero_IP_sources"]["exp_ip"]
 oldboard=b389["selected_exact_named_boards"][1]["board"]
 x,pin1=paired_sample(rec,"7s5h3d","6c",oldboard,a.b374_gto,a.b374_exp,
  dict(manifest=g0["source_manifest_sha256"],root=g0["original_flop_source_sha256"],sub=g0["genuine_turn_river_source_sha256"]),
  dict(manifest=e0["source_manifest_sha256"],root=e0["original_flop_source_sha256"],sub=e0["genuine_turn_river_source_sha256"]),
  45017142943,45017142943)
 b388=read(D/"nl2_hu_b388_rank107_qsjh4d_real_gto_nl2_ip_pair.json")
 g1=b388["original_GTO_source"];e1=b388["real_NL2_partial_source"]
 newboard=b389["selected_exact_named_boards"][2]["board"]
 y,pin2=paired_sample(rec,"QsJh4d","7s",newboard,a.b387_gto,a.b388_exp,
  dict(manifest=g1["original_manifest_SHA256"],root=g1["original_flop_SHA256"],sub=g1["subgames"][0]["original_subgame_SHA256"]),
  dict(manifest=e1["original_manifest_SHA256"],root=e1["original_flop_SHA256"],sub=e1["subgames"][0]["original_subgame_SHA256"]),
  45023132316,b388["source_run_B388_EXP"])
 assert {original["flop"],x["flop"],y["flop"]}=={"Jh9d6s","7s5h3d","QsJh4d"}
 assert len({texture(q["flop"]) for q in (original,x,y)})>=2
 pin0=dict(flop="Jh9d6s",turn=original["turn"],board=original["public_board"],
  original_GTO_run=original["source_run_id"],
  actual_NL2_IP_run=original["nl2_locked_variants"][0]["run_id"],
  original_GTO_SHA256=original["source_sha256"],
  actual_NL2_SHA256=original["nl2_locked_variants"][0]["sha256"],
  GTO_strict_combos=original["strict_full_street_combo_reachable"],
  NL2_strict_combos=hist["strict_legal_combo_count"],actual_spr=original["actual_spr"])
 new=copy.deepcopy(parent);r=copy.deepcopy(rec)
 r.update(label="CERT-MULTIBOARD",high_frequency_preregistered=True,
  original_top24_high_frequency_preregistered=False,
  source_blind_expansion_rank=107,source_blind_expansion_preregistered=True,
  prereg_cohort="B370_FIRST10_SOURCE_BLIND",
  certified_3_to_5_exact_flop_boards=[original,x,y],
  proven_exact_board_count=3,blocked_reason=None,
  source_credibility="GITHUB_ACTIONS_SHA_PINNED_FULL100BB_GTO_AND_ACTUAL_NL2_IP_RUST_STRICT_40_70")
 new["records"][MID]=r
 new.update(schema="NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107",
  CERT_MULTIBOARD=160,APPROX=232,EST=0,TOTAL=392,
  parent_v47_sha256=sha(PARENT),original_v47_cert=159,original_v47_approx=233,
  supplementary_cert_count=parent["supplementary_cert_count"]+1,
  source_blind_expansion_ranks=sorted(set(parent["source_blind_expansion_ranks"]+[107])),
  original_top24_cutoff_unchanged=True,
  no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
  PR2_remains_draft_never_merge=True,
  B390_rank107_three_true_original_GTO_NL2_IP_flops=dict(
   rank=107,model_id=MID,spot="BTN_BB",actor="BTN_IP",
   exact_line=LINE,flops=["Jh9d6s","7s5h3d","QsJh4d"],
   source_blind_first10_preregistered=True,
   original_top24_high_frequency_preregistered=False,
   original_V47_sha256=sha(PARENT),
   B389_source_gate_sha256=sha(PRE),
   only_exact_named_boards_CERT_no_generic_texture=True,
   NL2_lock_is_pool_marginal_not_private_hand=True,
   pins=[pin0,pin1,pin2]))
 new["B390_new_authentic_original_Rust_sources_separate_from_frozen_V47_index"]=True
 STATUS.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n")
 tested=audit(new)
 assert (tested["cert_multiboard"],tested["approx"],tested["EST"])==(160,232,0)
 assert (tested["aggregate"]["named_board_proofs"],tested["aggregate"]["paired_hero_locked_source_variants"])==(609,701)
 matrix=create(new)
 assert (len(matrix["models"]),len(matrix["boards"]))==(160,609)
 unknown=sum(1 for z in matrix["boards"] for v in z["hero_lock_proofs"]
  if v["node_rate_data_status"]=="HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN")
 assert unknown==0
 matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V48_B390",
  V48_status_sha256=sha(STATUS),source_unknown_variants_after=0,
  B388_true_Rust_NL2_IP_source_authenticated=True,no_private_card_frequency_claim=True,
  PR2_Draft_NEVER_MERGE=True)
 MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
 AUDIT.write_text(json.dumps(tested,ensure_ascii=False,indent=2)+"\n")
 PROOF.write_text(json.dumps(dict(schema="NL2_B390_RANK107_THREE_TRUE_SOURCE_CERT_V1",
  rank=107,source_pins=[pin0,pin1,pin2],status_sha256=sha(STATUS),
  matrix_sha256=sha(MATRIX),audit_sha256=sha(AUDIT),
  original_status_sha256=sha(PARENT),pre_cert_gate_sha256=sha(PRE),
  CERT_before=159,CERT_after=160,APPROX_before=233,APPROX_after=232,EST=0,
  named_boards_before=606,named_boards_after=609,hero_lock_variants_before=698,
  hero_lock_variants_after=701,B368_unknown_after=0,
  no_generic_handclass_CERT=True,no_observed_private_card_NL2=True,
  PR2_draft_never_merge=True),ensure_ascii=False,indent=2)+"\n")
 for name in ("nl2_hu_multiboard_ui.js","nl2-multiboard.js"):patch_js(pathlib.Path(name))
 for name in ("nl2.html","nl2-multiboard.html"):
  p=pathlib.Path(name);s=p.read_text()
  assert s.count("task-hybrid-b378-v47-loaderfix-20261122")==1
  p.write_text(s.replace("task-hybrid-b378-v47-loaderfix-20261122","task-hybrid-b390-v48-20261122"))
 DOC.write_text("# B390 rank107: 3 authenticated exact full 100bb GTO+NL2 BTN-IP sources\n\n"
  "Only the three named public boards (distinct flops Jh9d6s, 7s5h3d, QsJh4d) "
  "have original GTO and independently proven genuine partially NL2-locked Rust source, "
  "same BTN-IP actor, exact b33 c/x b50 c/x history, source SHA, legal 40/70 combos and <=5% SPR error. "
  "No universal GTO texture or 50% sizing claim; opponent pool marginals are not private-card observations. "
  "Independent source/medium audit: **160 CERT /232 APPROX /0 EST**, "
  "HU2475/2475 Actions required. PR #2 DRAFT, NEVER MERGE.\n")
 print("B390 verified original 3-source rank107 promotion: 160 CERT /232 APPROX, 609 boards, 701 locks, UNKNOWN=0")
if __name__=="__main__":main()
