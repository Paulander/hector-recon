# KRK Selector Objective Recommendation Analysis v0

This analysis reviews recommendation-only observability records. It does not authorize or implement behavior-changing selection.

## Decision

- status: `selector_recommendations_need_more_observation_data`
- future_behavior_changing_selector_review_packet_allowed: `False`
- selector_runtime_ready: `False`

## Summary

- observed_row_count: `8`
- recommendation_count_by_class: `{'preserve_selected_owner': 5, 'prefer_visible_alternative': 3, 'abstain_context_only': 0}`
- rows_with_visible_alternatives: `8`
- rows_without_visible_alternatives: `0`
- offline_label_alignment_count: `7`
- offline_label_mismatch_count: `1`
- preserve_recommendation_count: `5`
- preserve_safe_owner_count: `4`
- preserve_on_selected_owner_failure_count: `1`
- switch_recommendation_count: `3`
- switch_on_selected_owner_failure_count: `3`
- abstain_recommendation_count: `0`
- abstain_weak_evidence_count: `0`
- unsafe_if_made_causal_count: `1`
- capacity_label_used_as_ownership_label_count: `0`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- stage7_remains_held_out: `True`
- runtime_behavior_changed: `False`
- no_runtime_behavior_changes: `True`
- runtime_dtm_or_tablebase_use: `False`
- gameplay_topology_mutation: `False`
- unique_source_term_count: `10`
- unique_explanation_term_count: `20`
- source_terms: `['active_landmark_label.drive_to_edge', 'active_landmark_label.fence_established', 'candidate_strategy_family.edge_trap', 'candidate_strategy_family.fence_established', 'candidate_strategy_family.stage0_basin', 'offline_validated_provider_capacity_evidence', 'runtime_review_packet.krk_candidate_generation_training_refresh_runtime_review_packet_v3', 'source_stage.stage5', 'source_stage.stage6', 'stage5_6_candidate_generation_refresh_scope']`
- explanation_terms: `['active_landmark_label.drive_to_edge', 'active_landmark_label.fence_established', 'box_area_relevance.low', 'box_area_relevance.medium', 'edge_bucket.at_edge', 'edge_bucket.near_edge', 'positive_trace_count_bucket.high', 'positive_trace_count_bucket.low', 'positive_trace_count_bucket.medium', 'positive_trace_provider_candidate_count.10', 'positive_trace_provider_candidate_count.14', 'positive_trace_provider_candidate_count.16', 'positive_trace_provider_candidate_count.2', 'selected_piece.king', 'selected_piece.rook', 'selector_model.combined_simple_rule', 'source_stage.stage5', 'source_stage.stage6', 'support_bucket.close', 'support_bucket.far']`
- benchmark_best_model: `combined_simple_rule`
- benchmark_best_accuracy: `0.9523809523809523`
- benchmark_switch_contrast_recall: `0.8`
- benchmark_abstain_recall: `1.0`
- agent_brief_present: `True`

## Row Alignment

- `selector_objective_fresh_diversity.01` owner=selected_owner_failed recommendation=`prefer_visible_alternative` target=`prefer_visible_alternative` aligned=True unsafe_if_causal=False
- `selector_objective_fresh_diversity.02` owner=selected_owner_failed recommendation=`preserve_selected_owner` target=`prefer_visible_alternative` aligned=False unsafe_if_causal=True
- `selector_objective_fresh_diversity.03` owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner` aligned=True unsafe_if_causal=False
- `selector_objective_fresh_diversity.04` owner=selected_owner_failed recommendation=`prefer_visible_alternative` target=`prefer_visible_alternative` aligned=True unsafe_if_causal=False
- `selector_objective_fresh_diversity.05` owner=selected_owner_failed recommendation=`prefer_visible_alternative` target=`prefer_visible_alternative` aligned=True unsafe_if_causal=False
- `selector_objective_fresh_diversity.06` owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner` aligned=True unsafe_if_causal=False
- `selector_objective_fresh_diversity.07` owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner` aligned=True unsafe_if_causal=False
- `selector_objective_fresh_diversity.08` owner=selected_owner_converted recommendation=`preserve_selected_owner` target=`preserve_selected_owner` aligned=True unsafe_if_causal=False
