# NL2 publication pipeline

These modules were copied from `/workspace/outputs/poker_lines_v2` for the
semantic repair. `common.py` and `vclass.py` are vendored classifier dependencies.
`build_lines.py` imports this directory, never publication code from the output
workspace. `run9_apply` delegates to the included `run9c_apply`.

The archived evidence remains input data, not bundled Python code:
`/workspace/outputs/poker/lines1105` (aggregates and HW pickle),
`/workspace/outputs/poker_lines_v2/results` (solver jobs, results and provenance).
These large archives must be available to reproduce the build. The original
source paths inside evidence JSON are retained for provenance and reaggregation.
Python requires `phevaluator`; Node is used to read site data.

Order: evidence gate, run6–run10 migrations, explicit ISO/LMP sample partition
before run10 aggregation, river-history closing-call strata, per-spot semantic
labels, semantic contract, HW matching, publication. No generated JS is edited.
The historical `lmp_*` namespace includes ISO callers: run10 partitions its full
samples by the archived `limp_*` / `iso_*` source-job families and examples by `t`.
Unknown source families fail the build. All resulting frequencies are recomputed.

River history strata require n>=40 closing calls and an independently
partitioned same-history GTO baseline. Significant pool strata use the closing-call
verdict; non-significant strata use that history’s GTO strategy. Insufficient
strata retain all-history strategy and are recorded in `river_history_audit`. Size intervals on
rule cards show both endpoint pot-odds thresholds rather than inventing a single
point estimate.
