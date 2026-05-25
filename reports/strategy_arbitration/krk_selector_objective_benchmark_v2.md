# KRK Selector Objective Benchmark v2

This benchmark evaluates runtime-visible feature models over the v2 selector-objective seed set. It does not train or authorize a selector.

## Decision

- status: `selector_objective_benchmark_v2_runtime_feature_review_ready`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `write_selector_objective_benchmark_review_packet`

## Summary

- seed_row_count: `18`
- target_action_counts: `{'abstain': 5, 'preserve': 8, 'switch': 5}`
- runtime_feature_model_count: `26`
- runtime_threshold_passing_model_count: `1`
- context_row_count: `41`
- best_runtime_model: `visible_failure_risk_heuristic_v2`
- best_runtime_accuracy: `1.0`
- best_runtime_switch_precision: `1.0`
- best_runtime_switch_recall: `1.0`
- best_runtime_preserve_recall: `1.0`
- best_runtime_abstain_recall: `1.0`
- offline_oracle_accuracy: `1.0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- seed_probe_status: `selector_objective_seed_probe_v2_ready_for_non_causal_benchmark`

## Runtime Feature Models

- `active_landmark_label` accuracy=0.5555555555555556 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.75 abstain_recall=0.8
- `active_landmark_support` accuracy=0.6666666666666666 switch_precision=0.5 switch_recall=0.4 preserve_recall=0.875 abstain_recall=0.6
- `active_support_piece_positive_bucket` accuracy=0.5555555555555556 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.875 abstain_recall=0.6
- `box_area_delta_bucket` accuracy=0.16666666666666666 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.375 abstain_recall=0.0
- `box_area_relevance` accuracy=0.4444444444444444 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=0.0
- `conservative_visible_failure_risk_heuristic_v2` accuracy=0.8888888888888888 switch_precision=1.0 switch_recall=0.6 preserve_recall=1.0 abstain_recall=1.0
- `edge_bucket` accuracy=0.4444444444444444 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=0.0
- `has_positive_trace_capacity` accuracy=0.7222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=1.0
- `positive_trace_count_bucket` accuracy=0.8888888888888888 switch_precision=1.0 switch_recall=0.6 preserve_recall=1.0 abstain_recall=1.0
- `rook_distance_delta_bucket` accuracy=0.2222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=0.5 abstain_recall=0.0
- `selected_piece` accuracy=0.3888888888888889 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.875 abstain_recall=0.0
- `selected_provider_family` accuracy=0.3888888888888889 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.875 abstain_recall=0.0
- `source_stage` accuracy=0.6111111111111112 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.75 abstain_recall=1.0
- `stage_active_landmark` accuracy=0.5555555555555556 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.75 abstain_recall=0.8
- `stage_active_support_positive_bucket` accuracy=0.6111111111111112 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=0.6
- `stage_box_relevance_positive_bucket` accuracy=0.7222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=1.0
- `stage_positive_bucket` accuracy=0.7222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=1.0
- `stage_provider_family` accuracy=0.7222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=1.0
- `stage_provider_positive_bucket` accuracy=0.7222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=1.0
- `stage_support_positive_bucket` accuracy=0.6111111111111112 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=0.6
- `stage_support_rook_positive_bucket` accuracy=0.6111111111111112 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=0.6
- `stage_trace_positive_bucket` accuracy=0.7222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=1.0
- `support_bucket` accuracy=0.2222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=0.5 abstain_recall=0.0
- `support_positive_bucket` accuracy=0.5 switch_precision=0.0 switch_recall=0.0 preserve_recall=0.75 abstain_recall=0.6
- `trace_source_profile` accuracy=0.7222222222222222 switch_precision=None switch_recall=0.0 preserve_recall=1.0 abstain_recall=1.0
- `visible_failure_risk_heuristic_v2` accuracy=1.0 switch_precision=1.0 switch_recall=1.0 preserve_recall=1.0 abstain_recall=1.0

## Interpretation

- runtime_feature_benchmark_ready_for_review: `True`
- selector_training_supported: `False`
- runtime_selector_supported: `False`
- independent_validation_required_before_runtime: `True`
- offline_semantics_confirmed: `True`
- reason: `Seed v2 supports a non-causal benchmark with switch/preserve/abstain labels. Passing runtime-feature models would justify a later review packet only; this artifact does not train or implement a selector. Heuristic probes are not enough for runtime use without independent protected validation.`
