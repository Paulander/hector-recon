# KRK Selector Observability Expanded Recommendations v0

## Decision

- status: `selector_observability_expanded_recommendations_complete`
- runtime_changes_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- behavior_changing_selector_allowed: `False`

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

## Rows

- `stage4_joined_trace_ownership_1` stage=stage4 owner=selected_owner_failed recommendation=`prefer_visible_alternative` target=`prefer_visible_alternative`
- `stage4_joined_trace_ownership_2` stage=stage4 owner=selected_owner_failed recommendation=`abstain_context_only` target=`abstain_context_only`
- `stage4_joined_trace_ownership_3` stage=stage4 owner=selected_owner_failed recommendation=`abstain_context_only` target=`abstain_context_only`
- `stage4_joined_trace_ownership_4` stage=stage4 owner=selected_owner_failed recommendation=`abstain_context_only` target=`abstain_context_only`
- `stage4_joined_trace_ownership_5` stage=stage4 owner=selected_owner_failed recommendation=`abstain_context_only` target=`abstain_context_only`
- `stage4_joined_trace_ownership_6` stage=stage4 owner=selected_owner_failed recommendation=`abstain_context_only` target=`abstain_context_only`
- `selector_objective_fresh_diversity.01` stage=stage5 owner=selected_owner_failed recommendation=`prefer_visible_alternative` target=`prefer_visible_alternative`
- `selector_objective_fresh_diversity.02` stage=stage5 owner=selected_owner_failed recommendation=`preserve_selected_owner` target=`prefer_visible_alternative`
- `selector_objective_fresh_diversity.03` stage=stage5 owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner`
- `selector_objective_fresh_diversity.04` stage=stage6 owner=selected_owner_failed recommendation=`prefer_visible_alternative` target=`prefer_visible_alternative`
- `selector_objective_fresh_diversity.05` stage=stage6 owner=selected_owner_failed recommendation=`prefer_visible_alternative` target=`prefer_visible_alternative`
- `selector_objective_fresh_diversity.06` stage=stage6 owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner`
- `selector_objective_fresh_diversity.07` stage=stage5 owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner`
- `selector_objective_fresh_diversity.08` stage=stage6 owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner`
