# KRK Selector Objective Fresh Diversity Collection v0

This report records the explicitly approved bounded Stage 5/6 observation-only collection. It does not train or authorize a selector.

## Decision

- status: `fresh_stage5_6_selector_objective_collection_complete`
- collection_valid: `True`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `review_fresh_stage5_6_selector_objective_collection_result`

## Summary

- attempted_row_count: `8`
- collected_row_count: `8`
- joined_row_count: `8`
- stage_counts: `{'stage5': 4, 'stage6': 4}`
- selected_owner_counts: `{'selected_owner_converted': 4, 'selected_owner_failed': 4}`
- objective_channel_counts: `{'candidate_switch_contrast_seed': 4, 'progress_window_failure_contrast_candidate': 2, 'safe_preservation_contrast_seed': 2}`
- selected_provider_counts: `{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.fence_established': 1, 'krk.stage0_basin': 5}`
- generated_frame_count: `76`
- generated_frame_count_by_stage: `{'stage5': 45, 'stage6': 31}`
- generated_frame_count_by_provider_family: `{'edge_trap': 12, 'fence_established': 2, 'stage0_basin': 62}`
- selected_failure_with_visible_positive_capacity_count: `4`
- safe_preservation_with_visible_positive_capacity_count: `4`
- selected_failure_trace_context_only_count: `0`
- safe_preservation_trace_context_only_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- baseline_refresh_frame_count: `0`
- direct_request_false_count: `76`
- score_delta_zero_count: `76`
- invalid_frame_count: `0`
- default_off_equivalence_passed: `True`
- runtime_behavior_changed: `False`

## Rows

- `selector_objective_fresh_diversity.01` stage=stage5 label=selected_owner_failed frames=10 positive_capacity_frames=10 class=`selected_failure_with_visible_positive_capacity`
- `selector_objective_fresh_diversity.02` stage=stage5 label=selected_owner_failed frames=13 positive_capacity_frames=13 class=`selected_failure_with_visible_positive_capacity`
- `selector_objective_fresh_diversity.03` stage=stage5 label=selected_owner_converted frames=12 positive_capacity_frames=12 class=`safe_preservation_with_visible_positive_capacity`
- `selector_objective_fresh_diversity.04` stage=stage6 label=selected_owner_failed frames=10 positive_capacity_frames=10 class=`selected_failure_with_visible_positive_capacity`
- `selector_objective_fresh_diversity.05` stage=stage6 label=selected_owner_failed frames=1 positive_capacity_frames=1 class=`selected_failure_with_visible_positive_capacity`
- `selector_objective_fresh_diversity.06` stage=stage6 label=selected_owner_converted frames=10 positive_capacity_frames=10 class=`safe_preservation_with_visible_positive_capacity`
- `selector_objective_fresh_diversity.07` stage=stage5 label=selected_owner_converted frames=10 positive_capacity_frames=10 class=`safe_preservation_with_visible_positive_capacity`
- `selector_objective_fresh_diversity.08` stage=stage6 label=selected_owner_converted frames=10 positive_capacity_frames=10 class=`safe_preservation_with_visible_positive_capacity`
