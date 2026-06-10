# KRK State-Local Paired Ownership Probe v0

Non-causal leave-state-out probe over state-local owner pairs.

## Summary

- `row_count`: `32`
- `state_count`: `13`
- `prefer_capacity_count`: `7`
- `preserve_selected_count`: `25`
- `safe_preservation_pair_count`: `23`
- `strong_conflict_pair_count`: `9`
- `stage7_row_count`: `0`
- `inventory_ready`: `True`

## Best Result

- `objective`: `owner_family_pair@0.25`
- `features`: `['owner_a_family', 'owner_b_family']`
- `row_count`: `32`
- `threshold`: `0.25`
- `true_positive`: `6`
- `false_positive`: `6`
- `true_negative`: `19`
- `false_negative`: `1`
- `accuracy`: `0.78125`
- `prefer_capacity_precision`: `0.5`
- `prefer_capacity_recall`: `0.8571428571428571`
- `selected_preservation_recall`: `0.76`
- `strong_conflict_accuracy`: `0.8888888888888888`
- `safe_preservation_recall`: `0.7391304347826086`

## Best Balanced Result

- `objective`: `owner_family_pair@0.25`
- `features`: `['owner_a_family', 'owner_b_family']`
- `row_count`: `32`
- `threshold`: `0.25`
- `true_positive`: `6`
- `false_positive`: `6`
- `true_negative`: `19`
- `false_negative`: `1`
- `accuracy`: `0.78125`
- `prefer_capacity_precision`: `0.5`
- `prefer_capacity_recall`: `0.8571428571428571`
- `selected_preservation_recall`: `0.76`
- `strong_conflict_accuracy`: `0.8888888888888888`
- `safe_preservation_recall`: `0.7391304347826086`

## Decision

- `status`: `paired_objective_feature_model_insufficient`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `review_paired_objective_before_any_runtime_work`
