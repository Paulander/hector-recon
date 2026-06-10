# KRK Strategy-Sequence Repair-Monitor Trace Features v1

This artifact folds repair-monitor observation frames into the strategy-sequence evidence track as trace-only features. It does not alter the base dataset and does not authorize selector behavior.

## Decision

- status: `repair_monitor_trace_features_folded_non_causal`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `strategy_sequence_trace_feature_integration_review`

## Added Trace Features

- trace_frame_count: 6
- stage_counts: `{'stage4': 1, 'stage5': 4, 'stage6': 1}`
- strategy_family_counts: `{'terminal.krk.repair_needed_monitor': 6}`
- risk_term_counts: `{'post_fence_conversion_needed': 6, 'repair_or_reestablish_cut_available': 6, 'rook_safe': 6}`
- stage7_trace_frame_count: 0
- selector_training_row_count: 0
- candidate_generation_training_row_count: 0

## Base Dataset Context

- base_frame_count: 256
- base_stage7_challenge_row_count: 198
- base_readiness_training_stage7_row_count: 0

## Boundary

These frames are context evidence only. They are not capacity labels, ownership labels, selector rows, guardrail triggers, routing requests, or score changes.
