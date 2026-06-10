# KRK Selector Objective Independent Validation Blocker v0

This review closes the current selector-objective validation slice. It does not authorize runtime selector work.

## Decision

- status: `selector_objective_runtime_blocked_pending_independent_switch_contrasts`
- selector_allowed: `False`
- selector_training_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `targeted_stage4_failure_discovery_or_keep_selector_blocked`

## Evidence Summary

- validation_status: `selector_objective_independent_validation_underpowered`
- label_count: `10`
- target_counts: `{'preserve': 10}`
- prediction_counts: `{'preserve': 10}`
- accuracy: `1.0`
- switch_recall: `0.0`
- preserve_recall: `1.0`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`

## Blocker

- runtime_selector_blocked: `True`
- blocker_class: `independent_switch_contrast_absent`
- why: `The independent bounded protected slice validated safe preservation only; it produced no selected-owner failure/switch rows, so switch recall cannot be independently validated.`

## Recommended Next Evidence

- `targeted protected selected-owner failure discovery from Stage 4 caveat cases`
- `normal-routing failure rows with visible competing proposal evidence`
- `paired switch-vs-preserve rows that exclude current benchmark seed states`

## Explicitly Forbidden

- `runtime_selector`
- `selector_training`
- `score_changes`
- `provider_suppression`
- `direct_provider_routing`
- `capacity_labels_as_ownership_labels`
- `stage7_training_or_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
