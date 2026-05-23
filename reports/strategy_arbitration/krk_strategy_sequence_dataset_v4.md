# KRK Strategy-Sequence Dataset v4

This non-causal dataset refresh appends approved candidate-generation refresh sandbox trace features to the latest protected capacity-merged strategy-sequence dataset. It does not authorize selector behavior.

## Decision

- status: `strategy_sequence_dataset_v4_refreshed_non_causal_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `probe_strategy_sequence_dataset_v4_quality_non_causal`

## Summary

- row_count: `307`
- added_candidate_generation_refresh_trace_row_count: `25`
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 31, 'validated_provider_capacity': 36, 'visible_provider_proposal': 87}`
- runtime_trace_feature_row_count_by_source: `{'candidate_generation_refresh_sandbox': 25, 'repair_monitor_observation': 6}`
- source_stage_counts: `{'stage4': 18, 'stage5': 60, 'stage6': 31, 'stage7': 198}`
- candidate_generation_training_row_count: `26`
- candidate_generation_training_row_count_by_channel: `{'validated_provider_capacity': 26}`
- selector_training_row_count: `0`
- stage7_challenge_row_count: `198`
- stage7_readiness_training_row_count: `0`
- runtime_trace_feature_row_count: `31`

## Boundary

V4 keeps all selector-training rows false. Candidate-generation refresh rows are runtime-observation context only, not capacity labels, ownership labels, routing requests, or score changes.
