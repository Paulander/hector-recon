# KRK Candidate-Generation v4 Context Benchmark

This replay-free benchmark compares protected capacity rows with candidate-generation refresh trace context in dataset v4. It does not authorize selection or runtime changes.

## Decision

- status: `candidate_generation_v4_context_useful_selector_still_blocked`
- selector_allowed: `False`
- recommended_next_step: `architecture_review_candidate_generation_context_to_next_runtime_boundary`

## Summary

- capacity_row_count: `36`
- positive_capacity_count: `26`
- negative_capacity_count: `10`
- runtime_trace_row_count: `31`
- refresh_trace_row_count: `25`
- runtime_trace_row_count_by_source: `{'candidate_generation_refresh_sandbox': 25, 'repair_monitor_observation': 6}`
- exact_positive_capacity_recall_from_refresh_trace: `0.19230769230769232`
- state_provider_positive_capacity_recall_from_refresh_trace: `0.19230769230769232`
- stage_family_positive_capacity_recall_from_refresh_trace: `0.7692307692307693`
- policy_cell_positive_capacity_recall_from_refresh_trace: `0.7692307692307693`
- exact_negative_capacity_exposure_from_refresh_trace: `0.0`
- stage_family_negative_capacity_exposure_from_refresh_trace: `0.0`
- policy_cell_negative_capacity_exposure_from_refresh_trace: `0.0`
- exact_positive_capacity_covered_count: `5`
- policy_cell_positive_capacity_covered_count: `20`
- policy_cell_negative_capacity_exposed_count: `0`
- selector_training_row_count: `0`
- stage7_readiness_training_row_count: `0`

## Interpretation

- context_useful_for_candidate_generation_analysis: `True`
- selector_supported: `False`
- guardrails_supported: `False`
- capacity_labels_are_not_ownership_labels: `True`
- trace_rows_are_not_training_labels: `True`
- risk: `Refresh trace context cleanly exposes reviewed candidate-generation cells, but it remains a candidate-generation signal, not an ownership selector or score calibration mechanism.`
