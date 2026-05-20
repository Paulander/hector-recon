# KRK Ownership Selection Feature Probe v0

Non-causal probe over recovered normal-routing ownership-selection labels.

## Summary

- `row_count`: `14`
- `state_count`: `14`
- `positive_owner_count`: `9`
- `negative_owner_count`: `5`
- `source_stage_counts`: `{'stage4': 5, 'stage5': 5, 'stage6': 4}`
- `provider_family_counts`: `{'stage0_basin': 11, 'edge_trap': 3}`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Best Result

`{'objective': 'raw_score_bucket@0.5', 'features': ['raw_score_bucket'], 'row_count': 14, 'threshold': 0.5, 'true_positive': 9, 'false_positive': 2, 'true_negative': 3, 'false_negative': 0, 'accuracy': 0.8571428571428571, 'positive_precision': 0.8181818181818182, 'positive_recall': 1.0, 'negative_suppression': 0.6}`

## Decision

- `status`: `ownership_selection_probe_promising_underpowered`
- `recommended_next_step`: `review_split_objective_readiness_with_recovered_ownership_labels`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
