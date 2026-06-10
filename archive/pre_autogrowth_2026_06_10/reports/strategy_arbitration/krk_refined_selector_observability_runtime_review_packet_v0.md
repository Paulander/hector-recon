# KRK Refined Selector Observability Runtime Review Packet v0

This packet reviews a possible future default-off refined selector-objective observability sandbox. It does not implement or authorize behavior-changing selection.

## Decision

- status: `refined_selector_observability_runtime_review_ready`
- implementation_authorized_by_this_packet: `False`
- behavior_changing_selector_allowed: `False`
- runtime_sandbox_authorized_by_this_packet: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `explicit_approval_required_before_default_off_trace_only_refined_observability_sandbox`

## Proposed Sandbox

- name: `default_off_refined_selector_objective_observability_sandbox`
- implementation_status: `not_implemented`
- default_off: `True`
- opt_in_only: `True`
- opt_in_flag: `--enable-krk-refined-selector-objective-observability`
- trace_only: `True`
- recommendation_only: `True`
- base_model: `combined_simple_rule`
- refinement_id: `preserve_only_if_no_selected_owner_failure_risk_terms`
- preserve_failure_risk_refinement: `abstain_context_only_when_runtime_visible_failure_risk_terms_are_present`
- may_emit_recommendations: `['preserve_selected_owner', 'prefer_visible_alternative', 'abstain_context_only']`

## Allowed Effect If Separately Approved Later

- emit_recommendation_metadata: `True`
- record_source_terms: `True`
- record_explanation_terms: `True`
- record_selected_owner_before_recommendation: `True`
- record_visible_alternatives: `True`
- direct_request: `False`
- score_delta: `0.0`
- causal_status: `recommendation_only`
- selected_move_delta_allowed: `False`
- selected_provider_delta_allowed: `False`

## Explicitly Forbidden

- `behavior_changing_selection`
- `routing_changes`
- `score_changes`
- `provider_selection_changes`
- `provider_suppression`
- `runtime_default_changes`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
- `treating_capacity_labels_as_ownership_labels`

## Supporting Evidence

- recommendation_class_balance: `{'abstain_context_only': 5, 'prefer_visible_alternative': 4, 'preserve_selected_owner': 5}`
- preserve_failure_risk_status: `preserve_failure_risk_resolved_non_causal`
- recommended_refinement_id: `preserve_only_if_no_selected_owner_failure_risk_terms`
- refined_prediction_counts: `{'abstain_context_only': 6, 'prefer_visible_alternative': 4, 'preserve_selected_owner': 4}`
- refined_preserve_on_failure_count: `0`
- refined_safe_preservation_recall: `1.0`
- refined_switch_contrast_recall: `0.8`
- refined_abstain_recall: `1.0`
- refined_switch_on_safe_owner_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- capacity_label_used_as_ownership_label_count: `0`

## Remaining Risks

- `small_dataset`
- `recommendation_only_not_selector_training`
- `not_tested_as_behavior_changing_policy`
- `stage7_held_out`
- `switch_contrast_recall_less_than_1_0`
- `candidate_quality_remains_separate_from_selector_quality`

## Requirements Before Later Implementation

- `explicit_approval`
- `default_off_equivalence`
- `no_selected_move_or_provider_delta`
- `score_delta_count_equals_zero`
- `recommendation_only_metadata`
- `focused_tests`
- `full_suite_if_reasonable`

## Possible Statuses

- `refined_selector_observability_runtime_review_ready`
- `refined_selector_observability_needs_more_evidence`
- `refined_selector_observability_blocked`
