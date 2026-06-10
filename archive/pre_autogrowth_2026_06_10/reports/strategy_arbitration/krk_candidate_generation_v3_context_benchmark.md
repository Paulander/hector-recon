# KRK Candidate-Generation v3 Context Benchmark

This replay-free benchmark compares protected capacity rows with runtime-observation trace context in dataset v3. It does not authorize selection or runtime changes.

## Decision

- status: `candidate_generation_v3_context_useful_selector_still_blocked`
- selector_allowed: `False`
- recommended_next_step: `architecture_review_candidate_generation_context_to_runtime_boundary`

## Summary

- capacity_row_count: `36`
- positive_capacity_count: `26`
- negative_capacity_count: `10`
- runtime_trace_row_count: `44`
- runtime_trace_row_count_by_source: `{'repair_monitor_observation': 6, 'stage5_6_candidate_generation_refresh': 38}`
- exact_positive_capacity_recall_from_trace: `0.3076923076923077`
- state_provider_positive_capacity_recall_from_trace: `0.3076923076923077`
- stage_family_positive_capacity_recall_from_trace: `0.7692307692307693`
- stage_family_negative_capacity_exposure_from_trace: `0.0`
- exact_positive_capacity_covered_count: `8`
- state_provider_positive_capacity_covered_count: `8`
- stage_family_positive_capacity_covered_count: `20`
- stage_family_negative_capacity_exposed_count: `0`
- selector_training_row_count: `0`
- stage7_readiness_training_row_count: `0`

## Interpretation

- context_useful_for_candidate_generation_analysis: `True`
- selector_supported: `False`
- risk: Trace context improves visibility of Stage 5/6 proposal scope, but stage-family coverage also overlaps negative-capacity families; it cannot become a selector without explicit ownership labels.
