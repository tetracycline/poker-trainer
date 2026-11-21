#!/usr/bin/env python3
"""Make a display delta from independently audited raw CFR and sequential masks.
No inferred/model data, no source probabilities or best-EV edits."""
import argparse, base64, collections, gzip, hashlib, json, pathlib
p=argparse.ArgumentParser()
p.add_argument('--exact',action='append',required=True,type=pathlib.Path)
p.add_argument('--reach',action='append',required=True,type=pathlib.Path)
p.add_argument('--output',required=True,type=pathlib.Path)
a=p.parse_args()
games={}
for f in a.exact:
 d=json.loads(f.read_bytes())
 assert d['schema']=='HU_NL2_EXACT_BOARD_CFR_V1' and d['generic_model_upgrades']==0
 for s in d['subgames']:
  assert s['source_sha256'] not in games
  games[s['source_sha256']]=s
out={}
for f in a.reach:
 proof=f.read_bytes();r=json.loads(proof)
 assert r['schema']=='HU_SEQUENTIAL_HIGHEST_ACTION_REACH_AUDIT_V1' and not r['errors']
 for sg in r['subgames']:
  sha=sg['source_sha256']
  assert sha not in out
  game=games[sha];raws={(n['board'],n['line'],n['acting_seat']):n for n in game['nodes']}
  assert len(raws)==len(sg['nodes'])
  assert sg['hands_by_seat']==game['hands_by_seat']
  nodes={}
  for v in sg['nodes']:
   key=(v['board'],v['line'],v['actor']);n=raws[key]
   assert v['actions']==n['actions'] and v['raw_actor_reachable_combos']==n['reachable_combos']
   x=base64.b64decode(v['path_eligible_action_masks_b64'],validate=True)
   y=base64.b64decode(n['eligible_action_masks_b64'],validate=True)
   assert len(x)==len(y) and all((a&b)==a for a,b in zip(x,y))
   assert sum(bool(i) for i in x)==v['path_actor_reachable_combos']
   cards=set(v['board'][i:i+2] for i in range(0,len(v['board']),2))
   assert all(not bits or cards.isdisjoint({h[:2],h[2:]}) for h,bits in zip(sg['hands_by_seat'][v['actor']],x))
   node_key='|'.join(map(str,key));assert node_key not in nodes
   nodes[node_key]={'count':v['path_actor_reachable_combos'],'mask':v['path_eligible_action_masks_b64']}
  out[sha]={'proof_sha256':hashlib.sha256(proof).hexdigest(),'parent_sha256':sg['parent_sha256'],'nodes':nodes}
data={'schema':'HU_NL2_SEQUENTIAL_REACH_OVERLAY_V1','scope':'Navigation filtering through actual ancestor action frequencies, not a GTO re-solve under pruned ranges.','subgames_by_source_sha256':out}
a.output.write_bytes(gzip.compress((json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
print(json.dumps({'source_games':len(out),'decision_nodes':sum(len(s['nodes']) for s in out.values()),'gzip_bytes':a.output.stat().st_size}))
