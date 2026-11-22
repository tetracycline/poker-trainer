#!/usr/bin/env python3
"""B427: rank216/218 each get three exact original GTO + actual NL2-IP partial-lock flop sources.
Only named boards, exact CO-IP line, full-street sequential 40/70 hero combos, same SPR.
No generic texture, no villain private-card observation claims, no blanket 50% GTO.
"""
import argparse,copy,hashlib,importlib,json,pathlib
from hu_b421_rank216_218_true_co_ip_pairs import check as source_check
from hu_sequential_cfr_reach import game_reach
from hu_multiboard_promote import texture
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create
from verify_hu_multiboard_100bb import strict_medium_evidence,lock_scope,locked_model_gain

D=pathlib.Path("data")
PARENT=D/"nl2_hu_multiboard_status_v50_b417_rank166.json"
TRIAGE=D/"nl2_hu_b370_first10_approx_source_triage.json"
B393=D/"nl2_hu_b393_five_cobb_gto_first_three_flops.json"
B400=D/"nl2_hu_b400_five_cobb_gto_second_three_flops.json"
B412=D/"nl2_hu_b412_r216218_one_real_nl2_ip_original_pair.json"
B421=D/"nl2_hu_b421_r216218_one_real_nl2_ip_original_pair.json"
PRE=D/"nl2_hu_b427_r216218_three_true_source_pre_cert_gate.json"
STATUS=D/"nl2_hu_multiboard_status_v51_b427_rank216_218.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v51_b427.json"
AUDIT=D/"nl2_hu_cert_lock_medium_audit_v51_b427.json"
PROOF=D/"nl2_hu_b427_rank216218_three_true_source_cert_proof.json"
DOC=pathlib.Path("docs/NL2_HU_B427_R216218_THREE_TRUE_SOURCE_CERT.md")
TARGET={216:"ln-ipfr-r_model-7kv23r",218:"ln-ipfr-r_model-h0c7q7"}
FLOPS=("Js9h4d","Td8h3c","Js9h5d")
LINE="x b50 c/x b50 c/x"
V51="NL2_HU_392_MULTIBOARD_CERT_STATUS_V51_B427_R216_R218"
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"

def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def legacy_b2_check(root,flop,version,expected_sub_sha):
 """Authenticate the original B2 CO_BB artifact whose run-level verifier was skipped
 because an unrelated SB3_BTN job failed; both target CO_BB jobs themselves succeeded.
 """
 mp=root/"evidence"/f"CO_BB-{version}-{flop}.json"
 assert mp.is_file(),("B2 original evidence manifest missing",mp)
 assert (root/"evidence/poker-solver-pinned-SHA.txt").read_text().strip()==PIN
 assert (root/"evidence/rust-engine-pin-SHA.txt").read_text().strip()==RUST
 m=read(mp)
 assert (m["schema"],m["spot"],m["pot_family"],m["version"],m["flop"])==(
  "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","CO_BB","SRP",version,flop)
 assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
 assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
 assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
 assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
 assert "x b50 c" in m["selected_lines"] and len(m["turns"])==1
 assert not m["failures"] and m["solved_cases"]==len(m["cases"])
 fp=root/"solver/postflop"/m["file_flop"]
 assert fp.is_file() and sha(fp)==m["file_flop_sha256"]
 fr=read(fp);assert (fr["flop"],fr["pot"],fr["stack"])==(flop,550,9750)
 expected_status="GTO_EXACT_ONLY" if version=="gto" else "NL2_IMPUTED_MARGINAL_LOCKED_EXPERIMENT"
 real=[]
 for c in m["cases"]:
  if c["line"]!="x b50 c" or c["source_sha256"]!=expected_sub_sha:continue
  assert c["status"]==expected_status
  assert c["gto_gap_pct"] is not None and 0<=c["gto_gap_pct"]<=.5
  if version=="gto":assert c["hero_gap_pct"] is None
  else:assert c["hero_gap_pct"] is not None and 0<=c["hero_gap_pct"]<=.5
  sub=root/"solver/postflop"/c["source_path"]
  assert sub.is_file() and sha(sub)==c["source_sha256"]
  d=read(sub);assert (d["flop"],d["turn"],d["line0"])==(flop,c["turn"],"x b50 c")
  seq,stats=game_reach(fr,d);nodes={}
  for n in d["nodes"]:
   if n["player"]!=1 or n["line"]!=LINE or len(n["board"])!=10:continue
   q=seq["|".join((n["board"],n["line"],"1"))]
   nodes[n["board"]]=dict(public_board=n["board"],
    strict_40_70_IP_hero_combos=q["count"],
    exact_SPR=round((d["stack"]-max(n["bets"]))/n["pot"],6),
    parent_actor_decisions=q["parent_actor_decisions"])
  real.append(dict(line=c["line"],turn=c["turn"],source_sha256=c["source_sha256"],
   original_GTO_gap_pct=c["gto_gap_pct"],original_hero_gap_pct=c["hero_gap_pct"],
   actor_IP_target_nodes=nodes,strict_fullstreet_reach_stats=dict(stats)))
 assert len(real)==1,("B2 exact original source case absent or ambiguous",flop,version,expected_sub_sha)
 return dict(status="GENUINE_RUST_EXACT_SOURCE",manifest_sha256=sha(mp),
  root_original_Rust_SHA256=sha(fp),preflop_source_SHA256=m["preflop_ranges"]["full_sha256"],
  pool_stats_SHA256=m["pool_source_sha256"],manifest=m,real_cases=real)

