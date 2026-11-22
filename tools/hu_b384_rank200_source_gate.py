#!/usr/bin/env python3
"""B384 rank200 genuine exact original Rust GTO plus NL2 partial IP pairs, strict 40%-70%."""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
FLOPS=('7s5h3d','9s6h3d')
VERSIONS=('gto','exp_ip')
TARGET='x b50 c/x b50 c/x'
PIN='abe310c3aad02dd4a7c77fb2831801fd490cf51b'
RUST='9d1509fe5077d019825f833eed04b16d342dfda1'
D=pathlib.Path('data')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--downloads',type=pathlib.Path,required=True);ap.add_argument('--run-id',type=int,required=True)
 args=ap.parse_args();samples=[];valid={}
 for flop in FLOPS:
  for ver in VERSIONS:
   folder=args.downloads/f'nl2-multiboard-B384_R200-LMP_CO_BB-{flop}-{ver}'
   mp=folder/'evidence'/f'LMP_CO_BB-{flop}-{ver}.json'
   result=dict(flop=flop,version=ver,source_artifact=folder.name,manifest_present=mp.is_file(),cases=[])
   if not mp.is_file():
    result['excluded_reason']='NO_ORIGINAL_RUST_MANIFEST_NOT_CERT';samples.append(result);continue
   assert (folder/'evidence/poker-solver-pin.txt').read_text().strip()==PIN
   assert (folder/'evidence/rust-pin.txt').read_text().strip()==RUST
   m=read(mp)
   assert (m['schema'],m['spot'],m['flop'],m['version'],m['pot_family'])==('NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1','LMP_CO_BB',flop,ver,'LMP')
   assert (m['root_pot_bb'],m['root_remaining_bb'])==(2.5,99.0)
   assert (m['preflop_ranges']['source'],m['flop_size_profile'])==('ASSUMED_EXPLICIT_169CLASS','full')
   assert m['flop_action_sizes']==['33%','50%','75%','100%'] and not m['restricted_tree_assumption']
   assert (m['flop_line_policy'],m['selected_lines'])==('checked-b50only',['x b50 c'])
   assert len(m['turns'])==1 and m['solved_cases']==len(m['cases'])
   root=folder/'solver/postflop'/m['file_flop']
   assert root.is_file() and sha(root)==m['file_flop_sha256']
   fr=read(root);assert (fr['flop'],fr['pot'],fr['stack'])==(flop,250,9900)
   result.update(manifest_sha256=sha(mp),original_flop_sha256=sha(root),
     original_flop_job_sha256=sha(root.with_suffix('.job.json')),
     original_solve_errors=m['failures'],actual_solved_cases=m['solved_cases'])
   for c in m['cases']:
    assert c['line']=='x b50 c' and c['turn'] in m['turns']
    assert c['gto_gap_pct'] is not None and c['gto_gap_pct']<=.5
    if ver=='exp_ip':
     assert c['hero_gap_pct'] is not None and c['hero_gap_pct']<=.5
     assert any(int(x.get('n') or 0)>=500 and str(x.get('scope','')).startswith('IMPUTED_HISTORY_FROM_TRUE') for x in m['locks'])
     assert any(x.get('nodes',0)>0 for x in c['lock_stats'].values())
    p=folder/'solver/postflop'/c['source_path']
    assert p.is_file() and sha(p)==c['source_sha256']
    d=read(p);assert (d['flop'],d['turn'],d['line0'])==(flop,c['turn'],'x b50 c')
    mask,stats=game_reach(fr,d)
    exact=[]
    for n in d['nodes']:
     if n['line']==TARGET and n['player']==1 and len(n['board'])==10:
      q=mask['|'.join((n['board'],n['line'],'1'))]
      exact.append(dict(public_board=n['board'],strict_actor_IP_combos=q['count'],
       exact_source_spr=round((d['stack']-max(n['bets']))/n['pot'],6)))
    result['cases'].append(dict(turn=c['turn'],source_sha256=c['source_sha256'],
     gto_gap_pct=c['gto_gap_pct'],locked_hero_gap_pct=c['hero_gap_pct'],
     strict_full_street_summary=dict(stats),exact_actor_IP_target_line_runouts=exact))
    valid[(flop,ver)]=result['cases'][-1]
   samples.append(result)
 paired=[]
 for flop in FLOPS:
  g=valid.get((flop,'gto'));e=valid.get((flop,'exp_ip'))
  if not g or not e or g['turn']!=e['turn']:continue
  ga={n['public_board']:n for n in g['exact_actor_IP_target_line_runouts'] if n['strict_actor_IP_combos']>0}
  ea={n['public_board']:n for n in e['exact_actor_IP_target_line_runouts'] if n['strict_actor_IP_combos']>0}
  for board in sorted(set(ga)&set(ea)):
   x,y=ga[board],ea[board];spr=x['exact_source_spr']
   if abs(spr-y['exact_source_spr'])>1e-6 or abs(spr-9.525)/max(1,spr)>.05:continue
   paired.append(dict(flop=flop,turn=g['turn'],exact_public_board=board,
    exact_line=TARGET,actor='CO_IP',actual_spr=spr,
    genuine_GTO_strict_combo_count=x['strict_actor_IP_combos'],
    genuine_NL2_partial_strict_combo_count=y['strict_actor_IP_combos'],
    GTO_source_SHA256=g['source_sha256'],NL2_partial_source_SHA256=e['source_sha256']))
 s=read(D/'nl2_hu_multiboard_status_v47_b364_rank96.json')
 mid='ln-iso-lmp_r_model-68efr6'
 assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(159,233,0,392)
 assert s['records'][mid]['label']=='APPROX' and s['records'][mid]['frequency_rank']==200
 first=read(D/'nl2_hu_b370_first10_approx_source_triage.json')
 rank=next(x for x in first['source_blind_selected_ten'] if x['frequency_rank']==200)
 assert rank['true_paired_measured_NL2_hero_lock_flops']==1 and rank['strictly_measured_pairs'][0]['flop']=='8s8h3d'
 report=dict(schema='NL2_HU_B384_RANK200_TWO_ACTUAL_GTO_NL2_IP_STRICT_SOURCE_V1',
  run_id=args.run_id,model_id=mid,rank=200,actor='CO_IP',exact_line=TARGET,source_spot='LMP_CO_BB',
  source_flops=list(FLOPS),solver_pin=PIN,rust_pin=RUST,
  true_original_Rust_source_evidence=samples,
  same_exact_public_board_full_street_40_70_source_pairs=paired,
  distinct_new_flops_with_true_positive_pairs=sorted(set(x['flop'] for x in paired)),
  first_preexisting_source_8s8h3d_from_V47_not_reused_as_new=True,
  preflop_LMP_169class_assumed_not_NL2_observed_private_cards=True,
  no_cert_before_independent_three_distinct_flop_source_gate=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,PR2_draft_never_merge=True)
 (D/'nl2_hu_b384_rank200_two_new_true_source_strict_pairs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 pathlib.Path('docs/NL2_HU_B384_RANK200_TWO_FLOP_SOURCE.md').write_text(
  '# B384 rank200 genuine 100bb GTO plus partial NL2 IP source-only\n\n'
  +f"New strict GTO/NL2 matching river nodes: {len(paired)}; distinct qualifying flops: {len(report['distinct_new_flops_with_true_positive_pairs'])}. "
  +'No source-to-generic-texture extrapolation. LMP preflop range is assumed 169-class. '
  +'No model upgraded until all 3 distinct true original pair flops pass separate SHA/SPR/40-70 gate. '
  +'159 CERT / 233 APPROX unchanged.\n')
 print('B384 strict source summary',len(paired),'same-board river pairs;',len(report['distinct_new_flops_with_true_positive_pairs']),'new flops; CERT159 APPROX233')
if __name__=='__main__':main()
