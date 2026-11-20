# B50 | 33 exact named-board CERT / 359 APPROX (versioned V4)

Draft PR #2 only; do not merge. Original V1 24/368, V2 26/366 and V3 27/365 remain immutable.
Six rank-preselected models 31,34,36,37,38,39 have 3–5 distinct real GTO/hero-lock flop proofs:
| Rank | Model | Flops | source GTO run IDs | lock runs | Thin strict-reach warnings |
| ---: | --- | --- | --- | --- | --- |
| 31 | ln-opfr-t_model-1xzqrwx | AsKh3d, Ks7h2d, 9s6h3d | [44522421850, 44654973894, 44806967313] | [44522421850, 44654973894, 44806967313] | [{'flop': '9s6h3d', 'n': 1}] |
| 34 | ln-iso-lmp_r_model-1jgtf86 | 4s4h2d, 7s5h3d, 2s4h6d | [44762388523, 44769773770] | [44762388523, 44769773770] | [{'flop': '7s5h3d', 'n': 2}, {'flop': '2s4h6d', 'n': 1}] |
| 36 | ln-ipfr-t_model-1ktwuv7 | Jh9d6s, KsQh4d, As9h2d | [44666285424, 44732810327] | [44666285424, 44732810327] | [] |
| 37 | ln-ipfr-t_model-1u5hox2 | AsQh8d, 9s6h3d, Js9h4d, KsQh4d, Ks7s2s | [44521980749, 44525865923, 44653774402] | [44521980749, 44525865923, 44653774402, 44666285424] | [] |
| 38 | ln-ipfr-t_model-1xz5oyp | 8s8h3d, As9h2d, Js9h4d, KsQh4d, 9s6h3d | [44525865923, 44653774402, 44666285424] | [44525865923, 44653774402, 44666285424] | [] |
| 39 | ln-ipfr-t_model-dzbacd | KsQh4d, Js9h4d, 8s8h3d, Ks7s2s, Jh9d6s | [44525865923, 44653774402, 44732810327] | [44525865923, 44653774402, 44666285424, 44732810327] | [{'flop': 'Ks7s2s', 'n': 2}, {'flop': 'Jh9d6s', 'n': 1}] |

101 existing +24 new =125 named board certificates. Each has correct acting seat, actual SPR, source SHA, legal combos and hero-side lock.
LMP rank34 uses assumed 169-class preflop ranges and a RESTRICTED 50% single-size flop tree, NOT unrestricted GTO.
Any 1–2 strictly reachable combos are thin evidence and cannot justify generic six-texture strategies.
50% pot depolarization is research-only on explicitly supported named boards. Unsupported examples are NOT recommendations.
NL2 observed aggregate marginals do not measure particular private-hand action frequencies.
Batch E 44732810327 remained VERIFIED, river links previously 2475/2475. PR stays Draft/Open.
