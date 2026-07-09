# Phase 3.19 Summary

Artifacts:

- `../phase3_19_noop_ablation_control/summary.json`
- `summary.json`

No-op ablation control: failed. The old 3.17 per-cell ablation path, run with no cell disabled,
showed nonzero offsets for 154/154 subjects. Median full-minus-noop offsets by seed were
-34, -31, -34, -35, -34. The old "154 harmful" verdict is therefore runner-provenance contaminated.

Dose-response probation: 198 probation tests, 792 dose tests at x1/x3/x9/x27. Every nominee was
`flat_all_doses`: confirmed=0, demoted=0, nonzero dose discordants=0.

Controlled heldout ablation: the exact-adversarial no-op control passed, but there were no confirmed
cells to ablate.

Outcome-audition accounting: first-flip and bounded-outcome verdicts agree only 0.480 overall.
Stage B agreement by seed: 0.467, 0.505, 0.433, 0.368, 0.400.

Interpretation: first-flip auditions are misaligned, but dose-response shows the current nominees
are causally silent in validation even at high dose. Next test should use outcome-paired nomination
and instrument activation/proposal/choice-change per nominee and dose.
