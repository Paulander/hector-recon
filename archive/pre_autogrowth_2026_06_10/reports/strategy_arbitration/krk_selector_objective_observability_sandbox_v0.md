# KRK Selector Objective Observability Sandbox v0

This report records the explicitly approved default-off selector-objective observability sandbox. It emits recommendation-only metadata and does not train or authorize a runtime selector.

## Decision

- status: `selector_observability_sandbox_wired_default_off_equivalent`
- selector_runtime_ready: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `non_causal_recommendation_analysis`

## Summary

- attempted_row_count: `8`
- default_off_equivalence_passed: `True`
- enabled_recommendation_count: `8`
- flag_off_selector_recommendation_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- runtime_behavior_changed: `False`
- recommendation_counts_by_class: `{'prefer_visible_alternative': 3, 'preserve_selected_owner': 5}`
- source_term_coverage: `{'unique_source_term_count': 10, 'unique_explanation_term_count': 20, 'source_terms': ['active_landmark_label.drive_to_edge', 'active_landmark_label.fence_established', 'candidate_strategy_family.edge_trap', 'candidate_strategy_family.fence_established', 'candidate_strategy_family.stage0_basin', 'offline_validated_provider_capacity_evidence', 'runtime_review_packet.krk_candidate_generation_training_refresh_runtime_review_packet_v3', 'source_stage.stage5', 'source_stage.stage6', 'stage5_6_candidate_generation_refresh_scope'], 'explanation_terms': ['active_landmark_label.drive_to_edge', 'active_landmark_label.fence_established', 'box_area_relevance.low', 'box_area_relevance.medium', 'edge_bucket.at_edge', 'edge_bucket.near_edge', 'positive_trace_count_bucket.high', 'positive_trace_count_bucket.low', 'positive_trace_count_bucket.medium', 'positive_trace_provider_candidate_count.10', 'positive_trace_provider_candidate_count.14', 'positive_trace_provider_candidate_count.16', 'positive_trace_provider_candidate_count.2', 'selected_piece.king', 'selected_piece.rook', 'selector_model.combined_simple_rule', 'source_stage.stage5', 'source_stage.stage6', 'support_bucket.close', 'support_bucket.far'], 'visible_alternative_count': 72}`
- direct_request_false_count: `8`
- score_delta_zero_count: `8`
- stage7_rows_remain_held_out: `True`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_dtm_or_tablebase_use: `False`
- gameplay_topology_mutation: `False`
- invalid_metadata_count: `0`

## Rows

- `selector_objective_fresh_diversity.01` stage=stage5 recommendation=`prefer_visible_alternative` reason=`near_edge_or_medium_box_relevance` move_delta=False provider_delta=False score_delta=False
- `selector_objective_fresh_diversity.02` stage=stage5 recommendation=`preserve_selected_owner` reason=`high_positive_trace_count_bucket` move_delta=False provider_delta=False score_delta=False
- `selector_objective_fresh_diversity.03` stage=stage5 recommendation=`preserve_selected_owner` reason=`high_positive_trace_count_bucket` move_delta=False provider_delta=False score_delta=False
- `selector_objective_fresh_diversity.04` stage=stage6 recommendation=`prefer_visible_alternative` reason=`stage6_far_white_king_support` move_delta=False provider_delta=False score_delta=False
- `selector_objective_fresh_diversity.05` stage=stage6 recommendation=`prefer_visible_alternative` reason=`stage6_far_white_king_support` move_delta=False provider_delta=False score_delta=False
- `selector_objective_fresh_diversity.06` stage=stage6 recommendation=`preserve_selected_owner` reason=`default_preserve_selected_owner` move_delta=False provider_delta=False score_delta=False
- `selector_objective_fresh_diversity.07` stage=stage5 recommendation=`preserve_selected_owner` reason=`default_preserve_selected_owner` move_delta=False provider_delta=False score_delta=False
- `selector_objective_fresh_diversity.08` stage=stage6 recommendation=`preserve_selected_owner` reason=`default_preserve_selected_owner` move_delta=False provider_delta=False score_delta=False
