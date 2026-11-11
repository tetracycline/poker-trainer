#!/usr/bin/env python3
"""牌型逐街轉換表（真實發牌）：用正式分類器 run10_common.classes（翻牌/轉牌/河牌，含河牌強聽未中規則）
隨機發 4,000 萬手（固定種子 0..159，每批 25 萬），記錄每種「翻牌質地｜各街最高張 T 以上/9 以下」下
出現過的 翻牌→轉牌→河牌 牌型序列。輸出 tools/class_trans.json：{ "質地|hhh": "三字母序列 ..." }，
字母 s=兩對+ g=頂對好 w=頂對弱 m=中小對 d=強聽 k=弱聽 a=空氣。
用法：python3 tools/build_class_trans.py [批數=160]"""
import sys, os, random, json, collections
from multiprocessing import Pool
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(H, 'lines_pipeline'), '/workspace/outputs/poker/lines1105', '/workspace/outputs/poker_solver/read_v1']
from run10_common import classes
from common import texture
R = '23456789TJQKA'; DECK = [r + s for r in R for s in 'cdhs']
C = {'S': 's', 'TPG': 'g', 'TPW': 'w', 'MID': 'm', 'DRAW': 'd', 'WDRAW': 'k', 'AIR': 'a'}
def hi(cs): return 'T' if max(R.index(c[0]) for c in cs) >= R.index('T') else 'L'
def work(seed):
    rnd = random.Random(seed); cnt = collections.Counter()
    for _ in range(250000):
        d = rnd.sample(DECK, 7); h = ''.join(d[:2]); b = d[2:]
        k = texture(''.join(b[:3])) + '|' + hi(b[:3]) + hi(b[:4]) + hi(b[:5])
        cnt[(k, ''.join(C[classes(h, ''.join(b[:n]))[0]] for n in (3, 4, 5)))] += 1
    return cnt
if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 160
    tot = collections.Counter()
    with Pool(8) as p:
        for c in p.imap_unordered(work, range(n)): tot.update(c)
    out = collections.defaultdict(list)
    for (k, s), v in sorted(tot.items()): out[k].append(s)
    meta = {'_samples': n * 250000, '_rare_lt5': sorted(f'{k}:{s}={v}' for (k, s), v in tot.items() if v < 5)}
    json.dump({**meta, **{k: ' '.join(v) for k, v in sorted(out.items())}}, open(os.path.join(H, 'class_trans.json'), 'w'), ensure_ascii=False, indent=0)
    print(len(out), sum(len(v) for v in out.values()), 'sequences')
