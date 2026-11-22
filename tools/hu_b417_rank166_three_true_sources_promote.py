#!/usr/bin/env python3
"""B417: independent source-blind rank166 3-flop 100bb Rust GTO+NL2 IP CERT.
Three distinct exact original 100bb GTO plus genuine NL2-IP partially locked
runouts each, full-street max/40%-70% combo reach; never certify generic texture.
"""
import argparse,copy,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,texture
from hu_sequential_cfr_reach import game_reach
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create
from verify_hu_multiboard_100bb import strict_medium_evidence,lock_scope,locked_model_gain
from hu_b407_rank166_true_co_ip_pairs import check as source_check

D=pathlib.Path("data")
PARENT=D/"nl2_hu_multiboard_status_v49_b405_rank214_219.json"
PRE=D/"nl2_hu_b409_rank166_three_true_source_flops_pre_cert.json"
B400=D/"nl2_hu_b400_five_cobb_gto_second_three_flops.json"
B407=D/"nl2_hu_b407_r166_two_real_nl2_ip_original_pairs.json"
TRIAGE=D/"nl2_hu_b370_first10_approx_source_triage.json"
STATUS=D/"nl2_hu_multiboard_status_v50_b417_rank166.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v50_b417.json"
AUDIT=D/"nl2_hu_cert_lock_medium_audit_v50_b417.json"
PROOF=D/"nl2_hu_b417_rank166_three_true_source_cert_proof.json"
DOC=pathlib.Path("docs/NL2_HU_B417_R166_THREE_ORIGINAL_TRUE_CERT.md")
TARGET={166:"ln-ipfr-r_model-1spq1ko"}
FLOPS=("Js9h4d","KcJh7d","QhTc5d")
LINE="x b100 c/x x/x"
V50="NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def verified_new_sample(model,flop,board,original,partial,gr,er,rank,sourcepin):
 assert original["status"]==partial["status"]=="GENUINE_RUST_EXACT_SOURCE"
 assert original["preflop_source_SHA256"]==partial["preflop_source_SHA256"]
 assert original["pool_stats_SHA256"]==partial["pool_stats_SHA256"]
 assert sourcepin["original_GTO_source_sha256"] in {c["source_sha256"] for c in original["real_cases"]}
 assert sourcepin["NL2_IP_source_sha256"] in {c["source_sha256"] for c in partial["real_cases"]}
 gc=next(c for c in original["manifest"]["cases"] if c["source_sha256"]==sourcepin["original_GTO_source_sha256"])
 ec=next(c for c in partial["manifest"]["cases"] if c["source_sha256"]==sourcepin["NL2_IP_source_sha256"])
 assert (gc["line"],ec["line"],gc["turn"],ec["turn"])==("x b100 c","x b100 c",gc["turn"],gc["turn"])
 assert (gc["gto_gap_pct"],ec["gto_gap_pct"],ec["hero_gap_pct"]) and ec["hero_gap_pct"] is not None
 assert gc["gto_gap_pct"]<=.5 and ec["gto_gap_pct"]<=.5 and ec["hero_gap_pct"]<=.5
 gm=original["manifest"];em=partial["manifest"]
 fp=gr/"solver/postflop"/gm["file_flop"]
 ep=er/"solver/postflop"/em["file_flop"]
 gfr=read(fp);efr=read(ep)
 gp=gr/"solver/postflop"/gc["source_path"]
 es=er/"solver/postflop"/ec["source_path"]
 assert sha(gp)==gc["source_sha256"] and sha(es)==ec["source_sha256"]
 gd=read(gp);ed=read(es)
 gmask,gstats=game_reach(gfr,gd);emask,estats=game_reach(efr,ed)
 assert gstats["sequential_actor_combo_nodes"]>0 and estats["sequential_actor_combo_nodes"]>0
 def nodal(d,seq):
  rows=[n for n in d["nodes"] if n["board"]==board and n["line"]==LINE and n["player"]==1]
  assert len(rows)==1,(flop,board,len(rows))
  node=rows[0]
  q=seq["|".join((board,LINE,"1"))]
  assert q["count"]>0,(flop,board,"ZERO_STRICT_HERO_IP_SOURCE_COMBOS")
  spr=(d["stack"]-max(node["bets"]))/node["pot"]
  assert abs(spr-model["assumed_model_node_spr"])/max(1,spr)<=.05
  return node,q,spr
 gn,gq,gspr=nodal(gd,gmask)
 en,eq,espr=nodal(ed,emask)
 assert abs(gspr-espr)<1e-5
 assert (gq["count"],eq["count"])==(
  sourcepin["GTO_legal_40_70_hero_IP_combos"],sourcepin["NL2_IP_legal_40_70_hero_combos"])
 assert abs(gspr-sourcepin["actual_spr"])<1e-5
 scope=lock_scope(ed,em["locks"],"exp_ip")
 assert scope["observed_marginal_source_nodes"]>0
 assert scope["villain_decision_nodes"]==scope["observed_marginal_source_nodes"]+scope["imputed_assumption_nodes"]+scope["unmatched_nodes"]
 medium=strict_medium_evidence(gn,gd,gq["mask"])
 assert medium["eligible"]>=0 and (not medium["candidate"] or medium["eligible"]>0)
 lock=dict(version="exp_ip",run_id=45029267778,sha256=ec["source_sha256"],
  source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",
  villain_observed_pattern_node_share_pct=scope["coverage_pct"],
  source_not_real_per_combo_observation=True,
  unknown_history_frequency_filled_with_default=scope["imputed_assumption_nodes"]>0,
  observed_marginal_source_nodes=scope["observed_marginal_source_nodes"],
  assumed_default_source_nodes=scope["imputed_assumption_nodes"],
  unlocked_source_nodes=scope["unmatched_nodes"],
  hero_model_gain_bb=locked_model_gain(ed,"exp_ip"))
 sample=dict(flop=flop,turn=gc["turn"],public_board=board,
  actual_exact_action_line=LINE,acting_seat=1,exact_flop_action="x b100 c",
  actual_pot_bb=gn["pot"]/100,
  actual_effective_stack_bb=(gd["stack"]-max(gn["bets"]))/100,
  actual_spr=gspr,model_assumed_spr=model["assumed_model_node_spr"],
  relative_spr_error_pct=round(100*abs(gspr-model["assumed_model_node_spr"])/max(1,gspr),4),
  genuine_gto_exploitability_pct=gc["gto_gap_pct"],
  source_run_id=45028060598,source_sha256=gc["source_sha256"],
  source_kind="PINNED_PREFLOP_CFR",assumed_preflop_ranges=False,
  exact_combo_reachable=sum(float(w)>1e-4 for w in gn["w"][1]),
  strict_full_street_combo_reachable=gq["count"],exact_node_actions=gn["acts"],
  medium_50pct_eligible_combos=medium["eligible"],
  b50_nonpolarized_relative_equity_research_candidate=medium["candidate"],
  nl2_locked_variants=[lock],flop_texture=texture(flop))
 proof=dict(model_rank=rank,flop=flop,public_board=board,turn=gc["turn"],
  original_GTO_run=45028060598,actual_NL2_IP_run=45029267778,
  original_GTO_SHA256=gc["source_sha256"],actual_NL2_SHA256=ec["source_sha256"],
  GTO_strict_combos=gq["count"],NL2_strict_combos=eq["count"],
  original_Rust_root_SHA256=original["root_original_Rust_SHA256"],
  real_NL2_IP_root_SHA256=partial["root_original_Rust_SHA256"],
  exact_action_line=LINE,acting_seat=1,actual_spr=gspr,
  observed_marginal_source_nodes=scope["observed_marginal_source_nodes"],
  assumed_source_nodes=scope["imputed_assumption_nodes"],
  unmatched_unlocked_nodes=scope["unmatched_nodes"],
  only_exact_named_public_board=True)
 return sample,proof

