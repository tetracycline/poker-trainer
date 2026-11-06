"""Re-aggregate the MW approximation with common display classes. Locked
models supply follow-up responses only; a locked earlier action is not advice.
"""
import json,math
from pathlib import Path
from collections import defaultdict
from run10_common import classes
from run10_reach import reaches,metrics
B=Path('/workspace/outputs/poker_lines_v2');O=B/'results/run10';A={'x':'過牌','f':'棄牌','c':'跟注','r':'加注','small':'小注','big':'大注'}
def main():
 manifest=json.load(open(O/'mw_manifest.json'));acc=defaultdict(list)
 for m in manifest:
  for locked in [False,True]if m['locked']else[False]:
   path=Path(m['path']if locked else m['source']);d=json.load(open(path));j=json.load(open(path.with_suffix('.job.json')));p=m['player'];nodes=[n for n in d['nodes']if n['player']==p];rr=reaches(d,j,nodes);nh=len(d['hands'][p])
   for n in nodes:
    cur=n['line'].split();facing='f'in n['acts'];ag=sum(a.startswith(('b','r','a'))for a in cur);nd=m['job'][0]+('_vs_3b'if facing and ag>=3 else'_vs_xr'if facing and ag>=2 else'_vs_bet'if facing else'_bet')
    if locked!=('vs_xr'in nd and m['locked']):continue
    for cl in ['S','TPG','TPW','MID','DRAW','WDRAW','AIR']:
     mt,inds,jw=metrics(d,j,n,rr[(n['board'],n['line'])],cl)
     if not inds or mt['base_mass']<=1e-12:continue
     f=defaultdict(float)
     for k,a in enumerate(n['acts']):f[a if a in ['x','c','f']else'r'if facing else'small'if a in ['b33','b50']else'big']+=sum(jw[i]*n['strat'][k*nh+i]for i in inds)
     z=sum(f.values())
     if z<=1e-12:continue
     acc[nd+'|'+m['role']+'|'+cl].append(dict(job=m['job'],path=str(path),board=n['board'],line=n['line'],player=p,reach=mt,joint_reach=z,locked=locked,counterfactual=False,freq={a:v/z for a,v in f.items()},spr=(d['stack']-max(n['bets']))/n['pot'],pot=n['pot']/100,info=d['info']))
 out={}
 for key,vs in acc.items():
  groups=defaultdict(list)
  for v in vs:groups[v['job']].append(v)
  f=defaultdict(float)
  for samples in groups.values():
   z=sum(v['joint_reach']for v in samples)
   for v in samples:
    for a,p in v['freq'].items():f[a]+=p*v['joint_reach']/z/len(groups)
  out[key]=dict(freq=dict(f),samples=vs)
 # Reclassify closing calls from saved hand-level records and split 3-bets.
 obs=json.load(open(B/'results/run8/mw_calls.json'))['observations'];groups=defaultdict(list)
 for v in obs:
  e=v['eg'];v=dict(v,hc=classes(e['h'],e['b'])[0]);acts=[tk.split(':',1)[1]for tk in e['l'].split('/')[-1].split()];ag=sum(a.startswith(('b','r','a'))for a in acts)
  if v['nd']=='r_vs_xr':
   mine=[tk.split(':',1)[1]for tk in e['l'].split('/')[-1].split()if tk.split(':',1)[0]==e['me']]
   hero_raised=any(a.startswith('r')for a in mine);hero_bet=any(a.startswith(('b','a'))for a in mine)
   v['nd']='r_vs_3b'if hero_raised else'r_vs_reraise'if hero_bet and ag>=3 else'r_vs_xr'if hero_bet else'r_vs_cold_raise'
  groups[v['nd']+'|'+v['hc']].append(v)
 pool={}
 for key,vs in groups.items():
  n=len(vs);w=sum(v['w']for v in vs);p=100*w/n;need=100*sum(v['need']for v in vs)/n;e=1.96*math.sqrt(max((p/100)*(1-p/100),1e-9)/n)*100;a='c'if p>=need else'f'
  pool[key]=dict(w=w,n=n,need=need,ci=[p-e,p+e],closes=True,significant=n>=40 and abs(p-need)>e,a=a,ok=[]if abs(p-need)>e else['f'if a=='c'else'c'],examples=[v['eg']for v in vs[:6]])
 json.dump(dict(cells=out,pool=pool),open(O/'mw_common.json','w'),ensure_ascii=False);print('MW cells',len(out),'jobs',len(manifest),'pool',len(pool))
def apply(out):
 pack=json.load(open(O/'mw_common.json'));original={(r['nd'],r['c']['hr'],r['hc'][0]):r for r in out['rows']if r['sp']=='mw'}
 for r in out['rows']:
  if r['sp']!='mw':continue
  key=r['nd']+'|'+r['c']['hr']+'|'+r['hc'][0];v=pack['cells'].get(key)
  if not v:continue
  f=v['freq'];freq='／'.join(f'{A[a]} {p*100:.1f}%'for a,p in sorted(f.items(),key=lambda kv:-kv[1]));locked=any(s['locked']for s in v['samples']);r['classifier']='common-hcls-v2'
  baseline=dict(freq=f,samples=v['samples']);pool=pack['pool'].get(r['nd']+'|'+r['hc'][0])
  if r['b']=='pool'and pool and pool['significant']:
   r.update(a=pool['a'],ok=pool['ok'],river_pool={k:pool[k]for k in ['w','n','need','ci','closes']},baseline=baseline,eg=pool['examples']);out['mw_grid']['cells'][r['nd']+'|'+r['hc'][0]]={k:pool[k]for k in ['w','n','need','ci','closes']};r['ev']=f"玩家池 UTG–BB；跟注即結束行動；common.hcls；n={pool['n']}；勝率 {100*pool['w']/pool['n']:.2f}%；95% CI {pool['ci'][0]:.2f}–{pool['ci'][1]:.2f}%；需要 {pool['need']:.2f}% → 顯著；GTO 近似基準："+freq
  else:
   r.update(a=max(f,key=f.get),ok=[a for a,p in f.items()if a!=max(f,key=f.get)and p>=.3],b='gtoa',evidence='run10-mw:'+key,solver=baseline,why='GTO 近似：'+freq);r.pop('river_pool',None)
   r['ev']='GTO 近似（兩人 solver）：沿用 run9c 的真實底池／剩餘深度及最強對手分布模型，忽略對手彼此撞牌、聽牌未來潛力；每街從翻前重建，非多人均衡。common.hcls；逐職責與牌面聚合；下注半池、加注全下；抽水 5% cap10bb。'+('先前英雄下注按 HW 逐職責／街／牌型實測頻率鎖定（Jeffreys 0.5 平滑，原始小樣本及回退鍵見 run10 鎖定紀錄），後續回應另行求解，沒有使用零自身到達的反事實頻率。'if locked else'採用原始未鎖定模型的可到達節點。')+'頻率：'+freq
  r['eg']=[e for e in r.get('eg',[])if r['hc'][0]in classes(e['h'],e['b'])]
 out['notes']=[n for n in out['notes']if '反事實回應'not in n]
if __name__=='__main__':main()
