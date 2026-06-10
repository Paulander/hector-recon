# KRK Strategy-Sequence Dataset v2 Cross-Stage Capacity-Merged

This non-causal refresh merges bounded cross-stage forced-provider capacity labels into dataset v2. Labels remain capacity evidence, not ownership labels.

## Decision

- status: `strategy_sequence_dataset_v2_cross_stage_capacity_merged_non_causal`
- selector_allowed: `False`
- recommended_next_step: `rerun_candidate_generation_refresh_probe`

## Summary

- row_count: `282`
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 6, 'validated_provider_capacity': 36, 'visible_provider_proposal': 87}`
- source_stage_counts: `{'stage4': 18, 'stage5': 36, 'stage6': 30, 'stage7': 198}`
- candidate_generation_training_row_count: `26`
- candidate_generation_training_row_count_by_channel: `{'validated_provider_capacity': 26}`
- selector_training_row_count: `0`
- stage7_challenge_row_count: `198`
- stage7_readiness_training_row_count: `0`
- merged_cross_stage_label_row_count: `8`
- merged_cross_stage_label_capacity_counts: `{'negative_capacity': 1, 'positive_capacity': 7}`