def patch_ui(path):
 text=path.read_text(encoding="utf-8")
 marker="const v49b405=d=>{"
 assert text.count(marker)==1
 validator="""const v50b417=d=>{
 const q=d.B417_rank166_three_true_original_GTO_NL2_IP_flops;
 const r=d.records?.['ln-ipfr-r_model-1spq1ko'];
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166'||
  d.CERT_MULTIBOARD!==163||d.APPROX!==229||d.EST!==0||d.TOTAL!==392||
  !q||q.rank!==166||q.spot!=='CO_BB'||q.actor!=='CO_IP'||
  q.line!=='x b100 c/x x/x'||q.flops?.join(',')!=='Js9h4d,KcJh7d,QhTc5d'||
  q.pins?.length!==3||q.pins.some(z=>z.GTO_strict_combos<=0||
   z.NL2_strict_combos<=0||z.original_GTO_SHA256?.length!==64||z.actual_NL2_SHA256?.length!==64)||
  r?.label!=='CERT-MULTIBOARD'||r?.frequency_rank!==166||
  r?.solver_profile!=='CO_BB'||r?.proven_exact_board_count!==3||
  r.certified_3_to_5_exact_flop_boards?.length!==3||
  r.certified_3_to_5_exact_flop_boards.some(z=>
   z.acting_seat!==1||z.actual_exact_action_line!=='x b100 c/x x/x'||
   z.strict_full_street_combo_reachable<=0||z.relative_spr_error_pct>5||
   !z.nl2_locked_variants?.some(v=>v.version==='exp_ip'&&v.sha256?.length===64))||
  d.no_generic_texture_GTO!==true||d.PR2_remains_draft_never_merge!==true)
   throw Error('B417 exact rank166 genuine original three-flop sources failclosed');
 return d;
};
"""
 text=text.replace(marker,validator+marker)
 old="return fetch('data/nl2_hu_multiboard_status_v49_b405_rank214_219.json',{cache:'no-store'}).then(open).then(v49b405)"
 new="return fetch('data/nl2_hu_multiboard_status_v50_b417_rank166.json',{cache:'no-store'}).then(open).then(v50b417)\\n    .catch(()=>fetch('data/nl2_hu_multiboard_status_v49_b405_rank214_219.json',{cache:'no-store'}).then(open).then(v49b405))"
 assert text.count(old)==1
 text=text.replace(old,new.replace('\\n','\n'))
 oldschema="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219','NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107'"
 assert text.count(oldschema)==1
 text=text.replace(oldschema,"'"+V50+"',"+oldschema)
 if path.name=="nl2-multiboard.js":
  oldm="fetch('data/nl2_hu_cert_lock_medium_matrix_v49_b405.json',{cache:'no-store'}).catch"
  assert text.count(oldm)==1
  text=text.replace(oldm,"fetch('data/nl2_hu_cert_lock_medium_matrix_v50_b417.json',{cache:'no-store'}).catch(()=>fetch('data/nl2_hu_cert_lock_medium_matrix_v49_b405.json',{cache:'no-store'})).catch")
  old49="status?.schema==='NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219'"
  if text.count(old49)==1:text=text.replace(old49,"['NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219','"+V50+"'].includes(status?.schema)")
  oldlist="['NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219'].includes(status?.schema)"
  if text.count(oldlist)==1:text=text.replace(oldlist,"['NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219','"+V50+"'].includes(status?.schema)")
 path.write_text(text,encoding="utf-8")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--gto-root",required=True,type=pathlib.Path)
 p.add_argument("--exp-root",required=True,type=pathlib.Path)
 a=p.parse_args()
 parent=read(PARENT);pre=read(PRE);src=read(B407);gto=read(B400)
 assert (parent["CERT_MULTIBOARD"],parent["APPROX"],parent["EST"],parent["TOTAL"])==(162,230,0,392)
 assert parent["records"]["ln-ipfr-r_model-1t7q0mn"]["label"]=="CERT-MULTIBOARD"
 assert parent["records"]["ln-ipfr-r_model-kp19if"]["label"]=="CERT-MULTIBOARD"
 assert pre["schema"]=="NL2_B409_RANK166_THREE_TRUE_GTO_NL2_IP_SOURCE_READY_V1"
 assert pre["source_blind_first10_preregistered"] and pre["independent_raw_artifact_SHA_matrix_frontend_HU2475_gate_still_required"]
 assert pre["genuine_distinct_original_flops"]==list(FLOPS)
 assert pre["source_V49_status_sha256"]==sha(PARENT)
 assert pre["original_B400_GTO_source_sha256"]==sha(B400)
 assert pre["new_B407_NL2_Rust_source_sha256"]==sha(B407)
 assert (pre["model_id"],pre["frequency_rank"],pre["spot"],pre["actor"],pre["exact_line"])==(
  TARGET[166],166,"CO_BB","CO_IP",LINE)
 assert src["schema"]=="NL2_B407_RANK166_TWO_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIRS_V1"
 assert src["new_distinct_qualifying_flops_by_rank"]["166"]==["KcJh7d","QhTc5d"]
 assert (src["original_GTO_run"],src["new_NL2_IP_run"])==(45028060598,45029267778)
 assert src["B400_frozen_original_GTO_source_sha256"]==sha(B400)
 assert gto["original_run_id"]==45028060598
 old=parent["records"][TARGET[166]]
 assert (old["label"],old["solver_profile"],old["frequency_rank"],old["street"])==("APPROX","CO_BB",166,2)
 original_paths=[pathlib.Path(x) for x in parent["source_evidence"]["source_files"]]
 assert all(x.is_file() for x in original_paths)
 idx,locked,_=build_source_index(D,original_paths)
 historical=next(x for x in read(TRIAGE)["source_blind_selected_ten"] if x["frequency_rank"]==166)["strictly_measured_pairs"][0]
 model=dict(family=old["family"],spot=old["solver_profile"],street=old["street"],
  preflop_text=old["preflop_text"],abstract_action_history=old["abstract_action_history"],
  approx_spr=old["assumed_model_node_spr"])
 candidates_original,reason=candidates(model,idx,locked,None)
 assert reason is None
 prior=[z for z in candidates_original if z["flop"]=="Js9h4d" and z["public_board"]==historical["exact_public_board"]
  and z["source_sha256"]==historical["gto_source_sha256"]
  and any(v["version"]=="exp_ip" and v["sha256"]==historical["nl2_hero_lock_sha256"] for v in z["nl2_locked_variants"])]
 assert prior,("rank166 immutable historic source absent")
 h=copy.deepcopy(prior[0]);h["flop_texture"]=texture(h["flop"])
 h["nl2_locked_variants"]=[v for v in h["nl2_locked_variants"] if v["version"]=="exp_ip" and v["sha256"]==historical["nl2_hero_lock_sha256"]][:1]
 assert len(h["nl2_locked_variants"])==1 and h["strict_full_street_combo_reachable"]>=historical["strict_legal_combo_count"]>0
 pins=[dict(model_rank=166,flop="Js9h4d",public_board=h["public_board"],turn=h["turn"],
  original_GTO_run=h["source_run_id"],actual_NL2_IP_run=h["nl2_locked_variants"][0]["run_id"],
  original_GTO_SHA256=h["source_sha256"],actual_NL2_SHA256=h["nl2_locked_variants"][0]["sha256"],
  GTO_strict_combos=h["strict_full_street_combo_reachable"],NL2_strict_combos=historical["strict_legal_combo_count"],
  exact_action_line=LINE,acting_seat=1,actual_spr=h["actual_spr"],only_exact_named_public_board=True)]
 selected=[h]
 provided=pre["original_paired_source_pins"]
 assert len(provided)==3 and [x["flop"] for x in provided]==list(FLOPS)
 assert pins[0]["original_GTO_SHA256"]==provided[0]["genuine_GTO_sha256"]
 assert pins[0]["actual_NL2_SHA256"]==provided[0]["actual_NL2_IP_sha256"]
 for z in provided[1:]:
  flop=z["flop"]
  srcrow=next(r for r in gto["real_original_GTO_only_solve_sources"] if r["flop"]==flop)
  assert srcrow["source_status"]=="ORIGINAL_GTO_ANY_TARGET_POSITIVE"
  gp=a.gto_root/f"nl2-multiboard-B400_COBB_FIVE_GTO_FIRST-CO_BB-{flop}-gto"
  ep=a.exp_root/f"nl2-multiboard-B407_R166_NL2_IP-CO_BB-{flop}-exp_ip"
  G=source_check(gp,flop,"gto",srcrow)
  E=source_check(ep,flop,"exp_ip",None)
  assert G and E and G["status"]==E["status"]=="GENUINE_RUST_EXACT_SOURCE"
  assert len(G["real_cases"])==len(E["real_cases"])==2
  converted=dict(original_GTO_source_sha256=z["genuine_GTO_sha256"],
   NL2_IP_source_sha256=z["actual_NL2_IP_sha256"],
   GTO_legal_40_70_hero_IP_combos=z["genuine_GTO_strict_40_70_combos"],
   NL2_IP_legal_40_70_hero_combos=z["actual_NL2_IP_strict_40_70_combos"],
   actual_spr=z["actual_spr"])
  sample,pin=verified_new_sample(old,flop,z["exact_public_board"],G,E,gp,ep,166,converted)
  selected.append(sample);pins.append(pin)
 assert [z["flop"] for z in selected]==list(FLOPS)
 assert len({texture(z["flop"]) for z in selected})>=2
 new=copy.deepcopy(parent)
 r=copy.deepcopy(old)
 r.update(label="CERT-MULTIBOARD",high_frequency_preregistered=True,
  original_top24_high_frequency_preregistered=False,
  source_blind_expansion_rank=166,source_blind_expansion_preregistered=True,
  prereg_cohort="B370_FIRST10_ORIGINAL_100BB_CO_IP_THREE_ACTUAL_FLOPS",
  certified_3_to_5_exact_flop_boards=selected,proven_exact_board_count=3,
  blocked_reason=None,source_credibility="GITHUB_ACTIONS_AUTHENTIC_FULL100BB_SHA_NL2_IP_PARTIAL_LOCK_40_70")
 new["records"][TARGET[166]]=r
 new.update(schema=V50,CERT_MULTIBOARD=163,APPROX=229,EST=0,TOTAL=392,
  parent_V49_sha256=sha(PARENT),B409_preregistered_source_sha256=sha(PRE),
  supplementary_cert_count=parent["supplementary_cert_count"]+1,
  source_blind_expansion_ranks=sorted(set(parent["source_blind_expansion_ranks"]+[166])),
  original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
  no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True,
  B417_rank166_three_true_original_GTO_NL2_IP_flops=dict(rank=166,model_id=TARGET[166],
    spot="CO_BB",actor="CO_IP",line=LINE,flops=list(FLOPS),
    source_blind_first10_preregistered=True,
    B409_source_pre_cert_sha256=sha(PRE),B407_original_exp_source_sha256=sha(B407),
    pins=pins,only_exact_public_board_not_generic_texture=True))
 STATUS.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n")
 auditPath=pathlib.Path("tools/hu_cert_lock_medium_audit.py")
 originalAudit=auditPath.read_text(encoding="utf-8")
 marker="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219')"
 assert originalAudit.count(marker)==1
 auditPath.write_text(originalAudit.replace(marker,
  "'NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219','"+V50+"')"),encoding="utf-8")
 import importlib,hu_cert_lock_medium_audit as source_audit,hu_cert_lock_medium_coverage_matrix as med
 source_audit=importlib.reload(source_audit);med.audit=source_audit.audit
 checked=source_audit.audit(new)
 assert (checked["cert_multiboard"],checked["approx"],checked["EST"])==(163,229,0)
 assert (checked["aggregate"]["named_board_proofs"],checked["aggregate"]["paired_hero_locked_source_variants"])==(618,710)
 matrix=med.create(new)
 assert (len(matrix["models"]),len(matrix["boards"]))==(163,618)
 unknown=sum(1 for b in matrix["boards"] for l in b["hero_lock_proofs"]
  if l["node_rate_data_status"]=="HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN")
 assert unknown==0
 matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V50_B417",
  V50_status_sha256=sha(STATUS),source_unknown_variants_after=0,
  original_Rust_rank166_three_GTO_NL2_IP_sources=True,
  no_private_card_conditional_NL2_opponent_observation_claim=True,PR2_Draft_NEVER_MERGE=True)
 MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
 AUDIT.write_text(json.dumps(checked,ensure_ascii=False,indent=2)+"\n")
 PROOF.write_text(json.dumps(dict(schema="NL2_B417_RANK166_THREE_GENUINE_GTO_NL2_IP_CERT_SOURCE_V1",
  rank=166,source_pins=pins,
  original_V49_sha256=sha(PARENT),source_B409_sha256=sha(PRE),
  original_100bb_rust_actual_GTO_and_NL2_IP_same_public_line_SPR=True,
  all_three_flop_strict_40_70_hero_combo_positive=True,
  no_generic_texture_GTO=True,no_observed_NL2_private_card_action_rates=True,
  CERT_before=162,CERT_after=163,APPROX_before=230,APPROX_after=229,EST=0,
  named_boards_before=615,named_boards_after=618,
  hero_lock_variants_before=707,hero_lock_variants_after=710,
  unknown_lock_denominators_after=0,
  V50_status_sha256=sha(STATUS),V50_matrix_sha256=sha(MATRIX),V50_audit_sha256=sha(AUDIT),
  PR2_draft_never_merge=True),ensure_ascii=False,indent=2)+"\n")
 for file in ("nl2_hu_multiboard_ui.js","nl2-multiboard.js"):patch_ui(pathlib.Path(file))
 for file in ("nl2.html","nl2-multiboard.html"):
  path=pathlib.Path(file);txt=path.read_text(encoding="utf-8")
  tags=("task-hybrid-b405-v49-20261122","task-hybrid-b414-persistent-20261122")
  matches=[t for t in tags if t in txt]
  assert len(matches)==1 and txt.count(matches[0])==1
  path.write_text(txt.replace(matches[0],"task-hybrid-b417-v50-20261122"),encoding="utf-8")
 p=pathlib.Path("tools/hu_b378_v47_loader_runtime_test.cjs")
 txt=p.read_text(encoding="utf-8")
 old="|414-persistent)-20261122"
 assert txt.count(old)==1
 p.write_text(txt.replace(old,"|414-persistent|417-v50)-20261122"),encoding="utf-8")
 DOC.write_text("# B417 rank166: independent full100bb GTO and NL2-IP exact 3-flop source certification\n\n"
  "Only named Js9h4d, KcJh7d and QhTc5d exact original public boards, CO IP x b100 c/x x/x "
  "action history, full-street strict hero combo reach and GTO gap <=0.5%, plus actual partially "
  "NL2 pool-marginal locked Rust sources on identical boards. Opponent pool marginals are NOT "
  "individual private-hand conditional decisions. 50%-pot depolarized research only for exact "
  "named boards with verified eligibility; no generic texture extrapolation. "
  "**163 CERT /229 APPROX /0 EST**, 618 named boards, 710 NL2 locked source variants, UNKNOWN=0. "
  "Independent full 2475 HU routes and UI Actions must PASS. PR2 draft/unmerged.\n")
 print("PASS B417 independent original Rust 3 flops CO_BB rank166: 163 CERT /229 APPROX, 618 boards, 710 locks UNKNOWN0")
if __name__=="__main__":main()
