# KRK Selector Observability Readiness Review v0

## Decision

- status: `selector_observability_blocked_by_preserve_failure_risk`
- runtime_changes_allowed: `False`
- selector_runtime_ready: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- future_behavior_changing_selector_review_packet_allowed: `False`
- recommended_next_step: `review_preserve_failure_risk_before_any_behavior_changing_selector`

## Summary

- attempted_row_count: `14`
- recommendation_count_by_class: `{'preserve_selected_owner': 5, 'prefer_visible_alternative': 4, 'abstain_context_only': 5}`
- preserve_on_failure_count: `1`
- switch_on_safe_owner_count: `0`
- abstain_recommendation_count: `5`
- abstain_weak_evidence_count: `5`
- offline_label_alignment_count: `13`
- offline_label_mismatch_count: `1`
- rows_with_visible_alternatives: `9`
- source_term_coverage: `{'unique_source_term_count': 10, 'unique_explanation_term_count': 28, 'source_terms': ['active_landmark_label.drive_to_edge', 'active_landmark_label.fence_established', 'candidate_strategy_family.edge_trap', 'candidate_strategy_family.fence_established', 'candidate_strategy_family.stage0_basin', 'offline_validated_provider_capacity_evidence', 'runtime_review_packet.krk_candidate_generation_training_refresh_runtime_review_packet_v3', 'source_stage.stage5', 'source_stage.stage6', 'stage5_6_candidate_generation_refresh_scope'], 'explanation_terms': ['active_landmark_label.drive_to_edge', 'active_landmark_label.edge_trap_wrong_tempo', 'active_landmark_label.fence_established', 'active_landmark_label.wrong_tempo_control', 'box_area_relevance.low', 'box_area_relevance.medium', 'edge_bucket.at_edge', 'edge_bucket.near_edge', 'positive_trace_count_bucket.high', 'positive_trace_count_bucket.low', 'positive_trace_count_bucket.medium', 'positive_trace_count_bucket.none', 'positive_trace_provider_candidate_count.0', 'positive_trace_provider_candidate_count.10', 'positive_trace_provider_candidate_count.14', 'positive_trace_provider_candidate_count.16', 'positive_trace_provider_candidate_count.2', 'positive_trace_provider_candidate_count.3', 'selected_piece.king', 'selected_piece.rook', 'selector_model.combined_simple_rule', 'source_stage.stage4', 'source_stage.stage5', 'source_stage.stage6', 'source_stage.unknown', 'support_bucket.close', 'support_bucket.far', 'support_bucket.medium']}`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- runtime_behavior_changed: `False`
- runtime_dtm_or_tablebase_use: `False`
- gameplay_topology_mutation: `False`
- default_off_selector_recommendation_count: `0`
- trace_only_recommendation_count: `14`
- class_balance: `{'preserve_selected_owner': 5, 'prefer_visible_alternative': 4, 'abstain_context_only': 5}`
- no_runtime_deltas: `True`
- stage7_remains_held_out: `True`
- evidence_improved_over_prior: `True`
- ready_for_runtime_review_packet: `False`
