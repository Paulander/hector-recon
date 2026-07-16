# Native R0 competence-envelope V2 training-only preregistration

Date: 2026-07-16
Status: frozen before execution
Authority prerequisite: mature-envelope addendum commit 84e423f passed

## Scope

This is one touched-data, training-only competence-envelope package. It uses
only the purity-corrected 64-event tape already used by the admission abort:
48 historically named R0-train contexts and 16 historically named train-decoy
contexts. Those names are provenance only and are not learner-visible classes.

Do not access validation, regression, the 65 retired successors, R1, final, or
fresh data. Stop after the three-round lifecycle regardless of outcome.

## Frozen admission

Replay real completion observations through the purity-corrected R0 path and
require, before learning:

- exactly 40 successes and 24 failures;
- a policy response on all 64 events;
- 64 unique evidence keys;
- zero fabricated reward;
- exact persistent R0 identity;
- complete actuation and active-signal parity with the immutable addendum tape.

Failure closes the package before learning.

## Frozen learning arms

1. Connected: actual 40/24 outcomes.
2. Outcome-shuffled: the same records and fixed permutation seed 2026071602,
   changing outcome responsibility only.

Both arms use the unchanged GraphNativeCompetenceEnvelope defaults:

- minimum support 4;
- Wilson z 1.6448536269514722;
- lower-bound threshold 0.55;
- positive/refuted capacities 32/32;
- trial and proposal capacities 192/192;
- exactly three structural rounds;
- CompetenceContextGrowthGenome seed 2026071606;
- retrieval budget 16.

The global-evidence descriptive control is the actual prevalence 40/64 = 0.625.
It is not 0.75. No exact-mask or false-positive handover gate is run because
this package stops before inference; future such gates must consume the exact
wrapper-emitted handover mask.

## Required persistence

For each arm and each round persist:

- proposal and rejection counts;
- duplication histogram;
- support histogram;
- pure/impure/no-support histogram;
- exact success:failure mixture histogram;
- arity histogram;
- prune-reason histogram.

Persist full envelope manifests, training-only descriptive classification
metrics, frozen configuration, permutation hash, tripwires, and persistent R0
identity.

## Post-run laboratory diagnostic

After lifecycle, enumerate every base-signal singleton, pair, and triple with
support at least 4 and pure observed outcomes. This diagnostic is read-only and
may not nominate, mature, prune, or otherwise feed patterns back into either
arm.

Interpretation is frozen:

- pure patterns exist but none were proposed: nomination/responsibility failure;
- no pure patterns exist: current internal representation is insufficient;
- pure patterns were proposed but none matured: lifecycle defect;
- at least one pure pattern matured: maturation occurred; report selectivity
  descriptively and stop.

Whatever the result, close after lifecycle and request review.
