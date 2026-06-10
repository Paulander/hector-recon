# KRK Strategy-Sequence Dataset v3 Quality Probe

This probe validates dataset v3 channel semantics. It does not train a selector or authorize runtime changes.

## Decision

- status: `strategy_sequence_dataset_v3_quality_candidate_generation_context_ready_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `candidate_generation_v3_context_review_or_bounded_non_causal_probe`

## Summary

- row_count: 320
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 44, 'validated_provider_capacity': 36, 'visible_provider_proposal': 87}`
- runtime_trace_feature_row_count_by_source: `{'repair_monitor_observation': 6, 'stage5_6_candidate_generation_refresh': 38}`
- candidate_generation_training_row_count: 26
- selector_training_row_count: 0
- runtime_trace_feature_row_count: 44
- stage7_readiness_training_row_count: 0

## Selector Blockers

- `no_explicit_ownership_selector_rows`
- `runtime_trace_features_are_context_not_selector_labels`
- `capacity_rows_are_candidate_generation_not_ownership_labels`
