# KRK Selector Directed Fix Review v0

This review consolidates the non-causal evidence for a directed selector-side fix.

## Evidence Summary

- `candidate_generation_gap`: `{'current_positive_capacity_recall': 0.0, 'expanded_positive_capacity_recall': 1.0, 'expanded_negative_capacity_inclusion': 1.0, 'interpretation': 'Validated-provider candidate expansion fixes recall but includes hard negatives.'}`
- `selector_negative_gap`: `{'training_positive_count': 9, 'training_negative_count': 3, 'training_negative_state_count': 1, 'best_negative_suppression': 0.0, 'interpretation': 'Current selector evidence cannot suppress negatives; negatives are sparse and concentrated.'}`
- `geometry_gap`: `{'best_geometry_objective': 'provider_family', 'best_geometry_negative_suppression': 0.0, 'geometry_underpowered': True, 'interpretation': 'Simple geometry terms alone do not fix suppression on current data.'}`

## Rejected Fixes

- `runtime_selector_now`: selection negative suppression is 0.0 in current probes
- `runtime_candidate_generator_now`: candidate expansion includes negative-capacity providers and needs selection semantics
- `train_selector_on_forced_capacity_as_positive`: forced-provider capacity is not a direct runtime ownership label
- `add_simple_geometry_terms_only`: geometry feature probe still has 0.0 negative suppression
- `return_to_stage7_patch`: Stage 7 is held-out boundary evidence, not the current training target

## Directed Fix Requirements

- `keep candidate generation and selection as separate channels`
- `create a hard-negative selector target dataset from protected capacity negatives`
- `keep forced-capacity labels distinct from selected-playout labels`
- `add move/post-move geometry only as non-causal scoring features`
- `evaluate leave-state-out suppression before any sandbox`
- `keep Stage 7 held out`

## Recommended Fix Class

- Name: `non_causal_hard_negative_selector_target_design`
- Description: Build a reviewed selector benchmark that uses protected capacity negatives as hard-negative evaluation/training candidates only after preserving label semantics, and adds geometry/post-move features to test suppression.

## Decision

- `status`: `directed_fix_review_complete_runtime_blocked`
- `recommended_next_step`: `design_hard_negative_selector_target_dataset_v0`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
