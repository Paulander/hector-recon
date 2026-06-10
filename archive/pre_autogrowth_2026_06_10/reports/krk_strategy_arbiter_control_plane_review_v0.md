# KRK Strategy Arbiter Control-Plane Review v0

This review closes the current observability/control-label work package.

## Decision

Status: `selector_objective_and_label_semantics_review_required`

The default-off, trace-only observability path is working. It is not enough to authorize a runtime arbiter or even a default-off selector sandbox.

## Evidence

Observability smoke:

- Default-off and enabled behavior metrics matched.
- The only expected delta was non-causal observation metadata.

Observation separability:

- Trace-only KRK context terms are now present.
- Source-term counts range from `13` to `21`.
- Provider summaries expose `7` provider families per record.

Labeled controls:

- Records: `21`
- Labeled controls: `14`
- Selected labels: `9` positive, `5` negative, `7` unknown
- Positive rate on labeled controls: `0.6428571428571429`
- Stage 7 unknown holdouts: `6`

## Interpretation

The observation layer is now useful for offline selector research. The current raw-selected provider is not reliable enough on labeled controls to become the selector objective.

The label space is still mixed:

- selected playout success,
- forced-provider conversion,
- same-move provider compatibility,
- held-out Stage 7 challenge status,
- guardrail safety.

Those target types must be separated before a selector can be designed.

## Allowed Next Work

- Non-causal selector-objective design.
- Label-semantics split review.
- Small replay-free selector dataset with explicit target kind.
- Additional bounded labels only if a review authorizes them.

## Blocked

- Runtime arbiter.
- Default-off selector sandbox.
- Score bonus or provider penalty.
- Provider support adapter.
- Stage 7 repair or promotion.
- Stage 8 training.
- Runtime DTM/tablebase.
- Gameplay-time topology mutation.
- M3/M4 arbitration update.

## Recommended Next Step

`krk_selector_objective_label_semantics_v0`

Define and separate selector target types before any sandbox: selected playout success, forced-provider conversion, same-move provider compatibility, held-out challenge status, and guardrail safety.
