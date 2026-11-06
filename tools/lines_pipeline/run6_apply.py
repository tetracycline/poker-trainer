"""Publish only evidence-backed additions; preserve one exact cell key.
Run run6_extract.py and run6_river_extract.py first. Missing evidence stays
visible to the strict contract/QA, never replaced by a made-up action.
"""
import json,re
from pathlib import Path
B=Path('/workspace/outputs/poker_lines_v2');O=B/'results/run6'

def supported_pool(r):
 e=r.get('ev','')
 return r.get('b')!='pool' or (bool(re.search(r'95%\s*CI',e)) and bool(re.search(r'GTO\s*基準',e)) and not bool(re.search(r'無.*GTO.*基準',e)) and bool(re.search(r'n=([\d,]+)',e)))

def apply(out,cond_lab):
 rows=out['rows'];removed=[];added=[];replaced=[]
 for r in list(rows):
  if not supported_pool(r):rows.remove(r);removed.append(r)
 candidates=[]
 p=O/'additions.json'
 if p.exists():pack=json.load(open(p));candidates+=pack['rows']
 p=O/'river_additions.json'
 if p.exists():candidates+=json.load(open(p))
 # Prefer the dedicated river tree for responses, including 150% bets/raises.
 unique={}
 for r in candidates:
  for hc in r['hc']:unique[(r['sp'],r['nd'],hc,json.dumps(r.get('c')or{},sort_keys=True))]=r
 for (sp,nd,hc,cond),r in unique.items():
  if any(x['sp']==sp and x['nd']==nd and hc in x['hc'] and json.dumps(x.get('c')or{},sort_keys=True)==cond for x in rows):continue
  r=dict(r);r['hc']=[hc];r['cl']=cond_lab(r.get('c'));rows.append(r);added.append(r)
 if (O/'example_bank.json').exists():
  bank=json.load(open(O/'example_bank.json'))['rows']
  index={}
  for r in bank:
   for hc in r['hc']:
    index[(r['sp'],r['nd'],hc,json.dumps(r.get('c')or{},sort_keys=True))]=r['eg']
  for r in rows:
   eg=[]
   for hc in r['hc']:
    for e in index.get((r['sp'],r['nd'],hc,json.dumps(r.get('c')or{},sort_keys=True)),[]):
     if e not in eg:eg.append(e)
   if eg:r['eg']=eg[:6]
 # IDs assigned after all replacements. Solver provenance stays in separate
 # reproducibility artifacts; production rows retain a compact evidence ID.
 for i,r in enumerate(rows):
  r['id']=f"{r['sp']}.{r['nd']}.{i}";r['cl']=cond_lab(r.get('c'))
  if r.get('evidence','').startswith('run6:'):
   samples=r['solver']['samples'];paths={v['path']for v in samples}
   sources=pack['sources']
   sizes=set()
   for p in paths:
    j=json.load(open(sources[p]['job']));prefix='flop_'if r['nd'].startswith('f_')or'_f_'in r['nd'] else'turn_'if r['nd'].startswith('t_')or'_t_'in r['nd'] else'river_'
    for k in [prefix+'oop',prefix+'ip']:
     sizes.update(v for v in j.get(k,'').split(',')if v)
   if sizes=={'66%'}:r['L']={'big':'下注約 ⅔ 池'}
   elif prefix=='river_'and sizes=={'75%'}:r['L']={'big':'下注 ¾ 池'}
  r.pop('solver',None)
 out['built']='2026-11-06';out['ver']='lines-run6'
 out['notes'].append('第六次補算的範圍、牌面、下注樹與每次實際迭代／可剝削度，保存在第六次求解紀錄。河牌聽牌欄指轉牌聽牌未完成且河牌沒有成對的子集；多人池缺有效比較的格子仍由完整性檢查列為缺口。')
 stats=dict(before=len(json.load(open(O/'before.json'))['rows']),after=len(rows),added=len(added),removed=len(removed),added_by_spot_street={},removed_ids=[r['id']for r in removed])
 from collections import Counter
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from lines_contract import street,diff
 stats['added_by_spot_street']={'|'.join(k):v for k,v in Counter((r['sp'],street(r['nd']),r['b'])for r in added).items()};stats['unresolved']=diff(out)
 json.dump(stats,open(O/'audit.json','w'),ensure_ascii=False,indent=2)
 audit=json.load(open(B/'results/audit.json'))
 for entry in audit:
  if entry.get('disposition')=='pool' and any(entry['sp']==r['sp'] and entry['nd']==r['nd'] and set(entry['hc']) & set(r['hc']) and (entry.get('condition')or{})==(r.get('c')or{}) for r in removed):
   entry.update(disposition='removed',new_action=None,reason='run6：缺同節點 GTO 基準或 95% CI；依本次一致證據規則撤下。')
   if 'retained_classes' in entry:entry.update(retained_classes=[],removed_classes=entry.get('source_hc',entry['hc']))
 for r in added:audit.append(dict(old_id=None,sp=r['sp'],nd=r['nd'],hc=r['hc'],condition=r.get('c'),old_basis=None,old_action=None,new_action=r['a'],disposition=r['b'],reason='run6：實際求解策略；詳細來源見 results/run6。',evidence=r['evidence']))
 json.dump(audit,open(B/'results/audit.json','w'),ensure_ascii=False,indent=2)
 return stats
