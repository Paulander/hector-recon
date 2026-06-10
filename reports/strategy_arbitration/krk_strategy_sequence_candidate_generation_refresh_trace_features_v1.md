# KRK Strategy-Sequence Candidate-Generation Refresh Trace Features v1

This artifact folds emitted candidate-generation refresh sandbox frames into the strategy-sequence evidence track as trace-only features. It does not alter runtime behavior and does not authorize selector behavior.

## Decision

- status: `candidate_generation_refresh_trace_features_folded_non_causal`
- selector_allowed: `False`
- recommended_next_step: `build_strategy_sequence_dataset_v4_non_causal`

## Trace Features

- trace_frame_count: `25`
- stage_counts: `{'stage5': 24, 'stage6': 1}`
- strategy_family_counts: `{'edge_trap': 19, 'fence_established': 3, 'stage0_basin': 3}`
- capacity_label_counts: `{'positive_capacity': 5, 'positive_capacity_scope': 20}`
- policy_cell_counts: `{'stage5|edge_trap': 19, 'stage5|fence_established': 3, 'stage5|stage0_basin': 2, 'stage6|stage0_basin': 1}`
- stage7_trace_frame_count: `0`
- selector_training_row_count: `0`
- candidate_generation_training_row_count: `0`

## Boundary

These frames are context evidence only. They are not capacity labels, ownership labels, selector rows, guardrail triggers, routing requests, or score changes.
