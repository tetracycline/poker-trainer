#!/usr/bin/env python3
"""B383 two completed original GTO flop sources for rank115/116 show ZERO strict target IP combos.
Never count authentic solve as certificate without the exact sequential legal hand reaches.
"""
import hashlib,json,pathlib,sys
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path('data')
PINS={
 '7s5h3d':dict(turn='6c',manifest='4e15215869544c596a5889cebfabc85455dd02b137da2909dbec63b493b6fef9',
    root='69bd6a238b9ff15b9a0e9940348d71ffe651a767026961e1101f6a8e061b4ee6',
    sub='b8a2bd8ecd11183ead0c0106d73abce0c542b920ffe18c331899f00f201b367f'),
 '8s8h3d':dict(turn='5s',manifest='cac5cc762d6d1f05ea11e3a487b4fcbb7b02c3c0c1749ba6e8ac14d60e0625f1',
    root='a9fd7263c7537ec1de670e8425fadaa4cd77670ccc186844b6c67d935fc87312',
    sub='d32c1178f1d9894edf37f3ce571a5beb055c306241ca57eea1eac12943cedaf5')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 source=pathlib.Path(sys.argv[1]);rows=[]
 for flop,pin in PINS.items():
  folder=source/f'nl2-multiboard-B375_R115116-LMP_CO_BB-{flop}-gto'
  mp=folder/'evidence'/f'LMP_CO_BB-{flop}-gto.json'
  fp=folder/'solver/postflop/out/LMP_CO_BB/gto'/f'{flop}_multiboard.json'
  sp=folder/'solver/postflop/out/LMP_CO_BB/gto'/f'{flop}_b33c_{pin["turn"]}.json'
  assert all(f.is_file() for f in (mp,fp,sp))
  assert (sha(mp),sha(fp),sha(sp))==(pin['manifest'],pin['root'],pin['sub'])
  assert (folder/'evidence/poker-solver-pin.txt').read_text().strip()=='abe310c3aad02dd4a7c77fb2831801fd490cf51b'
  assert (folder/'evidence/rust-pin.txt').read_text().strip()=='9d1509fe5077d019825f833eed04b16d342dfda1'
  m,fr,d=load(mp),load(fp),load(sp)
  assert (m['spot'],m['flop'],m['version'],m['pot_family'])==('LMP_CO_BB',flop,'gto','LMP')
  assert m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
  assert (m['root_pot_bb'],m['root_remaining_bb'])==(2.5,99.0)
  assert (m['flop_size_profile'],m['flop_action_sizes'])==('full',['33%','50%','75%','100%'])
  assert (m['selected_lines'],m['turns'])==(['b33 c'],[pin['turn']])
  assert m['solved_cases']==1 and len(m['cases'])==1 and not m['failures']
  assert (fr['flop'],fr['pot'],fr['stack'])==(flop,250,9900)
  c=m['cases'][0]
  assert c['source_sha256']==pin['sub'] and 0<=c['gto_gap_pct']<=.5
  assert (d['flop'],d['turn'],d['line0'])==(flop,pin['turn'],'b33 c')
  masks,stats=game_reach(fr,d)
  targets=[]
  for node in d['nodes']:
   if node['line']=='b33 c/x b50 c/x' and node['player']==1 and len(node['board'])==10:
    v=masks['|'.join((node['board'],node['line'],'1'))]
    targets.append(dict(exact_public_board=node['board'],acting_seat=1,
       strict_40_70_reachable_hero_IP_combos=v['count'],
       actual_spr=round((d['stack']-max(node['bets']))/node['pot'],6)))
  assert len(targets)==2 and len({n['exact_public_board'] for n in targets})==2
  assert all(n['strict_40_70_reachable_hero_IP_combos']==0 for n in targets)
  rows.append(dict(flop=flop,turn=pin['turn'],GTO_gap_pct=c['gto_gap_pct'],
       original_SHA256=pin,strict_full_street_summary=dict(stats),excluded_exact_nodes=targets))
 s=load(D/'nl2_hu_multiboard_status_v47_b364_rank96.json')
 assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'])==(159,233,0)
 mids={'ln-iso-lmp_r_model-17dzvwx':115,'ln-iso-lmp_r_model-1c6f833':116}
 assert all(s['records'][mid]['label']=='APPROX' and s['records'][mid]['frequency_rank']==rank for mid,rank in mids.items())
 r=dict(schema='NL2_B383_B375_TWO_GENUINE_GTO_FLOPS_R115_116_ZERO_TARGET_IP_V1',
    original_run_id=45017303339,model_ids=mids,exact_actor='CO_IP',
    target_line='b33 c/x b50 c/x',true_original_Rust_GTO_but_strict_negative=rows,
    no_new_qualifying_distinct_GTO_flops=True,
    preflop_range_assumed_169class_not_observed_NL2=True,
    B368_not_rerun=True,CERT_MULTIBOARD=159,APPROX=233,EST=0,
    PR2_draft_never_merge=True)
 (D/'nl2_hu_b383_rank115_116_b375_two_original_gto_zero_strict_negatives.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 pathlib.Path('docs/NL2_HU_B383_RANK115_116_STRICT_GTO_ZERO_NEGATIVES.md').write_text(
   '# B383 ranks 115/116 exact original GTO source negatives\n\n'
   'Original Rust 100bb GTO solves on 7s5h3d/6c and 8s8h3d/5s both converged, '
   'but CO-IP actor at b33 c/x b50 c/x is ZERO strictly legal max/40%-70% combos '
   'on every named river runout. Sources are original, not usable for CERT. '
   'Preflop 169-class LMP ranges are assumed. 159 CERT /233 APPROX unchanged.\n')
 print('PASS B383: 2 original true GTO flops zero target actor IP; 159 CERT / 233 APPROX')
if __name__=='__main__':main()
