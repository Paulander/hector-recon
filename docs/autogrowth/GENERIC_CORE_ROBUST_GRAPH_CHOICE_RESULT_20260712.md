# Generic-Core Robust Graph Choice: Failed Development Package

Date: 2026-07-12. Track: generic-core development. Verdict: instrument failure.
Confirmation claim: none. The package is closed without tuning or rerun.

## Frozen execution

The contract was committed and pushed at `0377712`. Implementation, lifecycle
tests, and runner were committed and pushed at `7063921`; the full generic
library suite passed 38 tests. Only then were seeds 20260821–20260840 generated
and executed once.

## Raw gates

| Measurement | Frozen requirement | Observed |
|---|---:|---:|
| Lower-tail chooses consistent action | at least 19/20 | 20/20 |
| Mean chooses refutable action | at least 19/20 | 0/20 |
| Lower-tail minimum exceeds mean minimum | at least 19/20 | 0/20 |
| Graph/memory prediction mismatches | zero | zero |
| Matched configured budgets | 20/20 | 20/20 |

Both arms chose the consistent action at final evaluation. Their evaluation mean
and minimum were therefore both +0.4. The preregistered discriminatory prediction
failed.

Artifact:
`reports/autogrowth/generic_core/robust_graph_choice_rare_refutation_20260712.json`

- artifact SHA-256:
  `ca1202667d66fb21034adb6865b2a2ac4db7491316dbcc8ce45a808910ea8cf9`;
- source commit:
  `706392143c74525549896b1ba039c4f5449197f2`;
- task-row SHA-256:
  `b2639e70810fe3a94dc0327e5ff0addb84a32e822c46f1120fc18b805aad0847`;
- graph-policy implementation SHA-256:
  `2d564513d205a29a3b63498384b0a4cffca1fef889369e4d82b371440445f8b0`;
- return-memory implementation SHA-256:
  `3d8e8fc217bd0112e18e4bb83ea76adfd0f71c5156f2591bac400c2f98daf532`;
- runner SHA-256:
  `4581dfb86c8435a446077a79cd1a5d8cece8f39622bdf4b0ca80af174d19c68f`.

## Failure classification

This is an instrument failure, not evidence that empirical mean and lower-tail
choice are behaviorally equivalent.

`RobustReturnMemory` stores at most 256 samples. On every overflow,
`_compress` deliberately retains the lowest 10% and deterministic coverage of
the rest. `estimate().mean` is then calculated from that tail-enriched retained
buffer, not from an independent running sum/count. Repeated compression therefore
turns the advertised `mean_score` into another downside-biased statistic.

The artifact exposes the effect:

- the mean arm observed the refutable action 687–758 times per task;
- its retained 256-sample buffers contained 33.2%–39.1% catastrophic returns,
  although the environment emits exactly 12.5% in every block;
- retained refutable means were only 0.21875–0.33594 rather than the
  environment's +0.75 mean;
- consistent-action mean scores stayed near +0.399, so the nominal mean arm
  rationally selected the consistent action according to the corrupted
  statistic.

The earlier rare-refutation lifecycle test used only eight observations, below
the capacity boundary. It correctly tested the quantile rule but could not expose
long-run compression bias. This is a concrete example of a recurring project
failure mode: a semantic unit test passes below the regime where the research
instrument changes behavior.

## What remains valid

- Graph edge weights exactly matched their selected memory statistic: zero
  parity mismatches.
- RNG calls and episode budgets matched.
- Lower-tail selected the consistent action 20/20, but its advantage over a
  valid empirical-mean control is unidentified because that control was broken.
- The raw artifact and failure are preserved; no rescue narrative or robust
  policy claim is permitted.

## Required next decision

Do not patch and rerun this package. A future, separately authorized package
would need an estimator contract separating:

- exact streaming mean via uncompromised running sum/count;
- bounded lower-tail sketch/reservoir;
- confidence based on total observation count;
- capacity-crossing and long-horizon calibration tests;
- a fresh seed range and new frozen runner.

Until that work is authorized and passes, robust closed-loop choice remains
unestablished and the combined key-door/mid-run-change experiment must not start.
