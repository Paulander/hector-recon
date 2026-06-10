# Stage 7 State-Local Contrast Audit

This audit is offline-only and non-causal. It checks whether existing visible terms separate positives from hard negatives inside each state.

## Status

- Candidate status: `state_local_single_terms_available`
- Recommended next step: non-causal visible term refinement audit before any runtime patch
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Summary

- Step count: `195`
- Diagnosis counts: `{'term_interactions_separate_positive_from_hard_negative': 44, 'visible_terms_collide_with_hard_negatives': 22, 'single_terms_separate_positive_from_hard_negative': 129}`
- Separability rates: `{'single_term_rate': 0.6615384615384615, 'single_or_pair_term_rate': 0.8871794871794871, 'collision_rate': 0.11282051282051282}`

## Top Positive-Unique Terms

- `post_move_terms.white_king_file_opposition_distance_two_after_move`: 50
- `post_move_terms.box_area_decreases_after_move`: 45
- `move_shape_terms.rook_transfer_vertical`: 32
- `post_move_terms.black_king_escape_count_decreases_after_move`: 20
- `move_shape_terms.rook_to_edge_rank`: 16
- `move_shape_terms.king_moves_toward_enemy`: 15
- `post_move_terms.white_king_distance_to_enemy_decreases`: 15
- `post_move_terms.white_king_distance_to_rook_decreases`: 12
- `move_shape_terms.rook_to_checking_line`: 10
- `move_shape_terms.safe_check_created`: 10
- `post_move_terms.checking_line_created`: 10
- `post_move_terms.box_area_not_increased_after_move`: 10

## Top Hard-Negative-Unique Terms

- `move_shape_terms.rook_to_edge_file`: 174
- `move_shape_terms.rook_to_edge_rank`: 152
- `move_shape_terms.rook_to_checking_line`: 144
- `move_shape_terms.safe_check_created`: 144
- `post_move_terms.checking_line_created`: 144
- `move_shape_terms.rook_lateral_transfer`: 141
- `move_shape_terms.rook_destination_far_from_enemy`: 131
- `move_shape_terms.candidate_is_rook_transfer`: 112
- `move_shape_terms.rook_transfer_vertical`: 108
- `move_shape_terms.king_moves_toward_rook_support`: 107
- `post_move_terms.white_king_and_rook_split_rank_side_after_move`: 93
- `post_move_terms.white_king_and_rook_split_file_side_after_move`: 84

## Top Positive-Unique Term Pairs

- `move_shape_terms.candidate_is_king_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: 50
- `move_shape_terms.rook_destination_not_adjacent_enemy` + `post_move_terms.box_area_decreases_after_move`: 46
- `move_shape_terms.rook_destination_not_adjacent_enemy` + `post_move_terms.box_area_not_increased_after_move`: 45
- `move_shape_terms.candidate_is_rook_move` + `post_move_terms.box_area_decreases_after_move`: 45
- `move_shape_terms.candidate_is_rook_move` + `post_move_terms.box_area_not_increased_after_move`: 44
- `piece.K` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: 41
- `post_move_terms.black_king_escape_count_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: 40
- `move_shape_terms.rook_destination_far_from_enemy` + `post_move_terms.black_king_escape_count_not_increased_after_move`: 36
- `post_move_terms.box_area_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: 34
- `post_move_terms.enemy_corner_distance_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: 34
- `post_move_terms.enemy_edge_distance_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: 34
- `post_move_terms.rook_safe_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: 34

## Sample Rows

- traj 0 step 0: `term_interactions_separate_positive_from_hard_negative`, positive_unique=[]
- traj 0 step 1: `term_interactions_separate_positive_from_hard_negative`, positive_unique=[]
- traj 0 step 2: `visible_terms_collide_with_hard_negatives`, positive_unique=[]
- traj 0 step 3: `single_terms_separate_positive_from_hard_negative`, positive_unique=['move_shape_terms.king_moves_toward_rook_support']
- traj 0 step 4: `term_interactions_separate_positive_from_hard_negative`, positive_unique=[]
- traj 0 step 5: `single_terms_separate_positive_from_hard_negative`, positive_unique=['move_shape_terms.rook_to_checking_line', 'move_shape_terms.safe_check_created', 'post_move_terms.checking_line_created', 'post_move_terms.cut_created_after_move', 'post_move_terms.fence_exists_after_move']
- traj 0 step 6: `term_interactions_separate_positive_from_hard_negative`, positive_unique=[]
- traj 0 step 7: `single_terms_separate_positive_from_hard_negative`, positive_unique=['move_shape_terms.rook_to_checking_line', 'move_shape_terms.safe_check_created', 'post_move_terms.checking_line_created', 'post_move_terms.cut_created_after_move', 'post_move_terms.fence_exists_after_move']

## Blocked Next Steps

- runtime_repair
- stage7_promotion
- stage8_training
- support_adapter
- score_bonus_or_provider_penalty
- runtime_dtm_or_tablebase
- gameplay_topology_mutation
