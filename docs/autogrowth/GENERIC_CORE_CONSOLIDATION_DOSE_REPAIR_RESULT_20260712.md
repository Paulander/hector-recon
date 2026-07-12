# Generic-Core Consolidation Dose: No Eligible Fixed Dose

Date: 2026-07-12. Track: generic-core development. Verdict: valid preserved
measurements, no selected dose, and one overstrict laboratory invariant. No
automatic repair, new mechanism, confirmation, or KRK transfer authorized.

## Execution

The repair contract was committed at `61e9735`; the direct-comparison repair
and six synthetic regression tests were committed at `c96ea2f`. Before fresh
task generation, the full ReCoN core suite plus repair tests passed 56/56.

The frozen runner then completed one execution on 20 disjoint seeds
20261401--20261420 and wrote the full artifact.

## Frozen dose results

| Post-maturity scale | Median old joint | Median new joint | Median key old/new | Old beats control | Mature new pair | Median topology ablation |
|---:|---:|---:|---:|---:|---:|---:|
| 0.10 | 0.671875 | 1.000000 | 1.0 / 1.0 | 20/20 | 19/20 | 0.532715 |
| 0.25 | 0.427734 | 1.000000 | 1.0 / 1.0 | 18/20 | 20/20 | 0.514160 |
| 0.50 | 0.211914 | 1.000000 | 1.0 / 1.0 | 15/20 | 20/20 | 0.379883 |
| 1.00 control | 0.000000 | 1.000000 | 1.0 / 1.0 | 0/20 | 20/20 | 0.276855 |

No non-control dose reached the preregistered 0.85 old-regime median. Scale
0.50 also missed the paired old-over-control count. Therefore no dose is
eligible under the scientific gates, independent of the invariant issue below.
The runner selected no arm and no scale.

All four arms had a mature channel and post-maturity candidate/shared updates on
every task. Graph/update mismatch count and trial-root leakage were zero.
Observed capacity stayed within bounds (maximum four live and 32 total
proposals, versus limits four and 64).

## Stability-plasticity interpretation

The fixed positive-scale ladder shows an ordered response: decreasing shared
plasticity monotonically improves old-regime retention, while all tested
positive doses preserve median new-regime joint success of 1.0. Composite
ablation grows as the scale falls, showing that self-grown contextual topology
carries increasing causal responsibility.

This supports a real learner-local stability-plasticity control effect, but it
falsifies the preregistered claim that one of {0.10, 0.25, 0.50} achieves the
required coexistence level. Combined descriptively with the earlier scale-0
package (old/new medians 0.803711/0.645508 on different development tasks), the
fixed law appears unable to preserve both regimes at the demanded level.
Cross-package endpoint comparisons are descriptive only because seeds differ.

## Overstrict action-distribution invariant

The repaired check required the complete per-action `selection_count`
dictionaries to be identical across doses. This failed on 0/20 tasks. That is
not evidence of unequal compute: different learned policies legitimately choose
different actions.

The preserved artifact shows:

- training/evaluation episode counts and RNG-call counts equal on 20/20 tasks;
- total action selections equal on 20/20 tasks;
- only the distribution of those selections between actions differs.

The preregistered invariant is therefore a laboratory-design defect. It is not
relaxed post hoc, so `invariants_pass` remains false in the artifact. Removing
it would still select no dose because every non-control arm already fails at
least one scientific eligibility gate.

## Artifact and provenance

`reports/autogrowth/generic_core/consolidation_dose_key_door_20260712.json`

- artifact SHA-256:
  `33564685190112f1c9e46a429fc86a151e7cd864a4e4b2ee938c63d50331bc81`;
- source commit:
  `c96ea2f9958b331e17105b7d6d67050cf5d0a611`;
- task-row SHA-256:
  `5129359b5dcf8f8ddeed8ede3ddaf163dd391500b6fe722d5cdc468fd4c8cd91`;
- runner hash matches the frozen source;
- all 20 rows and all frozen helper hashes are present.

## Supported, falsified, and unshown

Supported:

- post-maturity shared learning rate causally orders retention;
- positive fixed doses preserve acquisition on these tasks;
- graph-grown composites remain behaviorally causal and bounded;
- the runner repair preserved complete auditable measurements.

Falsified:

- none of the preregistered positive fixed doses reaches the old/new coexistence
  criterion;
- exact per-action-count equality is not a valid equal-budget invariant.

Unshown:

- confidence-, age-, interference-, or activation-sensitive consolidation;
- replay or slow-target consolidation;
- independent confirmation;
- integration with the intrinsic curriculum or KRK.

## Required PI decision

This package is closed. The strongest next generic-core question is a new,
separately preregistered adaptive local consolidation law: shared plasticity
should decay with mature evidence/confidence or detected interference instead
of switching immediately to one fixed global fraction. It must be compared
against the frozen 0.10 and 1.00 development controls on fresh tasks, with equal
total experience/selection count but not equal per-action distributions.

An alternative is to stop generic-core mechanism development and reassess the
integration roadmap. Neither path is automatically authorized by this result.
