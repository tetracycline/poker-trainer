"""Independent river closing-call evidence, partitioned by prior opener history.
Only observed >=40-call strata are published; no aggregate n is relabelled.
"""
import json,math
from run10_apply import aggregate, key, render
from collections import defaultdict
from pathlib import Path
LABELS={'bet_bet':'你翻牌、轉牌都下注','check_turn':'你轉牌隨後過牌','other':'其他前面行動線'}
def category(line):
    streets=line.split('/')
    if len(streets)<2:return 'other'
    if all('Ab' in s.split() for s in streets[:2]):return 'bet_bet'
    if 'Ax' in streets[1].split() and 'Ab' not in streets[1].split():return 'check_turn'
    return 'other'
def example_category(e):
    parts=e['l'].split('/')
    if len(parts)<3:return 'other'
    acts=[[a.split(':',1)[1] for a in s.split() if a.startswith(e['me']+':')] for s in parts[:2]]
    if all(any(a.startswith('b') for a in aa) for aa in acts):return 'bet_bet'
    if acts[1]==['x']:return 'check_turn'
    return 'other'
def apply(out):
    rv=json.load(open('/workspace/outputs/poker/lines1105/river.json'))
    buckets={'le50':['s33','s50'],'p75':['s75','s100'],'o150':['s150']}
    sizes={'s33':.33,'s50':.5,'s75':.75,'s100':1,'s150':1.5}
    rows=out['rows'];added=[];audit=[]
    cells=json.load(open('/workspace/outputs/poker_lines_v2/results/run10/river_common.json'))['cells']
    for r in list(rows):
        if r['sp']!='ipfr' or r['nd']!='r_vs_bet' or r.get('x') or r['hc'][0] not in ('TPG','TPW','MID'):continue
        hc=r['hc'][0];sz=r.get('c',{}).get('sz')
        if sz not in buckets:continue
        groups=defaultdict(lambda:[0,0,0])
        for k,v in rv['W'].items():
            spot,line,bucket,ct,c=k.split('|')
            if spot!='SRP_CALLERbets_OOP' or line=='*' or bucket not in buckets[sz] or ct!='*' or c!=hc:continue
            g=groups[category(line)];g[0]+=v[0];g[1]+=v[1];g[2]+=v[1]*sizes[bucket]/(1+2*sizes[bucket])*100
        for prior,(w,n,weighted) in groups.items():
            record=dict(hc=hc,sz=sz,prior=prior,n=n,published=False)
            audit.append(record)
            if n<40:continue
            p=100*w/n;need=weighted/n;ci=196*math.sqrt(max(w/n*(1-w/n),1e-9)/n);sig=abs(p-need)>ci
            # Keep the significant-pool evidence policy and a same-history GTO baseline.
            vs=cells.get(key(r),[])
            def source_category(v):
                parts=v['line'].split('/')[:2];p=v['player']
                acts=[st.split()[p::2] for st in parts]
                if len(acts)==2 and all(any(a.startswith('b') for a in aa) for aa in acts):return 'bet_bet'
                if len(acts)==2 and acts[1]==['x']:return 'check_turn'
                return 'other'
            selected=[v for v in vs if v.get('reliable',True) and v.get('freq') and source_category(v)==prior]
            baseline=aggregate(selected)
            if not baseline:
                record['fallback']='全部前面行動線：此分組無可靠同線 GTO 基準';continue
            a='c' if p>=need else 'f';ok=[] if sig else ['f' if a=='c' else 'c']
            rr=dict(r,c=dict(r.get('c',{}),prior=prior),x=1,a=a,ok=ok,b='pool',evidence='semantic-river-history:'+prior,
                why=f'{LABELS[prior]}；跟注後攤牌勝率 {p:.1f}%，需要 {need:.1f}% → '+('跟' if a=='c' else '棄')+('（差距在誤差內，跟或棄都可以）' if not sig else ''),
                ev=f'玩家池 UTG–BB；SRP 有位置開池者面對沒位置跟注者河牌領打；{LABELS[prior]}；{hc}；尺寸桶 {sz}；跟注結束行動、必定攤牌；n={n}；勝率 {p:.2f}%；95% CI {p-ci:.2f}–{p+ci:.2f}%；按此組每個尺寸跟注數加權需要 {need:.2f}% → '+('顯著' if sig else '不明顯')+'；同位置同先前行動線 GTO 基準：'+json.dumps(baseline,ensure_ascii=False),
                eg=[e for e in r['eg'] if example_category(e)==prior])
            for k in ('solver','reach','pool_recount','baseline','historical_src'):rr.pop(k,None)
            rr['baseline']={'freq':baseline,'sample_count':len(selected)}
            rr['cl']=LABELS[prior]+'・'+out.get('size_labels',{}).get(sz,{'le50':'≤½ 池','p75':'¾–1 池','o150':'超池（1.5 池）'}[sz])
            if not sig:
                rr=render(rr,selected,rr['eg'],lambda c:rr['cl'],'history')
                rr['why']+='；此先前行動線玩家池與所需勝率差距不顯著，照同線 GTO。'
                rr['ev']+=f'；UTG–BB 玩家池同線跟注 n={n}，勝率 {p:.2f}%、需要 {need:.2f}%，95% CI {p-ci:.2f}–{p+ci:.2f}%；差距不明顯，未作玩家池偏離。'
            record['published']=True;record['basis']=rr['b']
            added.append(rr)
    rows.extend(added);out['river_history_audit']=audit
