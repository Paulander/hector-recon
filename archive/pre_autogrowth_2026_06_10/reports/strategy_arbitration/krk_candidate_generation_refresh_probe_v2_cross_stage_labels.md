# KRK Candidate-Generation Refresh Probe v2 Cross-Stage Labels

This reruns the non-causal candidate-generation refresh probe after merging cross-stage capacity labels.

## Decision

- status: `candidate_generation_refresh_supported_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `design_candidate_generation_training_refresh_non_causal`

## Summary

- capacity_row_count: 36
- capacity_label_counts: `{'negative_capacity': 10, 'positive_capacity': 26}`
- best_non_oracle_policy: `stage_family_pure_positive_with_support_2`
- best_non_oracle_metrics: `{'row_count': 36, 'positive_count': 26, 'negative_count': 10, 'predicted_count': 20, 'true_positive': 20, 'false_positive': 0, 'false_negative': 6, 'true_negative': 10, 'positive_recall': 0.7692307692307693, 'positive_precision': 1.0, 'negative_suppression': 1.0, 'balanced_recall_risk': 0.8846153846153846}`
- leave_stage_out_aggregate: `{'row_count': 36, 'positive_count': 26, 'negative_count': 10, 'predicted_count': 24, 'true_positive': 15, 'false_positive': 9, 'false_negative': 11, 'true_negative': 1, 'positive_recall': 0.5769230769230769, 'positive_precision': 0.625, 'negative_suppression': 0.1, 'balanced_recall_risk': 0.3384615384615384}`
