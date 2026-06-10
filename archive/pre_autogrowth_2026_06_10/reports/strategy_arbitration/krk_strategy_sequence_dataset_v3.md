# KRK Strategy-Sequence Dataset v3

This non-causal dataset refresh appends Stage 5/6 candidate-generation refresh trace features to the latest capacity-merged strategy-sequence dataset. It does not authorize selector behavior.

## Decision

- status: `strategy_sequence_dataset_v3_refreshed_non_causal_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `probe_strategy_sequence_dataset_v3_quality_non_causal`

## Summary

- row_count: 320
- added_stage5_6_refresh_trace_row_count: 38
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 44, 'validated_provider_capacity': 36, 'visible_provider_proposal': 87}`
- runtime_trace_feature_row_count_by_source: `{'repair_monitor_observation': 6, 'stage5_6_candidate_generation_refresh': 38}`
- source_stage_counts: `{'stage4': 18, 'stage5': 73, 'stage6': 31, 'stage7': 198}`
- stage7_challenge_row_count: 198
- stage7_readiness_training_row_count: 0
- selector_training_row_count: 0
- candidate_generation_training_row_count: 26
- runtime_trace_feature_row_count: 44

## Boundary

V3 keeps all selector-training rows false. Stage 5/6 refresh rows are runtime-observation context only, not capacity labels, ownership labels, routing requests, or score changes.
