#!/usr/bin/env python3
"""B385 rank232 two genuine source flops, exact SB-OOP original Rust GTO and NL2 marginal lock only."""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path('data')
FLOPS=('7s5h3d','8s8h3d')
TARGET='x b33 c/x x/'
PIN='abe310c3aad02dd4a7c77fb2831801fd490cf51b'
RUST='9d1509fe5077d019825f833eed04b16d342dfda1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--downloads',type=pathlib.Path,required=True);ap.add_argument('--run-id',type=int,required=True)
 a=ap.parse_args();all_sources=[];gates={}
 for flop in FLOPS:
  for version in ('gto','exp_oop'):
   folder=a.downloads/f'nl2-multiboard-B385_R232-SB3_BTN-{flop}-{version}'
   mp=folder/'evidence'/f'SB3_BTN-{flop}-{version}.json'
   record=dict(flop=flop,version=version,artifact=folder.name,manifest_present=mp.is_file(),cases=[])
   if not mp.is_file():
    record['explicit_negative']='ORIGINAL_RUST_MANIFEST_MISSING_OR_UNFINISHED'
    all_sources.append(record);continue
   assert (folder/'evidence/poker-solver-pin.txt').read_text().strip()==PIN
   assert (folder/'evidence/rust-pin.txt').read_text().strip()==RUST
   m=read(mp)
   assert (m['schema'],m['spot'],m['pot_family'],m['version'],m['flop'])==(
    'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1','SB3_BTN','3BP',version,flop)
   assert (m['root_pot_bb'],m['root_remaining_bb'])==(21.0,90.0)
   assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
   assert m['flop_size_profile']=='full' and m['flop_action_sizes']==['33%','50%','75%','100%']
   assert not m['restricted_tree_assumption']
   assert (m['flop_line_policy'],m['selected_lines'])==('checked-b33only',['x b33 c'])
   assert len(m['turns'])==1 and m['solved_cases']==len(m['cases'])
   fp=folder/'solver/postflop'/m['file_flop']
   assert fp.is_file() and sha(fp)==m['file_flop_sha256']
   fr=read(fp);assert (fr['flop'],fr['pot'],fr['stack'])==(flop,2100,9000)
   record.update(manifest_SHA256=sha(mp),original_flop_SHA256=sha(fp),
     job_SHA256=sha(fp.with_suffix('.job.json')),
     authentic_solve_errors=m['failures'],real_solved_cases=m['solved_cases'])
   for c in m['cases']:
    assert c['line']=='x b33 c' and c['turn'] in m['turns']
    assert c['gto_gap_pct'] is not None and c['gto_gap_pct']<=.5
    if version=='exp_oop':
     assert c['hero_gap_pct'] is not None and c['hero_gap_pct']<=.5
     assert any(int(x.get('n') or 0)>=500 for x in m['locks'])
     assert any(x.get('nodes',0)>0 for x in c['lock_stats'].values())
    path=folder/'solver/postflop'/c['source_path']
    assert path.is_file() and sha(path)==c['source_sha256']
    d=read(path);assert (d['flop'],d['turn'],d['line0'])==(flop,c['turn'],'x b33 c')
    reach,stats=game_reach(fr,d)
    exact=[]
    for n in d['nodes']:
     if n['line']==TARGET and n['player']==0 and len(n['board'])==10:
      q=reach['|'.join((n['board'],n['line'],'0'))]
      exact.append(dict(public_board=n['board'],strict_actor_SB_OOP_combos=q['count'],
       actual_spr=round((d['stack']-max(n['bets']))/n['pot'],6)))
    item=dict(turn=c['turn'],source_SHA256=c['source_sha256'],
     GTO_gap_pct=c['gto_gap_pct'],hero_gap_pct=c['hero_gap_pct'],
     authentic_strict_full_street_stats=dict(stats),exact_SB_OOP_target_runouts=exact)
    record['cases'].append(item);gates[(flop,version)]=item
   all_sources.append(record)
 paired=[]
 for flop in FLOPS:
  g,e=gates.get((flop,'gto')),gates.get((flop,'exp_oop'))
  if not g or not e or g['turn']!=e['turn']:continue
  gnodes={x['public_board']:x for x in g['exact_SB_OOP_target_runouts'] if x['strict_actor_SB_OOP_combos']>0}
  enodes={x['public_board']:x for x in e['exact_SB_OOP_target_runouts'] if x['strict_actor_SB_OOP_combos']>0}
  for board in sorted(set(gnodes)&set(enodes)):
   x,y=gnodes[board],enodes[board];spr=x['actual_spr']
   if abs(spr-y['actual_spr'])>1e-6 or abs(spr-2.371)/max(1,spr)>.05:continue
   paired.append(dict(flop=flop,turn=g['turn'],public_board=board,
    actor='SB_OOP',exact_line=TARGET,actual_spr=spr,
    original_GTO_true_combo_count=x['strict_actor_SB_OOP_combos'],
    true_NL2_partial_lock_combo_count=y['strict_actor_SB_OOP_combos'],
    GTO_source_sha256=g['source_SHA256'],NL2_source_sha256=e['source_SHA256']))
 s=read(D/'nl2_hu_multiboard_status_v47_b364_rank96.json')
 mid='ln-3bp-3b_r_model-19o21hu'
 assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'])==(159,233,0)
 assert (s['records'][mid]['label'],s['records'][mid]['frequency_rank'])==('APPROX',232)
 b=read(D/'nl2_hu_b370_first10_approx_source_triage.json')
 first=next(x for x in b['source_blind_selected_ten'] if x['frequency_rank']==232)
 assert first['true_paired_measured_NL2_hero_lock_flops']==1 and first['strictly_measured_pairs'][0]['flop']=='KsQh4d'
 result=dict(schema='NL2_B385_RANK232_TWO_ACTUAL_3BP_GTO_NL2_OOP_STRICT_SOURCES_V1',
  run_id=a.run_id,rank=232,model_id=mid,spot='SB3_BTN',family='3BP',
  original_source_poker_solver_pin=PIN,original_Rust_pin=RUST,
  exact_target_actor='SB_OOP',exact_line=TARGET,
  newly_solving_distinct_flops=list(FLOPS),original_Rust_source_artifacts=all_sources,
  strict_full_street_GTO_NL2_OOP_paired_public_runouts=paired,
  new_distinct_qualifying_flops=sorted({x['flop'] for x in paired}),
  existing_exact_KsQh4d_qualifying_flop_not_counted_twice=True,
  no_2026_opponent_private_hand_source_claim=True,
  no_CERT_upgrade_without_separate_three_flop_proof=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,PR2_draft_never_merge=True)
 (D/'nl2_hu_b385_rank232_3bp_two_flop_strict_source_proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 pathlib.Path('docs/NL2_HU_B385_RANK232_TRUE_TWO_FLOP_SOURCES.md').write_text(
  '# B385 rank232 genuine 3BP SB-OOP 100bb source-only\n\n'
  +f"Strict new exact GTO + partial NL2 SB-OOP river pairs: {len(paired)} "
  +f"from {len(result['new_distinct_qualifying_flops'])} different flops. "
  +'Original preflop CFR is pinned, opponent NL2 marginal frequencies are not actual private combo observations. '
  +'No CERT before 3 distinct exact correct-actor/SPR/full-reach flops pass the independent registry gate. '
  +'159 CERT / 233 APPROX unchanged.\n')
 print('PASS B385 source-only true runouts',len(paired),'new distinct flops',result['new_distinct_qualifying_flops'],'CERT159 APPROX233')
if __name__=='__main__':main()
