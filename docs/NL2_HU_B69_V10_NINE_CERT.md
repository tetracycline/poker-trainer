# B69 | 66 CERT / 326 APPROX source-blind V10

PR #2 stays Draft; never merge. V1–V9 ledgers remain byte-for-byte unchanged; current V9 57/335 is the verified parent.
Nine source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 98 | ln-opfr-r_model-1kk2wqn | Ks7h2d, AsKh3d, 9s6h3d | [44522421850, 44654973894, 44806967313] | [44522421850, 44654973894, 44806967313] | [{'flop': '9s6h3d', 'strict': 1}] |
| 100 | ln-iso-lmp_r_model-1hgiamg | 9s6h3d, KsQh4d, 8s8h3d | [44666294821] | [44666294821] | [] |
| 101 | ln-iso-lmp_r_model-1hk7lr8 | 9s6h3d, KsQh4d, 8s8h3d | [44666294821] | [44666294821] | [] |
| 102 | ln-ipc-r_model-1at1re2 | As9h2d, Js9h4d, Ks7h2d, 8s8h3d | [44654973894, 44666285424] | [44654973894, 44666285424] | [{'flop': '8s8h3d', 'strict': 3}] |
| 104 | ln-ipfr-r_model-1k916pi | KsQh4d, As9h2d, Jh9d6s, 8s8h3d | [44666285424, 44732810327] | [44666285424, 44732810327] | [{'flop': '8s8h3d', 'strict': 6}] |
| 105 | ln-ipfr-r_model-1v72njh | KsQh4d, Jh9d6s, As9h2d | [44666285424, 44732810327] | [44666285424, 44732810327] | [] |
| 106 | ln-ipfr-r_model-5ce65m | KsQh4d, Jh9d6s, As9h2d | [44666285424, 44732810327] | [44666285424, 44732810327] | [] |
| 112 | ln-ipfr-r_model-9eqgjz | Ks7s2s, AsQh8d, Jh9d6s, 9s6h3d, AsAh5h | [44521980749, 44525865923, 44732810327] | [44521980749, 44525865923, 44732810327] | [] |
| 113 | ln-bb-r_model-123cy01 | Js9h4d, As9h2d, 8s8h3d | [44653774402, 44666290556] | [44653774402, 44666290556] | [] |

253 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