def verify_pin(model,pin,original,partial,groot,eroot,rank):
 assert original["status"]==partial["status"]=="GENUINE_RUST_EXACT_SOURCE"
 assert original["preflop_source_SHA256"]==partial["preflop_source_SHA256"]
 assert original["pool_stats_SHA256"]==partial["pool_stats_SHA256"]
 gc=next(c for c in original["real_cases"] if c["source_sha256"]==pin["original_GTO_source_sha256"] and c["turn"]==pin["turn"])
 ec=next(c for c in partial["real_cases"] if c["source_sha256"]==pin["NL2_IP_source_sha256"] and c["turn"]==pin["turn"])
 assert (gc["line"],ec["line"])==("x b50 c","x b50 c")
 assert gc["original_GTO_gap_pct"]<=.5 and ec["original_GTO_gap_pct"]<=.5
 assert ec["original_hero_gap_pct"] is not None and ec["original_hero_gap_pct"]<=.5
 gm=original["manifest"];em=partial["manifest"]
 fp=groot/"solver/postflop"/gm["file_flop"]
 ep=eroot/"solver/postflop"/em["file_flop"]
 assert fp.is_file() and ep.is_file()
 gfr=read(fp);efr=read(ep)
 gp=groot/"solver/postflop"/gc["source_path"]
 es=eroot/"solver/postflop"/ec["source_path"]
 assert sha(gp)==gc["source_sha256"] and sha(es)==ec["source_sha256"]
 gd=read(gp);ed=read(es)
 gmask,gstats=game_reach(gfr,gd);emask,estats=game_reach(efr,ed)
 assert gstats["sequential_actor_combo_nodes"]>0 and estats["sequential_actor_combo_nodes"]>0
 def nodal(d,seq):
  rows=[n for n in d["nodes"] if n["board"]==pin["public_board"] and n["line"]==LINE and n["player"]==1]
  assert len(rows)==1,(rank,pin["flop"],pin["public_board"],len(rows))
  node=rows[0];q=seq["|".join((pin["public_board"],LINE,"1"))]
  assert q["count"]>0
  spr=(d["stack"]-max(node["bets"]))/node["pot"]
  assert abs(spr-model["assumed_model_node_spr"])/max(1,spr)<=.05
  return node,q,spr
 gn,gq,gspr=nodal(gd,gmask);en,eq,espr=nodal(ed,emask)
 assert abs(gspr-espr)<1e-5
 assert (gq["count"],eq["count"])==(
  pin["GTO_legal_40_70_hero_IP_combos"],pin["NL2_IP_legal_40_70_hero_IP_combos"])
 assert abs(gspr-pin["actual_spr"])<1e-5
 scope=lock_scope(ed,em["locks"],"exp_ip")
 assert scope["observed_marginal_source_nodes"]>0
 assert scope["villain_decision_nodes"]==scope["observed_marginal_source_nodes"]+scope["imputed_assumption_nodes"]+scope["unmatched_nodes"]
 medium=strict_medium_evidence(gn,gd,gq["mask"])
 assert medium["eligible"]>=0 and (not medium["candidate"] or medium["eligible"]>0)
 lock=dict(version="exp_ip",run_id=pin["NL2_hero_IP_run_id"],sha256=ec["source_sha256"],
  source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",
  villain_observed_pattern_node_share_pct=scope["coverage_pct"],
  source_not_real_per_combo_observation=True,
  unknown_history_frequency_filled_with_default=scope["imputed_assumption_nodes"]>0,
  observed_marginal_source_nodes=scope["observed_marginal_source_nodes"],
  assumed_default_source_nodes=scope["imputed_assumption_nodes"],
  unlocked_source_nodes=scope["unmatched_nodes"],
  hero_model_gain_bb=locked_model_gain(ed,"exp_ip"))
 sample=dict(flop=pin["flop"],turn=pin["turn"],public_board=pin["public_board"],
  actual_exact_action_line=LINE,acting_seat=1,exact_flop_action="x b50 c",
  actual_pot_bb=gn["pot"]/100,
  actual_effective_stack_bb=(gd["stack"]-max(gn["bets"]))/100,
  actual_spr=gspr,model_assumed_spr=model["assumed_model_node_spr"],
  relative_spr_error_pct=round(100*abs(gspr-model["assumed_model_node_spr"])/max(1,gspr),4),
  genuine_gto_exploitability_pct=gc["original_GTO_gap_pct"],
  source_run_id=pin["GTO_run_id"],source_sha256=gc["source_sha256"],
  source_kind="PINNED_PREFLOP_CFR",assumed_preflop_ranges=False,
  exact_combo_reachable=sum(float(w)>1e-4 for w in gn["w"][1]),
  strict_full_street_combo_reachable=gq["count"],exact_node_actions=gn["acts"],
  medium_50pct_eligible_combos=medium["eligible"],
  b50_nonpolarized_relative_equity_research_candidate=medium["candidate"],
  nl2_locked_variants=[lock],flop_texture=texture(pin["flop"]))
 proof=dict(model_rank=rank,flop=pin["flop"],public_board=pin["public_board"],turn=pin["turn"],
  original_GTO_run=pin["GTO_run_id"],actual_NL2_IP_run=pin["NL2_hero_IP_run_id"],
  original_GTO_SHA256=gc["source_sha256"],actual_NL2_SHA256=ec["source_sha256"],
  GTO_strict_combos=gq["count"],NL2_strict_combos=eq["count"],
  original_Rust_root_SHA256=original["root_original_Rust_SHA256"],
  real_NL2_IP_root_SHA256=partial["root_original_Rust_SHA256"],
  exact_action_line=LINE,acting_seat=1,actual_spr=gspr,
  observed_marginal_source_nodes=scope["observed_marginal_source_nodes"],
  assumed_source_nodes=scope["imputed_assumption_nodes"],
  unmatched_unlocked_nodes=scope["unmatched_nodes"],only_exact_named_public_board=True)
 return sample,proof

