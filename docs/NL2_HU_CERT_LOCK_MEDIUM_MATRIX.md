# Exact NL2 CERT source: node-lock coverage and 50% pot research status

Draft PR #2. Never merge from this report.
Every row below is a **named true public board** with a solver run/SHA.
Opponent action rates refer only to **observed NL2 pool marginals**, not per-board/private-hand conditional behavior.
Unknown historical per-node source counts remain unknown; defaults and unmatched villain nodes are separately counted.
50% pot is a research candidate on the named runout, not a universal bet size recommendation.

Verified: 24 CERT / 368 APPROX; 88 named boards.

| rank | model | named board proof | GTO run | lock run(s) | measured / assumed / unlocked nodes | 50% pot |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1 | ln-iso-lmp_t_model-19hfq8v | 2s4h6d Kh | 44769773770 | 44769773770 | 14/9/8 | unproven |
| 1 | ln-iso-lmp_t_model-19hfq8v | 4s4h2d 8s | 44762388523 | 44762388523 | 14/11/15 | candidate |
| 1 | ln-iso-lmp_t_model-19hfq8v | 7s5h3d 6c | 44769773770 | 44769773770 | 12/11/9 | unproven |
| 1 | ln-iso-lmp_t_model-19hfq8v | 8s8h3d 5s | 44767785255 | 44666294821,44767785255 | 14/10/14 | unproven |
| 2 | ln-opfr-t_model-19esov6 | 9s6h3d Ts | 44732810327 | 44732810327 | 17/10/22 | unproven |
| 2 | ln-opfr-t_model-19esov6 | As9h2d Kd | 44666285424 | 44666285424 | 11/10/12 | unproven |
| 2 | ln-opfr-t_model-19esov6 | KsQh4d Tc | 44736420272 | 44736420272 | 17/9/21 | candidate |
| 3 | ln-opfr-t_model-1wej9w5 | AsTh4d Td | 44522421850 | 44522421850 | unknown | candidate |
| 3 | ln-opfr-t_model-1wej9w5 | Jh9d6s 3c | 44736420272 | 44752125878 | 9/2/5 | unproven |
| 3 | ln-opfr-t_model-1wej9w5 | Ks7h2d 9d | 44654973894 | 44654973894,44775751657 | unknown | candidate |
| 4 | ln-opfr-t_model-trdt3w | As7h3d Kd | 44736420272 | 44751432807 | 9/2/6 | unproven |
| 4 | ln-opfr-t_model-trdt3w | As9h2d Kd | 44666285424 | 44666285424 | 10/10/14 | unproven |
| 4 | ln-opfr-t_model-trdt3w | Ks7h2d 9d | 44654973894 | 44654973894,44775751657 | unknown | candidate |
| 5 | ln-opfr-t_model-id38uf | 8s8h3d 5s | 44666285424 | 44666285424,44737532081 | 14/11/27 | candidate |
| 5 | ln-opfr-t_model-id38uf | 9s6h3d Ts | 44732810327 | 44732810327,44741462253,44765475084 | 14/11/8 | candidate |
| 5 | ln-opfr-t_model-id38uf | As7h3d Kd | 44736420272 | 44765475084 | 5/3/6 | unproven |
| 5 | ln-opfr-t_model-id38uf | Jh9d6s 3c | 44736420272 | 44736420272 | 14/8/5 | unproven |
| 5 | ln-opfr-t_model-id38uf | Ks7h2d 9d | 44654973894 | 44654973894,44775751657 | unknown | unproven |
| 6 | ln-bb-t_model-1n6d5u3 | 8s8h3d 5s | 44653774402 | 44653774402,44666285424 | unknown | candidate |
| 6 | ln-bb-t_model-1n6d5u3 | 9s6h3d Ts | 44525865923 | 44525865923,44779505990 | unknown | candidate |
| 6 | ln-bb-t_model-1n6d5u3 | Js9h4d Ts | 44653774402 | 44653774402 | unknown | candidate |
| 6 | ln-bb-t_model-1n6d5u3 | Ks7s2s 9d | 44525865923 | 44525865923,44779505990 | unknown | unproven |
| 6 | ln-bb-t_model-1n6d5u3 | KsQh4d Tc | 44653774402 | 44653774402,44666285424 | unknown | unproven |
| 7 | ln-iso-lmp_t_model-1e9jvm0 | 8s8h3d 5s | 44666294821 | 44666294821 | 13/10/8 | candidate |
| 7 | ln-iso-lmp_t_model-1e9jvm0 | 9s6h3d Ts | 44666294821 | 44666294821 | 14/11/7 | candidate |
| 7 | ln-iso-lmp_t_model-1e9jvm0 | KsQh4d Tc | 44666294821 | 44666294821 | 14/10/1 | candidate |
| 8 | ln-ipfr-t_model-qcljc6 | As9h2d Kd | 44666285424 | 44666285424 | 17/7/12 | unproven |
| 8 | ln-ipfr-t_model-qcljc6 | Jh9d6s 3c | 44732810327 | 44732810327 | 21/7/14 | candidate |
| 8 | ln-ipfr-t_model-qcljc6 | KsQh4d Tc | 44666285424 | 44666285424 | 22/7/24 | candidate |
| 9 | ln-opfr-t_model-4t8fsk | 8s8h3d 5s | 44666285424 | 44666285424,44737532081 | 4/6/8 | unproven |
| 9 | ln-opfr-t_model-4t8fsk | 9s6h3d Ts | 44732810327 | 44732810327 | 4/7/14 | unproven |
| 9 | ln-opfr-t_model-4t8fsk | As9h2d Kd | 44666285424 | 44666285424 | 4/7/16 | unproven |
| 9 | ln-opfr-t_model-4t8fsk | Jh9d6s 3c | 44736420272 | 44736420272 | 4/7/16 | unproven |
| 9 | ln-opfr-t_model-4t8fsk | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | unproven |
| 10 | ln-iso-lmp_t_model-1nf06ka | 8s8h3d 5s | 44666294821 | 44666294821 | 21/7/12 | unproven |
| 10 | ln-iso-lmp_t_model-1nf06ka | 9s6h3d Ts | 44666294821 | 44666294821 | 20/7/13 | unproven |
| 10 | ln-iso-lmp_t_model-1nf06ka | KsQh4d Tc | 44666294821 | 44666294821 | 19/7/13 | unproven |
| 11 | ln-bb-t_model-1c7tu96 | 9s6h3d Ts | 44525865923 | 44525865923 | unknown | unproven |
| 11 | ln-bb-t_model-1c7tu96 | As9h2d Kd | 44666285424 | 44666285424 | 9/2/13 | unproven |
| 11 | ln-bb-t_model-1c7tu96 | Js9h4d Ts | 44653774402 | 44653774402 | unknown | unproven |
| 11 | ln-bb-t_model-1c7tu96 | Ks7s2s 9d | 44525865923 | 44525865923 | unknown | unproven |
| 11 | ln-bb-t_model-1c7tu96 | KsQh4d Tc | 44653774402 | 44653774402,44666285424 | unknown | unproven |
| 12 | ln-ipc-t_model-btptzw | 8s8h3d 5s | 44666285424 | 44666285424 | 19/2/6 | unproven |
| 12 | ln-ipc-t_model-btptzw | As9h2d Kd | 44666285424 | 44666285424 | 27/2/12 | unproven |
| 12 | ln-ipc-t_model-btptzw | Js9h4d Ts | 44666285424 | 44666285424 | 22/2/16 | candidate |
| 12 | ln-ipc-t_model-btptzw | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | unproven |
| 13 | ln-iso-lmp_t_model-10v4wiz | 8s8h3d 5s | 44666294821 | 44666294821 | 3/6/0 | unproven |
| 13 | ln-iso-lmp_t_model-10v4wiz | 9s6h3d Ts | 44666294821 | 44666294821 | 4/7/6 | unproven |
| 13 | ln-iso-lmp_t_model-10v4wiz | KsQh4d Tc | 44666294821 | 44666294821 | 4/6/7 | unproven |
| 14 | ln-bb-t_model-cge9jz | 8s8h3d 5s | 44653774402 | 44653774402 | unknown | unproven |
| 14 | ln-bb-t_model-cge9jz | As9h2d Kd | 44666290556 | 44666290556 | 9/2/14 | unproven |
| 14 | ln-bb-t_model-cge9jz | Js9h4d Ts | 44666290556 | 44666290556 | 9/2/14 | unproven |
| 15 | ln-opfr-r_model-1bv0680 | As9h2d Kd | 44666285424 | 44758653460 | 4/2/0 | unproven |
| 15 | ln-opfr-r_model-1bv0680 | AsTh4d 4s | 44522421850 | 44522421850 | unknown | candidate |
| 15 | ln-opfr-r_model-1bv0680 | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | unproven |
| 16 | ln-opfr-r_model-j55znd | 9s6h3d Ts | 44732810327 | 44732810327 | 17/10/22 | unproven |
| 16 | ln-opfr-r_model-j55znd | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | candidate |
| 16 | ln-opfr-r_model-j55znd | KsQh4d Tc | 44736420272 | 44736420272 | 17/9/21 | candidate |
| 17 | ln-opfr-r_model-j5b75a | 8s8h3d 5s | 44666285424 | 44666285424 | 10/9/0 | unproven |
| 17 | ln-opfr-r_model-j5b75a | 9s6h3d Ts | 44732810327 | 44732810327 | 7/8/0 | unproven |
| 17 | ln-opfr-r_model-j5b75a | As9h2d Kd | 44666285424 | 44666285424 | 14/9/13 | unproven |
| 17 | ln-opfr-r_model-j5b75a | Jh9d6s 3c | 44736420272 | 44736420272 | 3/0/0 | candidate |
| 17 | ln-opfr-r_model-j5b75a | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | unproven |
| 18 | ln-opfr-r_model-ka3vbv | As9h2d Kd | 44666285424 | 44758653460 | 4/2/0 | unproven |
| 18 | ln-opfr-r_model-ka3vbv | AsTh4d 4s | 44522421850 | 44522421850 | unknown | candidate |
| 18 | ln-opfr-r_model-ka3vbv | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | unproven |
| 19 | ln-3bp-3b_t_model-1gg0bw | 8s8h3d 5s | 44653774402 | 44653774402 | unknown | unproven |
| 19 | ln-3bp-3b_t_model-1gg0bw | As7h3d Jh | 44522421850 | 44522421850 | unknown | candidate |
| 19 | ln-3bp-3b_t_model-1gg0bw | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | candidate |
| 20 | ln-ipfr-t_model-xbvh6 | 9s6h3d Ts | 44525865923 | 44525865923,44779505990 | unknown | candidate |
| 20 | ln-ipfr-t_model-xbvh6 | AsAh5h 8s | 44521980749 | 44521980749 | unknown | candidate |
| 20 | ln-ipfr-t_model-xbvh6 | AsQh8d 3c | 44521980749 | 44521980749 | unknown | candidate |
| 20 | ln-ipfr-t_model-xbvh6 | Jh9d6s 3c | 44732810327 | 44732810327 | 22/6/18 | candidate |
| 20 | ln-ipfr-t_model-xbvh6 | Ks7s2s 9d | 44525865923 | 44525865923,44779505990 | unknown | candidate |
| 21 | ln-opfr-r_model-1eyhxd9 | 9s6h3d Ts | 44732810327 | 44732810327 | 14/11/8 | candidate |
| 21 | ln-opfr-r_model-1eyhxd9 | As9h2d Kd | 44666285424 | 44666285424 | 14/11/18 | unproven |
| 21 | ln-opfr-r_model-1eyhxd9 | Jh9d6s 3c | 44736420272 | 44736420272 | 14/8/5 | unproven |
| 21 | ln-opfr-r_model-1eyhxd9 | Ks7h2d 9d | 44654973894 | 44654973894 | unknown | candidate |
| 21 | ln-opfr-r_model-1eyhxd9 | KsQh4d Tc | 44736420272 | 44736420272 | 13/8/7 | unproven |
| 22 | ln-opfr-r_model-bkt7sm | 8s8h3d 5s | 44737532081 | 44737532081 | 14/11/28 | candidate |
| 22 | ln-opfr-r_model-bkt7sm | 9s6h3d Ts | 44741462253 | 44741462253 | 14/11/9 | candidate |
| 22 | ln-opfr-r_model-bkt7sm | KsQh4d Tc | 44741462253 | 44741462253 | 12/8/9 | unproven |
| 23 | ln-opfr-r_model-f6iab7 | 8s8h3d 5s | 44737532081 | 44737532081 | 14/11/28 | unproven |
| 23 | ln-opfr-r_model-f6iab7 | 9s6h3d Ts | 44741462253 | 44741462253 | 14/11/9 | candidate |
| 23 | ln-opfr-r_model-f6iab7 | KsQh4d Tc | 44741462253 | 44741462253 | 12/8/9 | unproven |
| 24 | ln-opfr-r_model-iry60z | 9s6h3d Ts | 44763159052 | 44765475084 | 5/3/4 | candidate |
| 24 | ln-opfr-r_model-iry60z | As7h3d Kd | 44763159052 | 44765475084 | 5/3/6 | candidate |
| 24 | ln-opfr-r_model-iry60z | KsQh4d Tc | 44763159052 | 44765475084 | 5/3/4 | unproven |

No CERT from generic texture mapping or unsupported downstream action lines.
