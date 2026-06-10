# KRK Hard-Negative Selector Target Dataset v0

This dataset packages protected capacity labels and geometry features as non-causal selector target candidates. It does not authorize selector training.

## Summary

- `row_count`: `16`
- `target_kind_counts`: `{'positive_capacity_context': 11, 'hard_negative_capacity': 5}`
- `source_stage_counts`: `{'stage5': 7, 'stage6': 3, 'stage4': 6}`
- `provider_family_counts`: `{'stage0_basin': 3, 'fence_established': 3, 'edge_trap': 9, 'drive_to_edge': 1}`
- `stage7_row_count`: `0`
- `training_row_count`: `0`
- `state_count`: `6`

## Rows

- state=`state.02feb8593cc6` target=`positive_capacity_context` provider=`krk.stage0_basin` move=`b6c7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.02feb8593cc6` target=`positive_capacity_context` provider=`krk.fence_established` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.326222aefdf1` target=`positive_capacity_context` provider=`krk.stage0_basin` move=`a6b7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.326222aefdf1` target=`positive_capacity_context` provider=`krk.fence_established` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.3dca34326fca` target=`positive_capacity_context` provider=`krk.edge_trap_close` move=`h7d7` piece=`rook` king_delta=`0` rook_delta=`-4`
- state=`state.3dca34326fca` target=`positive_capacity_context` provider=`krk.edge_trap_wrong_tempo` move=`h7d7` piece=`rook` king_delta=`0` rook_delta=`-4`
- state=`state.3dca34326fca` target=`positive_capacity_context` provider=`krk.edge_trap_enemy_between` move=`h7b7` piece=`rook` king_delta=`0` rook_delta=`-6`
- state=`state.699f0003a511` target=`positive_capacity_context` provider=`krk.stage0_basin` move=`a5b6` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.699f0003a511` target=`hard_negative_capacity` provider=`krk.drive_to_edge` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.699f0003a511` target=`hard_negative_capacity` provider=`krk.fence_established` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.256a3da30f0f` target=`positive_capacity_context` provider=`krk.edge_trap_close` move=`d6d5` piece=`king` king_delta=`0` rook_delta=`0`
- state=`state.256a3da30f0f` target=`positive_capacity_context` provider=`krk.edge_trap_wrong_tempo` move=`d6d5` piece=`king` king_delta=`0` rook_delta=`0`
- state=`state.256a3da30f0f` target=`positive_capacity_context` provider=`krk.edge_trap_enemy_between` move=`d6d5` piece=`king` king_delta=`0` rook_delta=`0`
- state=`state.b11124d658cf` target=`hard_negative_capacity` provider=`krk.edge_trap_close` move=`c8c7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.b11124d658cf` target=`hard_negative_capacity` provider=`krk.edge_trap_wrong_tempo` move=`c8c7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.b11124d658cf` target=`hard_negative_capacity` provider=`krk.edge_trap_enemy_between` move=`c8c7` piece=`king` king_delta=`-1` rook_delta=`0`

## Decision

- `status`: `hard_negative_selector_target_candidates_built`
- `recommended_next_step`: `review_hard_negative_target_training_semantics`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
