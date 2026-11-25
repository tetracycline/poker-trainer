# B844 external handoff: CI evidence checkpoint (no promotion)

Source branch: `fix/nl2-hu-lines-audit-20261118`. Frozen registry: **158 CERT-MULTIBOARD / 234 APPROX / 0 EST**, 392 total; weighted model-opportunity coverage **84.700987%**. The 90% hypothetical threshold is **not attained**.

- B839 `5db0af332`: Actions native run **45527116296 success**, full batch audit **45527116109 success**; rank29 remains APPROX pending independently validated exact-board provenance and strict positive reach.
- B840 `c97ab1e6d`: Actions native run **45527191880 success**, full batch audit **45527191595 success**; rank57 remains APPROX absent positive verified source.
- B841 `a64d376fc`: Actions native run **45527456112 success**, full batch audit **45527456024 success**; rank80 remains APPROX absent positive verified source.
- B843 `ba47f3906`: seven authentic priority source results archived, **no promotion**. Native archive workflow **45529311703 success** at `95db479da`.
- B844 `3adcd4ccb`: native run **45535807925 success** with all three job conclusions success for `7h6h2c`, `8h7h3c`, `9h8h2c`; resulting artifact IDs: `14987535334`, `14986942830`, `14986593813`. Full batch audit run **45535807868 success**. Artifact ingestion, original SHA checks, precise actor/action/SPR, and strictly positive per-combo sequential reach are **not verified by this checkpoint**. Ranks92–94 remain APPROX, not CERT, until source archive and independent audit.

The existing source-blind frozen priority file `data/nl2_hu_b838_234_approx_frequency_priority.json` determines the order. Priority rank29: 1.378548% estimated per-hand opportunity; rank57: 0.767868%; rank75: 0.613597%; rank76: 0.609789%; rank80: 0.560271%. These are estimated *node opportunities*, not observed joint private-card frequencies. No re-run of successful Actions is authorized or needed.

Do not downgrade existing CERT without contrary authenticated evidence. Keep PR #2 draft, open, never merge, never force push. This document is a read-only CI provenance checkpoint and **does not itself certify any model**.
