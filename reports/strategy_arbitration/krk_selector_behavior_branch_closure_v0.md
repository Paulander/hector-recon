# KRK Selector Behavior Branch Closure v0

- decision: `selector_behavior_branch_closed_return_to_control_plane`
- causal_status: `architecture_branch_closure_no_runtime_change`
- runtime_behavior_changed: `False`
- runtime_selector_authorized: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Branch Status

The behavior-changing selector sandbox is quarantined. Trace-only selector observability and recommendation analysis remain useful as non-causal evidence, but they do not authorize provider choice, move choice, score, routing, default, or suppression changes.

## Timeline

- `krk_selector_objective_benchmark_v0.json`: promising offline benchmark, non-causal only.
- `krk_refined_selector_initial_owner_observability_sandbox_v0.json`: refined trace-only, default-off, initial-owner-only observability.
- `krk_refined_selector_initial_owner_next_gate_v0.json`: ready to write a future behavior review packet only, not implementation.
- `krk_selector_behavior_sandbox_v0.json`: tiny target sample improved under a default-off behavior sandbox.
- `krk_selector_behavior_sandbox_validation_v0.json`: protected validation regressed one safe-control h40 row and produced no h40 improvements.
- `krk_selector_behavior_regression_decision_v0.json`: selector behavior quarantined due to safe regression.
- `krk_selector_continuation_scope_decision_v0.json`: continuation scope is not supported by the initial-owner selector evidence.

## Lesson

Recommendation correctness is not enough for causal provider switching. Safe-owner preservation is fragile, and continuation behavior cannot be inferred from initial-owner recommendations. A future causal path needs state-local paired ownership evidence and a broader KRK strategy or sequence control plane before provider-choice override is reconsidered.

## Next Direction

Return to KRK strategy and sequence control-plane work. Do not pursue behavior-changing selector variants from this branch without a new architecture decision and explicit approval.
