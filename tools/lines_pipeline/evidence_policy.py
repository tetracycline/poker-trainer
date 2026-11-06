"""Strict evidence gate for build_lines.py. Original IDs are audit keys only."""
import json,re
from pathlib import Path
B=Path('/workspace/outputs/poker_lines_v2')

def apply(rows,ld):
    solved=json.load(open(B/'results/solved.json'))['strategies']
    overrides=json.load(open(B/'results/review_overrides.json'))
    mw=json.load(open(B/'results/mw_comparison.json'))
    original=json.load(open(B/'results/original.json'))['rows']
    assert len(rows)==len(original)==480, 'Source changed: re-audit before publishing'
    rules={r['id']:r for r in ld['rules']}; out=[]; audit=[]
    config='SB_BB：SB 開池 vs BB 跟；GTO 翻前範圍 ranges.py；6bb/97bb；抽水5% cap10bb；翻牌33/75%、加注3x/全下，轉牌66%、河牌75%、加注全下；依牌面子集（各類至少4翻牌）；實際停止見manifest、exploitability≤0.5% pot；results/solved.json 完整範圍/牌面/迭代。'
    for i,r in enumerate(rows):
        old=original[i]; assert (r['sp'],r['nd'],r['hc'],r['a'])==(old['sp'],old['nd'],old['hc'],old['a'])
        status='keep';reason=''; before=r['a']; evidence=None
        key='|'.join([r['sp'],r['nd'],r.get('c',{}).get('tx','*'),r['hc'][0]])
        if old['id'] in overrides and not overrides[old['id']].get('unreachable'):
            v=overrides[old['id']];r.update(b='gto',a=v['a'],ok=v['ok'],why='代表子集按實際到達範圍聚合，採最高頻動作。',ev=v['config']+'｜有效牌面數='+str(v['boards'])+'｜GTO頻率 '+json.dumps(v['freq'],ensure_ascii=False),evidence='review:'+old['id'])
            evidence=r['evidence'];reason=r['ev']
            if old['b']=='pool' and '不明顯' in old['ev']:
                obs=re.search(r'n=([\d,]+).*?(?:勝率|棄)\s*(\d+)%.*?(?:需要|保本)\s*(\d+)%',old['ev'])
                assert obs,old['id']
                label='棄牌率' if '頻率統計' in old['ev'] else '勝率'
                r['pool_fallback']=f'池數據不顯著（n={obs[1]}，{label} {obs[2]}% vs 需要 {obs[3]}%）→ 照 GTO'
                r['ev']+='｜'+r['pool_fallback'];reason=r['ev']
            if old['b']=='pool' and '顯著' in old['ev'] and '不明顯' not in old['ev'] and '保本' in old['ev']:
                obs=re.search(r'n=([\d,]+)：棄 (\d+)%±(\d+)（保本 (\d+)%）',old['ev'])
                if obs and 'opponent_fold33' in v:
                    lower=(int(obs[2])-int(obs[3]))/100
                    if lower>max(int(obs[4])/100,v['opponent_fold33']):
                        r.update(b='pool',a=old['a'],ok=old['ok'],ev=old['ev']+'｜GTO基準動作/頻率：'+json.dumps(v['freq'])+f'；GTO 對手面對33%下注棄牌 {v["opponent_fold33"]*100:.0f}%（24 翻牌等權；½池剝削以此樹的33%節點為基準）',evidence='review-pool:'+old['id'])
                        evidence=r['evidence'];reason=r['ev']
        elif old['id'] in overrides and overrides[old['id']].get('unreachable'):
            status='removed';reason=f'匹配解中牌型到達權重 {overrides[old["id"]]["reach_sum"]:.3g}，可用牌面 {overrides[old["id"]]["boards"]}；無有效到達。'
        elif old['sp']=='mw' and old['nd'] in ('f_vs_bet','t_vs_bet'):
            if old['hc']==['S']:
                r.update(b='pool',a=old['a'],ok=['c'] if old['a']=='r' else ['r'],
                         why=old['why'],ev='玩家池 UTG–BB 合併；'+old['ev']+'｜勝率檢定只比較跟/棄，加注依原表的池攤牌組成；沿用原表動作，非call-vs-raise最佳化；多人底池無 GTO 基準。',
                         evidence='mw-composition:'+old['id'])
                evidence=r['evidence'];reason=r['ev']
            else:
                weak=bool(set(old['hc']) & {'MID','WDRAW','AIR','DRAW','TPW'})
                candidates=[]
                for hc in old['hc']:
                    k=old['id']+'|'+hc if len(old['hc'])>1 else old['id']
                    v=mw[k]
                    qualifies=(v['n']>=40 and v['ci'][0]>=v['required']+.10) if weak else v['significant']
                    if qualifies:candidates.append((hc,k,v))
                if candidates:
                    for j,(hc,k,v) in enumerate(candidates):
                        target=r if j==len(candidates)-1 else dict(r)
                        target.update(hc=[hc],b='pool',a='c' if weak else v['a'],ok=[],
                            why='保守權益門檻：95% CI下界至少高於所需勝率10個百分點。' if weak else '攤牌條件勝率比較。',
                            ev='玩家池 UTG–BB；n='+str(v['n'])+'；equity='+str(v['equity'])+'；95% CI='+str(v['ci'])+'；pot odds='+str(v['required'])+'；攤牌樣本有偏差；無同節點 GTO 基準。'+('粗略實現率/後方玩家安全邊際：CI下界≥所需勝率+10個百分點；不等於實際淨bb結果。' if weak else ''),
                            evidence='mw_comparison:'+k)
                        if target is not r:
                            target.pop('hw',None);out.append(target)
                    evidence=r['evidence'];reason=r['ev']
                else:
                    status='removed'
                    reason='無可用實現淨bb比較：hw.pkl/mw.pkl缺派彩/淨輸贏，不能把未攤牌當輸；逐牌型檢定未過保守門檻（n≥40且equity CI下界≥pot odds+10個百分點）之弱牌列移除。' if weak else '攤牌權益比較未顯著。'
                    reason+='；'+json.dumps({hc:mw[old['id']+'|'+hc if len(old['hc'])>1 else old['id']] for hc in old['hc']},ensure_ascii=False)
        elif old['sp']=='mw' and old['b']=='pool':
            if '不明顯' in r['ev']:status='removed';reason=r['ev']
            else:
                r['ev']+='｜多人底池無 GTO baseline；觀察到的call結果/靜態詐唬門檻比較；攤牌樣本有偏差，非call-vs-raise因果EV。'
                reason=r['ev'];evidence='original-mw-pool'
        elif old['id']=='ipfr.f_vs_donk.370' and (B/'results/donk_summary.json').exists():
            v=json.load(open(B/'results/donk_summary.json'));r.update(b='gto',a=v['a'],ok=v['ok'],why='BTN 開池 vs BB donk：六個代表翻牌、33/75% donk 的 TPW/MID 合併最高頻動作；不是所有位置/尺寸的解。',ev='BTN vs BB，ranges.py GTO範圍；pot5.5bb/stack97.5bb；抽水5% cap10bb；BB可donk33/75%，翻牌加注3x、轉牌66%、河牌75%，轉河無加注；6翻牌各1種texture，按牌面/尺寸等權、牌型到達權重；target0.5% pot、max600 iterations，實際值見results/donk_summary.json；GTO頻率：'+json.dumps(v['freq']),evidence='donk_summary')
            evidence='donk_summary';reason=r['ev']
        elif old['b']=='rule':
            if key in solved and len(r['hc'])==1:
                v=solved[key];r.update(b='gto',a=v['a'],ok=v['ok'],why='此代表牌面子集，解算器最高頻動作。',ev=config+'｜動作頻率 '+json.dumps(v['freq'],ensure_ascii=False),evidence='solved:'+key)
                evidence='solved:'+key;reason=config
            else: status='removed';reason='未取得此節點/牌型的解算器策略，也沒有 n≥40 且95% CI支持的直接動作比較。隔離/limp 缺可辯護完整範圍；多人組成不能比較動作。'
        elif old['sp']=='mw':
            if old['b']=='read' or 'S' in r['hc']:
                status='removed';reason='多人攤牌組成未建立跟/棄或跟/加注EV比較；無多人GTO解。'
            elif '不明顯' in r['ev']:
                status='removed';reason='95% CI 未顯著。'
            else:
                r['ev']+='｜多人底池無 GTO 解，依玩家池數據；比較為文內勝率/所需勝率或全部棄牌率/詐唬保本率（不計未來權益的靜態比較）。'
                reason='直接玩家池頻率/勝率對保本門檻。'
        elif 'S' in r['hc'] and r['nd'] in ('r_vs_bet','3c_r_vs_bet2','r_vs_xr'):
            status='removed';reason='原來僅比較call/fold，不能排除value raise。已跑river.js有raise診斷；無抽水且僅轉牌check-through子集，不足覆蓋本列所有牌面/行動線，撤回call建議。見river_solved.json。'
        elif r.get('src','').startswith('ld:'):
            rr=rules[r['src'][3:]];gf=rr.get('gf',{}); best=max(gf,key=gf.get) if gf else None
            if old['b']=='gto' and best:
                r.update(a=best,ok=[a for a in gf if a!=best and gf[a]>=.3])
                r['ev']+='｜GTO基準動作/頻率：'+json.dumps(gf,ensure_ascii=False)+'｜本機既有GTO子集，範圍為ranges.py的GTO翻前範圍；SRP 5.5bb/97.5bb、3BP 20.5–21bb/90bb；抽水5% cap10bb；翻33/75%、轉50/100%、河50/100%或全下，加注3x/全下；既有抽樣翻牌/轉河子集，停止目標翻0.5%、轉子遊戲0.3% pot（max1000次，實際值與牌面見results/legacy_config.json及原始out jobs）；非全牌面精確解。'
                if best!=before:r['why']='解算器子集按牌型聚合，採最高頻動作。'
                r['evidence']='legacy:'+rr['id'];evidence=r['evidence'];reason='GTO頻率 '+json.dumps(gf,ensure_ascii=False)
            elif old['b']=='pool':
                if not re.search(r'n=[\d,]+',r['ev']) or '不明顯' in r['ev'] or '不顯著' in r['ev'] or ('顯著' not in r['ev']):
                    status='removed';reason='玩家池偏離沒有顯著性支持。'
                else:
                    r['ev']+='｜GTO基準動作/頻率：'+json.dumps(gf,ensure_ascii=False)
                    evidence='legacy-pool:'+rr['id']
            else:status='removed';reason='缺少可追溯的GTO策略頻率。'
        elif old['b']=='read':
            # Retain HU data as pool, explicitly identify the biased equity-model comparison.
            if old['id']=='ipfr.f_vs_donk.370':
                status='removed';reason='已新增donk樹重查，但六個代表翻牌不能支持合併TPW/MID跨尺寸跟注建議；撤回。見results/donk。'
            else:
                r['b']='pool';r['ev']+='｜玩家池組成勝率模型比較，未經CI驗證（不明顯）；UTG–BB 合併；無可計算的同節點GTO基準；僅攤牌條件樣本，不能識別完整決策EV。'
                # These cannot pass the strict CI gate. Do not relabel unsupported advice.
                status='removed';reason='已歸為pool審核；攤牌組成/模型勝率沒有直接動作比較的CI，未達保留門檻。'
        elif old['b']=='pool':
            if '不明顯' in r['ev']:
                status='removed';reason='95% CI 未顯著，沒有同節點GTO備援。'
            else:
                baseline={h:solved.get('|'.join([r['sp'],r['nd'],r.get('c',{}).get('tx','*'),h]),{}).get('freq') for h in r['hc']}
                if any(baseline.values()):
                    r['ev']+='｜SB_BB代表子集GTO基準：'+json.dumps(baseline,ensure_ascii=False)+'；此池偏離的直接依據是棄牌率95% CI超過詐唬保本率，非全範圍最佳回應。'
                else:
                    r['ev']+='｜無同節點GTO基準；玩家池比較：文內勝率 vs 跟注所需勝率，或棄牌率 vs 詐唬保本率；未比較其他加注尺寸。'
        # All surviving pool observations must actually have at least 40 decisions.
        if status!='removed' and r['b']=='pool':
            ns=[int(x.replace(',','')) for x in re.findall(r'n=([\d,]+)',r['ev'])]
            if not ns or min(ns)<40:status='removed';reason='直接決策樣本 n<40。'
        if status!='removed':
            r.pop('hw',None);out.append(r)
        audit.append(dict(old_id=old['id'],sp=r['sp'],nd=r['nd'],hc=r['hc'],condition=old.get('c'),old_basis=old['b'],old_action=before,new_action=r['a'] if status!='removed' else None,disposition=r['b'] if status!='removed' else 'removed',reason=reason or '沿用有顯著性的直接玩家池比較。',evidence=evidence))
    for entry in audit:
        old=next(x for x in original if x['id']==entry['old_id'])
        if old['sp']=='mw' and old['nd'] in ('f_vs_bet','t_vs_bet'):
            entry['source_hc']=old['hc']
            entry['retained_classes']=[hc for hc in old['hc'] if entry['new_action'] and (hc=='S' or (mw.get(old['id']+'|'+hc if len(old['hc'])>1 else old['id'],{}).get('n',0)>=40 and (hc=='TPG' or mw[old['id']+'|'+hc if len(old['hc'])>1 else old['id']]['ci'][0]>=mw[old['id']+'|'+hc if len(old['hc'])>1 else old['id']]['required']+.10)))]
            entry['removed_classes']=[hc for hc in old['hc'] if hc not in entry['retained_classes']]
            if old['hc']!=['S']:
                entry['class_tests']={hc:mw[old['id']+'|'+hc if len(old['hc'])>1 else old['id']] for hc in old['hc']}
                entry['realization_margin_pp']=10 if set(old['hc']) & {'MID','WDRAW','AIR','DRAW','TPW'} else 0
    json.dump(audit,open(B/'results/audit.json','w'),ensure_ascii=False,indent=2)
    return out
