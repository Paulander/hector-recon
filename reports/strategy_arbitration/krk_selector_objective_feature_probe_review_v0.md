# KRK Selector Objective Feature Probe Review v0

This review interprets the non-causal selector-objective feature probe. It does not authorize selector training or runtime behavior.

## Decision

- status: `selector_feature_probe_blocks_runtime_needs_diverse_evidence`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `collect_more_diverse_joined_trace_ownership_evidence`

## Summary

- seed_row_count: `12`
- target_channel_counts: `{'candidate_switch_contrast_seed': 4, 'safe_preservation_contrast_seed': 8}`
- runtime_threshold_passing_model_count: `0`
- best_switch_model: `selected_provider_family@0.25`
- best_switch_recall: `0.75`
- best_switch_preserve_recall: `0.0`
- best_switch_precision: `0.2727272727272727`
- best_preserve_model: `positive_trace_count_bucket@0.5`
- best_preserve_recall: `1.0`
- best_preserve_switch_recall: `0.5`
- best_precision_model: `positive_trace_count_bucket@0.5`
- best_precision: `1.0`
- best_precision_switch_recall: `0.5`
- offline_oracle_accuracy: `1.0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Blockers

- `simple_visible_features_do_not_pass_switch_and_preserve_thresholds`
- `best_switch_recall_models_overfire_and_destroy_preservation`
- `best_preservation_models_miss_too_many_switch_cases`
- `offline_outcome_oracle_is_not_runtime_feature_eligible`
- `seed_set_is_still_provider_family_narrow`

## Recommended Evidence

- `more_selected_failure_with_visible_positive_alternative_rows`
- `more_non_stage0_selected_owner_rows`
- `more_stage5_6_failure_rows_if_available`
- `separate_stage4_scope_review_if_stage4_rows_are_needed`
- `visible_progress_window_features_that_do_not_use_outcome_labels`
