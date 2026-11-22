#!/usr/bin/env python3
"""B353 corrected historical source: ORIGINAL stage2 run 44654973894, NOT B2.
SHA-pin actual UTG_CO Ks7h2d/9d real Rust GTO and exp_ip NL2 response,
independently verified original stage2 batch05, frozen B175 source provenance.
Never call pooled NL2 marginal by-size observations private-card conditional.
"""
import argparse,gzip,hashlib,json,pathlib
D=pathlib.Path('data')
SRC_RUN=44654973894
FLOP='Ks7h2d';TURN='9d';LINE='b50 c/x';BOARD='2d7hKs9d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--downloads',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 q=p.parse_args()
 proof_file=q.downloads/'provenance/STAGE2_BATCH05.json'
 assert proof_file.is_file()
 stage=json.loads(proof_file.read_text())
 assert stage['schema']=='NL2_HU_SOLVER_ARCHIVE_AUDIT_V1'
 assert (stage['run_id'],stage['artifact_count'],stage['solved_subgames'])==(SRC_RUN,12,139)
 assert not stage['errors']
 original={}
 for v in ('gto','exp_ip'):
  folder=q.downloads/v
  mf=folder/f'evidence/UTG_CO-{v}-{FLOP}.json'
  assert mf.is_file()
  m=json.loads(mf.read_text())
  assert (m['spot'],m['version'])==('UTG_CO',v)
  assert not m['failures'] and m['cases_solved']>=1
  assert FLOP in m['selected_flops']
  case=[c for c in m['cases'] if (c['flop'],c['turn'],c['line'])==(FLOP,TURN,'b50 c')]
  assert len(case)==1
  c=case[0]
  assert abs(c['turn_node_spr']-7)/7<=.05 and abs(c['parent_spr']-7)/7<=.05 if 'parent_spr' in c else abs(c['turn_node_spr']-7)/7<=.05
  assert (c['root_pot_bb'],c['root_stack_bb'])==(6.5,97.5)
  assert c['combo_reach_converged_for_cert'] and c['sub_gto_expl_pct']<=.5
  if v=='exp_ip':assert c['sub_hero_gap_pct']<=.5
  flop=folder/'solver/postflop'/c['flop_json']
  sub=folder/'solver/postflop'/c['sub_json']
  reach=folder/c['combo_reach_report']
  assert all(z.is_file() for z in (flop,sub,reach))
  assert (sha(flop),sha(sub),sha(reach))==(c['flop_sha256'],c['sub_sha256'],c['combo_reach_report_sha256'])
  fr=json.loads(flop.read_text());raw=json.loads(sub.read_text())
  mask=json.loads(gzip.decompress(reach.read_bytes()))
  assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,650,9750)
  assert (raw['flop'],raw['turn'],raw['line0'])==(FLOP,TURN,'b50 c')
  assert raw['info']['gto_expl_pct']<=.5 and len(raw['nodes'])>=1
  assert mask['schema']=='HU_CFR_REACH_V1'
  assert mask['source_sha256']==sha(sub) and mask['source_run']==str(SRC_RUN)
  assert (mask['source_flop'],mask['source_turn'],mask['source_flop_line'])==(FLOP,TURN,'b50 c')
  assert mask['converged_for_cert'] and mask['gto_exploitability_pct']<=.5
  nodes=[n for n in mask['nodes'] if (n['line'],n['board'],n['actor'])==(LINE,BOARD,1)
      and abs(n['node_spr']-7)/7<=.05]
  assert len(nodes)==1 and nodes[0]['reachable_combos']>0
  art=next(a for a in stage['artifacts'] if a['artifact']==f'nl2-stage2-UTG_CO-{v}-{FLOP}')
  verified=[a for a in art['cases'] if (a['flop'],a['turn'],a['line'])==(FLOP,TURN,'b50 c')]
  assert len(verified)==1
  assert verified[0]['source_sha256']==sha(sub)
  assert verified[0]['cert_converged']
  assert (verified[0]['parent_spr'],verified[0]['gto_gap_pct'])==(c['turn_node_spr'],c['sub_gto_expl_pct'])
  original[v]=dict(authentic_source_run=SRC_RUN,version=v,
      source_manifest_sha256=sha(mf),original_full_flop_root_sha256=sha(flop),
      actual_original_Rust_turn_source_sha256=sha(sub),
      true_actor_CO_IP_reached_combos=nodes[0]['reachable_combos'],
      actual_board=nodes[0]['board'],actual_actor=node_actor(nodes[0]),
      actual_model_spr=nodes[0]['node_spr'],
      original_real_NL2_rust_partial_lock=(v=='exp_ip'),
      observed_NL2_private_hand_conditionals=False)
 assert original['gto']['actual_board']==original['exp_ip']['actual_board']==BOARD
 historical=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
 h=json.loads(historical.read_text())
 hr=next(row for row in h['rows'] if row['rank']==79)
 records=[x for x in hr['exact_authentic_gto_source_proofs'] if
     (x['flop'],x['turn'],x['source_run'],x['exact_line'],x['actor'])==(FLOP,TURN,SRC_RUN,LINE,1)]
 assert len(records)==1 and records[0]['true_NL2_actor_locked']
 assert records[0]['source_sha']==original['gto']['actual_original_Rust_turn_source_sha256']
 assert records[0]['paired_lock_runs']==[SRC_RUN] and records[0]['strict_legal_combos']==18
 statusfile=D/'nl2_hu_multiboard_status_v45_b345_rank71.json'
 status=json.loads(statusfile.read_text())
 assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(157,235,0,392)
 mid='ln-ipc-t_model-1cla93g';m=status['records'][mid]
 assert m['frequency_rank']==79 and m['solver_profile']=='UTG_CO' and m['label']=='APPROX'
 assert m['assumed_model_node_spr']==7
 out=dict(schema='NL2_HU_B353_R79_STAGE2_ORIGINAL_KS7H2D_9D_GTO_AND_NL2_CO_IP_V1',
   authenticated_original_stage2_run=SRC_RUN,
   original_source_stage2_conclusion_success=True,
   original_12_artifact_provenance_sha256=sha(proof_file),
   frozen_B175_source_ledger_sha256=sha(historical),
   original_40_70_B175_GTO_strict_combos=records[0]['strict_legal_combos'],
   genuine_UTGCO_source_GTO=original['gto'],genuine_UTGCO_real_NL2_CO_IP_source=original['exp_ip'],
   target_rank=79,model_id=mid,spot='UTG_CO',flop=FLOP,turn=TURN,line=LINE,hero_actor='CO_IP',model_SPR=7,
   still_requires_two_other_distinct_original_GTO_and_real_NL2_actor_locked_flops=True,
   no_false_B2_original_parent_assumption=True,
   no_observed_private_card_conditional_NL2_frequency=True,
   V45_status_sha256=sha(statusfile),CURRENT_CERT=157,CURRENT_APPROX=235,CURRENT_EST=0,
   PR2_Draft_NEVER_MERGE=True)
 q.out.parent.mkdir(parents=True,exist_ok=True)
 q.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('PASS B353 authentic ORIGINAL stage2 rank79 historical GTO+NL2 IP',
       SRC_RUN,original['gto']['true_actor_CO_IP_reached_combos'],
       original['exp_ip']['true_actor_CO_IP_reached_combos'],
       'historical stricter B175 GTO',records[0]['strict_legal_combos'])
def node_actor(n):return n['actor']
if __name__=='__main__':main()
