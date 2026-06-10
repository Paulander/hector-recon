# KRK Candidate-Generation Refresh Probe v2

This probe evaluates non-causal candidate-generation policies over protected capacity rows from dataset v2. It is not selector training.

## Decision

- status: `candidate_generation_refresh_underpowered_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `collect_more_protected_capacity_or_explicit_ownership_labels`

## Summary

- capacity_row_count: 16
- capacity_label_counts: `{'negative_capacity': 5, 'positive_capacity': 11}`
- source_stage_counts: `{'stage4': 6, 'stage5': 7, 'stage6': 3}`
- candidate_family_counts: `{'drive_to_edge': 1, 'edge_trap': 9, 'fence_established': 3, 'stage0_basin': 3}`
- best_non_oracle_policy: `stage_family_pure_positive_with_support_2`
- best_non_oracle_metrics: `{'row_count': 16, 'positive_count': 11, 'negative_count': 5, 'predicted_count': 7, 'true_positive': 7, 'false_positive': 0, 'false_negative': 4, 'true_negative': 5, 'positive_recall': 0.6363636363636364, 'positive_precision': 1.0, 'negative_suppression': 1.0, 'balanced_recall_risk': 0.8181818181818181}`
- leave_stage_out_aggregate: `{'row_count': 16, 'positive_count': 11, 'negative_count': 5, 'predicted_count': 13, 'true_positive': 9, 'false_positive': 4, 'false_negative': 2, 'true_negative': 1, 'positive_recall': 0.8181818181818182, 'positive_precision': 0.6923076923076923, 'negative_suppression': 0.2, 'balanced_recall_risk': 0.5090909090909091}`

## Policies

- `emit_all_capacity_candidates`: recall=`1.000` precision=`0.688` negative_suppression=`0.000` balanced=`0.500`
- `family_positive_rate_at_least_half`: recall=`1.000` precision=`0.733` negative_suppression=`0.200` balanced=`0.600`
- `family_pure_positive_with_support_2`: recall=`0.273` precision=`1.000` negative_suppression=`1.000` balanced=`0.636`
- `stage_family_positive_rate_at_least_half`: recall=`1.000` precision=`0.786` negative_suppression=`0.400` balanced=`0.700`
- `stage_family_pure_positive_with_support_2`: recall=`0.636` precision=`1.000` negative_suppression=`1.000` balanced=`0.818`
- `oracle_positive_capacity_ceiling`: recall=`1.000` precision=`1.000` negative_suppression=`1.000` balanced=`1.000`

## Boundary

These are candidate-generation recall/risk policies. Capacity labels remain offline evidence and are not ownership-selector labels.
