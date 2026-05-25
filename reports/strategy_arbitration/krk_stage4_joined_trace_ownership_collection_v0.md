# KRK Stage 4 Joined Trace/Ownership Collection v0

This report records bounded Stage 4 observation-only trace collection. It joins trace frames with offline selected-owner labels; it does not train or authorize a selector.

## Decision

- status: `stage4_joined_trace_ownership_collection_complete`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `build_selector_objective_seed_manifest_v2`

## Summary

- attempted_row_count: `6`
- collected_row_count: `6`
- joined_row_count: `6`
- stage4_row_count: `6`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- generated_frame_count: `170`
- generated_frame_count_by_source: `{'candidate_move_frame': 104, 'validated_provider_pack': 66}`
- capacity_evidence_counts: `{'negative_capacity': 3, 'positive_capacity': 3, 'unknown_capacity': 164}`
- switch_contrast_with_positive_capacity_count: `1`
- selected_failure_trace_context_only_count: `5`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- baseline_observation_frame_count: `0`
- direct_request_false_count: `170`
- score_delta_zero_count: `170`
- invalid_frame_count: `0`
- default_off_equivalence_passed: `True`
- runtime_behavior_changed: `False`

## Joined Rows

- `state.256a3da30f0f` stage=stage4 label=selected_owner_failed frames=35 positive_capacity_frames=3 class=`stage4_selected_failure_with_visible_positive_capacity`
- `state.44938ccb8ab7` stage=stage4 label=selected_owner_failed frames=22 positive_capacity_frames=0 class=`stage4_selected_failure_trace_context_only`
- `state.80080a9a826d` stage=stage4 label=selected_owner_failed frames=26 positive_capacity_frames=0 class=`stage4_selected_failure_trace_context_only`
- `state.b09c954a787e` stage=stage4 label=selected_owner_failed frames=27 positive_capacity_frames=0 class=`stage4_selected_failure_trace_context_only`
- `state.b11124d658cf` stage=stage4 label=selected_owner_failed frames=31 positive_capacity_frames=0 class=`stage4_selected_failure_trace_context_only`
- `state.ea634c29ece7` stage=stage4 label=selected_owner_failed frames=29 positive_capacity_frames=0 class=`stage4_selected_failure_trace_context_only`
