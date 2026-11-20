# B61 | 56 CERT / 336 APPROX source-blind V8

PR #2 stays Draft; never merge. V1 24/368, V2 26/366, V3 27/365, V4 33/359, V5 41/351 and V6 42/350 remain immutable.
Eight source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 81 | ln-iso-lmp_r_model-1lno8ba | 8s8h3d, KsQh4d, 9s6h3d | [44666294821] | [44666294821] | [] |
| 82 | ln-3bp-3b_t_model-6vpmec | As7h3d, KsQh4d, Ks7h2d | [44522421850, 44654973894, 44666290556] | [44522421850, 44654973894, 44666290556] | [{'flop': 'Ks7h2d', 'strict': 7}] |
| 85 | ln-bb-r_model-1e6bpc | Ks7s2s, Js9h4d, KsQh4d, As9h2d, 9s6h3d | [44525865923, 44653774402, 44666285424] | [44525865923, 44653774402, 44666285424, 44781020650, 44799855318] | [] |
| 86 | ln-bb-r_model-myhu0j | Ks7s2s, AsQh8d, KsQh4d, Js9h4d, 9s6h3d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 87 | ln-3bp-3b_r_model-56w1du | 8s8h3d, As7h3d, Ks7h2d | [44522421850, 44653774402, 44654973894] | [44522421850, 44653774402, 44654973894] | [] |
| 90 | ln-opfr-r_model-1ixkq7a | 9s6h3d, Ks7h2d, Jh9d6s, 8s8h3d, As9h2d | [44654973894, 44666285424, 44732810327, 44736420272] | [44654973894, 44666285424, 44732810327, 44736420272, 44737532081] | [] |
| 91 | ln-opfr-r_model-1yd3f01 | 9s6h3d, Jh9d6s, Ks7h2d, 8s8h3d, As9h2d | [44654973894, 44666285424, 44732810327, 44736420272] | [44654973894, 44666285424, 44732810327, 44736420272, 44737532081] | [] |
| 95 | ln-opfr-r_model-107wn32 | Ks7h2d, AsKh3d, 9s6h3d | [44522421850, 44654973894, 44806967313] | [44522421850, 44654973894, 44806967313] | [{'flop': '9s6h3d', 'strict': 1}] |

219 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
