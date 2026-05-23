# KRK Candidate-Generation v5 Context Benchmark

This replay-free benchmark compares protected capacity rows with refresh plus exact-trace enrichment context in dataset v5. It does not authorize selection or runtime changes.

## Decision

- status: `candidate_generation_v5_context_useful_selector_still_blocked`
- selector_allowed: `False`
- recommended_next_step: `candidate_generation_v5_boundary_review_or_ownership_label_recovery`

## Summary

- capacity_row_count: `36`
- positive_capacity_count: `26`
- negative_capacity_count: `10`
- runtime_trace_row_count: `34`
- refresh_trace_row_count: `25`
- exact_trace_enrichment_trace_row_count: `3`
- candidate_generation_trace_row_count: `28`
- runtime_trace_row_count_by_source: `{'candidate_generation_refresh_sandbox': 25, 'exact_trace_enrichment_sandbox': 3, 'repair_monitor_observation': 6}`
- exact_positive_capacity_recall_from_refresh_trace: `0.19230769230769232`
- exact_positive_capacity_recall_from_exact_trace_enrichment: `0.11538461538461539`
- exact_positive_capacity_recall_from_candidate_generation_trace: `0.3076923076923077`
- state_provider_positive_capacity_recall_from_candidate_generation_trace: `0.3076923076923077`
- stage_family_positive_capacity_recall_from_candidate_generation_trace: `0.7692307692307693`
- policy_cell_positive_capacity_recall_from_candidate_generation_trace: `0.7692307692307693`
- exact_negative_capacity_exposure_from_candidate_generation_trace: `0.0`
- stage_family_negative_capacity_exposure_from_candidate_generation_trace: `0.0`
- policy_cell_negative_capacity_exposure_from_candidate_generation_trace: `0.0`
- exact_positive_capacity_covered_count: `8`
- exact_trace_enrichment_positive_capacity_covered_count: `3`
- policy_cell_positive_capacity_covered_count: `20`
- policy_cell_negative_capacity_exposed_count: `0`
- v4_exact_positive_capacity_recall_from_refresh_trace: `0.19230769230769232`
- exact_positive_capacity_recall_delta_vs_v4: `0.11538461538461539`
- selector_training_row_count: `0`
- stage7_readiness_training_row_count: `0`

## Interpretation

- context_useful_for_candidate_generation_analysis: `True`
- selector_supported: `False`
- guardrails_supported: `False`
- capacity_labels_are_not_ownership_labels: `True`
- trace_rows_are_not_training_labels: `True`
- exact_trace_enrichment_improved_exact_coverage: `True`
- risk: `V5 exact trace enrichment improves exact candidate visibility for reviewed policy-cell-covered gaps, but these rows remain trace context and do not provide ownership selector labels.`
