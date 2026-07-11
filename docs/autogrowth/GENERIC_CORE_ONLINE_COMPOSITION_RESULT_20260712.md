# Generic-Core Online Composition: Raw Development Result

Date: 2026-07-12. Track: generic-core development. Confirmation claim: none.
Builder and runner are the same agent; independent adjudication remains required.

## Frozen boundary

The work package was written before implementation. The tested implementation
was committed and pushed at `9f601cd`; the compile-checked runner was committed
and pushed at `f9ccd04`; only then was the frozen seed range executed once.
There was no outcome-driven learner, task, seed, threshold, or hyperparameter
change.

The learner received only anonymous active atom IDs and a scalar target. It did
not receive signal/nuisance identity, XOR, task identity, the correct pair,
evaluation results, or laboratory labels. The only factor between arms was
residual-ranked versus seeded-random selection among the same supported,
unproposed pair candidates.

## Raw measurements

| Measurement | Frozen requirement | Observed |
|---|---:|---:|
| Ranked lower final MSE than matched random | at least 16/20 tasks | 20/20 |
| Median random-minus-ranked final MSE | positive | 0.6776685605 |
| Ranked task with mature hidden signal pair | at least 16/20 | 20/20 |
| Trial prediction influence | zero | zero |
| Identical actual candidate count | 20/20 | 20/20 |

Additional descriptive measurements:

- ranked final evaluation MSE mean 0.019830, median 0.001097, range
  0.00000382–0.176820;
- matched-random final MSE mean 0.678408, median 0.723520, range
  0.383326–0.949964;
- ranked mature candidate counts ranged from two to four; every mature ranked
  candidate was a hidden signal-bit conjunction;
- matched random matured zero to two candidates and found a mature hidden
  signal pair in only three tasks.

Artifact:
`reports/autogrowth/generic_core/online_composition_anonymous_xor_20260712.json`

- artifact SHA-256:
  `88a89e6da44add84d49aa60a83ecabb9d35a67bc772bfe59c1afbb9ba8b5c88d`;
- source commit:
  `f9ccd0428918cf1c533f04fb2a70ad16177d8561`;
- task-row SHA-256:
  `7e52b3afb964dabda1eac87faba4a508634d2ab96f38734d84a4c50921959cfb`;
- learner implementation SHA-256:
  `0b647e16fc2173535d1d01bdfd076947a5dd2d0fc304a9372f805f8161941f2d`;
- runner SHA-256:
  `3694d0264af2a849efd029ec8faedac13d27fca679a37e628ae91f20e1ee5cc3`.

## What this supports

The raw development result supports a narrow mechanism statement: on this
frozen anonymous stream family, learner-local support-weighted residual contrast
identified co-active pair topology that trained in shadow, survived a future
paired-error/resource-cost test, and improved untouched evaluation much more
reliably than support- and budget-matched random proposals.

This directly answers one question from the external audit: a task-agnostic local
observable can cause pair structure to be born and future causal benefit minus a
resource cost can decide survival without an R1 label or target pair supplied by
the laboratory.

## What this does not support

- This is development evidence produced by the builder, not sealed independent
  confirmation.
- The generic mechanism is a new `recon_lite` component, not yet wired into the
  existing formal ReCoN engine's real activation traces, action selection,
  robust return distribution, or option lifecycle.
- The laboratory supplies binary literal atoms. The learner discovers useful
  conjunctions, not objects, variables, or literals from raw observations.
- The environment supplies scalar valence. That is an allowed genome/interface
  prior, not a learned goal.
- Anonymous XOR is a deliberately direct pair-composition test. It does not
  establish recursive composition, sequences, LAG, routing, exploration,
  self-selected curriculum, local consolidation, or KRK competence.
- The zero trial-influence measurement follows a structural code path and a
  lifecycle test; the runtime counter is a sentinel that remains zero rather
  than an independent intervention detector.
- Twenty randomized instances of one task family do not establish cross-domain
  generality.

## Decision boundary

Do not tune or rerun this package. Preserve it as development data. The next
scientifically meaningful step is not another XOR rescue or immediate KRK
factorial. It is an independently owned reproduction of the frozen hashes, or a
new preregistered integration package that connects this unchanged growth law to
actual ReCoN activation traces, persistent eligibility, lower-tail action value,
and a generic environment action loop. Only after that integration survives a
generic delayed/adversarial task should a frozen release return to fresh KRK
pools.
