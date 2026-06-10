# KRK Candidate-Generation Refresh Coverage Analysis v0

This replay-free analysis evaluates emitted candidate-generation-only refresh frames from the approved default-off sandbox. It does not authorize selection, scoring, routing, guardrails, promotion, or Stage 8 training.

## Decision

- status: `candidate_generation_refresh_coverage_ready_for_trace_dataset_refresh`
- selector_allowed: `False`
- recommended_next_step: `fold_refresh_sandbox_frames_into_non_causal_strategy_sequence_trace_dataset`

## Summary

- case_count: `3`
- emitted_refresh_frame_count: `25`
- emitted_frame_count_by_stage: `{'stage5': 24, 'stage6': 1}`
- emitted_frame_count_by_provider_family: `{'edge_trap': 19, 'fence_established': 3, 'stage0_basin': 3}`
- emitted_frame_count_by_policy_cell: `{'stage5|edge_trap': 19, 'stage5|fence_established': 3, 'stage5|stage0_basin': 2, 'stage6|stage0_basin': 1}`
- capacity_evidence_counts: `{'positive_capacity': 5, 'positive_capacity_scope': 20}`
- approved_positive_capacity_rows_in_sample: `5`
- negative_capacity_rows_in_sample: `5`
- exact_positive_capacity_hits: `5`
- exact_positive_capacity_recall: `1.0`
- stage_family_positive_capacity_hits: `5`
- stage_family_positive_capacity_recall: `1.0`
- exact_negative_capacity_exposures: `0`
- exact_negative_capacity_exposure_rate: `0.0`
- stage_family_negative_capacity_exposures: `0`
- stage_family_negative_capacity_exposure_rate: `0.0`
- positive_capacity_frame_count: `5`
- positive_capacity_scope_frame_count: `20`
- truncation_count: `2`
- truncated_frame_count: `24`
- invalid_frame_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- score_delta_count: `0`
- stage4_frame_count: `0`
- stage7_frame_count: `0`

## Interpretation

- approved_cells_only: `True`
- exact_capacity_recall_is_sample_limited: `False`
- stage_family_context_visible: `True`
- negative_capacity_suppression_preserved_in_sample: `True`
- candidate_volume_bound_exercised: `True`
- selector_supported: `False`
- guardrails_supported: `False`
- capacity_labels_are_not_ownership_labels: `True`

## Boundary

The emitted frames expand visible candidate-generation context only. Capacity labels remain capacity evidence, not selector or ownership labels.
