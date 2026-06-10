# KRK Selector Preserve Failure Risk Decision v0

## Decision

- status: `preserve_failure_risk_resolved_non_causal`
- runtime_changes_allowed: `False`
- selector_runtime_ready: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- behavior_changing_selector_implemented: `False`
- future_runtime_review_packet_recommended: `True`

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
- recommended_refinement_id: `preserve_only_if_no_selected_owner_failure_risk_terms`
- future_runtime_review_packet_recommendation: `{'scope': 'review_only_default_off_selector_refinement', 'recommended_rule': 'preserve_only_if_no_selected_owner_failure_risk_terms', 'runtime_effect_if_later_approved': 'recommendation_policy_only_review_not_implemented_here', 'must_remain_default_off': True, 'must_keep_trace_only_until_separately_approved': True}`
