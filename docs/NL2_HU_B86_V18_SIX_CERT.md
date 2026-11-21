# B86 | 114 CERT / 278 APPROX source-blind V18

PR #2 stays Draft; never merge. V1–V17 source ledgers remain byte-for-byte unchanged; V17 108/284 is the verified parent.
Six source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 256 | ln-3bp-3c_r_model-cfardb | Ks7h2d, As8h4d, Ks7s2s, 8s8h3d, Js9h4d | [44521980749, 44525865923, 44653774402, 44654973894] | [44521980749, 44525865923, 44653774402, 44654973894] | [] |
| 263 | ln-3bp-3b_r_model-1nr3lqx | As8h4d, KsQh4d, KsTh3d | [44521980749, 44653774402] | [44521980749, 44653774402] | [] |
| 264 | ln-3bp-3b_r_model-rlw959 | As8h4d, KsQh4d, KsTh3d | [44521980749, 44653774402] | [44521980749, 44653774402] | [] |
| 268 | ln-bb-r_model-175ikcz | 9s6h3d, As9h2d, 8s8h3d, KsQh4d, Js9h4d | [44525865923, 44653774402, 44666285424] | [44525865923, 44653774402, 44666285424] | [{'flop': 'As9h2d', 'strict': 7}, {'flop': '8s8h3d', 'strict': 4}, {'flop': 'KsQh4d', 'strict': 3}, {'flop': 'Js9h4d', 'strict': 2}] |
| 269 | ln-bb-r_model-1ae4cgz | 9s6h3d, 8s8h3d, AsQh8d, Ks7s2s, As9h2d | [44521980749, 44525865923, 44653774402, 44666285424] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 273 | ln-opfr-r_model-17ewtg3 | 8s8h3d, 9s6h3d, Js9h4d, Ks7h2d, Jh9d6s | [44654973894, 44666285424, 44732810327, 44736420272] | [44654973894, 44666285424, 44732810327, 44736420272, 44737532081, 44738324702] | [] |

453 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
