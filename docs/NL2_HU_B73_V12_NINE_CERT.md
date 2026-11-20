# B73 | 86 CERT / 306 APPROX source-blind V12

PR #2 stays Draft; never merge. V1–V11 source ledgers remain byte-for-byte unchanged; V11 77/315 is the verified parent.
Nine source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 136 | ln-ipfr-r_model-mbe4f | AsQh8d, Js9h4d, 9s6h3d, KsQh4d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 137 | ln-ipfr-r_model-zpwbil | As9h2d, AsAh5h, KsQh4d, Js9h4d, 9s6h3d | [44521980749, 44525865923, 44653774402, 44666285424] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 143 | ln-opfr-t_model-712wim | 9s6h3d, 8s8h3d, Jh9d6s, Ks7h2d, Js9h4d | [44654973894, 44666285424, 44732810327, 44736420272] | [44654973894, 44666285424, 44732810327, 44736420272, 44737532081, 44738324702] | [] |
| 144 | ln-3bp-3b_r_model-1bgfa05 | 8s8h3d, As7h3d, Ks7h2d | [44522421850, 44653774402, 44654973894] | [44522421850, 44653774402, 44654973894] | [{'flop': 'Ks7h2d', 'strict': 2}] |
| 145 | ln-3bp-3b_r_model-dz7v9p | As7h3d, KsQh4d, Ks7h2d | [44522421850, 44654973894, 44666290556] | [44522421850, 44654973894, 44666290556] | [] |
| 149 | ln-opfr-r_model-142idcm | 9s6h3d, AsKh3d, Ks7h2d | [44522421850, 44654973894, 44808905109] | [44522421850, 44654973894, 44808905109] | [{'flop': 'Ks7h2d', 'strict': 1}] |
| 152 | ln-ipc-t_model-1jnj1k6 | 8s8h3d, Js9h4d, AsTh4d | [44522421850, 44666285424] | [44522421850, 44666285424] | [{'flop': 'AsTh4d', 'strict': 3}] |
| 153 | ln-ipfr-r_model-1cbkgix | AsQh8d, Ks7s2s, 9s6h3d, Js9h4d, AsAh5h | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402] | [{'flop': '9s6h3d', 'strict': 6}, {'flop': 'Js9h4d', 'strict': 2}, {'flop': 'AsAh5h', 'strict': 1}] |
| 155 | ln-ipfr-r_model-v5g59j | Ks7s2s, AsAh5h, KsQh4d, Jh9d6s, 9s6h3d | [44521980749, 44525865923, 44653774402, 44732810327] | [44521980749, 44525865923, 44653774402, 44666285424, 44732810327] | [] |

334 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
