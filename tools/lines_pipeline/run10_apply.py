"""Final data-only classifier/node migration. Full provenance stays local."""
import json,re,hashlib
from pathlib import Path
from collections import defaultdict,Counter
B=Path('/workspace/outputs/poker_lines_v2');O=B/'results/run10';HANDS=['S','TPG','TPW','MID','DRAW','WDRAW','AIR'];A={'x':'過牌','c':'跟注','f':'棄牌','r':'加注','small':'小注','big':'大注'}
def key(r,h=None):return json.dumps(dict(sp=r['sp'],nd=r['nd'],hc=h or r['hc'][0],c=r.get('c')or{}),sort_keys=True)
def aggregate(vs):
 groups=defaultdict(list)
 seen=set()
 for v in vs:
  u=(v.get('path',v.get('source')),v['board'],v.get('line'),v.get('hist'))
  if u in seen or not v.get('freq'):continue
  seen.add(u);groups[(v.get('original_source',v.get('path',v.get('source'))),v['board'])].append(v)
 f=defaultdict(float)
 for vs in groups.values():
  masses=[v.get('reach',{}).get('joint_mass',0)for v in vs];z=sum(masses)
  for v,mass in zip(vs,masses):
   for a,p in v['freq'].items():f[a]+=p*(mass/z if z else 1/len(vs))/len(groups)
 return dict(f)
def render(r,vs,eg,cond_lab,origin):
 f=aggregate(vs)
 if not f:return None
 old=r.get('a');r=dict(r);r['a']=max(f,key=f.get);r['ok']=[a for a,v in f.items()if a!=r['a']and v>=.3];r['b']='gto';r['evidence']='run10:'+origin+':'+hashlib.sha256(key(r).encode()).hexdigest()[:12]
 if r.get('src'):r['historical_src']=r.pop('src')
 freq='／'.join(f'{A[a]} {p*100:.1f}%'for a,p in sorted(f.items(),key=lambda kv:-kv[1]));locked=any(v.get('locked')for v in vs);shares=[v['reach']['own_share']for v in vs if v.get('reach')];spr=[v['spr']for v in vs if 'spr'in v]
 locktxt='；先前英雄行動按 HW 已知底牌的逐牌型頻率鎖定（含未攤牌手；稀少組用 Jeffreys 0.5 平滑；各尺寸內分配沿用原 GTO，非實測尺寸；逐組 n 與回退鍵見求解紀錄）；這是鎖定模型的條件策略'if locked else''
 r['why']=('鎖定模型：'if locked else'GTO：')+freq
 r['ev']='本機解算器；common.hcls（頂對踢腳 J 以上）、common.texture、common.ctype；同來源同牌面的分支按相容節點到達質量加權，各來源牌面等權；保留同位置、原始底池／有效籌碼及原下注樹；完整範圍、節點、尺寸、迭代、到達率見 run10 求解紀錄。'+('節點類別到達率（以該子遊戲起點牌型權重為分母）'+f'{min(shares)*100:.3f}%–{max(shares)*100:.3f}%'if shares else'')+('；節點 SPR '+f'{min(spr):.3f}–{max(spr):.3f}'if spr else'')+locktxt+'；頻率：'+freq
 if any('hist'in v for v in vs):r['ev']+='；河牌樹：下注 50/75/150%，加注為跟注後底池的一倍（不是固定 3 倍），最多兩次；無抽水。'
 else:r['ev']+='；Rust 樹：抽水 5%、上限 10bb；加注 3 倍／全下依逐例原 job。'
 notes=sorted({v['note']for v in vs if v.get('note')})
 if notes:r['ev']+='；'+'；'.join(notes)+'。';r['why']+='（來源限制見證據）'
 r['solver']=dict(freq=f,sample_count=len(vs),samples=[{k:v[k]for k in ['path','source','original_source','board','line','hist','player','reach','original_reach','locked_prior_share','locked','spr']if k in v}for v in vs[:6]],provenance='results/run10/*_common.json cell '+key(r));r['reach']=dict(denominator='source-job root class weight after current board removal',own_share_min=min(shares)if shares else None,own_share_max=max(shares)if shares else None,locked=locked);r['classifier']='common-hcls-v2';r['eg']=eg or r.get('eg',[]);r['cl']=cond_lab(r.get('c'));r.pop('hw',None)
 return r

