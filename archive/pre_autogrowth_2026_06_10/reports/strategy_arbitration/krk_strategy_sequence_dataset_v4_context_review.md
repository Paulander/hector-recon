# KRK Strategy-Sequence Dataset v4 Context Review

This review closes the v4 integration slice. Dataset v4 is usable as candidate-generation context, not as selector training data.

## Decision

- status: `strategy_sequence_dataset_v4_context_integrated_selector_still_blocked`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `candidate_generation_v4_context_benchmark_non_causal`

## Summary

- row_count: `307`
- candidate_generation_training_row_count: `26`
- selector_training_row_count: `0`
- stage7_readiness_training_row_count: `0`
- runtime_trace_feature_row_count: `31`
- runtime_trace_feature_row_count_by_source: `{'candidate_generation_refresh_sandbox': 25, 'repair_monitor_observation': 6}`
- candidate_generation_refresh_trace_row_count: `25`
- quality_status: `strategy_sequence_dataset_v4_quality_candidate_generation_context_ready_selector_blocked`
- quality_selector_blockers: `['no_explicit_ownership_selector_rows', 'runtime_trace_features_are_context_not_selector_labels', 'capacity_rows_are_candidate_generation_not_ownership_labels']`
- quality_row_count: `307`

## Validated Progress

- `candidate_generation_refresh_sandbox_default_off_equivalent`
- `candidate_generation_refresh_frames_folded_non_causal`
- `candidate_generation_refresh_trace_source_integrated`
- `repair_monitor_trace_features_preserved`
- `capacity_labels_preserved_for_candidate_generation_only`

## Still Blocked

- `selector_training`
- `guardrail_campaign`
- `score_changes`
- `provider_routing`
- `stage7_promotion`
- `stage8_training`
- `stage4_runtime_scope`
