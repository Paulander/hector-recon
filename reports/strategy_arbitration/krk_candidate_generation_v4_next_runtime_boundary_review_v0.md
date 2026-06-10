# KRK Candidate-Generation v4 Next Runtime Boundary Review

This review decides what the v4 context benchmark permits. It preserves the existing default-off observation sandbox but does not authorize a selector, score changes, routing, guardrails, or a new runtime sandbox.

## Decision

- status: `candidate_generation_v4_next_runtime_boundary_context_ready_selector_blocked`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `non_causal_scope_gap_review_before_any_new_runtime_boundary`

## Summary

- capacity_row_count: `36`
- positive_capacity_count: `26`
- negative_capacity_count: `10`
- runtime_trace_row_count: `31`
- refresh_trace_row_count: `25`
- exact_positive_capacity_recall_from_refresh_trace: `0.19230769230769232`
- policy_cell_positive_capacity_recall_from_refresh_trace: `0.7692307692307693`
- exact_negative_capacity_exposure_from_refresh_trace: `0.0`
- policy_cell_negative_capacity_exposure_from_refresh_trace: `0.0`
- selector_training_row_count: `0`
- stage7_readiness_training_row_count: `0`

## Boundary Assessment

- current_candidate_generation_observation_sandbox_remains_valid: `True`
- policy_cell_context_is_useful: `True`
- negative_capacity_exposure_is_clean: `True`
- exact_move_provider_coverage_is_partial: `True`
- selector_training_still_absent: `True`
- stage7_remains_held_out: `True`

## Approved Now

- continue_non_causal_context_analysis: `True`
- keep_existing_default_off_observation_sandbox_available: `True`
- implement_new_runtime_sandbox: `False`
- selector_allowed: `False`
- score_changes_allowed: `False`
- provider_routing_allowed: `False`
- guardrails_allowed: `False`
- stage4_runtime_scope_allowed: `False`

## Still Forbidden

- `selector_training`
- `score_changes`
- `provider_routing`
- `guardrail_campaign_from_context_only`
- `stage4_runtime_scope_without_separate_review`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`

## Interpretation

- candidate_generation_context_is_ready_for_architecture_review: `True`
- not_a_selector_packet: `True`
- reason: `V4 integrates candidate-generation refresh traces and repair-monitor context as non-causal evidence. Policy-cell coverage is useful and negative exposure is clean, but exact move/provider coverage is partial and there are still no ownership selector labels.`
