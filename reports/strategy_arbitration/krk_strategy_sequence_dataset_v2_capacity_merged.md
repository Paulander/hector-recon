# KRK Strategy-Sequence Dataset v2 Capacity-Merged

This non-causal refresh merges bounded forced-provider capacity labels into dataset v2. Labels remain capacity evidence, not ownership labels.

## Decision

- status: `strategy_sequence_dataset_v2_capacity_merged_non_causal`
- selector_allowed: `False`
- recommended_next_step: `rerun_candidate_generation_refresh_probe`

## Summary

- row_count: 274
- merged_label_row_count: 12
- merged_label_capacity_counts: `{'negative_capacity': 4, 'positive_capacity': 8}`
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 6, 'validated_provider_capacity': 28, 'visible_provider_proposal': 87}`
- candidate_generation_training_row_count: 19
- selector_training_row_count: 0
- stage7_readiness_training_row_count: 0
