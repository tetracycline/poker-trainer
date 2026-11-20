# NL2 HU 392 models: multi-board CFR training labels and exact source evidence

Scope: PR #2 Draft, never merge without explicit authorization.
CERT-MULTIBOARD applies ONLY to 3–5 individually named true public board runs.
Every unlisted board/texture action remains APPROX, not GTO.

## Verified counts

| status | nodes |
| --- | ---: |
| CERT-MULTIBOARD | 14 |
| APPROX approximate | 378 |
| Total | 392 |

## Fixed frequency ranking and disclosure

Source: pinned poker-solver inputs/pool_stats.json, 2,334,487 NL2 hands.
Observed pot families: SRP 61.7%, 3BP 11.9%, limped 24.5%.
ISO not measured as an isolated postflop family: reserve 25% of limped as ISO proxy and 75% as LMP.
Sequential actions multiply marginal pooled frequencies, NOT observed exact multi-street frequencies.
Preregistered cutoff top 24 of 392, 6.12%; lower-ranked 368 remain APPROX.
CFR outcomes cannot be used to tune this cutoff.

## Genuine GitHub Actions batches

| batch | run | verified GTO games | partial NL2 lock games |
| --- | --- | ---: | ---: |
| B1 | 44666285424 | 88 | 159 |
| B2 | PENDING | 0 | 0 |
| B2_PARTIAL | 44666290556 | 65 | 166 |
| B2_REPAIRED_GTO | 44731732467 | 7 | 0 |
| B3 | 44666294821 | 43 | 90 |
| B4_MICRO | 44732810327 | 30 | 30 |
| B5_SBGAPS | PENDING | 0 | 0 |
| B6_REMAIN | PENDING | 0 | 0 |
| B7_RIVER | PENDING | 0 | 0 |
| B8_LOCK | PENDING | 0 | 0 |

## Top-24 preregistered game histories

