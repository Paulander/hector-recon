# KRK Selector Objective Benchmark v0

This artifact is non-causal. It does not train or authorize a runtime selector.

## Decision

- status: `selector_objective_benchmark_promising_non_causal`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `write_runtime_review_packet_not_implementation`

## Summary

- seed_row_count: `21`
- target_action_counts: `{'abstain_context_only': 5, 'prefer_visible_alternative': 5, 'preserve_selected_owner': 11}`
- benchmark_underpowered: `False`
- model_count: `8`
- runtime_feature_eligible_model_count: `6`
- promising_runtime_feature_model_count: `1`
- best_model: `combined_simple_rule`
- best_accuracy: `0.9523809523809523`
- best_safe_preservation_recall: `1.0`
- best_switch_contrast_recall: `0.8`
- best_abstain_recall: `1.0`
- offline_label_prediction_model_count: `0`
- runtime_feature_eligible_prediction_count: `126`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`
- seed_probe_status: `selector_objective_seed_probe_v2_ready_for_non_causal_benchmark`

## Models

- `majority_baseline` accuracy=0.5238095238095238 safe_recall=1.0 switch_recall=0.0 abstain_recall=0.0 runtime_feature_eligible=False
- `provider_prior` accuracy=0.47619047619047616 safe_recall=0.9090909090909091 switch_recall=0.0 abstain_recall=0.0 runtime_feature_eligible=True
- `stage_provider_family_prior` accuracy=0.7619047619047619 safe_recall=1.0 switch_recall=0.0 abstain_recall=1.0 runtime_feature_eligible=True
- `trace_context_feature_rule` accuracy=0.9047619047619048 safe_recall=1.0 switch_recall=0.6 abstain_recall=1.0 runtime_feature_eligible=True
- `proposal_count_positive_alternative_rule` accuracy=0.8571428571428571 safe_recall=1.0 switch_recall=0.4 abstain_recall=1.0 runtime_feature_eligible=True
- `combined_simple_rule` accuracy=0.9523809523809523 safe_recall=1.0 switch_recall=0.8 abstain_recall=1.0 runtime_feature_eligible=True
- `majority_baseline_leave_stage_out` accuracy=0.19047619047619047 safe_recall=0.36363636363636365 switch_recall=0.0 abstain_recall=0.0 runtime_feature_eligible=False
- `stage_provider_family_prior_leave_stage_out` accuracy=0.19047619047619047 safe_recall=0.36363636363636365 switch_recall=0.0 abstain_recall=0.0 runtime_feature_eligible=True
