"""Run 8 publication: shared river verdict, closing calls, precise solve labels."""
import json,math,re
from pathlib import Path
from collections import Counter
B=Path('/workspace/outputs/poker_lines_v2');O=B/'results/run8';O.mkdir(exist_ok=True)
PAIR={'BTN_BB':'BTN 開池範圍對 BB 跟注範圍','CO_BB':'CO 開池範圍對 BB 跟注範圍','SB_BB':'SB 開池範圍對 BB 跟注範圍','SB3_BTN':'SB 再加注範圍對 BTN 跟注再加注範圍','BB3_BTN':'BB 再加注範圍對 BTN 跟注再加注範圍','CALLER':'CO 跟注再加注範圍對 BTN 再加注範圍（取 BTN 跟注 BB 再加注的模型，交換行動順序）','IPC_COLD':'UTG 開池範圍對 CO 冷跟注範圍','ISO':'BTN 隔離加注範圍對 CO 溜入跟注範圍','ISO_OOP':'SB 隔離加注範圍對 CO 溜入跟注範圍','LIMP':'CO 溜入範圍對 BB 過牌範圍'}
ACT={'x':'過牌','c':'跟注','f':'棄牌','r':'加注','small':'小注','big':'大注'}
def tree_text(tree):
 out=[]
 for st,lab in [('flop','翻牌'),('turn','轉牌'),('river','河牌')]:
  sizes=set(v for k in [st+'_oop',st+'_ip',st+'_donk']for v in tree.get(k,'').split(',')if v)
  if sizes:out.append(lab+'下注 '+ '／'.join('全下' if v=='a' else v for v in sorted(sizes)))
  vals=set(tree.get(st+'_raise','').split(','))-{''}
  if vals:out.append(lab+'加注 '+ '／'.join('全下'if v=='a'else v.replace('x',' 倍')for v in sorted(vals)))
 return '；'.join(out)
def apply(out,cond_lab,verdict):
 pack=json.load(open(B/'results/run6/additions.json'));river=json.load(open(B/'results/run6/river_additions.json'));jobs=json.load(open(B/'results/run6/river_jobs.json'))
 candidates={r['evidence']:r for r in pack['rows']+river};sources=pack['sources'];jobmap={(j['source'],j['board'],j['line']):j for j in jobs}
 changed=0
 for r in out['rows']:
  src=candidates.get(r.get('evidence'))
  if not src or r['b']!='gto':continue
  samples=src['solver']['samples'];freq=src['solver']['freq'];boards=len(set(s['board']for s in samples));flops=len(set(s['board'][:6]for s in samples))
  if r['evidence'].startswith('run6-river:'):
   spots={jobmap[(s['source'],s['board'],s['line'])]['spot']for s in samples};tree='河牌下注 50%／75%／150%；加注為跟注後底池的倍數，最多兩次';rake='不含抽水';boardtext=f'{boards} 個代表河牌面（來自 {flops} 個翻牌，依實際翻轉行動線到達範圍）'
  else:
   ss=[sources[p]for p in {s['path']for s in samples}];spots={s['spot']for s in ss};tree='；'.join(sorted({tree_text(s['tree'])for s in ss}));jj=[json.load(open(s['job']))for s in ss];rake='／'.join(sorted({f'抽水 {j["rake_rate"]*100:g}%，上限 {j["rake_cap"]/100:g} 大盲'for j in jj}));boardtext=f'{boards} 個代表'+('翻牌面'if len(samples[0]['board'])==6 else '翻牌×轉牌類型'if len(samples[0]['board'])==8 else '河牌面')+f'（{flops} 個不同翻牌）'
  pairs='、'.join(PAIR[s]for s in sorted(spots));ranges='；隔離／溜入範圍採既有估計，攤牌樣本有偏差'if spots&{'ISO','ISO_OOP','LIMP'}else''
  counts='、'.join(f'{ACT[a]} {v*100:.0f}%'for a,v in sorted(freq.items()))
  r['ev']=f'本機解算器：{pairs}{ranges}；{boardtext}；各條件牌面等權；{tree}；{rake}；動作頻率：{counts}。完整加權組合與求解設定見第六次求解紀錄。';changed+=1
 calls=json.load(open(O/'mw_calls.json'));obs=calls['observations'];rows=[];cells={};H=['S','TPG','TPW','MID','DRAW','WDRAW','AIR']
 # One shared column avoids sparse cross products. No texture, line or size
 # split survives; each rendered class must independently reach n>=40.
 for nd in ['r_vs_bet','r_vs_xr']:
  for hc in H:
   vv=[v for v in obs if v['nd']==nd and v['hc']==hc];n=len(vv);rec=dict(n=n,rendered=n>=40,condition={})
   cells[nd+'|'+hc]=rec
   if n<40:rec['reason']='全部尺寸、行動線及牌面合併後仍 n<40';continue
   w=sum(v['w']for v in vv);need=sum(v['need']for v in vv)/n*100
   a,ok,sig,p,e=verdict(w,n,need);label='玩家池：差異顯著'if sig=='sig'else'玩家池：差異不顯著'
   stats=dict(w=w,n=n,need=need,ci=[p-e,p+e],closes=True)
   rec.update(stats);ev=f'{label}；UTG–BB 全位置；僅限河牌仍有三人以上、跟注即結束行動（後面無人待行動）；全部尺寸、三槍與非三槍、牌面合併；跟注 n={n:,}，攤牌勝率 {p:.1f}%，95% CI {p-e:.1f}% 至 {p+e:.1f}%；底池賠率所需勝率 {need:.1f}%（逐筆門檻按樣本數加權）；與單挑河牌使用相同勝率檢定。'
   rows.append(dict(sp='mw',nd=nd,hc=[hc],c={},cl='全部・跟注即結束行動',a=a,ok=ok,b='pool',why=label+'；'+ACT[a]+('，另一動作也可接受'if ok else ''),ev=ev,eg=[v['eg']for v in vv[:12]],evidence='run8:river:'+nd+':'+hc,river_pool=stats))
 out['rows'][:]=[r for r in out['rows']if r['sp']!='mw']+rows
 out['mw_grid']=dict(columns=[{}],hands={nd:[r['hc'][0]for r in rows if r['nd']==nd]for nd in ['f_bet','f_vs_bet','f_vs_xr','t_bet','t_vs_bet','t_vs_xr','r_bet','r_vs_bet','r_vs_xr']},cells=cells,observation_count=len(obs),evidence='results/run8/mw_calls.json',method='river_closing_call')
 for i,r in enumerate(out['rows']):r['id']=f'{r["sp"]}.{r["nd"]}.{i}'
 out['notes']=[n for n in out['notes']if '多人'not in n]
 out['notes'].append('多人河牌只呈現跟注即結束行動、且河牌仍有三人以上的跟／棄比較；全部尺寸、行動線及牌面合併，每個牌型至少四十筆。使用與單挑相同的攤牌勝率、底池賠率與九成五信賴區間檢定；差異不顯著時採估計期望值較高的動作，另一動作也可接受。邊池與未能完整跟上的短碼跟注未納入；不足四十筆的牌型不呈現、不出題。')
 out.update(ver='lines-run8',built='2026-11-06')
 json.dump(dict(rows=rows,cells=cells,ev_fixed=changed,audit=calls['audit']),open(O/'publication.json','w'),ensure_ascii=False,indent=2)
