# KRK Selector Objective Runtime Review Packet v0

This packet reviews a possible future default-off selector-objective sandbox. It does not implement or authorize runtime behavior.

## Decision

- status: `selector_runtime_review_packet_ready`
- implementation_authorized_by_this_packet: `False`
- runtime_sandbox_authorized_by_this_packet: `False`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `explicit_approval_required_before_default_off_trace_only_sandbox`

## Proposed Sandbox

- name: `default_off_selector_objective_sandbox`
- default_off: `True`
- opt_in_only: `True`
- traceable: `True`
- reversible: `True`
- default_behavior_change: `False`

## First Sandbox Scope If Separately Approved Later

- name: `trace_only_selector_objective_recommendation`
- may_compute: `combined_simple_rule_selector_objective`
- may_emit_recommendations: `['preserve_selected_owner', 'prefer_visible_alternative', 'abstain_context_only']`
- may_record: `['recommendation', 'explanation_terms', 'source_terms', 'selected_owner_observation']`
- direct_request: `False`
- score_delta: `0.0`
- selected_move_delta_allowed: `False`
- selected_provider_delta_allowed: `False`
- runtime_effect: `recommendation_only_no_selection`

## Allowed Only If Separately Approved Later

- `observe_current_selected_owner`
- `compute_combined_simple_rule_selector_objective`
- `emit_non_default_recommendation_preserve_selected_owner`
- `emit_non_default_recommendation_prefer_visible_alternative`
- `emit_non_default_recommendation_abstain_context_only`
- `trace_recommendation_inputs_and_outputs`

## Not Authorized By This Packet

- `implement_runtime_selector`
- `change_runtime_behavior`
- `select_move_or_provider`
- `change_scores_or_routes`
- `suppress_or_penalize_providers`
- `bounded_selection_among_visible_alternatives`

## Explicitly Forbidden

- `runtime_selector_implementation_in_this_slice`
- `score_changes`
- `routing_changes`
- `provider_selection_changes`
- `provider_suppression`
- `broad_provider_penalties`
- `runtime_default_changes`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_time_topology_mutation`
- `state_hash_exceptions`
- `treating_capacity_labels_as_ownership_labels`
- `hidden_python_controller`
- `guardrails_before_target_smoke`

## Supporting Evidence

- benchmark_status: `selector_objective_benchmark_promising_non_causal`
- seed_row_count: `21`
- target_action_counts: `{'abstain_context_only': 5, 'prefer_visible_alternative': 5, 'preserve_selected_owner': 11}`
- best_model: `combined_simple_rule`
- best_accuracy: `0.9523809523809523`
- safe_preservation_recall: `1.0`
- switch_contrast_recall: `0.8`
- abstain_recall: `1.0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Remaining Risks

- `small_seed`
- `possible_overfitting_to_hand_built_labels`
- `switch_contrast_recall_less_than_1_0`
- `stage7_held_out_not_training`
- `runtime_feature_eligibility_must_be_checked_carefully`
- `generated_candidate_quality_still_separate_from_selector_quality`
- `capacity_labels_are_not_ownership_labels`

## Future Sandbox Envelope Before Implementation

- `explicit_flag`
- `default_off_equivalence`
- `no_selected_move_delta_in_observation_mode`
- `no_selected_provider_delta_in_observation_mode`
- `trace_only_first`
- `report_recommendation_only`
- `no_score_changes`
- `no_routing_changes`
- `target_smoke_before_any_guardrails`
- `guardrails_before_promotion`
- `rollback_plan`

## Possible Statuses

- `selector_runtime_review_packet_ready`
- `selector_runtime_review_needs_more_evidence`
- `selector_runtime_review_blocked`
