# KRK Candidate-Generation Refresh Probe v2 After Labels

This reruns the non-causal candidate-generation refresh probe after merging the bounded capacity labels.

## Decision

- status: `candidate_generation_refresh_supported_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `design_candidate_generation_training_refresh_non_causal`

## Summary

- capacity_row_count: 28
- capacity_label_counts: `{'negative_capacity': 9, 'positive_capacity': 19}`
- best_non_oracle_policy: `stage_family_pure_positive_with_support_2`
- best_non_oracle_metrics: `{'row_count': 28, 'positive_count': 19, 'negative_count': 9, 'predicted_count': 14, 'true_positive': 14, 'false_positive': 0, 'false_negative': 5, 'true_negative': 9, 'positive_recall': 0.7368421052631579, 'positive_precision': 1.0, 'negative_suppression': 1.0, 'balanced_recall_risk': 0.868421052631579}`
- leave_stage_out_aggregate: `{'row_count': 28, 'positive_count': 19, 'negative_count': 9, 'predicted_count': 19, 'true_positive': 11, 'false_positive': 8, 'false_negative': 8, 'true_negative': 1, 'positive_recall': 0.5789473684210527, 'positive_precision': 0.5789473684210527, 'negative_suppression': 0.1111111111111111, 'balanced_recall_risk': 0.3450292397660819}`
