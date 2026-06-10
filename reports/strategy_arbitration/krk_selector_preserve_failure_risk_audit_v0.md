# KRK Selector Preserve Failure Risk Audit v0

## Decision

- status: `preserve_failure_risk_resolved_non_causal`
- runtime_changes_allowed: `False`
- selector_runtime_ready: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- recommended_next_step: `write_future_runtime_review_packet_recommendation_only`

## Summary

- failing_row_count: `1`
- safe_preserve_row_count: `4`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_behavior_changed: `False`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- prior_readiness_status: `selector_observability_blocked_by_preserve_failure_risk`
- viable_refinement_count: `2`

## Failing Row

- row_id: `selector_objective_fresh_diversity.02`
- stage: `stage5`
- selected_provider: `krk.stage0_basin`
- selected_move: `c6b6`
- target_label: `prefer_visible_alternative`
- recommendation: `preserve_selected_owner`
- decision_reason: `high_positive_trace_count_bucket`
- positive_trace_provider_candidate_count: `16`
- positive_trace_count_bucket: `high`
- selected_piece: `king`
- support_bucket: `close`
- active_landmark: `fence_established`

## Viable Refinements

- `preserve_only_if_no_selected_owner_failure_risk_terms` metrics=`{'prediction_counts': {'preserve_selected_owner': 4, 'prefer_visible_alternative': 4, 'abstain_context_only': 6}, 'preserve_on_failure_count': 0, 'switch_on_safe_owner_count': 0, 'safe_preservation_recall': 1.0, 'switch_contrast_recall': 0.8, 'abstain_recall': 1.0, 'offline_accuracy': 0.9285714285714286}`
- `abstain_for_exact_preserve_failure_pattern` metrics=`{'prediction_counts': {'preserve_selected_owner': 4, 'prefer_visible_alternative': 4, 'abstain_context_only': 6}, 'preserve_on_failure_count': 0, 'switch_on_safe_owner_count': 0, 'safe_preservation_recall': 1.0, 'switch_contrast_recall': 0.8, 'abstain_recall': 1.0, 'offline_accuracy': 0.9285714285714286}`
