# KRK Strategy-Sequence Dataset v2

This non-causal dataset refresh applies explicit evidence-channel semantics and adds the repair-monitor runtime-observation trace-feature channel.

## Decision

- status: `strategy_sequence_dataset_v2_refreshed_non_causal_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `probe_strategy_sequence_dataset_v2_quality_non_causal`

## Summary

- row_count: 262
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 6, 'validated_provider_capacity': 16, 'visible_provider_proposal': 87}`
- source_stage_counts: `{'stage4': 13, 'stage5': 27, 'stage6': 24, 'stage7': 198}`
- stage7_challenge_row_count: 198
- stage7_readiness_training_row_count: 0
- selector_training_row_count: 0
- candidate_generation_training_row_count: 11
- runtime_trace_feature_row_count: 6

## Boundary

V2 makes all selector-training rows false until explicit ownership labels are recovered. Positive forced-capacity rows remain candidate-generation evidence only.