| rank | model ID | family/spot | original SPR | label | named GTO flop boards |
| ---: | --- | --- | ---: | --- | --- |
| 1 | ln-iso-lmp_t_model-19hfq8v | LMP/LMP_CO_BB | 19.55 | APPROX | not enough authentic proof |
| 2 | ln-opfr-t_model-19esov6 | SRP/SB_BB | 5.056 | APPROX | not enough authentic proof |
| 3 | ln-opfr-t_model-1wej9w5 | SRP/SB_BB | 6.167 | APPROX | not enough authentic proof |
| 4 | ln-opfr-t_model-trdt3w | SRP/SB_BB | 7.833 | APPROX | not enough authentic proof |
| 5 | ln-opfr-t_model-id38uf | SRP/SB_BB | 16.167 | CERT-MULTIBOARD | 8s8h3d 5s, 9s6h3d Ts, Ks7h2d 9d, Js9h4d Ts, AsTh4d 4s |
| 6 | ln-bb-t_model-1n6d5u3 | SRP/BTN_BB | 17.727 | CERT-MULTIBOARD | 8s8h3d 5s, Ks7s2s 9d, 9s6h3d Ts, Js9h4d Ts, KsQh4d Tc |
| 7 | ln-iso-lmp_t_model-1e9jvm0 | LMP/LMP_CO_BB | 39.6 | CERT-MULTIBOARD | 8s8h3d 5s, 9s6h3d Ts, KsQh4d Tc |
| 8 | ln-ipfr-t_model-qcljc6 | SRP/BTN_BB | 8.364 | CERT-MULTIBOARD | Jh9d6s 3c, KsQh4d Tc, As9h2d Kd |
| 9 | ln-opfr-t_model-4t8fsk | SRP/SB_BB | 7.583 | CERT-MULTIBOARD | 9s6h3d Ts, Ks7h2d 9d, 8s8h3d 5s, Js9h4d Ts, As9h2d Kd |
| 10 | ln-iso-lmp_t_model-1nf06ka | LMP/LMP_CO_BB | 19.3 | CERT-MULTIBOARD | 9s6h3d Ts, KsQh4d Tc, 8s8h3d 5s |
| 11 | ln-bb-t_model-1c7tu96 | SRP/BTN_BB | 8.364 | CERT-MULTIBOARD | Ks7s2s 9d, Js9h4d Ts, KsQh4d Tc, As9h2d Kd, 9s6h3d Ts |
| 12 | ln-ipc-t_model-btptzw | SRP/SB_BB | 7.583 | CERT-MULTIBOARD | Js9h4d Ts, As9h2d Kd, Ks7h2d 9d, 8s8h3d 5s |
| 13 | ln-iso-lmp_t_model-10v4wiz | LMP/LMP_CO_BB | 19.3 | CERT-MULTIBOARD | 9s6h3d Ts, KsQh4d Tc, 8s8h3d 5s |
| 14 | ln-bb-t_model-cge9jz | SRP/CO_BB | 8.364 | CERT-MULTIBOARD | Js9h4d Ts, As9h2d Kd, 8s8h3d 5s |
| 15 | ln-opfr-r_model-1bv0680 | SRP/SB_BB | 2.833 | APPROX | not enough authentic proof |
| 16 | ln-opfr-r_model-j55znd | SRP/SB_BB | 2.278 | APPROX | not enough authentic proof |
| 17 | ln-opfr-r_model-j5b75a | SRP/SB_BB | 4.5 | CERT-MULTIBOARD | As9h2d Kd, 8s8h3d 5s, Ks7h2d 9d, 9s6h3d Ts, AsTh4d 4s |
| 18 | ln-opfr-r_model-ka3vbv | SRP/SB_BB | 2.833 | APPROX | not enough authentic proof |
| 19 | ln-3bp-3b_t_model-1gg0bw | 3BP/SB3_BTN | 1.414 | CERT-MULTIBOARD | 8s8h3d 5s, As7h3d Jh, Ks7h2d 9d |
| 20 | ln-ipfr-t_model-xbvh6 | SRP/BTN_BB | 17.727 | CERT-MULTIBOARD | Ks7s2s 9d, AsQh8d 3c, Jh9d6s 3c, AsAh5h 8s, 9s6h3d Ts |
| 21 | ln-opfr-r_model-1eyhxd9 | SRP/SB_BB | 7.833 | CERT-MULTIBOARD | 9s6h3d Ts, Ks7h2d 9d, As9h2d Kd, AsTh4d Td |
| 22 | ln-opfr-r_model-bkt7sm | SRP/SB_BB | 6.167 | APPROX | not enough authentic proof |
| 23 | ln-opfr-r_model-f6iab7 | SRP/SB_BB | 9.5 | APPROX | not enough authentic proof |
| 24 | ln-opfr-r_model-iry60z | SRP/SB_BB | 6.643 | APPROX | not enough authentic proof |

## Reasons some MODEL nodes are not CERT

- LOWER_FREQUENCY_BELOW_PREREGISTERED_TOP24_CUTOFF: 368
- NOT_ENOUGH_DISTINCT_AUTHENTIC_FLOPS_WITH_HERO_LOCKED_SOURCE: 10

## Convergence, combo reach and NL2 lock limits

Each exact-board GTO proof must preserve the real flop-turn-river board, action history, actor, root range/pot/SPR,
true node pot and effective SPR, source GitHub Actions run ID + SHA256, GTO gap <=0.5%,
and at least one combo remaining after the earlier-street highest/near-mixed branch filter.
Secondary actions only survive if f(a)>=40% absolute AND f(a)>=70% of highest frequency.
NL2 only supplies aggregate observed action/street/size frequencies; missing conditional rates
are IMPLICIT DEFAULTS, explicitly tagged: after a check bet45%; 33/50/75/100% sizing 35/35/20/10%.
Real private-card player-pool behavior and fully locked villain range are not empirically known.
50% pot depolarization is only a source-derived exact-board relative equity and action EV study candidate.
A 3–5-board representative set NEVER proves the entire generic six-texture model cell is GTO.

Do NOT merge Draft PR #2.
