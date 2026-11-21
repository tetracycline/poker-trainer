# B12 exact SB-vs-BB source examples

Four locally solved exact GTO subgames independently passed raw archive and viewer-export checks. All use the SB-open/BB-call range lineage, 6 bb flop pot and 97 bb effective stack, with a turn 3× raise branch. Two Q-high examples used a 33/50/75% flop bet menu on both sides and are action-history comparisons only. Two low-flop examples used a restricted 33% OOP versus 50% IP flop menu. Neither implies equilibrium under a larger tree.

For the low-flop target `ln-ipc-r_model-1owtkm1`, the actual 48 bb pot, 76 bb stack and 1.5833 SPR do not match the MODEL's assumed SPR of 1.444. Only the explicit research instances below are linked. No generic cert was awarded.

- [8♠ 6♥ 3♦ / 5♣ / 7♦, BB decision after SB check](../nl2-cfr.html?spot=SB_BB&version=gto&sha=076978568f1610131e757eacf176b1a710995ff9fbd332d143fac9d1896e7d68&board=3d6h8s5c7d&line=x%20b50%20c%2Fx%20b50%20r%20c%2Fx): 63 eligible BB combos.
- [8♠ 6♥ 3♦ / 5♣ / 2♣, BB decision after SB check](../nl2-cfr.html?spot=SB_BB&version=gto&sha=076978568f1610131e757eacf176b1a710995ff9fbd332d143fac9d1896e7d68&board=3d6h8s5c2c&line=x%20b50%20c%2Fx%20b50%20r%20c%2Fx): 71 eligible BB combos.

The viewer also includes the repository's already-completed independent 139-case Batch05 pack (50 GTO and 89 experimental locks). Its gzip/raw SHA match the committed index; it was not re-solved. A missing independent pack is now visible as partial coverage. Generic MODEL promotions remain zero.
