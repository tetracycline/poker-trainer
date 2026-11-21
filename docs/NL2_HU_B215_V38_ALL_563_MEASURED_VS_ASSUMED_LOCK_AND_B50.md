# B215 exact named-board NL2 lock rate provenance audit

151 CERT /241 APPROX /0 EST.
All 581 named boards and 673 exact actor-lock variants were reconciled against B206 V38 independent sources.
50%-pot nonpolarized action is an exact-board research flag on 133 named boards only.
Observed NL2 rates are aggregate street/size marginals, never measured board-specific opponent private-hand conditional frequencies.
Unknown historical counts remain unknown; assumptions are NOT silently relabeled as observed data.
This report does not alter CERT labels, action policies or missing rate values.

## Source coverage counts

- HISTORICAL_SOURCE_COUNTS_UNKNOWN: 245
- MEASURED_POOL_MARGINAL_ONLY: 14
- MIXED_MEASURED_AND_ASSUMED_OR_UNKNOWN: 322
- assumed_default_nodes: 2139
- b50_candidate_boards: 133
- historical_unknown_source_variants: 315
- locked_source_variants: 673
- measured_source_nodes: 4510
- unmatched_villain_nodes: 3850

## Highest-frequency boards needing better measured source coverage

|Rank|Exact flop/turn|Model|Measured / assumed / unmatched|Unknown source variants|50% pot research|
|---:|---|---|---:|---:|---|
|1|2s4h6d Kh|ln-iso-lmp_t_model-19hfq8v|14/9/8|0|not proven|
|1|4s4h2d 8s|ln-iso-lmp_t_model-19hfq8v|14/11/15|0|exact-board candidate|
|1|7s5h3d 6c|ln-iso-lmp_t_model-19hfq8v|12/11/9|0|not proven|
|1|8s8h3d 5s|ln-iso-lmp_t_model-19hfq8v|28/19/29|0|not proven|
|2|9s6h3d Ts|ln-opfr-t_model-19esov6|17/10/22|0|not proven|
|2|As9h2d Kd|ln-opfr-t_model-19esov6|11/10/12|0|not proven|
|2|KsQh4d Tc|ln-opfr-t_model-19esov6|17/9/21|0|exact-board candidate|
|3|AsTh4d Td|ln-opfr-t_model-1wej9w5|0/0/0|1|exact-board candidate|
|3|Jh9d6s 3c|ln-opfr-t_model-1wej9w5|9/2/5|0|not proven|
|3|Ks7h2d 9d|ln-opfr-t_model-1wej9w5|9/2/5|1|exact-board candidate|
|4|As7h3d Kd|ln-opfr-t_model-trdt3w|9/2/6|0|not proven|
|4|As9h2d Kd|ln-opfr-t_model-trdt3w|10/10/14|0|not proven|
|4|Ks7h2d 9d|ln-opfr-t_model-trdt3w|8/2/3|1|exact-board candidate|
|5|8s8h3d 5s|ln-opfr-t_model-id38uf|28/22/55|0|exact-board candidate|
|5|9s6h3d Ts|ln-opfr-t_model-id38uf|33/25/21|0|exact-board candidate|
|5|As7h3d Kd|ln-opfr-t_model-id38uf|5/3/6|0|not proven|
|5|Jh9d6s 3c|ln-opfr-t_model-id38uf|14/8/5|0|not proven|
|5|Ks7h2d 9d|ln-opfr-t_model-id38uf|6/3/5|1|not proven|
|6|8s8h3d 5s|ln-bb-t_model-1n6d5u3|15/9/26|1|exact-board candidate|
|6|9s6h3d Ts|ln-bb-t_model-1n6d5u3|6/2/0|1|exact-board candidate|
|6|Js9h4d Ts|ln-bb-t_model-1n6d5u3|7/1/2|1|exact-board candidate|
|6|Ks7s2s 9d|ln-bb-t_model-1n6d5u3|7/2/3|1|not proven|
|6|KsQh4d Tc|ln-bb-t_model-1n6d5u3|20/9/0|1|not proven|
|7|8s8h3d 5s|ln-iso-lmp_t_model-1e9jvm0|13/10/8|0|exact-board candidate|
|7|9s6h3d Ts|ln-iso-lmp_t_model-1e9jvm0|14/11/7|0|exact-board candidate|
|7|KsQh4d Tc|ln-iso-lmp_t_model-1e9jvm0|14/10/1|0|exact-board candidate|
|8|As9h2d Kd|ln-ipfr-t_model-qcljc6|17/7/12|0|not proven|
|8|Jh9d6s 3c|ln-ipfr-t_model-qcljc6|21/7/14|0|exact-board candidate|
|8|KsQh4d Tc|ln-ipfr-t_model-qcljc6|22/7/24|0|exact-board candidate|
|9|8s8h3d 5s|ln-opfr-t_model-4t8fsk|8/13/16|0|not proven|
|9|9s6h3d Ts|ln-opfr-t_model-4t8fsk|4/7/14|0|not proven|
|9|As9h2d Kd|ln-opfr-t_model-4t8fsk|4/7/16|0|not proven|
|9|Jh9d6s 3c|ln-opfr-t_model-4t8fsk|4/7/16|0|not proven|
|9|Ks7h2d 9d|ln-opfr-t_model-4t8fsk|0/0/0|1|not proven|
|10|8s8h3d 5s|ln-iso-lmp_t_model-1nf06ka|21/7/12|0|not proven|
|10|9s6h3d Ts|ln-iso-lmp_t_model-1nf06ka|20/7/13|0|not proven|
|10|KsQh4d Tc|ln-iso-lmp_t_model-1nf06ka|19/7/13|0|not proven|
|11|9s6h3d Ts|ln-bb-t_model-1c7tu96|5/2/6|1|not proven|
|11|As9h2d Kd|ln-bb-t_model-1c7tu96|9/2/13|0|not proven|
|11|Js9h4d Ts|ln-bb-t_model-1c7tu96|5/2/7|1|not proven|

Complete all-581 source data: data/nl2_hu_b215_v38_563_exact_lock_provenance.json.
Must pass full 2475/2475 HU link, reach, node-lock and contract audits before push.
PR2 remains Draft. NEVER MERGE.
