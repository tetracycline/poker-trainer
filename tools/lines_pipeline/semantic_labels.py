"""Publication semantics, after evidence aggregation and before IDs/HW matching."""
import re
from collections import defaultdict
ORDER = ['SB','BB','UTG','HJ','CO','BTN']
def is_ip(e):
    return ORDER.index(e['me']) == max(ORDER.index(p) for p in [e['pa']]+e['pc'] if p)
def apply(out):
    from river_history import apply as river_history
    river_history(out)
    rows=out['rows']
    for s in out['spots']:
        if s['id']=='ipc': s['t']='你翻後有位置跟注（主要 BB vs SB；另含冷跟）';s['sub']='SB 開池、BB 防守，或前位開池、後位冷跟；你翻後有位置'
        if s['id']=='bb': s['t']='BB/SB OOP 防守';s['sub']='你在 BB/SB 跟注有位置的開池者，翻後沒位置'
        if s['id']=='ipfr': s['t']='你翻前開池、翻後有位置'
    # Initial unprefixed limp decisions also have explicit LMP evidence.
    for r in rows:
        if r['sp']=='iso' and r['nd'] in ('f_stab','f_lead'):
            r['nd']='lmp_'+r['nd']
        if r['sp']=='mw' and '兩人 GTO 近似' not in r['ev']: r['ev']='兩人 GTO 近似；'+r['ev']
    labels=defaultdict(dict)
    for r in rows:
        sp,nd=r['sp'],r['nd'];base=re.sub(r'^(?:3[bc]_|lmp_|iso_)','',nd)
        st='翻牌' if base.startswith('f_') else '轉牌' if base.startswith('t_') else '河牌'
        rr=[x for x in rows if (x['sp'],x['nd'])==(sp,nd)]
        ips={is_ip(e) for x in rr for e in x['eg']}
        if sp in ('ipfr','ipc'): ips={True}
        if sp in ('opfr','bb'): ips={False}
        if sp=='mw': ips={True,False}  # OOP in MW need not be first among all live players.
        first='你有位置，對手先行動' if ips=={True} else '你沒位置先行動' if ips=={False} else '依位置：沒位置者先行動'
        history='（全部前面行動線；逐題列出翻前與先前各街）' if st!='翻牌' else '（翻前角色見情境及例題）'
        if 'vs_3b' in base: action='你加注後，被再加注／全下'
        elif 'vs_xr' in base: action='你下注後，被加注'
        elif base=='t_vs_probe':
            action=('對手先下注（先前街可能過牌或下注跟注）' if ips=={True} else '本街你先過牌，對手下注（翻牌可能過牌或下注跟注）' if ips=={False} else '對手下注；若你沒位置，本街已先過牌（翻牌行動見例題）')
        elif base=='r_vs_bet' and sp=='ipfr': action='沒位置的跟注者先下注（領打）'
        elif 'vs_' in base: action='對手下注後，輪到你回應'
        elif base.endswith('delay'):
            action='翻牌雙方過牌後，轉牌延遲搶池 (stab)' if sp in ('ipc','bb') or nd.startswith(('3c_','lmp_','iso_')) else '翻牌雙方過牌後，轉牌延遲 c-bet'
        elif base.endswith('cbet'): action='c-bet？'
        elif base.endswith('barrel'): action='先前你下注後，這街繼續下注？'
        else: action='輪到你決定下注或過牌（先前行動見例題）'
        prefix='溜入底池・' if nd.startswith('lmp_') else '隔離底池・' if nd.startswith('iso_') else ''
        labels[sp][nd]=prefix+st+'：'+first+'；'+action+history
    out['node_labels']=dict(labels)
    # Legacy consumers still get accurate neutral labels, with per-spot UI above.
    for nd in {r['nd'] for r in rows}:
        out['nd'][nd]=next(labels[r['sp']][nd] for r in rows if r['nd']==nd)
    for i,r in enumerate(rows):r['id']=f"{r['sp']}.{r['nd']}.{i}"
    out['ver']='lines-semantic-v1'
