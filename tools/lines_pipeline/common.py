import pickle,sys
from collections import Counter

from vclass import fine, texture, cards
from phevaluator import evaluate_cards
RVv={r:i+2 for i,r in enumerate('23456789TJQKA')}
def ctype(bd,k):
    pre=cards(bd[:2*(k+1)]); allc=cards(bd)
    if len(allc)<=k+1: return None
    c=allc[k+1]; pr=[RVv[x[0]] for x in pre]; r=RVv[c[0]]
    if r in pr: return 'pair'
    sc=Counter(x[1] for x in pre)
    if sc[c[1]]>=2: return 'flush'
    def win(rs):
        s=set(rs)|({1} if 14 in rs else set())
        return max(len({x for x in s if lo<=x<lo+5}) for lo in range(1,11))
    w0,w1=win(pr),win(pr+[r])
    if w1>=4 and w0<4: return 'str4'
    if w1>=3 and w0<3: return 'str3'
    if r>max(pr): return 'over'
    return 'blank'
def hcls(h,bd):
    f=fine(h,bd)
    return {'nuts':'S','set':'S','trips':'S','two_pair':'S','overpair':'TPG','tp_good':'TPG','tp_weak':'TPW','mid_pair':'MID','low_pair':'MID','fd':'DRAW','oesd':'DRAW','gut':'WDRAW','overs':'WDRAW','air':'AIR'}[f]
def ev(h,bd): c=cards(h)+cards(bd); return evaluate_cards(*c)
def load(): return pickle.load(open('/workspace/outputs/poker_solver/read_v1/data/hu.pkl','rb'))
def szb(x):
    return 's33' if x<=0.4 else 's50' if x<=0.6 else 's75' if x<=0.85 else 's100' if x<=1.15 else 's150'
SZ={'s33':0.33,'s50':0.5,'s75':0.75,'s100':1.0,'s150':1.5}
def streets(r):
    S={1:[],2:[],3:[]}
    for s,ro,a,x,ai in r['ac']: S[s].append((ro,a,x,ai))
    return S
def tok(seq): return ' '.join(ro+a for ro,a,x,ai in seq)
