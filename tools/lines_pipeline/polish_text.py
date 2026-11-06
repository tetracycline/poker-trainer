"""Presentation-only pass; never reads or writes solver actions."""
import json,re,math
from pathlib import Path
B=Path('/workspace/outputs/poker_lines_v2')
A={'x':'過','small':'小注','big':'大注','f':'棄','c':'跟','r':'加注'}
H={'S':'兩對以上','TPG':'頂對好','TPW':'頂對弱','MID':'中小對','DRAW':'強聽','WDRAW':'弱聽','AIR':'空氣'}
def freq(v):
 if all(isinstance(x,(float,int)) for x in v.values()):return '／'.join(f'{A[k]} {x*100:.0f}%' for k,x in sorted(v.items(),key=lambda kv:-kv[1]))
 return '；'.join(H.get(k,k)+'：'+freq(x) for k,x in v.items() if x)
def clean(t, setting=False):
 t=re.sub(r"(?:results/)?[A-Za-z_][A-Za-z_./]*(?:\.json|各job|與各job)", "設定紀錄",t)
 t=re.sub(r"results/[A-Za-z_0-9]+", "設定紀錄", t)
 # Intervals in percentage points, including old signed difference intervals.
 t=re.sub(r'95%\s*([+-]?\d+(?:\.\d+)?)~([+-]?\d+(?:\.\d+)?)',lambda m:f'95% CI ±{max(1,round((float(m[2])-float(m[1]))/2))}%',t)
 if not setting:t=re.sub(r'([+-]?\d+\.\d+)%',lambda m:f'{float(m[1]):.0f}%',t)
 replacements={'c-bet':'持續下注',' vs ':' 對 ','EV':'期望值','cap':'上限','baseline':'基準','call-vs-raise':'跟注對加注','call':'跟注','fold':'棄牌','raise':'加注','all-in':'全下','zero rake（solver不支援抽水）':'河牌解算器不含抽水','river.js':'河牌解算器','ranges.py':'翻前範圍表','pot-after-跟注':'跟注後底池倍數','rake':'抽水','flop':'翻牌','turn':'轉牌','river':'河牌','stack':'有效籌碼','pot':'底池','target':'收斂目標','max':'迭代上限','iterations':'次迭代','texture':'牌面質地','action':'動作','HU':'單挑','pool':'玩家池','limp-跟注':'溜入跟注','limp':'溜入','HWR.iso':'你的隔離範圍','HWR':'你的翻前範圍','CO>BTN':'CO 溜入、BTN 隔離','OOP/IP':'無位置／有位置','OOP':'無位置','IP':'有位置','caller':'跟注者','3bettor':'再加注者','donk':'領打','bet':'下注','line':'行動線','distinct':'不同','runout':'後續牌面','marginals':'邊際權重','card compatibility':'卡牌相容性','archive':'既有存檔','manifest':'設定清單','exploitability':'可剝削度','response':'回應','ok':'可接受動作','原始out jobs':'原始工作紀錄'}
 for a,b in sorted(replacements.items(),key=lambda kv:-len(kv[0])):t=t.replace(a,b)
 t=t.replace('vs',' 對 ').replace('3x','3 倍').replace('s底池','位置配置')
 t=re.sub(r'(?:results/)?[A-Za-z_][A-Za-z_./]*(?:\.json|各job|與各job)', '設定紀錄',t)
 t=t.replace('底池-after-跟注','跟注後底池倍數').replace('溜入-跟注','溜入跟注')
 t=re.sub(r'(\d+)%±(\d+)', r'\1%（95% CI ±\2%）', t)
 t=t.replace('job','工作紀錄').replace('spot','位置配置').replace('SRP','單加注底池').replace('3BP','再加注底池')
 return t

