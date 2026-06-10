# KRK Ownership Selection Feature Probe v1

Non-causal probe over expanded normal-routing ownership-selection labels.

## Summary

- `row_count`: `34`
- `state_count`: `34`
- `positive_owner_count`: `25`
- `negative_owner_count`: `9`
- `source_stage_counts`: `{'stage4': 15, 'stage5': 11, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 31, 'edge_trap': 3}`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Best Result

`{'objective': 'stage_provider_family@0.75', 'features': ['source_stage', 'provider_family'], 'row_count': 34, 'threshold': 0.75, 'true_positive': 14, 'false_positive': 4, 'true_negative': 5, 'false_negative': 11, 'accuracy': 0.5588235294117647, 'positive_precision': 0.7777777777777778, 'positive_recall': 0.56, 'negative_suppression': 0.5555555555555556}`

## Decision

- `status`: `ownership_selection_signal_underpowered`
- `recommended_next_step`: `review_split_objective_readiness_with_expanded_ownership_labels`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
