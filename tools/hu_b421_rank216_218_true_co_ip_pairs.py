#!/usr/bin/env python3
"""B421: two GTO-positive CO_BB public flops, paired with newly solved original Rust NL2 IP.
Ranks216_218 exact 100bb actions only. Source-only, never CERT from one board.
"""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach

D=pathlib.Path('data')
B393=D/'nl2_hu_b393_five_cobb_gto_first_three_flops.json'
OUT=D/'nl2_hu_b421_r216218_one_real_nl2_ip_original_pair.json'
DOC=pathlib.Path('docs/NL2_HU_B421_R216218_TWO_TRUE_IP_LOCKS.md')
FLOPS=('Js9h5d',)
RANKS=(216,218)
LINE='x b50 c/x b50 c/x'
PIN='abe310c3aad02dd4a7c77fb2831801fd490cf51b'
RUST='9d1509fe5077d019825f833eed04b16d342dfda1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(root,flop,ver,src):
 mp=root/'evidence'/f'CO_BB-{flop}-{ver}.json'
 if not mp.is_file():return None
 assert (root/'evidence/poker-solver-pin.txt').read_text().strip()==PIN
 assert (root/'evidence/rust-pin.txt').read_text().strip()==RUST
 m=read(mp)
 assert (m['schema'],m['spot'],m['pot_family'],m['version'],m['flop'])==(
  'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1','CO_BB','SRP',ver,flop)
 assert (m['root_pot_bb'],m['root_remaining_bb'])==(5.5,97.5)
 assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
 assert (m['flop_size_profile'],m['restricted_tree_assumption'])==('full',False)
 assert m['flop_action_sizes']==['33%','50%','75%','100%']
 assert (m['flop_line_policy'],m['selected_lines'])==('checked-b50b100only',['x b50 c','x b100 c'])
 assert m['solved_cases']==len(m['cases']) and len(m['turns'])==1
 if src is not None:assert sha(mp)==src['original_manifest_SHA256']
 if m['failures']:
  return dict(status='GENUINE_RUST_ERRORS_NO_CERT',manifest_sha256=sha(mp),manifest=m,real_cases=[])
 if not m['cases']:
  return dict(status='GENUINE_RUST_ZERO_SOLVES_NO_CERT',manifest_sha256=sha(mp),manifest=m,real_cases=[])
 fp=root/'solver/postflop'/m['file_flop']
 assert fp.is_file() and sha(fp)==m['file_flop_sha256']
 fr=read(fp);assert (fr['flop'],fr['pot'],fr['stack'])==(flop,550,9750)
 if src is not None:assert sha(fp)==src['original_root_SHA256']
 real=[]
 for c in m['cases']:
  assert c['line'] in ('x b50 c','x b100 c') and c['turn'] in m['turns']
  assert c['gto_gap_pct'] is not None and 0<=c['gto_gap_pct']<=.5
  if ver=='gto':
   assert c['status']=='GTO_EXACT_ONLY' and c['hero_gap_pct'] is None
  else:
   assert c['hero_gap_pct'] is not None and 0<=c['hero_gap_pct']<=.5
   assert c['status']=='NL2_IMPUTED_MARGINAL_LOCKED_EXPERIMENT'
  subp=root/'solver/postflop'/c['source_path']
  assert subp.is_file() and sha(subp)==c['source_sha256']
  d=read(subp)
  assert (d['flop'],d['turn'],d['line0'])==(flop,c['turn'],c['line'])
  masks,stats=game_reach(fr,d)
  target={}
  for n in d['nodes']:
   if n['player']!=1 or n['line']!=LINE or len(n['board'])!=10:continue
   q=masks['|'.join((n['board'],n['line'],'1'))]
   target[n['board']]=dict(public_board=n['board'],
     strict_40_70_IP_hero_combos=q['count'],
     exact_SPR=round((d['stack']-max(n['bets']))/n['pot'],6),
     parent_actor_decisions=q['parent_actor_decisions'])
  real.append(dict(line=c['line'],turn=c['turn'],source_sha256=c['source_sha256'],
    original_GTO_gap_pct=c['gto_gap_pct'],original_hero_gap_pct=c['hero_gap_pct'],
    actor_IP_target_nodes=target,strict_fullstreet_reach_stats=dict(stats)))
 return dict(status='GENUINE_RUST_EXACT_SOURCE',manifest_sha256=sha(mp),
   root_original_Rust_SHA256=sha(fp),original_root_job_sha256=sha(fp.with_suffix('.job.json')),
   preflop_source_SHA256=m['preflop_ranges']['full_sha256'],
   pool_stats_SHA256=m['pool_source_sha256'],manifest=m,real_cases=real)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--gto-root',type=pathlib.Path,required=True)
 ap.add_argument('--exp-root',type=pathlib.Path,required=True)
 ap.add_argument('--run-id',type=int,required=True)
 a=ap.parse_args()
 first=read(B393)
 assert first['schema']=='NL2_B393_FIVE_COBB_APPROX_THREE_FROZEN_ORIGINAL_GTO_ONLY_V1'
 assert first['original_run_id']==45026396521
 for rank in RANKS:
  assert first['distinct_new_GTO_positive_flops_by_rank'][str(rank)]==list(FLOPS)[::-1] or set(first['distinct_new_GTO_positive_flops_by_rank'][str(rank)])==set(FLOPS)
  assert first['models'][str(rank)]['exact_line']==LINE
 status=read(D/'nl2_hu_multiboard_status_v50_b417_rank166.json')
 assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(163,229,0,392)
 rows=[]
 positives={str(rank):[] for rank in RANKS}
 for flop in FLOPS:
  src=next(x for x in first['real_original_GTO_only_solve_sources'] if x['flop']==flop)
  assert src['source_status']=='ORIGINAL_GTO_ANY_TARGET_POSITIVE'
  nameg=f'nl2-multiboard-B393_COBB_FIVE_GTO_FIRST-CO_BB-{flop}-gto'
  namee=f'nl2-multiboard-B421_R216218_NL2_IP-CO_BB-{flop}-exp_ip'
  original=check(a.gto_root/nameg,flop,'gto',src)
  partial=check(a.exp_root/namee,flop,'exp_ip',None)
  assert original and original['status']=='GENUINE_RUST_EXACT_SOURCE'
  assert original['manifest']['solved_cases']==2
  paired=[]
  if partial and partial['status']=='GENUINE_RUST_EXACT_SOURCE':
   assert original['preflop_source_SHA256']==partial['preflop_source_SHA256']
   assert original['pool_stats_SHA256']==partial['pool_stats_SHA256']
   for rank in RANKS:
    wanted=first['exact_actor_IP_positive_river_nodes_by_model'][str(rank)]
    for q in wanted:
     if q['flop']!=flop:continue
     board=q['public_board']
     gcase=next(c for c in original['real_cases'] if c['turn']==q['turn'] and c['source_sha256']==q['original_GTO_sha256'])
     ecase=next((c for c in partial['real_cases'] if c['line']==gcase['line'] and c['turn']==gcase['turn']),None)
     if ecase is None:continue
     g=gcase['actor_IP_target_nodes'][board]
     n=ecase['actor_IP_target_nodes'].get(board)
     assert g['strict_40_70_IP_hero_combos']==q['legal_full_street_40_70_combos']>0
     if not n or n['strict_40_70_IP_hero_combos']<=0:continue
     assert abs(g['exact_SPR']-n['exact_SPR'])<1e-5
     expected=status['records'][first['models'][str(rank)]['model_id']]['assumed_model_node_spr']
     assert abs(g['exact_SPR']-expected)/max(1,g['exact_SPR'])<=.05
     entry=dict(rank=rank,flop=flop,turn=q['turn'],exact_public_board=board,
       actor='CO_IP',exact_history=LINE,actual_SPR=g['exact_SPR'],
       GTO_strict_40_70_combos=g['strict_40_70_IP_hero_combos'],
       actual_NL2_IP_strict_40_70_combos=n['strict_40_70_IP_hero_combos'],
       original_GTO_source_run=45026396521,original_GTO_sha256=q['original_GTO_sha256'],
       new_NL2_IP_source_run=a.run_id,new_NL2_IP_sha256=ecase['source_sha256'])
     positives[str(rank)].append(entry)
     paired.append(entry)
  rows.append(dict(flop=flop,original_GTO=original,actual_partial_NL2_IP=partial,
    exact_GTO_NL2_IP_positive_named_river_nodes=paired,
    distinct_matched_true_source_flops=set(x['flop'] for x in paired) and [flop] or [],
    original_GTO_artifact=nameg,new_NL2_IP_artifact=namee))
 eligible={rank:sorted(set(x['flop'] for x in positives[str(rank)])) for rank in RANKS}
 out=dict(schema='NL2_B421_RANK216_218_ONE_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIR_V1',
  B393_frozen_original_GTO_source_sha256=sha(B393),original_GTO_run=45026396521,
  new_NL2_IP_run=a.run_id,spot='CO_BB',actor='CO_IP',exact_line=LINE,
  source_poker_solver_pin=PIN,original_Rust_pin=RUST,source_evidence=rows,
  positive_40_70_named_river_pairs_by_rank=positives,
  new_distinct_qualifying_flops_by_rank={str(k):v for k,v in eligible.items()},
  original_preflop_CFR_not_NL2_observed_private_actions=True,
  opponent_NL2_is_pool_marginal_proxy_not_exact_private_hand=True,
  no_automatic_CERT_while_no_three_independent_original_sources=True,
  no_2026_private_hand_NL2_observations_used=True,
  CERT_MULTIBOARD=162,APPROX=230,EST=0,PR2_remains_draft_unmerged=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 DOC.write_text('# B421 ranks216/218 real CO-IP NL2 partial-lock after B393 source-first\n\n'
   'Frozen source flop Js9h5d. Real Rust full 100bb GTO original and new NL2 IP partially locked '
   'sources must have the same public runout, x b50 c/x b50 c/x line, original SHA and strictly legal sequential 40/70 combos. '
   +'; '.join(f'rank{k}: {len(v)} matched distinct new flops' for k,v in eligible.items())
   +'. Certification still requires independent 3-distinct-flop source audit; '
   'NL2 pool frequency is aggregated marginal and not villain per-private-card observation. 163 CERT/229 APPROX until promotion.\n')
 print('PASS B421 original GTO/NL2 CO-IP paired source check',eligible,'new flops; no early CERT')
if __name__=='__main__':main()
