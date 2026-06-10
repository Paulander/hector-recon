# KRK Selector Objective Feature Probe v0

This non-causal probe tests simple visible feature keys over the v1 selector-objective seed set. It does not train or authorize a selector.

## Decision

- status: `selector_objective_feature_probe_no_runtime_ready_features`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `collect_more_diverse_joined_trace_ownership_evidence`

## Summary

- seed_row_count: `12`
- target_channel_counts: `{'candidate_switch_contrast_seed': 4, 'safe_preservation_contrast_seed': 8}`
- runtime_feature_model_count: `21`
- runtime_threshold_passing_model_count: `0`
- best_runtime_model: `selected_provider_family@0.25`
- best_runtime_switch_recall: `0.75`
- best_runtime_preserve_recall: `0.0`
- best_runtime_switch_precision: `0.2727272727272727`
- best_runtime_accuracy: `0.25`
- offline_oracle_accuracy: `1.0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- seed_probe_status: `selector_objective_seed_ready_for_non_causal_feature_probe`

## Interpretation

- selector_feature_probe_ready_for_review: `False`
- selector_training_supported: `False`
- runtime_selector_supported: `False`
- offline_semantics_confirmed: `True`
- reason: `The seed set is now large enough to probe visible features, but simple visible feature keys do not yet constitute selector training or runtime selector authorization.`

## Runtime Feature Models

- `positive_trace_count_bucket@0.25` switch_recall=0.5 preserve_recall=0.25 switch_precision=0.25 accuracy=0.3333333333333333
- `positive_trace_count_bucket@0.5` switch_recall=0.5 preserve_recall=1.0 switch_precision=1.0 accuracy=0.8333333333333334
- `positive_trace_count_bucket@0.75` switch_recall=0.5 preserve_recall=1.0 switch_precision=1.0 accuracy=0.8333333333333334
- `selected_provider_family@0.25` switch_recall=0.75 preserve_recall=0.0 switch_precision=0.2727272727272727 accuracy=0.25
- `selected_provider_family@0.5` switch_recall=0.0 preserve_recall=0.875 switch_precision=0.0 accuracy=0.5833333333333334
- `selected_provider_family@0.75` switch_recall=0.0 preserve_recall=0.875 switch_precision=0.0 accuracy=0.5833333333333334
- `source_stage@0.25` switch_recall=0.5 preserve_recall=0.0 switch_precision=0.2 accuracy=0.16666666666666666
- `source_stage@0.5` switch_recall=0.0 preserve_recall=0.75 switch_precision=0.0 accuracy=0.5
- `source_stage@0.75` switch_recall=0.0 preserve_recall=1.0 switch_precision=None accuracy=0.6666666666666666
- `stage_provider_family@0.25` switch_recall=0.25 preserve_recall=0.0 switch_precision=0.1111111111111111 accuracy=0.08333333333333333
- `stage_provider_family@0.5` switch_recall=0.0 preserve_recall=0.75 switch_precision=0.0 accuracy=0.5
- `stage_provider_family@0.75` switch_recall=0.0 preserve_recall=1.0 switch_precision=None accuracy=0.6666666666666666
- `stage_provider_trace_count@0.25` switch_recall=0.5 preserve_recall=0.0 switch_precision=0.2 accuracy=0.16666666666666666
- `stage_provider_trace_count@0.5` switch_recall=0.0 preserve_recall=0.75 switch_precision=0.0 accuracy=0.5
- `stage_provider_trace_count@0.75` switch_recall=0.0 preserve_recall=1.0 switch_precision=None accuracy=0.6666666666666666
- `stage_provider_trace_source@0.25` switch_recall=0.5 preserve_recall=0.0 switch_precision=0.2 accuracy=0.16666666666666666
- `stage_provider_trace_source@0.5` switch_recall=0.0 preserve_recall=0.75 switch_precision=0.0 accuracy=0.5
- `stage_provider_trace_source@0.75` switch_recall=0.0 preserve_recall=1.0 switch_precision=None accuracy=0.6666666666666666
- `trace_source_profile@0.25` switch_recall=0.25 preserve_recall=0.0 switch_precision=0.1111111111111111 accuracy=0.08333333333333333
- `trace_source_profile@0.5` switch_recall=0.0 preserve_recall=0.75 switch_precision=0.0 accuracy=0.5
- `trace_source_profile@0.75` switch_recall=0.0 preserve_recall=1.0 switch_precision=None accuracy=0.6666666666666666
