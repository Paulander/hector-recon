# KRK State-Local Paired Ownership Review v0

Final non-causal review for the paired ownership work package.

## Summary

- `inventory_pair_count`: `40`
- `inventory_state_count`: `14`
- `same_state_conflict_pair_count`: `9`
- `selected_failure_with_alternative_success_count`: `7`
- `safe_preservation_pair_count`: `23`
- `stage7_row_count`: `0`
- `inventory_ready`: `True`
- `best_balanced_objective`: `owner_family_pair@0.25`
- `prefer_capacity_recall`: `0.8571428571428571`
- `selected_preservation_recall`: `0.76`
- `safe_preservation_recall`: `0.7391304347826086`
- `strong_conflict_accuracy`: `0.8888888888888888`

## Interpretation

- Replay-free extraction now satisfies the pair-count and same-state-conflict thresholds, so no bounded h40 expansion was needed.
- The paired objective is better aligned with the architecture than global provider-row classification because it keeps selected ownership and forced capacity in separate channels.
- The current simple family/context feature model still over-selects capacity alternatives in safe-preservation cases; this blocks runtime work.
- The next improvement should target safe-preservation features or pair-specific feature interactions, not more blind label collection.

## Decision

- `status`: `feature_model_insufficient`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `design_stronger_safe_preservation_features_before_runtime`
