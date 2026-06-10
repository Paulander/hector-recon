# KRK Validated Provider Candidate Set Audit v0

This is a non-causal audit of a possible validated-provider candidate-set expansion. It does not implement runtime candidate generation.

## Policy

- Name: `validated_provider_pack_candidates_for_protected_contexts`
- Runtime default: `not_implemented`

## Summary

- `state_count`: `6`
- `added_candidate_count`: `16`
- `added_positive_capacity_count`: `11`
- `added_negative_capacity_count`: `5`
- `positive_capacity_recall_if_included`: `1.0`
- `negative_capacity_inclusion_rate`: `0.3125`
- `stage7_row_count`: `0`
- `source_stage_counts`: `{'stage5': 7, 'stage6': 3, 'stage4': 6}`
- `provider_family_counts`: `{'stage0_basin': 3, 'fence_established': 3, 'edge_trap': 9, 'drive_to_edge': 1}`

## Interpretation

- `benefit`: `A validated-provider candidate-set expansion would recover the currently missing protected positive-capacity providers.`
- `risk`: `The same expansion also introduces negative-capacity providers; candidate generation cannot replace selection/scoring.`
- `architecture_split`: `Treat candidate generation and strategy selection as separate non-causal evidence tracks before runtime work.`

## State Summaries

- state=`state.02feb8593cc6` stage=`stage5` added=`['krk.fence_established', 'krk.stage0_basin']` positive=`2` negative=`0`
- state=`state.256a3da30f0f` stage=`stage4` added=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']` positive=`3` negative=`0`
- state=`state.326222aefdf1` stage=`stage5` added=`['krk.fence_established', 'krk.stage0_basin']` positive=`2` negative=`0`
- state=`state.3dca34326fca` stage=`stage5` added=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']` positive=`3` negative=`0`
- state=`state.699f0003a511` stage=`stage6` added=`['krk.drive_to_edge', 'krk.fence_established', 'krk.stage0_basin']` positive=`1` negative=`2`
- state=`state.b11124d658cf` stage=`stage4` added=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']` positive=`0` negative=`3`

## Decision

- `status`: `validated_provider_candidate_set_recall_promising_requires_selector_semantics`
- `recommended_next_step`: `design_two_stage_candidate_generation_and_selection_review`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
