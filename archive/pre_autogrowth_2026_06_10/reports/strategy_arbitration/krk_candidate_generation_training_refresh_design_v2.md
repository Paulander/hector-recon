# KRK Candidate-Generation Training Refresh Design v2

Define a non-causal candidate-generation training refresh that can improve proposal recall from protected capacity evidence while preserving the capacity-vs-ownership label boundary.

## Decision

- status: `candidate_generation_training_refresh_design_ready`
- selector_allowed: `False`
- runtime_candidate_generator_refresh_allowed: `False`
- recommended_next_step: `candidate_generation_training_refresh_benchmark_or_cross_stage_capacity_review`

## Evidence

- dataset_status: `strategy_sequence_dataset_v2_capacity_merged_non_causal`
- probe_status: `candidate_generation_refresh_supported_selector_blocked`
- capacity_row_count: 28
- capacity_label_counts: `{'negative_capacity': 9, 'positive_capacity': 19}`
- candidate_generation_training_row_count: 19
- selector_training_row_count: 0
- stage7_readiness_training_row_count: 0

## Candidate Policy Seed

- policy_name: `stage_family_pure_positive_with_support_2`
- policy_role: `analysis_seed_for_candidate_generation_only`
- positive_recall: 0.7368421052631579
- positive_precision: 1.0
- negative_suppression: 1.0

Known limitations:

- `capacity_labels_are_not_ownership_labels`
- `leave_stage_out_generalization_is_weak`
- `dataset_is_small`
- `negative_capacity_candidates_remain_present`
- `candidate_generation_does_not_select_or_score_candidates`

## Readiness Assessment

- candidate_refresh_supported: `True`
- cross_stage_generalization_supported: `False`
- selector_supported: `False`
- runtime_candidate_generator_refresh_supported_now: `False`
- reason_runtime_blocked: The protected in-sample candidate-generation signal improved, but leave-stage-out negative suppression remains too weak for runtime refresh or selector use.

## Minimum Requirements For Any Future Refresh

- `preserve label_semantics on every row`
- `train or fit only candidate-generation emission/risk features`
- `produce no selector weights`
- `produce no provider score deltas`
- `emit no runtime routes or direct provider requests`
- `keep Stage 7 challenge rows out of training/readiness metrics`
- `evaluate leave-stage-out and report weak generalization explicitly`
- `require a separate review before any runtime candidate-generator refresh`

## Forbidden Next Steps

- `runtime_selector`
- `provider_score_tuning`
- `provider_suppression`
- `direct_provider_routing`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
- `using_capacity_labels_as_ownership_labels`
