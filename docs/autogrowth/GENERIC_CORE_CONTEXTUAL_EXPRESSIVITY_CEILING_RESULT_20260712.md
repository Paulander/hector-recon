# Generic-Core Contextual Expressivity Ceiling: Additive Pairs Are Sufficient

Date: 2026-07-12. Track: generic-core development. Verdict: positive
laboratory ceiling. Coverage and gain independently compensate for the sparse,
bounded failure. This is not an autogrowth or KRK result.

## Frozen execution

The contract and resource amendment were committed at `b2ae707` and
`26de760`. The byte-identical shared freeze, 2x2 runner, exhaustive injection,
and tests were committed at `69859fb`.

Before fresh tasks:

- focused ceiling/learner tests passed 30/30;
- complete core and generic-runner suites passed 80/80;
- the full runner completed on one retired non-evidentiary smoke seed.

The once-only execution completed on seeds 20261701--20261720. All tasks passed
phase-0 mastery (median 1.0, minimum 0.951172), every checkpoint clone matched,
and shared parameters remained byte-identical in every arm/task.

## Frozen 2x2 results

| Arm | Median old | Median new | Tasks both >=0.85 | Median old/new topology effect | Full coverage | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Sparse-bounded | 0.959961 | 0.675781 | 5/20 | 0.372070 / 0.675781 | 0/20 | fail |
| Sparse-high-gain | 1.000000 | 1.000000 | 17/20 | 0.364258 / 1.000000 | 0/20 | pass |
| Exhaustive-bounded | 1.000000 | 1.000000 | 18/20 | 0.474609 / 1.000000 | 20/20 | pass |
| Exhaustive-high-gain | 1.000000 | 1.000000 | 20/20 | 0.474609 / 1.000000 | 20/20 | pass |

All three preregistered ceiling arms pass their gates. The fully combined
ceiling is perfect on 20/20 tasks.

## Factor interpretation

Sparse-bounded reproduces the prior insufficiency despite protected shared
weights. Either intervention independently repairs it:

- higher gain makes the sparse discovered topology sufficient on 17/20;
- exhaustive content-blind pair coverage makes current bounded gain sufficient
  on 18/20;
- combining both removes all remaining failures.

Coverage and gain are therefore alternative compensating bottlenecks, not two
jointly necessary ingredients on this generator. Additive cue x regime pairs
have now passed a direct expressivity ceiling; a second memory store or richer
operator is not required to represent coexistence here.

Final sparse coverage differed downstream (median 3/8 bounded versus 4/8
high-gain) because gain changed behavior, residuals, and subsequent proposal
lifecycle. Thus the high-gain effect may be mediated partly by improved
self-grown topology as well as larger scores. Exhaustive-bounded is the clean
evidence that coverage alone is sufficient.

## Retention trajectory

Median old development performance:

| Arm | 512 | 1,024 | 2,048 | 4,096 |
|---|---:|---:|---:|---:|
| Sparse-bounded | 0.7764 | 0.8945 | 0.9414 | 0.9688 |
| Sparse-high-gain | 0.7861 | 0.9873 | 1.0000 | 1.0000 |
| Exhaustive-bounded | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Exhaustive-high-gain | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Exhaustive zero-weight contextual adapters learn the new regime without
damaging the mastered old policy, using terminal outcome only.

## Gain and clipping

Bounded arms show heavy mature-parameter clipping:

- sparse-bounded: 58,828 clipped mature updates;
- exhaustive-bounded: 57,209;
- median output clipping: 505 and 353 scored actions respectively.

High-gain arms reduce mature clipping to 7,208 aggregate events and eliminate
final output clipping on the evaluation pools. Their median raw maxima remain
only about 1.47 sparse and 1.25 exhaustive, so the wider bound mainly prevents
training-time saturation and decision ties rather than producing extreme final
scores.

Diagnostic caveat: the inherited `contextual_coverage.saturated_count` field
uses the legacy absolute-weight threshold 1.0. In high-gain arms it therefore
counts legacy-threshold crossings, not true saturation at 4.0. This field was
not a gate; actual clipping counters and output diagnostics above use the
configured bounds.

## Integrity and claim boundary

All invariant gates passed:

- clone parity and equal standard budgets: 20/20;
- shared state unchanged: every arm/task;
- exhaustive mature coverage: 8/8 on 20/20 tasks;
- zero graph/update mismatches and trial-root leakage;
- sparse maximum live candidates four;
- exhaustive door maximum live candidates eight;
- maximum total proposals 36, below 64.

The exhaustive candidates were laboratory-authored Cartesian products with
zero weights and no sign, action target, inversion, correctness, or solution
labels. They establish representational sufficiency only.

## Artifact and provenance

`reports/autogrowth/generic_core/contextual_expressivity_ceiling_20260712.json`

- artifact SHA-256:
  `0f30a1caad41a14920004ad5dcd1ce4cfa145b7693ebd82da10712fd9a522b67`;
- source commit:
  `69859fb5fd3a87c9bc44c805e17243ca729cf4e3`;
- task-row SHA-256:
  `3c3fb1e38042b3e4d0bc2023e0aaf9a294c8af81230eb25ef290eaeb330f29f5`;
- runner hash matches frozen source;
- all 20 checkpoints and task rows are present.

## Supported, unshown, and next decision

Supported:

- additive contextual pair topology can express stable old/new coexistence;
- missing coverage and bounded gain each explain part of the prior failure;
- shared weights can remain exactly frozen while contextual outcome learning
  acquires the new regime;
- exhaustive content-blind coverage plus higher gain achieves 20/20.

Unshown:

- autonomous discovery of sufficient coverage;
- a learner-local rule for contextual gain;
- whether gain alone or its downstream topology effect is the smaller
  autonomous mechanism;
- independent confirmation, native predecessor-child behavior, and KRK.

This package is closed. Do not convert the laboratory pair injection or phase
freeze into a runtime solution.

The cleanest next autonomy package is self-grown coverage under the ordinary
[-1, 1] bounds: from a mastered frozen-shared checkpoint, compare the current
four-live residual-ranked ecology with a preregistered eight-live
residual-ranked ecology and an eight-live matched-random control. Require
coverage, causal topology effect, and coexistence without Cartesian pair
injection or semantic labels. This asks whether ordinary ReCoN nomination can
reach the now-proven sufficient topology when its local ecological capacity is
not too small.

That next mechanism requires separate PI authorization. Even a pass remains
generic-core development and must precede the native predecessor-child bridge.