def apply(out,cond_lab):
 rows=out['rows'];before=json.load(open(O/'before.json'));packs={n:json.load(open(O/(n+'.json')))for n in ['raw_common','legacy_raw','review_raw','river_common','locked_common']};pool=json.load(open(O/'pool_common.json'));legacy=json.load(open(O/'legacy_common.json'));changes=[];unresolved=[];new=[]
 cells=defaultdict(list);examples={}
 for name in ['raw_common','legacy_raw','review_raw']:
  for k,vs in packs[name]['cells'].items():cells[k]+=vs
  examples.update({k:v for k,v in packs[name]['examples'].items()if v})
 for name in ['river_common','locked_common']:
  for k,vs in packs[name]['cells'].items():cells[k]=vs
  examples.update({k:v for k,v in packs[name]['examples'].items()if v})
 # The old lmp namespace included ISO callers. Partition full solver samples,
 # not the truncated published sample list, before computing any strategy.
 def kind(v):
  path=Path(v.get('original_source',v.get('path',v.get('source',''))))
  # These archived source jobs are explicitly named limp_* or iso_*.
  if path.name.startswith('limp_'): return 'LMP'
  if path.name.startswith(('iso_', 'iso_oop_')): return 'ISO'
  raise ValueError('Unknown isolation/limp source: '+str(path))
 def limp_examples(vs,hc):
  result=[]
  from run10_common import classes
  for v in vs:
   path=Path(v.get('original_source',v.get('path',v.get('source'))))
   d=json.load(open(path));p=v['player'];pos=['BB','CO']
   for h in d['hands'][p]:
    if hc not in classes(h,v['board']):continue
    if len(set([h[i:i+2] for i in (0,2)]+[v['board'][i:i+2] for i in range(0,len(v['board']),2)])) != 2+len(v['board'])//2:continue
    segments=[]
    line=v['line']
    if 'hist' in v:
     hist=' '.join('b'+a[1:] if a.startswith('B') else 'r3' if a=='R' else 'a' if a=='A' else a for a in re.findall(r'B\d+|[xRA]',v['hist']))
     line=line+hist
    for st in line.split('/'):
     segments.append(' '.join(pos[k%2]+':'+('b'+str(int(a[1:])/100) if a.startswith('b') else 'r3' if a=='r' else a) for k,a in enumerate(st.split())))
    e=dict(h=h,b=v['board'],me=pos[p],t='LMP',pa=None,pc=pos,pot=2.5,stk=99,l='/'.join(segments),role=['post',''])
    if e not in result:result.append(e)
    break
   if len(result)>=6:break
  return result
 splitcells=defaultdict(list); splitexamples={}
 for k,vs in cells.items():
  m=json.loads(k)
  if not m['nd'].startswith('lmp_'): splitcells[k]=vs;continue
  for t in ('LMP','ISO'):
   mm=dict(m,nd=('lmp_' if t=='LMP' else 'iso_')+m['nd'][4:]);kk=json.dumps(mm,sort_keys=True)
   splitcells[kk]=[v for v in vs if kind(v)==t]
   splitexamples[kk]=[e for e in examples.get(k,[]) if e['t']==t]
   if t=='LMP' and not splitexamples[kk]: splitexamples[kk]=limp_examples(splitcells[kk],m['hc'])
 cells=splitcells;examples.update(splitexamples)
 templates=[]
 for r in rows:
  if not r['nd'].startswith('lmp_'): templates.append(r);continue
  for t in ('LMP','ISO'):
   rr=dict(r,nd=('lmp_' if t=='LMP' else 'iso_')+r['nd'][4:],eg=[e for e in r.get('eg',[]) if e['t']==t])
   # Only create strategies for pot types with source evidence.
   if any(cells.get(key(rr,h)) for h in rr['hc']): templates.append(rr)
 rows[:]=templates
 mapping={'t_delay':'srp_fold_delay','t_probe':'srp_fold_probe','r_stab':'srp_fold_rstab'}
 for r0 in rows:
  for hc in r0['hc']:
   r=dict(r0,hc=[hc]);k=key(r);old=dict(r);vs=cells.get(k,[]);eligible=[v for v in vs if v.get('reliable',True)and v.get('freq')]
   legacy_source=r.get('src','').startswith('ld:');migration=legacy_source or r.get('evidence','').startswith(('legacy:','review:','solved:','run6:','run6-river:'))
   if r['sp']=='mw':new.append(r);continue
   if r['b']=='pool'and legacy_source:
    claim=(mapping.get(r['nd'])if r['sp']=='ipfr'else'srp_fold_probe'if r['sp']=='bb'and r['nd']=='t_probe'else'srp_fold_rlead'if r['sp']=='bb'and r['nd']=='r_stab'else'3bp_fold_cbB'if r['nd']=='3b_f_cbet'else'3bp_fold_t'if r['nd']=='3b_t_barrel'else None)
    v=pool.get(claim+'|'+r['a'])if claim and r['a']in ['small','big']else None
    if v and v['significant']:
     r['historical_src']=r.pop('src');r['evidence']='run10-pool:'+claim+':'+r['a'];r['classifier']='common-hcls-v2';r['pool_recount']=v;r['L']={r['a']:'下注約 '+str(round(v['size_mean']*100))+'% 池（樣本組平均）'}
     gf=aggregate(eligible)if eligible else legacy.get('|'.join([r['sp'],r['nd'],r.get('c',{}).get('tx','*'),hc]),{}).get('freq',{})
     r['ev']=f"玩家池 UTG–BB 合併（該位置角色依原始 HU HH 篩選）；有效 >=40bb；全部牌面；直接觀察棄牌，不需攤牌或底牌，對任何英雄牌型適用；n={v['n']}；棄 {v['p']*100:.2f}%；95% CI {v['ci'][0]*100:.2f}–{v['ci'][1]*100:.2f}%；該組尺寸加權保本 {v['break_even']*100:.2f}% → 顯著；common.hcls 重聚合的同節點 GTO 基準："+json.dumps(gf,ensure_ascii=False)
     r['why']='該組直接棄牌率 95% CI 高於按每手尺寸加權的靜態保本率；有未來權益／尺寸選擇限制。'
     shares=[s['reach']['own_share']for s in eligible if s.get('reach')]
     r['baseline']=dict(freq=gf,sample_count=len(eligible));r['reach']=dict(source='same-cell common-class GTO baseline',own_share_min=min(shares)if shares else None,own_share_max=max(shares)if shares else None,pool_class_reach='not identifiable from hidden pool cards; fold claim is class independent')
     new.append(r);continue
    r['pool_fallback']='舊的攤牌組成比較未用共同牌型重建直接動作 CI，或新直接頻率不顯著；改同格 common.hcls GTO。'
   if eligible and migration:
    nr=render(r,eligible,examples.get(k),cond_lab,'reaggregate');r=nr or r
   elif migration and legacy_source:
    v=legacy.get('|'.join([r['sp'],r['nd'],r.get('c',{}).get('tx','*'),hc]))
    if v:
     r=render(r,v['samples'],examples.get(k),cond_lab,'compact');r['ev']+='；只存有舊版壓縮節點（頻率取整、移除低權重組合），不聲稱還原完整未壓縮範圍。'
    else:unresolved.append(dict(key=k,reason='no common-class stored source'));new.append(r);continue
   elif migration and not eligible and r.get('x'):
    continue # Unsupported exception falls through to the ordinary same-cell row.
   elif migration and not eligible:
    unresolved.append(dict(key=k,reason='no >=1% own-reach common-class source'));new.append(r);continue
   if old['a']!=r['a']:changes.append(dict(sp=r['sp'],nd=r['nd'],hc=hc,c=r.get('c')or{},before=old['a'],after=r['a'],evidence=old.get('evidence'),src=old.get('src')))
   new.append(r)
 # Add separate re-raise decisions; never copy the old mixed frequency.
 existing={key(r)for r in new}
 for k,vs in cells.items():
  m=json.loads(k)
  if 'vs_3b'not in m['nd']or k in existing:continue
  eligible=[v for v in vs if v.get('reliable',True)and v.get('freq')]
  if not eligible and m['nd']=='lmp_t_vs_3b' and m['hc']=='AIR':
   eligible=[dict(v,note='此空氣再加注節點自身到達率低於 1%；僅作條件回應，不建議先前加注') for v in vs if v.get('freq')]
  if not eligible:unresolved.append(dict(key=k,reason='new reraise cell has no reliable or locked sample'));continue
  template=dict(sp=m['sp'],nd=m['nd'],hc=[m['hc']],c=m['c'],eg=[],b='gto',a='f',ok=[])
  r=render(template,eligible,examples.get(k),cond_lab,'split');new.append(r);existing.add(k)
 rows[:]=new
 from run10_mw_extract import apply as apply_mw
 apply_mw(out)
 from run10_common import classes,texture
 for r in rows:
  r['eg']=[e for e in r.get('eg',[])if r['hc'][0]in classes(e['h'],e['b']) and (not r.get('c',{}).get('tx')or texture(e['b'])==r['c']['tx'])]
 for r in rows:
  if 'vs_xr'not in r['nd']and'vs_3b'not in r['nd']:continue
  good=[]
  for e in r.get('eg',[]):
   actions=[tk.split(':',1)for tk in e['l'].split('/')[-1].split()];ag=sum(a.startswith(('b','r','a'))for _,a in actions);mine=[a for p,a in actions if p==e['me']]
   if 'vs_xr'in r['nd']and ag==2 and any(a.startswith(('b','a'))for a in mine):good.append(e)
   elif 'vs_3b'in r['nd']and ag>=3 and any(a.startswith('r')for a in mine):good.append(e)
  r['eg']=good
 out['tx'].update(mid_high='J/T 高面',low='9 以下低牌面')
 out['ct']={'str4':'本張令公牌首次達四張成順','flush':'本張令公牌至少三張同花','pair':'本張令公牌成對','str3':'本張令公牌首次達三張成順','over':'新高張','blank':'空白'}
 for nd in {r['nd']for r in rows}:
  st='翻牌'if nd.startswith('f_')or'_f_'in nd else'轉牌'if nd.startswith('t_')or'_t_'in nd else'河牌'
  if 'vs_3b'in nd:out['nd'][nd]=st+'：你加注（含過牌加注）後被再加注／全下'
  elif 'vs_xr'in nd:out['nd'][nd]=st+{'翻牌':'：你先下注被加注（加注 3 倍或全下）','轉牌':'：你先下注被加注（多數為全下；金額見題目）','河牌':'：你先下注被加注（加注為跟注後底池一倍或全下；金額見題目）'}[st]
  elif nd.endswith('r_stab'):out['nd'][nd]='河牌：未連續下注兩街，輪到你下注'
 for r in rows:
  if 'reach'not in r:
   samples=r.get('solver',r.get('baseline',{})).get('samples',[]);shares=[s['reach']['own_share']for s in samples if isinstance(s.get('reach'),dict)and'own_share'in s['reach']]
   r['reach']=dict(own_share_min=min(shares)if shares else None,own_share_max=max(shares)if shares else None,scope='source-job root class; pool reach not identifiable from hidden cards'if r['b']=='pool'else'source-job root class')
 for i,r in enumerate(rows):r['id']=f"{r['sp']}.{r['nd']}.{i}";r['cl']=cond_lab(r.get('c'))
 out['ver']='lines-run10';out['built']='2026-11-06';out['classifier_spec']='results/classifier_spec.md';out['notes'].append('第十次：拆開你下注被加注／你加注後被再加注；牌型採 common.hcls，J 以上踢腳；到達率及實測行動鎖定見逐列紀錄。')
 json.dump(dict(changed_actions=changes,unresolved=unresolved,row_counts={'|'.join(k):v for k,v in Counter((r['sp'],'flop'if r['nd'].startswith('f_')or'_f_'in r['nd']else'turn'if r['nd'].startswith('t_')or'_t_'in r['nd']else'river',r['b'])for r in rows).items()}),open(O/'publication_audit.json','w'),ensure_ascii=False,indent=2)
 return out
