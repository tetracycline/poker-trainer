#!/usr/bin/env python3
"""B344: SHA-verify original genuine restricted 100bb LMP GTO positive B50 roots and full rank71 actor ancestry.
Do not treat flop-positive as river-positive. Does not certify new generic model or observe private-card NL2 rates.
"""
import argparse, pathlib, hashlib, gzip, json, sys
from hu_sequential_cfr_reach import accepted,game_reach
D=pathlib.Path(__file__).resolve().parents[1]/'data'
CASES=[
 ('B19_LMP50_RESTRICTED',44762388523,'4s4h2d'),
 ('B26_LMP_NONPAIRED',44769773770,'7s5h3d'),
 ('B26_LMP_NONPAIRED',44769773770,'2s4h6d'),
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser()
 a.add_argument('--download-root',type=pathlib.Path,required=True)
 a.add_argument('--out',type=pathlib.Path,required=True)
 q=a.parse_args()
 records=[]
 for batch,run,flop in CASES:
  indexfile=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.index.json'
  gzfile=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.json.gz'
  idx=json.loads(indexfile.read_text())
  raw=gzip.decompress(gzfile.read_bytes());proof=json.loads(raw)
  assert idx['run_id']==run and sha(gzfile)==idx['gzip_sha256']
  assert hashlib.sha256(raw).hexdigest()==idx['source_sha256']
  assert not proof['errors'] and proof['source_run_id']==run
  art=next(x for x in proof['artifacts'] if x['flop']==flop and x['version']=='gto')
  assert not art['errors'] and art['cases']
  case=next(x for x in art['cases'] if x['flop_line']=='b50 c')
  folder=q.download_root/f'{batch}-{flop}'
  root=folder/f'solver/postflop/out/LMP_CO_BB/gto/{flop}_multiboard.json'
  manifest=folder/f'evidence/LMP_CO_BB-{flop}-gto.json'
  assert manifest.is_file()
  sub=folder/'solver/postflop'/json.loads(manifest.read_text())['cases'][0]['source_path']
  assert all(x.is_file() for x in (root,sub,manifest))
  assert case['flop_source_sha256']==sha(root) and case['source_sha256']==sha(sub)
  mf=json.loads(manifest.read_text()); fr=json.loads(root.read_text());su=json.loads(sub.read_text())
  assert mf['flop']==flop and mf['version']=='gto'
  assert (mf['flop_size_profile'],mf['restricted_tree_assumption'])==('lmp-50-only',True)
  assert fr['info']['gto_expl_pct']<=.5 and su['info']['gto_expl_pct']<=.5
  assert (fr['pot'],fr['stack'])==(250,9900)
  assert mf['selected_lines']==['b50 c'] and mf['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
  roots=[n for n in fr['nodes'] if n['line']=='' and n['player']==0 and len(n['board'])==6]
  assert len(roots)==1 and roots[0]['acts']==['x','b50']
  legal=accepted(roots[0],fr['hands'],'b50')
  nodes,stat=game_reach(fr,su)
  river=[v['count'] for k,v in nodes.items() if '|b50 c/x b50 c/|0' in k]
  assert river and len(legal)>0
  records.append(dict(flop=flop,source_batch=batch,original_run_id=run,restricted_root_action_choices=['x','b50'],
    root_legally_reachable_b50_OOP_combos=len(legal),GTO_actor_OOP_exact_turn_river_strict_combos=sum(river),
    GTO_actor_OOP_positive_river_nodes=sum(x>0 for x in river),
    source_original_GTO_full_flop_root_sha256=sha(root),
    source_original_GTO_turn_river_sha256=sha(sub),manifest_sha256=sha(manifest),
    already_certified_rank71_distinct_flop=flop in ('4s4h2d','7s5h3d'),
    new_flop_has_positive_root_but_zero_exact_river=(flop=='2s4h6d' and sum(river)==0),
    no_unknown_turn_or_texture_negative_extrapolation=True))
 assert [(x['flop'],x['root_legally_reachable_b50_OOP_combos']) for x in records]==[
   ('4s4h2d',248),('7s5h3d',2),('2s4h6d',6)]
 assert [(x['flop'],x['GTO_actor_OOP_exact_turn_river_strict_combos']) for x in records]==[
   ('4s4h2d',45),('7s5h3d',2),('2s4h6d',0)]
 result=dict(schema='NL2_HU_B344_HISTORICAL_RESTRICTED_50_RANK71_VERIFIED_POSITIVE_FLOP_V1',
    exact_source_records=records,
    same_comparable_restricted_100bb_original_b19_b26_tree=True,
    legal_flop_is_not_sufficient_for_legal_exact_turn_river=True,
    new_B343_flops_need_independent_original_GTO_and_real_NL2_OOP_lock=True,
    no_generic_suit_isomorphic_Certification=True,
    no_unrestricted_tree_claim=True,preflop_ranges_assumed_not_real_NL2=True,
    historical_model_CERT=156,historical_model_APPROX=236,PR2_Draft_NEVER_MERGE=True)
 q.out.parent.mkdir(parents=True,exist_ok=True)
 q.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('PASS B344 historical original positive B50 roots with exact downstream strict',[(x['flop'],
   x['root_legally_reachable_b50_OOP_combos'],x['GTO_actor_OOP_exact_turn_river_strict_combos']) for x in records])
if __name__=='__main__':main()
