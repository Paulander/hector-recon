# KRK Selector Behavior Sandbox Review Packet v0

This packet reviews a possible future default-off, narrow behavior-changing selector sandbox. It does not implement or authorize selector behavior.

## Decision

- status: `selector_behavior_sandbox_review_ready`
- implementation_authorized_by_this_packet: `False`
- behavior_changing_implementation_present: `False`
- behavior_changing_selector_allowed_by_this_packet: `False`
- runtime_changes_allowed_by_this_packet: `False`
- default_off_required: `True`
- selector_runtime_ready: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- runtime_dtm_or_tablebase_allowed: `False`
- gameplay_topology_mutation_allowed: `False`
- recommended_next_step: `seek_explicit_approval_before_any_default_off_behavior_sandbox_implementation`

## Proposed Sandbox

- name: `default_off_narrow_selector_behavior_sandbox`
- implementation_status: `not_implemented`
- authorization_status: `review_packet_only_not_approved_for_implementation`
- default_off_required: `True`
- opt_in_only: `True`
- opt_in_flag: `--enable-krk-selector-behavior-sandbox`
- active_only_when_recommendation: `prefer_visible_alternative`
- preserve_selected_owner_effect: `no_op`
- abstain_context_only_effect: `no_op`
- may_choose_only_already_visible_alternative: `True`
- new_candidate_generation_allowed: `False`
- direct_provider_request_allowed: `False`
- hidden_routing_allowed: `False`
- stage7_training_or_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Allowed Effect If Separately Approved Later

- bounded_switch_from_selected_owner_to_visible_alternative: `True`
- only_when_recommendation: `prefer_visible_alternative`
- record_original_selected_owner: `True`
- record_original_selected_move: `True`
- record_replacement_owner: `True`
- record_replacement_move: `True`
- record_source_terms: `True`
- record_explanation_terms: `True`
- direct_request: `False`
- score_delta: `0.0`
- runtime_dtm_or_tablebase_allowed: `False`
- gameplay_topology_mutation_allowed: `False`

## Required Vetoes

- `no_switch_if_recommendation_is_preserve_selected_owner`
- `no_switch_if_recommendation_is_abstain_context_only`
- `no_switch_if_no_visible_alternative_exists`
- `no_switch_if_safe_preservation_veto_fires`
- `no_switch_if_alternative_lacks_runtime_visible_provenance`
- `no_switch_if_stage7_row_or_training_context`
- `no_switch_if_source_terms_missing`

## Required Validation Before Later Implementation

- `explicit_approval`
- `default_off_equivalence`
- `trace_only_comparison_first`
- `tiny_targeted_switch_smoke`
- `selected_move_provider_deltas_allowed_only_when_enabled_and_reviewed_switch_case`
- `score_delta_remains_zero_unless_separately_reviewed`
- `target_improvement_before_guardrails`
- `guardrails_before_promotion`
- `rollback_tag`

## Explicitly Forbidden

- `implementation_by_this_packet`
- `runtime_default_change`
- `routing_changes`
- `score_changes_without_separate_review`
- `provider_suppression`
- `new_candidate_generation`
- `direct_provider_request`
- `hidden_routing`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
- `treating_capacity_labels_as_ownership_labels`

## Evidence

- refined_observability_status: `refined_selector_observability_ready_for_recommendation_analysis`
- enabled_recommendation_count: `14`
- recommendation_counts_by_class: `{'abstain_context_only': 6, 'prefer_visible_alternative': 4, 'preserve_selected_owner': 4}`
- switch_recommendation_count: `4`
- source_terms: `['active_landmark_label.drive_to_edge', 'active_landmark_label.fence_established', 'candidate_strategy_family.edge_trap', 'candidate_strategy_family.fence_established', 'candidate_strategy_family.stage0_basin', 'offline_validated_provider_capacity_evidence', 'runtime_review_packet.krk_candidate_generation_training_refresh_runtime_review_packet_v3', 'source_stage.stage5', 'source_stage.stage6', 'stage5_6_candidate_generation_refresh_scope']`
- preserve_on_failure_count: `0`
- abstain_recall: `1.0`
- switch_on_safe_owner_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- runtime_behavior_changed: `False`
- runtime_dtm_or_tablebase_use: `False`
- gameplay_topology_mutation: `False`
- capacity_label_used_as_ownership_label_count: `0`

## Remaining Risks

- `tiny_evidence_set`
- `switch_recall_less_than_perfect`
- `visible_alternatives_may_still_be_poor_candidates`
- `candidate_generation_quality_remains_separate`
- `selector_not_yet_tested_causally`

## Possible Statuses

- `selector_behavior_sandbox_review_ready`
- `selector_behavior_sandbox_needs_more_observation`
- `selector_behavior_sandbox_blocked`
