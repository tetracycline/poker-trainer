"""Fine hand class of a holding on a board (2-5 board cards at flop/turn/river), for hand reading."""
from collections import Counter
from phevaluator import evaluate_cards
RV = {r: i + 2 for i, r in enumerate('23456789TJQKA')}
FINE_ZH = dict(nuts='順子以上', set='暗三', trips='明三', two_pair='兩對', overpair='超對', tp_good='頂對好踢', tp_weak='頂對弱踢',
               mid_pair='中對', low_pair='小對', fd='同花聽', oesd='兩頭順聽', gut='卡順', overs='兩高張', air='空氣')
GROUP = dict(nuts='S', set='S', trips='S', two_pair='S', overpair='M', tp_good='M', tp_weak='W', mid_pair='W', low_pair='W',
             fd='D', oesd='D', gut='A', overs='A', air='A')
GROUP_ZH = dict(S='兩對以上', M='頂對好踢/超對', W='弱對', D='聽牌', A='空氣', G='後來棄牌')
def cards(s): return [s[i:i + 2] for i in range(0, len(s), 2)]
def pair_class(x, br, pocket):
    u = sorted(set(br), reverse=True)
    if pocket:
        if x > u[0]: return 'overpair'
        return 'mid_pair' if x > u[-1] else 'low_pair'
    return 'top' if x == u[0] else ('mid_pair' if len(u) > 1 and x == u[1] else 'low_pair')
def fine(hole, board):
    h = cards(hole); b = cards(board); hr = [RV[c[0]] for c in h]; br = [RV[c[0]] for c in b]
    r = evaluate_cards(*(h + b))
    if len(b) == 5 and evaluate_cards(*b) == r: return 'air'
    pocket = hr[0] == hr[1]; bc = Counter(br)
    if r <= 1609: return 'nuts'
    if r <= 2467:
        if pocket and hr[0] in bc: return 'set'
        if any(bc[x] == 2 for x in hr if x in bc): return 'trips'
    m = [x for x in set(hr) if x in bc]
    if not pocket and len(m) == 2: return 'two_pair'
    if pocket and hr[0] not in bc: return pair_class(hr[0], br, True)
    if len(m) >= 1:
        x = max(m); pc = pair_class(x, br, False)
        if pc == 'top':
            k = hr[1] if hr[0] == x else hr[0]
            return 'tp_good' if k >= 11 else 'tp_weak'
        return pc
    if len(b) < 5:
        sc = Counter(c[1] for c in h + b)
        if any(n >= 4 and any(c[1] == s for c in h) for s, n in sc.items()): return 'fd'
        allr = set(br + hr); allr |= {1} if 14 in allr else set(); hs = set(hr) | ({1} if 14 in hr else set())
        for lo in range(1, 11):
            w = set(range(lo, lo + 4))
            if w <= allr and w & hs and lo > 1 and lo + 3 < 14: return 'oesd'
        for lo in range(1, 11):
            w = set(range(lo, lo + 5))
            if len(w & allr) >= 4 and w & hs: return 'gut'
    if min(hr) > max(br): return 'overs'
    return 'air'
TEX = ['A_high', 'KQ_high', 'mid_high', 'low', 'paired', 'mono']
TEX_ZH = dict(A_high='A 高面', KQ_high='K/Q 高面', mid_high='J/T 高面', low='9 以下低牌面', paired='對子面', mono='單色面', ALL='全部牌面')
def texture(board):
    b = cards(board[:6]); rs = [RV[c[0]] for c in b]
    if len(set(c[1] for c in b)) == 1: return 'mono'
    if len(set(rs)) < 3: return 'paired'
    m = max(rs)
    return 'A_high' if m == 14 else 'KQ_high' if m >= 12 else 'mid_high' if m >= 10 else 'low'
if __name__ == '__main__':
    for hole, bd in [('KsKd', 'Kh7c2d'), ('Ah9h', 'Kh7h2d'), ('KdQc', 'Kh7c2d'), ('9c8c', 'Th7c2d'), ('7d7s', 'Kh7c2dKs'), ('AcJd', 'Kh7c2d'), ('5s5d', 'Kh7c2d'), ('Ac5c', 'Kh7c2d3s4h')]:
        print(hole, bd, fine(hole, bd))
