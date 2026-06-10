# KRK Joined Trace/Ownership Collection v0

This report records the explicitly approved bounded observation-only collection run. It emits trace context and joins it with existing ownership labels; it does not train or authorize a selector.

## Decision

- status: `joined_trace_ownership_collection_complete_seed_improved`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `build_selector_objective_seed_manifest_v1`

## Summary

- attempted_row_count: `8`
- collected_row_count: `8`
- joined_row_count: `8`
- switch_contrast_count: `2`
- safe_preservation_count: `6`
- stage_counts: `{'stage5': 5, 'stage6': 3}`
- provider_counts: `{'krk.stage0_basin': 8}`
- generated_frame_count: `80`
- generated_frame_count_by_stage: `{'stage5': 50, 'stage6': 30}`
- generated_frame_count_by_provider_family: `{'stage0_basin': 80}`
- direct_request_false_count: `80`
- score_delta_zero_count: `80`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- selected_move_provider_delta_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- baseline_refresh_frame_count: `0`
- invalid_frame_count: `0`
- default_off_equivalence_passed: `True`
- runtime_behavior_changed: `False`

## Joined Rows

- `state.0b1f2153179b` stage=stage5 label=selected_owner_failed frames=10 positive_frames=10 class=`selected_failure_with_visible_positive_alternative`
- `state.67a88e3b1dd2` stage=stage6 label=selected_owner_failed frames=10 positive_frames=10 class=`selected_failure_with_visible_positive_alternative`
- `state.18cfccc9c4c1` stage=stage5 label=selected_owner_converted frames=10 positive_frames=10 class=`safe_preservation_with_visible_positive_alternative`
- `state.2c1d6da27ea1` stage=stage5 label=selected_owner_converted frames=10 positive_frames=10 class=`safe_preservation_with_visible_positive_alternative`
- `state.388d05197dd9` stage=stage5 label=selected_owner_converted frames=10 positive_frames=10 class=`safe_preservation_with_visible_positive_alternative`
- `state.52085d244e9d` stage=stage6 label=selected_owner_converted frames=10 positive_frames=10 class=`safe_preservation_with_visible_positive_alternative`
- `state.69711173114a` stage=stage6 label=selected_owner_converted frames=10 positive_frames=10 class=`safe_preservation_with_visible_positive_alternative`
- `state.6e84c77a4520` stage=stage5 label=selected_owner_converted frames=10 positive_frames=10 class=`safe_preservation_with_visible_positive_alternative`
