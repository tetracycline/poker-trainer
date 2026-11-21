# Stage 2: reverified Batch 03 exact-board publication

The 12 existing archives of GitHub Actions run 44525865923 were downloaded without starting a workflow. Their bytes matched GitHub's archive SHA-256 metadata, and the pinned trainer's independent verifier accepted all 81 solved subgames (28 converged exact-board GTO, 53 experimental pool-locked responses; 3 excluded unreachable cases). See data/solver_evidence/STAGE2_BATCH03.json for the original source proof. Exported batch: 5,332 solver decision nodes.

- Compressed index SHA-256: `af482417b64c9bc5be226b819b999a998d50f06697bead8596120e324004a032`
- Decoded index SHA-256: `f60ffaa1e0fd5d84972e0ffea282092e75791edf25e9c4beaaa98c4560ced301`
- With the earlier 266 exact-board subgames, the viewer has 347 source subgames (114 exact-board GTO, 233 experimental locked responses). This is not 347 certified website MODEL nodes.
- The original 266-case payload is unchanged. Its literal backslash-n suffix is handled explicitly; the viewer shows legacy missing per-combo best-EV fields as unrecorded, not as solver advice.
- Generic MODEL upgrades: **0 / 392**. The generic queues do not specify fully matched public runout, exact action sizes, starting ranges and node SPR. No certification by matching texture, pot family, or approximate SPR alone. NL2 locked responses are experiments only where the matching source has observed frequencies.
- Viewer check: `node tools/test_nl2_cfr_viewer.cjs` exercises both batches, a missing delta, source labeling and readable legacy combo rows.
