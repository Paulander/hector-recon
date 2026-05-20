# KRK Two-Stage Candidate / Selection Benchmark Plan v0

This non-causal plan defines a benchmark that separates candidate generation from strategy selection.

## Tracks

- `candidate_generation` question: Does the candidate set represent protected providers with conversion capacity?
- `candidate_generation` metrics: `['positive_capacity_recall', 'candidate_count_per_state', 'negative_capacity_inclusion_rate', 'stage7_leakage_count']`
- `strategy_selection` question: Given a candidate set, can a selector suppress negative-capacity candidates while preserving positives?
- `strategy_selection` metrics: `['leave_state_out_positive_hit_rate', 'negative_capacity_suppression', 'false_positive_on_forced_capacity', 'stage7_heldout_suppression']`

## Minimum Inputs

- `krk_ranked_strategy_proposal_frames_v1`
- `krk_protected_provider_coverage_frames_v0`
- `krk_state_local_contrast_labels_v2`
- `krk_candidate_generator_coverage_audit_v0`
- `krk_validated_provider_candidate_set_audit_v0`

## Acceptance

- `stage7_training_rows`: `0`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `reports_candidate_generation_and_selection_separately`: `True`
- `explicitly_separates_label_semantics`: `True`

## Stop Conditions

- `benchmark requires new runtime behavior`
- `benchmark mixes forced-capacity labels as direct selected-success labels`
- `Stage 7 rows become training rows`
- `DTM/tablebase enters runtime policy`
- `topology mutation is required`

## Decision

- `status`: `two_stage_candidate_selection_benchmark_plan_ready`
- `recommended_next_step`: `build_two_stage_candidate_selection_benchmark_v0`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
