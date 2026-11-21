# B55 | 41 CERT / 351 APPROX source-blind V5

PR #2 stays Draft; never merge. V1 24/368, V2 26/366, V3 27/365 and V4 33/359 remain immutable.
Eight source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 42 | ln-3bp-3b_t_model-1fvksvd | 8s8h3d, 9s6h3d, KsTh3d, Js9h4d, As8h4d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402] | [] |
| 44 | ln-opfr-r_model-1jbfzu2 | As9h2d, KsQh4d, 9s6h3d | [44666285424, 44732810327, 44736420272] | [44666285424, 44732810327, 44736420272] | [{'flop': 'As9h2d', 'strict': 9}, {'flop': 'KsQh4d', 'strict': 6}, {'flop': '9s6h3d', 'strict': 2}] |
| 49 | ln-bb-r_model-1j900bm | 9s6h3d, Js9h4d, AsAh5h, KsQh4d, As9h2d | [44521980749, 44525865923, 44653774402, 44666285424] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 50 | ln-bb-r_model-7k7zqm | AsQh8d, 8s8h3d, Ks7s2s, Js9h4d, 9s6h3d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402, 44666285424, 44779505990, 44798496352] | [] |
| 51 | ln-bb-r_model-gy6l20 | 9s6h3d, Js9h4d, AsAh5h, KsQh4d, As9h2d | [44521980749, 44525865923, 44653774402, 44666285424] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 53 | ln-opfr-r_model-58bsyc | Jh9d6s, 9s6h3d, AsTh4d, Ks7h2d, 8s8h3d | [44522421850, 44654973894, 44666285424, 44732810327, 44736420272] | [44522421850, 44654973894, 44666285424, 44732810327, 44736420272, 44737532081, 44741462253] | [] |
| 54 | ln-opfr-r_model-qqvo52 | Jh9d6s, 9s6h3d, AsTh4d, Ks7h2d, 8s8h3d | [44522421850, 44654973894, 44666285424, 44732810327, 44736420272] | [44522421850, 44654973894, 44666285424, 44732810327, 44736420272, 44737532081, 44741462253] | [] |
| 55 | ln-ipfr-r_model-1mcb4lz | KsQh4d, Jh9d6s, As9h2d | [44666285424, 44732810327] | [44666285424, 44732810327] | [] |

161 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
