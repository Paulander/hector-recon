# KRK State-Local Paired Ownership Work Package v0

This work package implements a non-causal ownership objective that compares candidate owners within the same board/control context.

## Scope

- Build evidence, not runtime behavior.
- Compare normal selected-owner outcomes against same-state forced-capacity alternatives.
- Keep forced capacity, selected-playout, safe-preservation, and abstention evidence as separate channels.
- Exclude Stage 7 from training/readiness rows. Stage 7 remains held-out challenge evidence only.

## Thresholds

- Protected pairs: `30`
- Strong same-state conflicts: `8`
- Selected-failure-with-alternative-success cases: `4`
- Safe-preservation pairs: `12`
- Stage 7 training rows: `0`

## Evidence Channels

- `strong_same_state_conflict`: selected owner and same-state capacity alternative disagree on h40 conversion.
- `safe_preservation`: selected owner converts and same-state alternative also has conversion capacity.
- `abstain_or_insufficient_safe_owner`: selected owner fails and same-state alternative also fails.
- `weak_capacity_context`: capacity-only context that lacks enough ownership evidence for a preference.
- `heldout_stage7_challenge`: Stage 7 evidence excluded from training/readiness.

## Constraints

- No runtime selector.
- No selector training.
- No Stage 7 promotion.
- No Stage 8 training.
- No runtime DTM/tablebase.
- No gameplay-time topology mutation.
- No hidden controller.

## Stop Rule

Prefer replay-free extraction first. If inventory remains underpowered, allow at most one reviewed bounded h40 expansion of protected same-state conflict labels before stopping for architecture review.
