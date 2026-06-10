# KRK Joined Trace/Ownership Collection Manifest v0

This manifest identifies protected ownership-labeled states that lack provider trace context. It does not authorize a runtime run by itself.

## Decision

- status: `joined_trace_ownership_collection_manifest_ready_for_review`
- runtime_collection_allowed_by_manifest: `False`
- recommended_next_step: `review_bounded_observation_only_trace_collection_scope`

## Summary

- ownership_row_count: `41`
- existing_provider_trace_state_count: `4`
- missing_provider_trace_ownership_row_count: `37`
- approved_observation_scope_candidate_count: `18`
- excluded_requires_separate_review_count: `19`
- priority_counts: `{'excluded_requires_separate_review': 19, 'high_selected_failure': 2, 'medium_non_stage0_preservation': 1, 'medium_safe_preservation_control': 15}`
- missing_source_stage_counts: `{'stage4': 19, 'stage5': 11, 'stage6': 7}`
- missing_label_counts: `{'selected_owner_converted': 29, 'selected_owner_failed': 8}`
- approved_scope_label_counts: `{'selected_owner_converted': 16, 'selected_owner_failed': 2}`
- stage7_training_row_count: `0`
- runtime_collection_allowed_row_count: `0`

## Approved Refresh Cells

- `stage5`: `['edge_trap', 'fence_established', 'stage0_basin']`
- `stage6`: `['stage0_basin']`

## Highest Priority Rows

- `state.0b1f2153179b` stage=stage5 selected=krk.stage0_basin label=selected_owner_failed priority=`high_selected_failure`
- `state.67a88e3b1dd2` stage=stage6 selected=krk.stage0_basin label=selected_owner_failed priority=`high_selected_failure`
