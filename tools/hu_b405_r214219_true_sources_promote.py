#!/usr/bin/env python3
"""B405: independent original SHA-verified two CO_BB models rank214/219 CERT.
Three distinct exact original 100bb GTO plus genuine NL2-IP partially locked
runouts each, full-street max/40%-70% combo reach; never certify generic texture.
"""
import argparse,copy,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,texture
from hu_sequential_cfr_reach import game_reach
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create
from verify_hu_multiboard_100bb import strict_medium_evidence,lock_scope,locked_model_gain
from hu_b396_rank214_219_true_co_ip_pairs import check as source_check

D=pathlib.Path("data")
PARENT=D/"nl2_hu_multiboard_status_v48_b390_rank107.json"
PRE=D/"nl2_hu_b404_r214219_three_true_flop_pre_cert_gate.json"
B393=D/"nl2_hu_b393_five_cobb_gto_first_three_flops.json"
B396=D/"nl2_hu_b396_r214_219_two_real_nl2_ip_original_pairs.json"
TRIAGE=D/"nl2_hu_b370_first10_approx_source_triage.json"
STATUS=D/"nl2_hu_multiboard_status_v49_b405_rank214_219.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v49_b405.json"
AUDIT=D/"nl2_hu_cert_lock_medium_audit_v49_b405.json"
PROOF=D/"nl2_hu_b405_rank214_219_two_three_source_cert_proof.json"
DOC=pathlib.Path("docs/NL2_HU_B405_R214_R219_THREE_TRUE_CERT.md")
TARGET={214:"ln-ipfr-r_model-1t7q0mn",219:"ln-ipfr-r_model-kp19if"}
FLOPS=("Js9h4d","KsQh4d","Js9h5d")
LINE="x b100 c/x b50 c/x"
V49="NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219"
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
 lock=dict(version="exp_ip",run_id=45027557999,sha256=ec["source_sha256"],
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
  source_run_id=45026396521,source_sha256=gc["source_sha256"],
  source_kind="PINNED_PREFLOP_CFR",assumed_preflop_ranges=False,
  exact_combo_reachable=sum(float(w)>1e-4 for w in gn["w"][1]),
  strict_full_street_combo_reachable=gq["count"],exact_node_actions=gn["acts"],
  medium_50pct_eligible_combos=medium["eligible"],
  b50_nonpolarized_relative_equity_research_candidate=medium["candidate"],
  nl2_locked_variants=[lock],flop_texture=texture(flop))
 proof=dict(model_rank=rank,flop=flop,public_board=board,turn=gc["turn"],
  original_GTO_run=45026396521,actual_NL2_IP_run=45027557999,
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
 marker="const v48b390=d=>{"
 assert text.count(marker)==1
 validator="""const v49b405=d=>{
 const q=d.B405_r214219_three_true_original_GTO_NL2_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219'||
  d.CERT_MULTIBOARD!==162||d.APPROX!==230||d.EST!==0||d.TOTAL!==392||
  !q||q.ranks?.join(',')!=='214,219'||
  q.spot!=='CO_BB'||q.actor!=='CO_IP'||q.line!=='x b100 c/x b50 c/x'||
  q.authenticated_sources_by_rank?.length!==2||
  q.authenticated_sources_by_rank.some(item=>
    ![214,219].includes(item.rank)||item.pins?.length!==3||
    item.pins.some(pin=>pin.GTO_strict_combos<=0||pin.NL2_strict_combos<=0||
      pin.original_GTO_SHA256?.length!==64||pin.actual_NL2_SHA256?.length!==64))||
  [214,219].some(rank=>{
    const r=Object.values(d.records||{}).find(x=>x.frequency_rank===rank);
    return !r||r.label!=='CERT-MULTIBOARD'||r.proven_exact_board_count!==3||
      r.solver_profile!=='CO_BB'||r.certified_3_to_5_exact_flop_boards?.length!==3||
      r.certified_3_to_5_exact_flop_boards.some(z=>
        z.acting_seat!==1||z.strict_full_street_combo_reachable<=0||
        z.actual_exact_action_line!=='x b100 c/x b50 c/x'||
        z.relative_spr_error_pct>5||
        !z.nl2_locked_variants?.some(v=>v.version==='exp_ip'&&v.sha256?.length===64));
  })||
  d.no_generic_texture_GTO!==true||d.PR2_remains_draft_never_merge!==true)
   throw Error('B405 exact 3-flop original GTO/NL2 IP source failclosed');
 return d;
};
"""
 text=text.replace(marker,validator+marker)
 old="return fetch('data/nl2_hu_multiboard_status_v48_b390_rank107.json',{cache:'no-store'}).then(open).then(v48b390)"
 new="return fetch('data/nl2_hu_multiboard_status_v49_b405_rank214_219.json',{cache:'no-store'}).then(open).then(v49b405)\n    .catch(()=>fetch('data/nl2_hu_multiboard_status_v48_b390_rank107.json',{cache:'no-store'}).then(open).then(v48b390))"
 assert text.count(old)==1
 text=text.replace(old,new)
 oldschema="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B369_RANK27'"
 assert text.count(oldschema)==1
 text=text.replace(oldschema,"'"+V49+"',"+oldschema)
 if path.name=="nl2-multiboard.js":
  oldm="fetch('data/nl2_hu_cert_lock_medium_matrix_v48_b390.json',{cache:'no-store'}).catch"
  assert text.count(oldm)==1
  text=text.replace(oldm,"fetch('data/nl2_hu_cert_lock_medium_matrix_v49_b405.json',{cache:'no-store'}).catch(()=>fetch('data/nl2_hu_cert_lock_medium_matrix_v48_b390.json',{cache:'no-store'})).catch")
  oldschema="status?.schema==='NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107'){"
  assert text.count(oldschema)==1
  text=text.replace(oldschema,"['NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','"+V49+"'].includes(status?.schema)){")
 path.write_text(text,encoding="utf-8")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--gto-root",required=True,type=pathlib.Path)
 p.add_argument("--exp-root",required=True,type=pathlib.Path)
 a=p.parse_args()
 parent=read(PARENT);pre=read(PRE);src=read(B396);gto=read(B393)
 assert (parent["CERT_MULTIBOARD"],parent["APPROX"],parent["EST"],parent["TOTAL"])==(160,232,0,392)
 assert parent["records"]["ln-ipfr-r_model-ujl14x"]["label"]=="CERT-MULTIBOARD"
 assert pre["schema"]=="NL2_B404_RANK214219_THREE_AUTHENTIC_GTO_NL2_IP_SOURCE_PRECERT_V1"
 assert pre["ranks_with_three_full_street_40_70_positive_flops"]==[214,219]
 assert pre["readiness_only_no_CERT_upgrade"]
 assert pre["source_V48_status_sha256"]==sha(PARENT)
 assert pre["B396_true_NL2_IP_pair_proof_sha256"]==sha(B396)
 assert src["new_distinct_qualifying_flops_by_rank"]["214"]==["Js9h5d","KsQh4d"]
 assert src["new_distinct_qualifying_flops_by_rank"]["219"]==["Js9h5d","KsQh4d"]
 assert src["B393_frozen_original_GTO_source_sha256"]==sha(B393)
 original_index_paths=[pathlib.Path(x) for x in parent["source_evidence"]["source_files"]]
 assert all(path.is_file() for path in original_index_paths)
 idx,locked,_=build_source_index(D,original_index_paths)
 triage=read(TRIAGE)
 loaded={}
 for flop in ("KsQh4d","Js9h5d"):
  src_row=next(x for x in gto["real_original_GTO_only_solve_sources"] if x["flop"]==flop)
  gr=a.gto_root/f"nl2-multiboard-B393_COBB_FIVE_GTO_FIRST-CO_BB-{flop}-gto"
  er=a.exp_root/f"nl2-multiboard-B396_R214219_NL2_IP-CO_BB-{flop}-exp_ip"
  G=source_check(gr,flop,"gto",src_row)
  E=source_check(er,flop,"exp_ip",None)
  assert G and E and G["status"]==E["status"]=="GENUINE_RUST_EXACT_SOURCE"
  assert len(G["real_cases"])==len(E["real_cases"])==2
  loaded[flop]=(G,E,gr,er)
 new=copy.deepcopy(parent);pins=[];extra_proofs={}
 for rank,mid in TARGET.items():
  old=parent["records"][mid]
  assert (old["label"],old["solver_profile"],old["frequency_rank"],old["street"])==("APPROX","CO_BB",rank,2)
  original=next(z for z in triage["source_blind_selected_ten"] if z["frequency_rank"]==rank)["strictly_measured_pairs"][0]
  model=dict(family=old["family"],spot=old["solver_profile"],street=old["street"],
   preflop_text=old["preflop_text"],abstract_action_history=old["abstract_action_history"],
   approx_spr=old["assumed_model_node_spr"])
  candidates_original,reason=candidates(model,idx,locked,None)
  assert reason is None
  first=[z for z in candidates_original if z["flop"]=="Js9h4d"
   and z["public_board"]==original["exact_public_board"]
   and z["source_sha256"]==original["gto_source_sha256"]
   and any(v["version"]=="exp_ip" and v["sha256"]==original["nl2_hero_lock_sha256"] for v in z["nl2_locked_variants"])]
  assert first,(rank,"no historical real paired 100bb source")
  h=copy.deepcopy(first[0]);h["flop_texture"]=texture(h["flop"])
  h["nl2_locked_variants"]=[v for v in h["nl2_locked_variants"] if v["version"]=="exp_ip" and v["sha256"]==original["nl2_hero_lock_sha256"]][:1]
  assert len(h["nl2_locked_variants"])==1 and h["strict_full_street_combo_reachable"]>0
  selected=[h];proofs=[dict(model_rank=rank,flop=h["flop"],public_board=h["public_board"],turn=h["turn"],
   original_GTO_run=h["source_run_id"],actual_NL2_IP_run=h["nl2_locked_variants"][0]["run_id"],
   original_GTO_SHA256=h["source_sha256"],actual_NL2_SHA256=h["nl2_locked_variants"][0]["sha256"],
   GTO_strict_combos=h["strict_full_street_combo_reachable"],NL2_strict_combos=original["strict_legal_combo_count"],
   exact_action_line=LINE,acting_seat=1,actual_spr=h["actual_spr"],
   only_exact_named_public_board=True)]
  fproof=pre["eligible_rank_source_triples"][str(rank)]["three_authentic_distinct_flop_sources"]
  assert [v["flop"] for v in fproof]==list(FLOPS)
  assert fproof[0]["original_GTO_source_sha256"]==proofs[0]["original_GTO_SHA256"]
  assert fproof[0]["NL2_IP_source_sha256"]==proofs[0]["actual_NL2_SHA256"]
  for source_pin in fproof[1:]:
   flop=source_pin["flop"]
   G,E,gr,er=loaded[flop]
   sample,proof=verified_new_sample(old,flop,source_pin["public_board"],G,E,gr,er,rank,source_pin)
   selected.append(sample);proofs.append(proof)
  assert {z["flop"] for z in selected}==set(FLOPS)
  assert len({texture(z["flop"]) for z in selected})>=2
  record=copy.deepcopy(old)
  record.update(label="CERT-MULTIBOARD",high_frequency_preregistered=True,
    original_top24_high_frequency_preregistered=False,
    source_blind_expansion_rank=rank,source_blind_expansion_preregistered=True,
    prereg_cohort="B370_FIRST10_ORIGINAL_GTO_NL2_CO_BB_THREE_EXACT_SOURCE_FLOPS",
    certified_3_to_5_exact_flop_boards=selected,proven_exact_board_count=3,
    blocked_reason=None,source_credibility="GITHUB_ACTIONS_ORIGINAL_FULL100BB_SHA_AND_ACTUAL_NL2_IP_PARTIAL_LOCK_40_70")
  new["records"][mid]=record
  pins.append(dict(rank=rank,model_id=mid,pins=proofs))
  extra_proofs[str(rank)]=dict(new_source_flops=[z["flop"] for z in selected],source_run_gto=45026396521,
     source_run_NL2_IP=45027557999,nonextrapolated_co_actor_IP=True)
 new.update(schema=V49,CERT_MULTIBOARD=162,APPROX=230,EST=0,TOTAL=392,
  parent_V48_SHA256=sha(PARENT),B404_preregistered_three_flop_source_sha256=sha(PRE),
  supplementary_cert_count=parent["supplementary_cert_count"]+2,
  source_blind_expansion_ranks=sorted(set(parent["source_blind_expansion_ranks"]+[214,219])),
  original_top24_cutoff_unchanged=True,
  no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
  PR2_remains_draft_never_merge=True,
  B405_r214219_three_true_original_GTO_NL2_IP_flops=dict(
   ranks=[214,219],spot="CO_BB",actor="CO_IP",line=LINE,
   flops=list(FLOPS),source_blind_first10_preregistered=True,
   B396_genuine_source_SHA256=sha(B396),B404_pre_cert_SHA256=sha(PRE),
   authenticated_sources_by_rank=pins,only_exact_board_GTO_not_generic_texture=True))
 STATUS.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n")
 auditPath=pathlib.Path("tools/hu_cert_lock_medium_audit.py")
 content=auditPath.read_text(encoding="utf-8")
 old_allow="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107')"
 assert content.count(old_allow)==1
 auditPath.write_text(content.replace(old_allow,
  "'NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','"+V49+"')"),encoding="utf-8")
 checked=audit(new)
 assert (checked["cert_multiboard"],checked["approx"],checked["EST"])==(162,230,0)
 assert (checked["aggregate"]["named_board_proofs"],checked["aggregate"]["paired_hero_locked_source_variants"])==(615,705)
 matrix=create(new)
 assert (len(matrix["models"]),len(matrix["boards"]))==(162,615)
 unknown=sum(1 for z in matrix["boards"] for v in z["hero_lock_proofs"]
  if v["node_rate_data_status"]=="HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN")
 assert unknown==0
 matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V49_B405",
  V49_status_sha256=sha(STATUS),source_unknown_variants_after=0,
  true_40_70_full100bb_CO_IP_source_rank214_219=True,
  no_private_card_conditional_opponent_NL2_frequency_claim=True,
  PR2_Draft_NEVER_MERGE=True)
 MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
 AUDIT.write_text(json.dumps(checked,ensure_ascii=False,indent=2)+"\n")
 PROOF.write_text(json.dumps(dict(schema="NL2_B405_R214_219_TWO_MODELS_SIX_ORIGINAL_GTO_NL2_IP_CERT_BOARDS_V1",
  parent_V48_status_SHA256=sha(PARENT),B404_source_pre_cert_SHA256=sha(PRE),
  model_source_pins=pins,extra_proofs=extra_proofs,
  true_original_full100bb_CFR_source_and_40_70_check=True,
  same_exact_actor_line_SPR_and_paired_NL2_IP_hero_lock=True,
  only_named_board_no_generic_texture_GTO=True,no_NL2_villain_private_hand_observations=True,
  CERT_before=160,CERT_after=162,APPROX_before=232,APPROX_after=230,EST=0,
  named_boards_before=609,named_boards_after=615,
  locked_hero_variants_before=701,locked_hero_variants_after=705,
  unknown_lock_denominators_after=0,
  V49_status_sha256=sha(STATUS),V49_matrix_sha256=sha(MATRIX),V49_audit_sha256=sha(AUDIT),
  PR2_draft_never_merge=True),ensure_ascii=False,indent=2)+"\n")
 for p in (pathlib.Path("nl2_hu_multiboard_ui.js"),pathlib.Path("nl2-multiboard.js")):patch_ui(p)
 for filename in ("nl2.html","nl2-multiboard.html"):
  p=pathlib.Path(filename);s=p.read_text(encoding="utf-8")
  if "task-hybrid-b392-persistent-r107-20261122" in s:
   assert s.count("task-hybrid-b392-persistent-r107-20261122")==1
   s=s.replace("task-hybrid-b392-persistent-r107-20261122","task-hybrid-b405-v49-20261122")
  else:
   assert s.count("task-hybrid-b390-v48-20261122")==1
   s=s.replace("task-hybrid-b390-v48-20261122","task-hybrid-b405-v49-20261122")
  p.write_text(s,encoding="utf-8")
 regression=pathlib.Path("tools/hu_b378_v47_loader_runtime_test.cjs")
 txt=regression.read_text()
 old="378-v47-loaderfix|390-v48|392-persistent-r107"
 assert txt.count(old)==1
 regression.write_text(txt.replace(old,"378-v47-loaderfix|390-v48|392-persistent-r107|405-v49"))
 DOC.write_text("# B405 2 new CO_BB CERT models: rank214/219 exact three source flops each\n\n"
  "Rank214/219 matched historical Js9h4d and newly authenticated KsQh4d + Js9h5d. "
  "Each of the 6 named public boards has genuine original full-100bb GTO and true NL2-IP partly "
  "locked source SHA, exact CO-IP x b100 c/x b50 c/x, positive strict max/40%-70% "
  "hero combo reach, and <=5% SPR difference. "
  "Observed NL2 sources are pooled street/size marginals, not villain private-card conditional behavior. "
  "b50 depolarization applies only where the exact public-board source supports it, never to unsupported textures. "
  "**162 CERT /230 APPROX /0 EST**, 615 exact boards and 705 partial locked source variants; UNKNOWN=0, "
  "subject to full HU2475, frontend and source Actions gate. PR #2 DRAFT and never merge.\n")
 print("PASS B405 original CO-IP 2 rank three-GTO/NL2-source upgrade, 162 CERT 230 APPROX, 615 boards 705 locks UNKNOWN=0")
if __name__=="__main__":main()
