# KRK Capacity Geometry Feature Audit v0

This replay-free audit computes simple visible geometry terms for protected capacity labels.

## Summary

- `row_count`: `16`
- `capacity_label_counts`: `{'positive_capacity': 11, 'negative_capacity': 5}`
- `source_stage_counts`: `{'stage5': 7, 'stage6': 3, 'stage4': 6}`
- `provider_family_counts`: `{'stage0_basin': 3, 'fence_established': 3, 'edge_trap': 9, 'drive_to_edge': 1}`
- `forced_piece_type_by_label`: `{'positive_capacity': {'king': 6, 'rook': 5}, 'negative_capacity': {'rook': 2, 'king': 3}}`
- `term_true_counts_by_label`: `{'king_moves_toward_black': {'positive_capacity': 3, 'negative_capacity': 3}, 'king_moves_away_from_black': {'positive_capacity': 0, 'negative_capacity': 0}, 'rook_moves_toward_black': {'positive_capacity': 3, 'negative_capacity': 0}, 'rook_moves_away_from_black': {'positive_capacity': 2, 'negative_capacity': 2}, 'rook_same_file_as_black_after': {'positive_capacity': 1, 'negative_capacity': 0}, 'rook_same_rank_as_black_after': {'positive_capacity': 0, 'negative_capacity': 0}}`
- `black_king_edge_distance_values_by_label`: `{'positive_capacity': [0], 'negative_capacity': [0]}`
- `stage7_row_count`: `0`

## Rows

- state=`state.02feb8593cc6` label=`positive_capacity` provider=`krk.stage0_basin` move=`b6c7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.02feb8593cc6` label=`positive_capacity` provider=`krk.fence_established` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.326222aefdf1` label=`positive_capacity` provider=`krk.stage0_basin` move=`a6b7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.326222aefdf1` label=`positive_capacity` provider=`krk.fence_established` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.3dca34326fca` label=`positive_capacity` provider=`krk.edge_trap_close` move=`h7d7` piece=`rook` king_delta=`0` rook_delta=`-4`
- state=`state.3dca34326fca` label=`positive_capacity` provider=`krk.edge_trap_wrong_tempo` move=`h7d7` piece=`rook` king_delta=`0` rook_delta=`-4`
- state=`state.3dca34326fca` label=`positive_capacity` provider=`krk.edge_trap_enemy_between` move=`h7b7` piece=`rook` king_delta=`0` rook_delta=`-6`
- state=`state.699f0003a511` label=`positive_capacity` provider=`krk.stage0_basin` move=`a5b6` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.699f0003a511` label=`negative_capacity` provider=`krk.drive_to_edge` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.699f0003a511` label=`negative_capacity` provider=`krk.fence_established` move=`h7c7` piece=`rook` king_delta=`0` rook_delta=`1`
- state=`state.256a3da30f0f` label=`positive_capacity` provider=`krk.edge_trap_close` move=`d6d5` piece=`king` king_delta=`0` rook_delta=`0`
- state=`state.256a3da30f0f` label=`positive_capacity` provider=`krk.edge_trap_wrong_tempo` move=`d6d5` piece=`king` king_delta=`0` rook_delta=`0`
- state=`state.256a3da30f0f` label=`positive_capacity` provider=`krk.edge_trap_enemy_between` move=`d6d5` piece=`king` king_delta=`0` rook_delta=`0`
- state=`state.b11124d658cf` label=`negative_capacity` provider=`krk.edge_trap_close` move=`c8c7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.b11124d658cf` label=`negative_capacity` provider=`krk.edge_trap_wrong_tempo` move=`c8c7` piece=`king` king_delta=`-1` rook_delta=`0`
- state=`state.b11124d658cf` label=`negative_capacity` provider=`krk.edge_trap_enemy_between` move=`c8c7` piece=`king` king_delta=`-1` rook_delta=`0`

## Interpretation

- `primary`: `Simple geometry gives useful diagnostics but does not fully separate positive and negative capacity.`
- `notable_pattern`: `Several positive and negative rows share edge-distance and provider-family contexts; selector features need move/post-move geometry and same-state alternatives, not just provider family or normalized score.`
- `directed_fix_class`: `non_causal_geometry_augmented_selector_feature_benchmark`

## Decision

- `status`: `geometry_terms_partially_informative_not_sufficient`
- `recommended_next_step`: `add_geometry_terms_to_non_causal_selector_feature_benchmark`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
