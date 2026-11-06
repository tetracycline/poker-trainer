"""Restore significant old pool cells alongside the existing exact-cell solve."""
import json,re,copy
from pathlib import Path
from collections import defaultdict
B=Path('/workspace/outputs/poker_lines_v2');O=B/'results/run7'
def key(r,h):return r['sp'],r['nd'],h,json.dumps(r.get('c')or{},sort_keys=True)
def apply(out,cond_lab):
 rows=out['rows'];old=json.load(open(B/'results/run6/before.json'))['rows'];audit=[]
 solved={}
 for p in ['additions.json','river_additions.json']:
  d=json.load(open(B/'results/run6'/p))
  for r in d.get('rows',[]) if isinstance(d,dict) else d:
   for h in r['hc']:solved[key(r,h)]=r
 for r in old:
  if r['b']!='pool' or r['sp']=='mw':continue
  for h in r['hc']:
   k=key(r,h);current=next((x for x in rows if k in [key(x,c)for c in x['hc']]),None)
   if current and current['b']=='pool':continue
   ev=r['ev'];n=[int(v.replace(',',''))for v in re.findall(r'n=([\d,]+)',ev)]
   sig='顯著' in ev and not re.search('不明顯|不顯著',ev)
   # The stored policy used unrounded rates/thresholds. Rounded display
   # intervals can touch even when the underlying test was significant.
   item=dict(old_id=r['id'],sp=r['sp'],nd=r['nd'],hc=h,condition=r.get('c')or{},n=n)
   if not sig or not n or min(n)<40:
    item.update(status='dropped',reason='stored 95% CI does not exclude threshold, or n<40');audit.append(item);continue
   baseline=solved.get(k);subset=False
   if baseline is None and (r.get('c')or{}).get('ct'):
    from common import ctype
    cond=dict(r['c']);ct=cond.pop('ct');samples=[];seen=set()
    for sk,v in solved.items():
     if sk[:3]!=k[:3] or not all((v.get('c')or{}).get(c)==x for c,x in cond.items()):continue
     for s in v['solver']['samples']:
      if ctype(s['board'],3)!=ct:continue
      tag=json.dumps(s,sort_keys=True)
      if tag not in seen:samples.append(s);seen.add(tag)
    if samples:
     freq={a:sum(s['freq'].get(a,0)for s in samples)/len(samples)for a in set(a for s in samples for a in s['freq'])}
     baseline=dict(evidence='run7:subset-of-run6',solver=dict(freq=freq,samples=samples),a=max(freq,key=freq.get));subset=True
   if baseline is None:
    item.update(status='blocked',reason='No run-6 solve sample with exact condition');audit.append(item);continue
   freq=baseline['solver']['freq'];target=copy.deepcopy(r);target.update(hc=[h],b='pool',evidence='run7:restored:'+r['id']+':'+h)
   target['ev']=re.sub(r'；?此節點無 GTO 基準','',ev)+'｜GTO 基準（同格第六次求解'+('牌面條件子集'if subset else '')+'）：最高頻 '+max(freq,key=freq.get)+'；動作頻率 '+json.dumps(freq,ensure_ascii=False)+'；來源 '+baseline['evidence']
   target['gto_baseline']=dict(action=max(freq,key=freq.get),freq=freq,evidence=baseline['evidence'],subset=subset)
   target['eg']=current['eg'] if current and current.get('eg') else target['eg']
   if current:
    current['hc']=[c for c in current['hc']if c!=h]
    if not current['hc']:rows.remove(current)
   rows.append(target);item.update(status='restored',baseline=target['gto_baseline']);audit.append(item)
 mw=json.load(open(O/'mw.json'));rows[:]=[r for r in rows if r['sp']!='mw']+mw['rows']
 out['mw_grid']=dict(observation_count=len(mw['observations']),columns=[{}],label='全部',hands={nd:[r['hc'][0]for r in mw['rows']if r['nd']==nd]for nd in ['f_bet','f_vs_bet','f_vs_xr','t_bet','t_vs_bet','t_vs_xr','r_bet','r_vs_bet','r_vs_xr']},cells=mw['cells'],evidence='results/run7/mw.json')
 for i,r in enumerate(rows):r['id']=f"{r['sp']}.{r['nd']}.{i}";r['cl']=cond_lab(r.get('c'))
 out.update(ver='lines-run7',built='2026-11-06')
 out['basis']['pool']='玩家池數據（n≥40；95% CI，方法與偏差見每列）'
 out['notes'].append('多人欄位合併為全部；只納入發牌時已知底牌的實現淨bb比較，每個比較動作至少40筆。不足的牌型不出題。')
 json.dump(audit,open(O/'restoration.json','w'),ensure_ascii=False,indent=2)
