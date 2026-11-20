# Stage 2 B04: independently verified offline 3-bet GTO

- Local run: `LOCAL_20261120_B04_BB3_BTN_QsJh4d_GTO`; actual compute on the cloud workspace, not GitHub Actions.
- BTN opens, BB 3-bets, BTN calls; exact flop Q♠ J♥ 4♦; seeded turn 7♠; seven exact flop histories, two sampled rivers per solved history. This is not an all-runout solve.
- Pinned trainer runner source `a4f66dc79009e3cedadd4b456c9c9e7669681201`, solver `abe310c3aad02dd4a7c77fb2831801fd490cf51b`, upstream engine `9d1509fe5077d019825f833eed04b16d342dfda1`. Archived solver jobs preserve exact range weights, configuration and node previews.
- Runtime 108.21 s; parent exploitability 0.4910117%; 7/7 exact subgames pass the 0.5% convergence gate (0.1214–0.4631%); independent archived-input verification reports zero errors. 28,977 reachable combo-node observations, not unique hands.
- The viewer on this draft PR now shows 354 source subgames, including 121 exact-board GTO and 233 modelled pool-lock responses. The new seven solves are GTO only: no NL2 lock or whole-path max-frequency pruning is claimed. **Generic MODEL nodes upgraded: 0/392.**
- Reproduce the archived-input check by extracting the raw ZIP to a clean directory, then invoking `verify_downloads(extract_dir, "LOCAL_20261120_B04_BB3_BTN_QsJh4d_GTO")` from `tools/verify_hu_solver_bundle.py`, followed by `build(extract_dir, proof)` from `tools/export_hu_exact_board_cert.py`.
- SHA-256 raw ZIP `4748a1755bc2a3081680130972895a4a288c1a3b6129f986cbc1ff2a9861d2a7`; audit proof `97ac44441c3904fabb2e54f7950957025ed7a5f69ebe1881148dcf8dcf414351`; exact gzip index `fd02e55ad932bd0f162427a620154dd6b94b34d2e26cd2322ce404053de871e4`.
