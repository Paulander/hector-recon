# KRK Candidate Generator Coverage Audit v0

This is a non-causal audit of whether current proposal frames include protected providers with forced-provider conversion evidence.

## Summary

- `capacity_frame_count`: `16`
- `positive_capacity_count`: `11`
- `negative_capacity_count`: `5`
- `runtime_proposal_positive_recall_count`: `0`
- `runtime_proposal_negative_recall_count`: `0`
- `runtime_proposal_positive_recall_rate`: `0.0`
- `runtime_proposal_negative_recall_rate`: `0.0`
- `missing_positive_capacity_count`: `11`
- `stage7_row_count`: `0`
- `stage_family_counts`: `{'stage5': {'stage0_basin': 2, 'fence_established': 2, 'edge_trap': 3}, 'stage6': {'stage0_basin': 1, 'drive_to_edge': 1, 'fence_established': 1}, 'stage4': {'edge_trap': 6}}`
- `missing_positive_provider_family_counts`: `{'stage0_basin': 3, 'fence_established': 2, 'edge_trap': 6}`
- `missing_positive_source_stage_counts`: `{'stage5': 7, 'stage6': 1, 'stage4': 3}`

## Interpretation

- `primary_finding`: `The current proposal-frame export has zero recall for protected providers that converted under forced-provider capacity labels.`
- `architecture_implication`: `Selector work is premature unless the candidate/proposal set represents validated providers that can convert. This is a candidate-generation coverage gap, not a reason to patch Stage 7.`
- `still_non_causal`: `True`

## Missing Positive Examples

- state=`state.02feb8593cc6` stage=`stage5` provider=`krk.stage0_basin` forced_move=`b6c7` plies=`27` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- state=`state.02feb8593cc6` stage=`stage5` provider=`krk.fence_established` forced_move=`h7c7` plies=`15` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- state=`state.326222aefdf1` stage=`stage5` provider=`krk.stage0_basin` forced_move=`a6b7` plies=`27` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- state=`state.326222aefdf1` stage=`stage5` provider=`krk.fence_established` forced_move=`h7c7` plies=`37` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- state=`state.3dca34326fca` stage=`stage5` provider=`krk.edge_trap_close` forced_move=`h7d7` plies=`31` existing_frame_providers=`['krk.stage0_basin']`
- state=`state.3dca34326fca` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` forced_move=`h7d7` plies=`31` existing_frame_providers=`['krk.stage0_basin']`
- state=`state.3dca34326fca` stage=`stage5` provider=`krk.edge_trap_enemy_between` forced_move=`h7b7` plies=`31` existing_frame_providers=`['krk.stage0_basin']`
- state=`state.699f0003a511` stage=`stage6` provider=`krk.stage0_basin` forced_move=`a5b6` plies=`27` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- state=`state.256a3da30f0f` stage=`stage4` provider=`krk.edge_trap_close` forced_move=`d6d5` plies=`9` existing_frame_providers=`['krk.stage0_basin']`
- state=`state.256a3da30f0f` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` forced_move=`d6d5` plies=`9` existing_frame_providers=`['krk.stage0_basin']`
- state=`state.256a3da30f0f` stage=`stage4` provider=`krk.edge_trap_enemy_between` forced_move=`d6d5` plies=`9` existing_frame_providers=`['krk.stage0_basin']`

## Decision

- `status`: `candidate_generator_recall_gap_confirmed`
- `recommended_next_step`: `design_non_causal_validated_provider_candidate_set_audit`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
