# B71 | 77 CERT / 315 APPROX source-blind V11

PR #2 stays Draft; never merge. V1–V10 source ledgers remain byte-for-byte unchanged; V10 66/326 is the verified parent.
Eleven source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 117 | ln-iso-lmp_r_model-22vpzh | 9s6h3d, KsQh4d, 8s8h3d | [44666294821, 44767785255] | [44666294821] | [{'flop': '8s8h3d', 'strict': 3}] |
| 118 | ln-iso-lmp_r_model-zhthyp | 9s6h3d, KsQh4d, 8s8h3d | [44666294821, 44767785255] | [44666294821] | [{'flop': '8s8h3d', 'strict': 3}] |
| 119 | ln-opfr-r_model-lcxflf | Jh9d6s, 8s8h3d, 9s6h3d, Ks7h2d, As9h2d | [44654973894, 44666285424, 44732810327, 44736420272] | [44654973894, 44666285424, 44732810327, 44736420272] | [] |
| 120 | ln-3bp-3b_t_model-n5cvfv | As8h4d, KsQh4d, KsTh3d, Ks7h2d | [44521980749, 44653774402, 44654973894] | [44521980749, 44653774402, 44654973894] | [{'flop': 'Ks7h2d', 'strict': 3}] |
| 126 | ln-ipc-r_model-1h0u85n | Js9h4d, AsTh4d, Ks7h2d, As9h2d | [44522421850, 44654973894, 44666285424] | [44522421850, 44654973894, 44666285424] | [] |
| 127 | ln-ipc-r_model-ugjjw9 | Js9h4d, As9h2d, Ks7h2d | [44654973894, 44666285424] | [44654973894, 44666285424] | [] |
| 128 | ln-ipc-r_model-va4mgd | AsTh4d, Js9h4d, Ks7h2d, As9h2d | [44522421850, 44654973894, 44666285424] | [44522421850, 44654973894, 44666285424] | [] |
| 129 | ln-3bp-3b_r_model-1bnzddd | KsTh3d, 9s6h3d, 8s8h3d, As8h4d, Js9h4d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402] | [{'flop': 'Js9h4d', 'strict': 7}] |
| 130 | ln-3bp-3b_r_model-1qarh6x | Js9h4d, Ks7s2s, Ks7h2d, 8s8h3d, As8h4d | [44521980749, 44525865923, 44653774402, 44654973894] | [44521980749, 44525865923, 44653774402, 44654973894] | [{'flop': '8s8h3d', 'strict': 3}, {'flop': 'As8h4d', 'strict': 3}] |
| 132 | ln-bb-r_model-112apbt | Ks7s2s, Js9h4d, KsQh4d, 9s6h3d, As9h2d | [44525865923, 44653774402, 44666285424] | [44525865923, 44653774402, 44666285424] | [] |
| 134 | ln-ipfr-r_model-1iypoop | KsQh4d, Js9h4d, 8s8h3d, Jh9d6s | [44653774402, 44732810327] | [44653774402, 44666285424, 44732810327] | [{'flop': 'Js9h4d', 'strict': 9}, {'flop': '8s8h3d', 'strict': 6}, {'flop': 'Jh9d6s', 'strict': 1}] |

298 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
