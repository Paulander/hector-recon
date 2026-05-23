# KRK Strategy-Sequence Stage 5/6 Refresh Trace Features v0

This artifact folds Stage 5/6 refresh observation frames into the strategy-sequence evidence track as trace-only features. It does not alter the base dataset and does not authorize selector behavior.

## Decision

- status: `stage5_6_refresh_trace_features_folded_non_causal`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `strategy_sequence_dataset_v3_design_or_integration_review`

## Added Trace Features

- trace_frame_count: 38
- stage_counts: `{'stage5': 37, 'stage6': 1}`
- strategy_family_counts: `{'edge_trap': 22, 'fence_established': 3, 'stage0_basin': 13}`
- capacity_label_counts: `{'positive_capacity': 8, 'positive_capacity_scope': 30}`
- stage7_trace_frame_count: 0
- selector_training_row_count: 0
- candidate_generation_training_row_count: 0

## Base Dataset Context

- base_frame_count: 256
- base_stage7_challenge_row_count: 198
- base_readiness_training_stage7_row_count: 0

## Boundary

These frames are context evidence only. They are not capacity labels, ownership labels, selector rows, guardrail triggers, routing requests, or score changes.
