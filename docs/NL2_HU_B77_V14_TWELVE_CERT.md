# B77 | 101 CERT / 291 APPROX source-blind V14

PR #2 stays Draft; never merge. V1–V13 source ledgers remain byte-for-byte unchanged; V13 89/303 is the verified parent.
Twelve source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 177 | ln-3bp-3b_r_model-1mh38ma | 8s8h3d, KsTh3d, 9s6h3d, Js9h4d, As8h4d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402] | [{'flop': 'As8h4d', 'strict': 7}] |
| 178 | ln-3bp-3b_r_model-1tjmzq2 | As8h4d, Ks7s2s, Js9h4d, KsTh3d, 8s8h3d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402] | [{'flop': '8s8h3d', 'strict': 9}] |
| 181 | ln-ipfr-r_model-1cnb93g | 9s6h3d, AsQh8d, Js9h4d, 8s8h3d, KsQh4d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402, 44666285424] | [{'flop': 'Js9h4d', 'strict': 9}] |
| 182 | ln-ipfr-r_model-1h1ml0q | AsAh5h, 9s6h3d, KsQh4d, Js9h4d, As9h2d | [44521980749, 44525865923, 44653774402, 44666285424] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 183 | ln-ipfr-r_model-1iyohr9 | KsQh4d, 8s8h3d, Js9h4d, Ks7s2s | [44525865923, 44653774402] | [44525865923, 44653774402, 44666285424] | [{'flop': '8s8h3d', 'strict': 5}, {'flop': 'Js9h4d', 'strict': 3}, {'flop': 'Ks7s2s', 'strict': 2}] |
| 184 | ln-ipfr-r_model-1ola0zn | KsQh4d, 8s8h3d, Js9h4d, Ks7s2s | [44525865923, 44653774402] | [44525865923, 44653774402, 44666285424] | [{'flop': 'KsQh4d', 'strict': 4}, {'flop': '8s8h3d', 'strict': 2}, {'flop': 'Js9h4d', 'strict': 2}, {'flop': 'Ks7s2s', 'strict': 1}] |
| 185 | ln-ipfr-r_model-1qq7ky | AsAh5h, 9s6h3d, KsQh4d, Js9h4d, As9h2d | [44521980749, 44525865923, 44653774402, 44666285424] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 186 | ln-ipfr-r_model-qwhkll | 9s6h3d, AsQh8d, Js9h4d, 8s8h3d, KsQh4d | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402, 44666285424] | [{'flop': 'Js9h4d', 'strict': 9}] |
| 187 | ln-ipfr-r_model-wispda | KsQh4d, 8s8h3d, Js9h4d, Ks7s2s | [44525865923, 44653774402] | [44525865923, 44653774402, 44666285424] | [{'flop': 'KsQh4d', 'strict': 4}, {'flop': '8s8h3d', 'strict': 2}, {'flop': 'Js9h4d', 'strict': 2}, {'flop': 'Ks7s2s', 'strict': 1}] |
| 189 | ln-ipc-r_model-1ua8hb7 | As9h2d, Js9h4d, Ks7h2d | [44654973894, 44666285424] | [44654973894, 44666285424] | [] |
| 191 | ln-ipc-r_model-i19djk | As9h2d, Js9h4d, Ks7h2d | [44654973894, 44666285424] | [44654973894, 44666285424] | [] |
| 195 | ln-3bp-3c_t_model-1dv9vgr | 9s6h3d, Js9h4d, Ks7s2s, 8s8h3d, Ks7h2d | [44525865923, 44653774402, 44654973894] | [44525865923, 44653774402, 44654973894] | [] |

400 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
