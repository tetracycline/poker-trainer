"""Publish only MW changes; preserve every HU row byte-for-byte."""
import json
from pathlib import Path
B=Path('/workspace/outputs/poker_lines_v2');O=B/'results/run9c'
NOTE='多人採 GTO 近似（兩人 solver）：其餘兩位玩家按各自翻前玩家池範圍獨立抽樣，取公共牌上最強成牌分布；同強度均分。精確移除公共牌；忽略對手彼此撞牌，英雄撞牌由 solver 處理。英雄採對應位置 GTO 翻前範圍。你是開池者／你是跟注者分開求解、各自聚合；翻牌每欄六種質地各一代表，轉河每欄至少三個實際 HW 牌面。使用真實近 100bb 起始深度與街初底池／剩餘籌碼；每街下注半池、加注全下，抽水 5% 上限 10bb；翻轉收斂 ≤0.5%、河 ≤0.3% 底池。各牌面等權、同牌面按相容節點到達權重。完全不下注的牌型面對加注以英雄原始支援、對手到達範圍作反事實回應聚合，來源明列 counterfactual。後續街從翻前範圍重建，未擬合先前多人行動；成牌最大值忽略聽牌未來潛力，並非多人均衡。四個顯著河牌池檢定在兩角色欄共享同一樣本，僅測行動結束時跟／棄，附各角色近似基準與加注頻率。'

def apply(out,cond_lab):
 pack=json.load(open(O/'publication.json'));
 assert len(pack['rows'])==126
 manifest=json.load(open(O/'manifest.json'))
 for m in manifest:
  j=json.load(open(O/(m['key']+'.job.json')))
  d=json.load(open(O/(m['key']+'.json')))
  assert d['info']['gto_expl_pct']<=j['target_pct']
  from run9c_solve import digest
  assert d.get('job_sha256')==digest(j),('stale result',m['key'])
 for r in pack['rows']:
  expected={m['key'] for m in manifest if m['role']==r['c']['hr'] and m['key'][0]==r['nd'][0]}
  got={s['job']for s in r['solver']['samples']}
  assert got<=expected and got

 from sys import path
 path.insert(0,str(Path(__file__).resolve().parents[1]))
 from mw_sanity import check
 issues,_=check({'rows':pack['rows']})
 assert not issues,issues
 old={(r['nd'],r['hc'][0]):r for r in out['rows'] if r['sp']=='mw'};rows=[]
 for src in pack['rows']:
  r=dict(src);key=(r['nd'],r['hc'][0]);pool=old.get(key)
  if pool:
   if key in [('r_vs_bet','S'),('r_vs_bet','TPG'),('r_vs_bet','TPW'),('r_vs_xr','S')]:
    r={**pool,'c':src['c'],'cl':src['cl'],'ev':pool['ev']+' 此池樣本合併開池與跟注角色；兩欄沿用同一樣本，非兩個獨立檢定。 '+src['ev'],'baseline':src['solver'],'eg':src['eg']}
    if key[1]=='S':r['ev']+=' 池檢定僅比較跟／棄，未檢驗加注；近似加注頻率 '+str(round(100*src['solver']['freq'].get('r',0),1))+'%。'
   else:r['ev']+=' 既有池樣本差異不顯著，僅供參考：'+pool['ev']
  rows.append(r)
 # Earlier publication passes serialize frequency dictionaries in hash order.
 # Preserve the original HU objects, including those evidence text strings.
 before=json.load(open(B/'results/run9/before.json'))
 hu=[r for r in before['rows'] if r['sp']!='mw']
 assert {r['id'] for r in hu}=={r['id'] for r in out['rows'] if r['sp']!='mw'}
 out['rows'][:]=hu+rows
 # HU IDs and all other HU fields remain untouched.
 for i,r in enumerate(rows):r['id']='mw.'+r['nd']+'.'+r['c']['hr']+'.'+r['hc'][0]
 out['basis']['gtoa']='GTO 近似（兩人 solver）：以最強對手分布壓縮多人場；只適用多人近似，非多人均衡，限制及配置見每列。'
 out['notes']=[n for n in out['notes'] if '多人' not in n]+[NOTE]
 out['mw_grid']=dict(columns=[{'hr':'PFR'},{'hr':'CALL'}],hands={nd:list(out['hc']) for nd in pack['nodes']},cells={k:v for k,v in out['mw_grid']['cells'].items()},method='max_of_field',evidence='results/run9c/manifest.json')
 out.update(ver='lines-run9c',built='2026-11-06')