def polish(rows):
 ov=json.load(open(B/'results/review_overrides.json'));mw=json.load(open(B/'results/mw_comparison.json'));sol=json.load(open(B/'results/solved.json'))
 notes=['GTO 頻率取最高者為主動作，其他至少 30% 列為可接受；顯示百分比四捨五入，總和可能不等於 100%。CI 為 95% 誤差，± 以百分點表示；小於 1 點顯示 ±1%。設定中的收斂目標保留原精度。', '多人比較：全部位置 UTG–BB 合併，取最前至多 1500 個不同攤牌手牌；每手以固定種子抽 16 次後續牌面，對其他仍在底池且已揭露手牌估計權益。n 是不同手牌數；CI 含抽樣與模擬誤差，未校正攤牌偏差。未揭露對手未建模，不計未來下注及後方加注；不能識別跟注對加注的因果期望值或完整多人最佳回應。']
 configs={}
 def config(s):
  if s not in configs:
   configs[s]=len(notes)+1;notes.append(clean(s, setting=True))
  return f'設定註 {configs[s]}'
 for r in rows:
  ev=r['ev'];e=r.get('evidence','');fs=[]
  for m in re.finditer(r'\{',ev):
   try:
    v,_=json.JSONDecoder().raw_decode(ev[m.start():])
    if isinstance(v,dict) and v:fs.append(v)
   except ValueError:pass
  f=fs[0] if fs else None
  if e.startswith('review:'):
   v=ov[e[7:]];f=v['freq'];count=v['boards'];cfg=v['config'];ref=config(cfg)
   river=cfg.startswith('river.js')
   if river:
    spots=re.search(r'(?:BTN_BB|CO_BB|SB_BB|SB3_BTN|BB3_BTN)(?:,(?:BTN_BB|CO_BB|SB_BB|SB3_BTN|BB3_BTN))*',cfg)
    brief=(spots[0] if spots else 'ISO')+' 位置代理；河牌下注 50/75/150%，跟注後底池倍數加注、最多兩次；河牌解算器不含抽水'
   else:
    brief='；'.join(clean(cfg).split('；')[4:])
    # Full exact sizes, range, stack and stopping criteria stay in shared config note.
    brief=('ISO／溜入估計範圍；攤牌樣本有偏差' if r['sp']=='iso' else {'bb':'BTN 對 BB 位置代理','ipfr':'BTN 對 BB 位置代理','3bp':'再加注底池位置代理'}.get(r['sp'],'單挑位置代理'))+'；抽水 5%、上限 10bb'
   r['why']=f'GTO：{freq(f)}（{count} 個'+('河牌面' if river else '有效牌面')+'）'
   r['ev']=f'{brief}；{count} 個有效牌面；{ref}。GTO：{freq(f)}'
  elif e.startswith('solved:'):
   count=sol['selection'].get(r.get('c',{}).get('tx'),sum(sol['selection'].values()));ref=config(ev.split('｜動作頻率')[0]);r['why']=f'GTO：{freq(f)}（{count} 個翻牌面）';r['ev']=f'SB 開池對 BB 跟注；6bb／97bb；抽水 5%、上限 10bb；翻牌 33/75%、加注 3 倍／全下，轉牌 66%、河牌 75%、加注全下；{count} 個翻牌面；{ref}。GTO：{freq(f)}'
  elif e.startswith('mw-composition:'):
   r['why']=clean(r['why'])+'（原表池攤牌組成）'
   r['ev']=clean(ev)
  elif e.startswith('mw_comparison:'):
   v=mw[e.split(':',1)[1]];p=v['equity']*100;need=v['required']*100;ci=max(1,math.ceil((v['ci'][1]-v['ci'][0])*50))
   r['why']=f'池條件勝率 {p:.0f}%，需要 {need:.0f}%（n={v["n"]}）→ {A[r["a"]]}'
   r['ev']=f'玩家池 UTG–BB 合併；n={v["n"]}；條件勝率 {p:.0f}%（95% CI ±{ci}%），需要 {need:.0f}%，比較顯著；攤牌樣本有偏差；此節點無 GTO 基準（多人底池）；方法見註 2。'
   if set(r['hc']) & {'MID','WDRAW','AIR','DRAW','TPW'}:
    r['why']=f'條件勝率 CI 下界 {v["ci"][0]*100:.1f}% ≥ 所需 {need:.1f}%＋10 個百分點 → 跟'
    r['ev']+=f'；CI 下界 {v["ci"][0]*100:.1f}%；粗略實現率／後方玩家安全邊際：CI 下界≥所需勝率＋10 個百分點；非實際淨 bb 結果。'
  else:
   if '｜本機既有GTO子集' in ev:
    obs,cfg=ev.split('｜本機既有GTO子集',1);ref=config('本機既有GTO子集'+cfg);ev=obs+'；'+ref
   # Replace nested dictionaries from the outside inward.
   def replace_json(t):
    out='';i=0
    while i<len(t):
     if t[i]=='{':
      v,n=json.JSONDecoder().raw_decode(t[i:]);out+=freq(v);i+=n
     else:out+=t[i];i+=1
    return out
   ev=replace_json(ev)
   ev=ev.split('｜SB_BB代表子集GTO基準')[0]+'；GTO 基準：'+freq(f) if '｜SB_BB代表子集GTO基準' in ev and f else ev
   ev=re.sub(r'｜無同節點GTO基準；.*','；此節點無 GTO 基準；未比較其他加注尺寸。',ev)
   ev=re.sub(r'｜多人底池無 GTO (?:baseline|解).*','；此節點無 GTO 基準（多人底池）；攤牌樣本有偏差；靜態比較限制見註 2。',ev)
   ev=clean(ev).replace('GTO基準動作/頻率：','GTO 基準：')
   r['ev']=ev
   if r['b']=='gto':
    assert f,r['id'];r['why']='GTO：'+freq(f)
   else:
    # Use actual comparison from evidence, avoiding stale source slogans.
    win=re.search(r'(?:勝率|贏全部人)\s*(\d+)%',ev);need=re.search(r'(?:需要|所需|保本)\s*(?:約\s*)?(\d+)%',ev);n=re.search(r'n=([\d,]+)',ev)
    if win and need:r['why']=f'池跟注後勝率 {win[1]}%，需要 {need[1]}%（n={n[1]}）→ {A[r["a"]]}'
    else:
     comp=re.search(r'(空氣占比|兩對以上占比)：GTO (\d+)% 對 池 (\d+)%',ev)
     fold=re.search(r'GTO (\d+)% 對 池 (\d+)%',ev)
     if comp:r['why']=f'池{comp[1]} {comp[3]}%，GTO {comp[2]}%（n={n[1]}）→ {A[r["a"]]}'
     elif fold:r['why']=f'池棄牌 {fold[2]}%，GTO {fold[1]}%（n={n[1]}）→ {A[r["a"]]}'
     else:r['why']=clean(r['why'])+f'（n={n[1]}）'
    if ('攤牌' in ev or '勝率' in ev) and '頻率統計，不需攤牌' not in ev and '攤牌樣本有偏差' not in r['ev']:r['ev']+='；攤牌樣本有偏差'
    if f:r['why']+='；GTO 基準：'+freq(f)
    if 'GTO' not in r['ev']:r['ev']+='；此節點無 GTO 基準'+('（多人底池）' if r['sp']=='mw' else '')
  if e.startswith('review-pool:'):
   obs=re.search(r'n=([\d,]+)：棄 (\d+)%.*?保本 (\d+)%',r['ev'])
   r['why']=f'池棄牌 {obs[2]}%，保本 {obs[3]}%（n={obs[1]}）→ 小注；GTO 基準：'+freq(ov[e.split(':',1)[1]]['freq'])
  if r.get('pool_fallback'):r['ev']=r.pop('pool_fallback')+'；'+r['ev']
 return notes
