# KRK Strategy-Sequence Dataset v2 Quality Probe

This probe validates dataset-channel semantics. It does not train a selector or authorize runtime changes.

## Decision

- status: `strategy_sequence_dataset_v2_quality_candidate_generation_ready_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `review_candidate_generation_training_refresh_or_collect_ownership_labels`

## Summary

- row_count: 262
- protected_row_count: 64
- stage7_challenge_row_count: 198
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 6, 'validated_provider_capacity': 16, 'visible_provider_proposal': 87}`
- candidate_generation_training_row_count: 11
- selector_training_row_count: 0
- runtime_trace_feature_row_count: 6

## Selector Blockers

- `no_explicit_ownership_selector_rows`
- `runtime_trace_feature_channel_small`
- `stage7_present_only_as_heldout_challenge`
