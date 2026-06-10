# KRK Selector Objective Feature Probe v2

This is a non-causal feature probe over the v2 seed manifest. It does not train or authorize a selector.

## Decision

- status: `selector_objective_feature_probe_v2_review_ready`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `review_selector_objective_feature_probe_v2_before_any_runtime_design`

## Summary

- seed_row_count: `21`
- target_action_counts: `{'abstain': 5, 'preserve': 11, 'switch': 5}`
- runtime_feature_model_count: `26`
- runtime_threshold_passing_model_count: `1`
- best_runtime_model: `visible_failure_risk_heuristic_v2`
- best_runtime_accuracy: `0.9523809523809523`
- best_runtime_switch_precision: `1.0`
- best_runtime_switch_recall: `0.8`
- best_runtime_preserve_recall: `1.0`
- best_runtime_abstain_recall: `1.0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Passing Runtime-Visible Probe Models

- `visible_failure_risk_heuristic_v2` accuracy=0.9523809523809523 switch_precision=1.0 switch_recall=0.8 preserve_recall=1.0 abstain_recall=1.0

## Interpretation

- feature_probe_ready_for_review: `True`
- selector_training_supported: `False`
- runtime_selector_supported: `False`
- independent_validation_required_before_runtime: `True`
- offline_semantics_confirmed: `True`
- capacity_labels_are_not_ownership_labels: `True`
- reason: `Feature probe v2 summarizes runtime-visible non-causal models only. It does not train or authorize a selector and does not use ownership labels as runtime features.`
