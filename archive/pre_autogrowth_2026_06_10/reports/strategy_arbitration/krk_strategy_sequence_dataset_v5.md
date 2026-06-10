# KRK Strategy-Sequence Dataset v5

This non-causal dataset refresh appends approved exact trace enrichment sandbox trace features to dataset v4. It does not authorize selector behavior.

## Decision

- status: `strategy_sequence_dataset_v5_refreshed_non_causal_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `probe_strategy_sequence_dataset_v5_quality_non_causal`

## Summary

- row_count: `310`
- added_exact_trace_enrichment_row_count: `3`
- row_count_by_channel: `{'candidate_move_frame': 140, 'internal_monitor_candidate': 13, 'runtime_observation_trace_feature': 34, 'validated_provider_capacity': 36, 'visible_provider_proposal': 87}`
- runtime_trace_feature_row_count_by_source: `{'candidate_generation_refresh_sandbox': 25, 'exact_trace_enrichment_sandbox': 3, 'repair_monitor_observation': 6}`
- source_stage_counts: `{'stage4': 18, 'stage5': 63, 'stage6': 31, 'stage7': 198}`
- candidate_generation_training_row_count: `26`
- candidate_generation_training_row_count_by_channel: `{'validated_provider_capacity': 26}`
- selector_training_row_count: `0`
- stage7_challenge_row_count: `198`
- stage7_readiness_training_row_count: `0`
- runtime_trace_feature_row_count: `34`

## Boundary

V5 keeps all selector-training rows false. Exact trace enrichment rows are runtime-observation context only, not capacity labels, ownership labels, routing requests, or score changes.
