"""Runout category of the newest board card (turn: street 2, river: street 3). Shared by run 005 prep / worker / apply / site JS.
Priority: flush > straight > pair > over > draw (turn only) > brick.
 flush    : the new card is the 3rd (or 4th+) card of its suit on the board -> a flush is now possible
 straight : the new card makes a two-card straight possible where none was (max ranks in any 5-window: <3 -> >=3),
            or makes a one-card straight possible (<4 -> >=4); ace plays high and low
 pair     : the new card pairs the board
 over     : A or K, or higher than every previous board card
 draw     : (turn only) 2nd card of its suit (new flush draw), or within 1 rank of a board card (new straight draws)
 brick    : none of the above"""
RV = '23456789TJQKA'
CATS = {2: ['over', 'pair', 'flush', 'straight', 'draw', 'brick'], 3: ['over', 'pair', 'flush', 'straight', 'brick']}
def _w(rs):
    s = set(rs) | ({1} if 14 in rs else set())
    return max(sum(1 for x in range(lo, lo + 5) if x in s) for lo in range(1, 11))
def rcat(bd, street):
    cs = [bd[i:i + 2] for i in range(0, 2 * (2 + street), 2)]
    pre, c = cs[:-1], cs[-1]
    r = RV.index(c[0]) + 2; pr = [RV.index(x[0]) + 2 for x in pre]; su = [x[1] for x in pre]
    if su.count(c[1]) >= 2: return 'flush'
    w0, w1 = _w(pr), _w(pr + [r])
    if (w0 < 3 <= w1) or (w0 < 4 <= w1): return 'straight'
    if r in pr: return 'pair'
    if r >= 13 or r > max(pr): return 'over'
    if street == 2:
        if su.count(c[1]) == 1: return 'draw'
        lo = {1 if x == 14 else x for x in pr} | set(pr); rr = {r, 1} if r == 14 else {r}
        if any(abs(a - b) == 1 for a in rr for b in lo): return 'draw'
    return 'brick'