def patch_ui(path):
 s=path.read_text(encoding="utf-8")
 old="if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166'||"
 new="if(!['NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166','"+V51+"'].includes(d.schema)||"
 assert s.count(old)==1
 s=s.replace(old,new)
 old="d.CERT_MULTIBOARD!==163||d.APPROX!==229||d.EST!==0||d.TOTAL!==392||"
 new="d.CERT_MULTIBOARD!==(d.schema==='NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166'?163:165)||d.APPROX!==(d.schema==='NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166'?229:227)||d.EST!==0||d.TOTAL!==392||"
 assert s.count(old)==1
 s=s.replace(old,new)
 marker="const v49b405=d=>{"
 assert s.count(marker)==1
 validator="""const v51b427=d=>{
 v50b417(d);
 const q=d.B427_r216218_three_true_original_GTO_NL2_IP_flops;
 if(d.schema!=='"""+V51+"""'||d.CERT_MULTIBOARD!==165||d.APPROX!==227||d.EST!==0||d.TOTAL!==392||
  !q||q.ranks?.join(',')!=='216,218'||q.spot!=='CO_BB'||q.actor!=='CO_IP'||
  q.line!=='x b50 c/x b50 c/x'||q.flops?.join(',')!=='Js9h4d,Td8h3c,Js9h5d'||
  q.authenticated_sources_by_rank?.length!==2||
  q.authenticated_sources_by_rank.some(x=>![216,218].includes(x.rank)||x.pins?.length!==3||
   x.pins.some(p=>p.GTO_strict_combos<=0||p.NL2_strict_combos<=0||
    p.original_GTO_SHA256?.length!==64||p.actual_NL2_SHA256?.length!==64))||
  [216,218].some(rank=>{
   const r=Object.values(d.records||{}).find(x=>x.frequency_rank===rank);
   return !r||r.label!=='CERT-MULTIBOARD'||r.proven_exact_board_count!==3||
    r.solver_profile!=='CO_BB'||r.certified_3_to_5_exact_flop_boards?.length!==3||
    new Set(r.certified_3_to_5_exact_flop_boards.map(x=>x.flop)).size!==3||
    r.certified_3_to_5_exact_flop_boards.some(x=>
     x.acting_seat!==1||x.actual_exact_action_line!=='x b50 c/x b50 c/x'||
     x.strict_full_street_combo_reachable<=0||x.relative_spr_error_pct>5||
     !x.nl2_locked_variants?.some(v=>v.version==='exp_ip'&&v.sha256?.length===64));
  })||d.no_generic_texture_GTO!==true||d.PR2_remains_draft_never_merge!==true)
  throw Error('B427 exact rank216/218 three-flop original GTO/NL2 IP source failclosed');
 return d;
};
"""
 s=s.replace(marker,validator+marker)
 old="return fetch('data/nl2_hu_multiboard_status_v50_b417_rank166.json',{cache:'no-store'}).then(open).then(v50b417)"
 new="return fetch('data/nl2_hu_multiboard_status_v51_b427_rank216_218.json',{cache:'no-store'}).then(open).then(v51b427)\n    .catch(()=>fetch('data/nl2_hu_multiboard_status_v50_b417_rank166.json',{cache:'no-store'}).then(open).then(v50b417))"
 assert s.count(old)==1
 s=s.replace(old,new)
 allowed="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166','NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219'"
 assert s.count(allowed)==1
 s=s.replace(allowed,"'"+V51+"',"+allowed)
 if path.name=="nl2-multiboard.js":
  oldm="fetch('data/nl2_hu_cert_lock_medium_matrix_v50_b417.json',{cache:'no-store'}).catch"
  newm="fetch('data/nl2_hu_cert_lock_medium_matrix_v51_b427.json',{cache:'no-store'}).catch(()=>fetch('data/nl2_hu_cert_lock_medium_matrix_v50_b417.json',{cache:'no-store'})).catch"
  assert s.count(oldm)==1
  s=s.replace(oldm,newm)
  # Two earlier source-status allowlists.
  s=s.replace("'NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166'","'"+V51+"','NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166'")
  # Avoid duplicate V51 entries caused by the global replace on the main file.
  s=s.replace("'"+V51+"','"+V51+"',","'"+V51+"',")
 path.write_text(s,encoding="utf-8")

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--historical-gto",required=True,type=pathlib.Path)
 ap.add_argument("--historical-exp",required=True,type=pathlib.Path)
 ap.add_argument("--td-gto",required=True,type=pathlib.Path)
 ap.add_argument("--td-exp",required=True,type=pathlib.Path)
 ap.add_argument("--js-gto",required=True,type=pathlib.Path)
 ap.add_argument("--js-exp",required=True,type=pathlib.Path)
 a=ap.parse_args()
 parent=read(PARENT);triage=read(TRIAGE);b393=read(B393);b400=read(B400)
 b412=read(B412);b421=read(B421)
 assert (parent["CERT_MULTIBOARD"],parent["APPROX"],parent["EST"],parent["TOTAL"])==(163,229,0,392)
 assert b412["schema"]=="NL2_B412_RANK216_218_ONE_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIR_V1"
 assert b421["schema"]=="NL2_B421_RANK216_218_ONE_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIR_V1"
 assert (b412["original_GTO_run"],b412["new_NL2_IP_run"])==(45028060598,45029736915)
 assert (b421["original_GTO_run"],b421["new_NL2_IP_run"])==(45026396521,45052841553)
 assert b412["B400_frozen_original_GTO_source_sha256"]==sha(B400)
 assert b421["B393_frozen_original_GTO_source_sha256"]==sha(B393)
 assert b412["new_distinct_qualifying_flops_by_rank"]=={"216":["Td8h3c"],"218":["Td8h3c"]}
 assert b421["new_distinct_qualifying_flops_by_rank"]=={"216":["Js9h5d"],"218":["Js9h5d"]}
 loaded={}
 # Historical B2 source: both target CO_BB jobs succeeded even though an unrelated SB3_BTN job failed.
 for version,root in (("gto",a.historical_gto),("exp_ip",a.historical_exp)):
  row=next(x for x in triage["source_blind_selected_ten"] if x["frequency_rank"]==216)["strictly_measured_pairs"][0]
  expected=row["gto_source_sha256"] if version=="gto" else row["nl2_hero_lock_sha256"]
  loaded[("Js9h4d",version)]=legacy_b2_check(root,"Js9h4d",version,expected)
 # B412 and B421 are independently SHA-verified full100bb Rust GTO + real NL2 IP partial-lock artifacts.
 G412=source_check(a.td_gto,"Td8h3c","gto",None);E412=source_check(a.td_exp,"Td8h3c","exp_ip",None)
 G421=source_check(a.js_gto,"Js9h5d","gto",None);E421=source_check(a.js_exp,"Js9h5d","exp_ip",None)
 for z in (G412,E412,G421,E421):assert z and z["status"]=="GENUINE_RUST_EXACT_SOURCE"
 row412=b412["source_evidence"][0];row421=b421["source_evidence"][0]
 assert G412["manifest_sha256"]==row412["original_GTO"]["manifest_sha256"]
 assert G412["root_original_Rust_SHA256"]==row412["original_GTO"]["root_original_Rust_SHA256"]
 assert E412["manifest_sha256"]==row412["actual_partial_NL2_IP"]["manifest_sha256"]
 assert E412["root_original_Rust_SHA256"]==row412["actual_partial_NL2_IP"]["root_original_Rust_SHA256"]
 assert G421["manifest_sha256"]==row421["original_GTO"]["manifest_sha256"]
 assert G421["root_original_Rust_SHA256"]==row421["original_GTO"]["root_original_Rust_SHA256"]
 assert E421["manifest_sha256"]==row421["actual_partial_NL2_IP"]["manifest_sha256"]
 assert E421["root_original_Rust_SHA256"]==row421["actual_partial_NL2_IP"]["root_original_Rust_SHA256"]
 loaded[("Td8h3c","gto")]=G412;loaded[("Td8h3c","exp_ip")]=E412
 loaded[("Js9h5d","gto")]=G421;loaded[("Js9h5d","exp_ip")]=E421
 roots={"Js9h4d":(a.historical_gto,a.historical_exp),
        "Td8h3c":(a.td_gto,a.td_exp),"Js9h5d":(a.js_gto,a.js_exp)}
 pins_by_rank={}
 for rank,mid in TARGET.items():
  old=parent["records"][mid]
  assert (old["label"],old["frequency_rank"],old["solver_profile"],old["family"],old["street"])==(
   "APPROX",rank,"CO_BB","SRP",2)
  trow=next(x for x in triage["source_blind_selected_ten"] if x["frequency_rank"]==rank)
  assert trow["model_id"]==mid and trow["true_paired_measured_NL2_hero_lock_flops"]==1
  h=trow["strictly_measured_pairs"][0]
  assert h["flop"]=="Js9h4d" and h["exact_line"]==LINE and h["strict_legal_combo_count"]==6
  hist=dict(flop="Js9h4d",public_board=h["exact_public_board"],turn=h["exact_public_board"][6:8],
   GTO_run_id=h["gto_source_run_id"],NL2_hero_IP_run_id=h["nl2_hero_lock_run_id"],
   original_GTO_source_sha256=h["gto_source_sha256"],NL2_IP_source_sha256=h["nl2_hero_lock_sha256"],
   GTO_legal_40_70_hero_IP_combos=h["strict_legal_combo_count"],
   NL2_IP_legal_40_70_hero_IP_combos=h["strict_legal_combo_count"],actual_spr=h["actual_spr"],
   original_existing_V47_source=True,source_proof="B2_original_exact_board_source")
  td=next(x for x in b412["positive_40_70_named_river_pairs_by_rank"][str(rank)] if x["flop"]=="Td8h3c")
  js=next(x for x in b421["positive_40_70_named_river_pairs_by_rank"][str(rank)] if x["flop"]=="Js9h5d")
  def pin(x,proof):
   return dict(flop=x["flop"],public_board=x["exact_public_board"],turn=x["turn"],
    GTO_run_id=x["original_GTO_source_run"],NL2_hero_IP_run_id=x["new_NL2_IP_source_run"],
    original_GTO_source_sha256=x["original_GTO_sha256"],NL2_IP_source_sha256=x["new_NL2_IP_sha256"],
    GTO_legal_40_70_hero_IP_combos=x["GTO_strict_40_70_combos"],
    NL2_IP_legal_40_70_hero_IP_combos=x["actual_NL2_IP_strict_40_70_combos"],
    actual_spr=x["actual_SPR"],source_proof_sha256=sha(proof))
  pins=[hist,pin(td,B412),pin(js,B421)]
  assert [x["flop"] for x in pins]==list(FLOPS)
  assert len({texture(x["flop"]) for x in pins})>=2
  pins_by_rank[str(rank)]=dict(rank=rank,model_id=mid,pins=pins)
 # Source-first pre-cert gate. It explicitly does not alter model labels.
 pre=dict(schema="NL2_B427_R216218_THREE_AUTHENTIC_GTO_NL2_IP_SOURCE_PRECERT_V1",
  source_V50_status_sha256=sha(PARENT),B370_source_triage_sha256=sha(TRIAGE),
  B393_original_GTO_source_sha256=sha(B393),B400_original_GTO_source_sha256=sha(B400),
  B412_actual_NL2_IP_pair_proof_sha256=sha(B412),B421_actual_NL2_IP_pair_proof_sha256=sha(B421),
  ranks_with_three_full_street_40_70_positive_flops=[216,218],
  eligible_rank_source_triples=pins_by_rank,readiness_only_no_CERT_upgrade=True,
  source_blind_first10_preregistered=True,exact_spot="CO_BB",actor="CO_IP",exact_line=LINE,
  distinct_flops=list(FLOPS),distinct_texture_count=len({texture(x) for x in FLOPS}),
  original_preflop_CFR_is_not_NL2_conditional_private_hand_frequency=True,
  no_texture_level_GTO_or_blanket_50pct_strategy=True,
  separate_independent_original_archive_SHA_HU2475_UI_and_per_board_lock_audit_required=True,
  baseline_CERT_MULTIBOARD=163,baseline_APPROX=229,baseline_EST=0,PR2_remains_draft_unmerged=True)
 PRE.write_text(json.dumps(pre,ensure_ascii=False,indent=2)+"\n")
 new=copy.deepcopy(parent);authenticated=[]
 for rank,mid in TARGET.items():
  old=parent["records"][mid]
  model=dict(family=old["family"],spot=old["solver_profile"],street=old["street"],
   preflop_text=old["preflop_text"],abstract_action_history=old["abstract_action_history"],
   assumed_model_node_spr=old["assumed_model_node_spr"])
  selected=[];proofs=[]
  for pinrow in pins_by_rank[str(rank)]["pins"]:
   g,e=loaded[(pinrow["flop"],"gto")],loaded[(pinrow["flop"],"exp_ip")]
   gr,er=roots[pinrow["flop"]]
   sample,proof=verify_pin(model,pinrow,g,e,gr,er,rank)
   selected.append(sample);proofs.append(proof)
  assert [x["flop"] for x in selected]==list(FLOPS)
  assert len({texture(x["flop"]) for x in selected})>=2
  rec=copy.deepcopy(old)
  rec.update(label="CERT-MULTIBOARD",high_frequency_preregistered=True,
   original_top24_high_frequency_preregistered=False,
   source_blind_expansion_rank=rank,source_blind_expansion_preregistered=True,
   prereg_cohort="B370_FIRST10_ORIGINAL_GTO_NL2_CO_BB_THREE_EXACT_SOURCE_FLOPS",
   certified_3_to_5_exact_flop_boards=selected,proven_exact_board_count=3,
   blocked_reason=None,
   source_credibility="GITHUB_ACTIONS_ORIGINAL_FULL100BB_SHA_AND_ACTUAL_NL2_IP_PARTIAL_LOCK_40_70")
  new["records"][mid]=rec
  authenticated.append(dict(rank=rank,model_id=mid,pins=proofs))
 new.update(schema=V51,CERT_MULTIBOARD=165,APPROX=227,EST=0,TOTAL=392,
  parent_V50_SHA256=sha(PARENT),B427_preregistered_three_flop_source_sha256=sha(PRE),
  supplementary_cert_count=parent["supplementary_cert_count"]+2,
  source_blind_expansion_ranks=sorted(set(parent["source_blind_expansion_ranks"]+[216,218])),
  original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
  no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True,
  B427_r216218_three_true_original_GTO_NL2_IP_flops=dict(
   ranks=[216,218],spot="CO_BB",actor="CO_IP",line=LINE,flops=list(FLOPS),
   source_blind_first10_preregistered=True,source_pre_cert_sha256=sha(PRE),
   authenticated_sources_by_rank=authenticated,
   historical_B2_source_run=44666290556,B412_NL2_IP_run=45029736915,
   B421_NL2_IP_run=45052841553,only_exact_named_public_boards_no_generic_texture=True))
 STATUS.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n")
 audit_path=pathlib.Path("tools/hu_cert_lock_medium_audit.py")
 audit_text=audit_path.read_text(encoding="utf-8")
 old_allow="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166')"
 assert audit_text.count(old_allow)==1
 audit_path.write_text(audit_text.replace(old_allow,"'NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166','"+V51+"')"),encoding="utf-8")
 import hu_cert_lock_medium_audit as source_audit
 import hu_cert_lock_medium_coverage_matrix as medium_matrix
 source_audit=importlib.reload(source_audit);medium_matrix.audit=source_audit.audit
 checked=source_audit.audit(new)
 assert (checked["cert_multiboard"],checked["approx"],checked["EST"])==(165,227,0)
 assert (checked["aggregate"]["named_board_proofs"],checked["aggregate"]["paired_hero_locked_source_variants"])==(624,716)
 matrix=medium_matrix.create(new)
 assert (len(matrix["models"]),len(matrix["boards"]))==(165,624)
 unknown=sum(1 for b in matrix["boards"] for l in b["hero_lock_proofs"]
  if l["node_rate_data_status"]=="HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN")
 assert unknown==0
 matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V51_B427",
  V51_status_sha256=sha(STATUS),source_unknown_variants_after=0,
  true_40_70_full100bb_CO_IP_source_rank216_218=True,
  no_private_card_conditional_opponent_NL2_frequency_claim=True,
  exact_named_board_50pct_research_only=True,PR2_Draft_NEVER_MERGE=True)
 MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
 AUDIT.write_text(json.dumps(checked,ensure_ascii=False,indent=2)+"\n")
 PROOF.write_text(json.dumps(dict(schema="NL2_B427_R216_218_TWO_MODELS_SIX_ORIGINAL_GTO_NL2_IP_CERT_BOARDS_V1",
  parent_V50_status_SHA256=sha(PARENT),B427_source_pre_cert_SHA256=sha(PRE),
  model_source_pins=authenticated,source_blind_first10_preregistered=True,
  true_original_full100bb_CFR_source_and_40_70_check=True,
  same_exact_CO_IP_line_SPR_and_paired_NL2_IP_hero_lock=True,
  only_named_board_no_generic_texture_GTO=True,no_NL2_villain_private_hand_observations=True,
  CERT_before=163,CERT_after=165,APPROX_before=229,APPROX_after=227,EST=0,
  named_boards_before=618,named_boards_after=624,
  locked_hero_variants_before=710,locked_hero_variants_after=716,
  unknown_lock_denominators_after=0,
  V51_status_sha256=sha(STATUS),V51_matrix_sha256=sha(MATRIX),V51_audit_sha256=sha(AUDIT),
  b50_nonpolarized_marks_are_exact_named_board_research_only=True,PR2_draft_never_merge=True),
  ensure_ascii=False,indent=2)+"\n")
 for file in ("nl2_hu_multiboard_ui.js","nl2-multiboard.js"):patch_ui(pathlib.Path(file))
 for filename in ("nl2.html","nl2-multiboard.html"):
  p=pathlib.Path(filename);s=p.read_text(encoding="utf-8")
  assert s.count("task-hybrid-b417-v50-20261122")==1
  p.write_text(s.replace("task-hybrid-b417-v50-20261122","task-hybrid-b427-v51-20261122"),encoding="utf-8")
 test=pathlib.Path("tools/hu_b378_v47_loader_runtime_test.cjs")
 ts=test.read_text(encoding="utf-8")
 assert ts.count("414-persistent|417-v50")==1
 test.write_text(ts.replace("414-persistent|417-v50","414-persistent|417-v50|427-v51"),encoding="utf-8")
 DOC.write_text("# B427 ranks216/218: three exact original GTO + genuine NL2-IP paired source flops each\n\n"
  "Both source-blind first-ten CO_BB models are promoted only on the exact named flops Js9h4d, Td8h3c and Js9h5d. "
  "Each named public board has independently SHA-verified original full-100bb Rust GTO and NL2-IP partially locked "
  "source, identical CO-IP x b50 c/x b50 c/x line, positive sequential 40/70 hero combo reach and <=5% SPR error. "
  "Historical B2 CO_BB target jobs succeeded; the unrelated SB3_BTN failure did not invalidate these artifacts. "
  "Observed NL2 values are pooled marginals, not villain private-card conditional actions. "
  "The 50% non-polarized flag is a named-board research marker only, never a generic texture recommendation. "
  "**165 CERT /227 APPROX /0 EST**, 624 named boards, 716 paired NL2 source locks, UNKNOWN=0. "
  "Full HU2475, frontend and independent Actions audits required. PR #2 stays DRAFT and unmerged.\n")
 print("PASS B427 authentic three-flop paired GTO/NL2 IP rank216/218: 165 CERT /227 APPROX, 624 boards, 716 locks, UNKNOWN=0")
if __name__=="__main__":main()
