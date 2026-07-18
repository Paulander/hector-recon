# Native R0 competence-envelope V3C held-out result

V3C completed its preregistered validation cohort and closed without opening
conditional regression. The instrument and authority gates passed, but neither
strict generalization nor safe-narrow transfer passed.

## Freeze and admission

The synthetic-only runner, tests, metrics, gates, and stop rules were committed
and pushed at `838068e` before any held-out frame was executed. The run preserved
source commit `152fc01c165f64d9fe87e3d9ddf2fb0dd2c2151a`, V3B artifact
`90a5393e92516256b25f35f43c1a9b2355b15b0e450c2b8836989f1a9c5ce920`,
and organism-index digest
`8762aab81cbf72440371d40fef3e4a297bf312f7754d8afb30b372ed34ce2f3e`.
All 32 connected and 32 outcome-shuffled organisms were included, including
ordinal 13 and its empty connected envelope.

Validation admission passed before the scientific gates were applied:

- all 32 frozen rows produced graph-owned R0 policy responses;
- the positive and decoy halves produced exactly 16 completions and 16
  noncompletions;
- all 2,048 wrapper queries matched complete real-reference GraphActuation and
  active-signal identities bit-exactly;
- persistent R0, envelope, and combined-wrapper state remained exact;
- effect, fabricated-reward, mutation, fallback, weighted-selector, and
  child-priority tripwire counts were zero;
- the validation positive and decoy rows were exact- and D4-disjoint from their
  respective training provenance; no row was removed or regenerated.

Evaluation was inference-only. It inserted no evidence, reward, grounding,
weights, lifecycle, topology, or maturity updates. It accessed no fresh pool,
R1 row, or 65-row retired-successor set.

## Preregistered validation verdict

| Measure | Required | Observed | Gate |
|---|---:|---:|---|
| Connected strict passes | >=28/32 | **0/32** | fail |
| Connected false positives | 0/512 | **21/512** | fail |
| Shuffled strict passes | <=4/32 | **0/32** | pass |
| Paired strict margin | >=24 | **0** | fail |
| Connected organisms with any TP | >=24/32 | **27/32** | pass |
| Paired safe-narrow margin | >=20 | **15** | fail |
| Integrity and authority | exact | **exact** | pass |

Connected organisms emitted 178 true-positive and 21 false-positive AVAILABLE
decisions. Twelve of 32 connected organisms produced at least one false
positive. Twenty had zero false positives, but only 15 combined zero false
positives with nonzero positive coverage. Six reached TP >=14, yet each also
produced at least one false positive. No organism satisfied TP >=14 and FP == 0.

The outcome-shuffled controls emitted no AVAILABLE decisions at all: 0 TP and
0 FP. This establishes that real-outcome association created transferable
activity, but it does not rescue selectivity: the connected cells generalized
beyond the contexts in which R0 actually completed its requested action.

## Closure and interpretation

Both validation verdicts failed. Per the frozen stop rule, regression inference
did not open and no regression row was presented to an envelope.

The binding boundary is `selectivity_or_representation`:
training-pure conjunctions overgeneralize on envelope-unseen historical
contexts. Because 27/32 connected organisms produced at least one held-out TP,
the result is not the preregistered “mostly training-local” branch. It also does
not support more lifecycle, capacity, or nomination work. Any next package must
first address why the present active-signal representation treats some actual
noncompletions as equivalent to learned completion contexts.

The known terminal-provenance debt remains unchanged:
`extract_active_competence_signals` reconstructs inputs from the board, selected
action, and graph maps rather than consuming an actual frame-local terminal
trace. V3C neither repairs that debt nor proves it caused the false positives.
No in-package repair, threshold change, selected organism, ensemble, new pool,
or R1 canary was performed.

## Artifacts and validation

- canonical result:
  `reports/autogrowth/native_authority/native_competence_envelope_v3c_heldout_generalization.json`;
- result SHA-256:
  `5ec16c0a775ec14ceb3d1daf3952a8944a4a298daa0648566ef06a8036f50bbb`;
- canonical runtime: **5,048.68 seconds**;
- focused pre-data validation: **9 passed**;
- full post-closure repository suite: **934 passed in 47m53s**.
