# B90 | 122 CERT / 270 APPROX source-blind V20

PR #2 stays Draft; never merge. V1–V19 source ledgers remain byte-for-byte unchanged; V19 116/276 is the verified parent.
Six source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.

| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |
|---:|---|---|---|---|---|
| 297 | ln-bb-r_model-1xta9o0 | As9h2d, 8s8h3d, Js9h4d | [44522421850, 44653774402, 44666290556] | [44522421850, 44653774402, 44666290556] | [{'flop': 'Js9h4d', 'strict': 1}] |
| 298 | ln-bb-r_model-qvy09c | Js9h4d, As9h2d, 8s8h3d | [44522421850, 44653774402, 44666290556] | [44522421850, 44653774402, 44666290556] | [{'flop': '8s8h3d', 'strict': 5}] |
| 301 | ln-3bp-3c_r_model-1av2gz9 | Ks7h2d, As7h3d, 8s8h3d, KsQh4d | [44522421850, 44653774402, 44654973894, 44666290556] | [44522421850, 44653774402, 44654973894, 44666290556] | [] |
| 303 | ln-ipc-r_model-453wc7 | Js9h4d, AsTh4d, 8s8h3d | [44522421850, 44666285424] | [44522421850, 44666285424] | [{'flop': 'Js9h4d', 'strict': 6}, {'flop': 'AsTh4d', 'strict': 3}, {'flop': '8s8h3d', 'strict': 2}] |
| 304 | ln-ipc-r_model-a4yc6n | Ks7h2d, AsTh4d, Js9h4d, 8s8h3d, As9h2d | [44522421850, 44654973894, 44666285424] | [44522421850, 44654973894, 44666285424] | [{'flop': '8s8h3d', 'strict': 1}] |
| 310 | ln-bb-r_model-1fbdqqz | 8s8h3d, As9h2d, Js9h4d | [44522421850, 44653774402, 44666290556] | [44522421850, 44653774402, 44666290556] | [{'flop': 'Js9h4d', 'strict': 8}] |

482 exact named board certificates. Some proof has thin legal combos.
LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.
Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.
50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.
Unmatched, assumed and historical unknown node counts remain separate.
Batch E 44732810327 verified, 2475/2475 river navigation previously verified.
