# KRK Hard-Negative Label Semantics Review v1

This review separates forced-provider capacity evidence from runtime ownership evidence.

## Summary

- `row_count`: `40`
- `state_count`: `14`
- `capacity_positive_count`: `31`
- `capacity_negative_count`: `9`
- `capacity_negative_state_count`: `4`
- `state_local_contrast_state_count`: `2`
- `stage7_row_count`: `0`
- `source_channel_counts`: `{'protected_provider_capacity_v0': 16, 'balanced_protected_hard_negative_capacity': 24}`
- `label_by_source_channel`: `{'balanced_protected_hard_negative_capacity': {'capacity_positive': 20, 'capacity_negative': 4}, 'protected_provider_capacity_v0': {'capacity_positive': 11, 'capacity_negative': 5}}`
- `best_ablation_negative_suppression`: `0.2222222222222222`
- `best_ablation_positive_recall`: `1.0`

## Semantics

- `forced_provider_capacity_label` allowed=`candidate_capacity_evidence_and_offline_feature_probe` blocked=`direct_runtime_owner_selection_or_suppression`. The labels force a provider for the first White move and then release. A mate result shows the provider can participate in conversion under that intervention; a max_plies result shows this forced path failed, not that the provider is always unsafe.
- `state_local_capacity_contrast` allowed=`learn comparisons only within states or matched state families` blocked=`global provider-family suppression`. The same provider family can be positive in one protected state and negative in another. Global labels would over-suppress validated providers.
- `hard_negative_capacity` allowed=`offline risk feature and hard-negative mining` blocked=`selector training target until safe-owner preservation is separately validated`. The current hard-negative support is still sparse: nine rows across four states.

## Objective Split

- `capacity_recall_objective`: which validated providers should be present in candidate set
- `capacity_risk_objective`: which forced-provider paths are risky under current h40 continuation
- `ownership_selection_objective`: which provider should own normal runtime decision; not supplied by this dataset alone
- `safe_preservation_objective`: validated safe owners must be preserved before any suppression can be reviewed

## Decision

- `status`: `capacity_labels_not_direct_selector_targets`
- `recommended_next_step`: `run_stronger_capacity_risk_feature_review_non_causal`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
