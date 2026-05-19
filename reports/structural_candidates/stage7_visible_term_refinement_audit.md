# Stage 7 Visible-Term Refinement Audit

This audit is replay-free and non-causal. It derives visible-term refinement hypotheses from the ranking calibration and state-local contrast artifacts.

## Status

- Candidate status: `visible_term_refinement_candidates_non_causal`
- Recommended next step: architecture review or offline benchmark before any visible-term sandbox
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Summary

- Dataset: `{'step_count': 195, 'term_count': 36, 'ranking_candidate_status': 'term_collision_and_state_local_ranking_gap', 'state_local_candidate_status': 'state_local_single_terms_available'}`
- Positive term kind counts: `{'king_support': 14, 'box_progress': 2, 'rook_geometry': 4, 'other': 2, 'cut_fence_line': 3}`
- Interaction kind counts: `{'king_support': 3, 'box_progress+rook_geometry': 10, 'king_support+other': 1, 'king_support+rook_geometry': 4, 'box_progress+king_support': 1, 'edge_net_pressure+king_support': 2, 'rook_geometry': 4}`
- Positive terms requiring companion scope: `6`

## Positive-Term Refinement Candidates

- `post_move_terms.white_king_file_opposition_distance_two_after_move` (king_support): state_local=50, pos=66, hard_neg=189, status=`candidate_positive_term_requires_companion_scope`
- `post_move_terms.box_area_decreases_after_move` (box_progress): state_local=45, pos=182, hard_neg=508, status=`candidate_positive_term_requires_companion_scope`
- `move_shape_terms.rook_transfer_vertical` (rook_geometry): state_local=32, pos=193, hard_neg=807, status=`candidate_positive_term_weak_global_support`
- `post_move_terms.black_king_escape_count_decreases_after_move` (king_support): state_local=20, pos=165, hard_neg=249, status=`candidate_positive_term_requires_companion_scope`
- `move_shape_terms.rook_to_edge_rank` (rook_geometry): state_local=16, pos=43, hard_neg=722, status=`candidate_positive_term_weak_global_support`
- `move_shape_terms.king_moves_toward_enemy` (king_support): state_local=15, pos=99, hard_neg=54, status=`candidate_positive_term_requires_companion_scope`
- `post_move_terms.white_king_distance_to_enemy_decreases` (king_support): state_local=15, pos=99, hard_neg=54, status=`candidate_positive_term_requires_companion_scope`
- `post_move_terms.white_king_distance_to_rook_decreases` (king_support): state_local=12, pos=159, hard_neg=730, status=`candidate_positive_term_weak_global_support`
- `move_shape_terms.rook_to_checking_line` (king_support): state_local=10, pos=35, hard_neg=191, status=`candidate_positive_term_weak_global_support`
- `move_shape_terms.safe_check_created` (other): state_local=10, pos=35, hard_neg=191, status=`candidate_positive_term_weak_global_support`
- `post_move_terms.checking_line_created` (king_support): state_local=10, pos=35, hard_neg=191, status=`candidate_positive_term_weak_global_support`
- `post_move_terms.box_area_not_increased_after_move` (box_progress): state_local=10, pos=353, hard_neg=1495, status=`candidate_positive_term_weak_global_support`

## Interaction Candidates

- `move_shape_terms.candidate_is_king_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: count=50, status=`candidate_interaction_scopes_ambiguous_terms`
- `move_shape_terms.rook_destination_not_adjacent_enemy` + `post_move_terms.box_area_decreases_after_move`: count=46, status=`candidate_interaction_scopes_ambiguous_terms`
- `move_shape_terms.rook_destination_not_adjacent_enemy` + `post_move_terms.box_area_not_increased_after_move`: count=45, status=`candidate_interaction_positive_context`
- `move_shape_terms.candidate_is_rook_move` + `post_move_terms.box_area_decreases_after_move`: count=45, status=`candidate_interaction_scopes_ambiguous_terms`
- `move_shape_terms.candidate_is_rook_move` + `post_move_terms.box_area_not_increased_after_move`: count=44, status=`candidate_interaction_positive_context`
- `piece.K` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: count=41, status=`candidate_interaction_scopes_ambiguous_terms`
- `post_move_terms.black_king_escape_count_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: count=40, status=`candidate_interaction_scopes_ambiguous_terms`
- `move_shape_terms.rook_destination_far_from_enemy` + `post_move_terms.black_king_escape_count_not_increased_after_move`: count=36, status=`candidate_interaction_positive_context`
- `post_move_terms.box_area_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: count=34, status=`candidate_interaction_scopes_ambiguous_terms`
- `post_move_terms.enemy_corner_distance_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: count=34, status=`candidate_interaction_scopes_ambiguous_terms`
- `post_move_terms.enemy_edge_distance_not_increased_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: count=34, status=`candidate_interaction_scopes_ambiguous_terms`
- `post_move_terms.rook_safe_after_move` + `post_move_terms.white_king_file_opposition_distance_two_after_move`: count=34, status=`candidate_interaction_scopes_ambiguous_terms`

## Ambiguous Terms Requiring Scope

- `post_move_terms.black_king_escape_count_decreases_after_move` (king_support): pos=165, hard_neg=249, status=`ambiguous_but_state_local_positive`
- `move_shape_terms.king_moves_toward_enemy` (king_support): pos=99, hard_neg=54, status=`ambiguous_but_state_local_positive`
- `post_move_terms.white_king_distance_to_enemy_decreases` (king_support): pos=99, hard_neg=54, status=`ambiguous_but_state_local_positive`
- `post_move_terms.box_area_decreases_after_move` (box_progress): pos=182, hard_neg=508, status=`ambiguous_but_state_local_positive`
- `post_move_terms.white_king_file_opposition_distance_two_after_move` (king_support): pos=66, hard_neg=189, status=`ambiguous_but_state_local_positive`
- `post_move_terms.white_king_and_rook_split_file_side_after_move` (king_support): pos=119, hard_neg=406, status=`ambiguous_but_state_local_positive`

## Hard-Negative Or Veto Context Candidates

- `move_shape_terms.rook_to_edge_file` (rook_geometry): count=174, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.rook_to_edge_rank` (rook_geometry): count=152, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.rook_to_checking_line` (king_support): count=144, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.safe_check_created` (other): count=144, status=`candidate_hard_negative_suppression_context`
- `post_move_terms.checking_line_created` (king_support): count=144, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.rook_lateral_transfer` (rook_geometry): count=141, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.rook_destination_far_from_enemy` (rook_geometry): count=131, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.candidate_is_rook_transfer` (rook_geometry): count=112, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.rook_transfer_vertical` (rook_geometry): count=108, status=`candidate_hard_negative_suppression_context`
- `move_shape_terms.king_moves_toward_rook_support` (king_support): count=107, status=`candidate_hard_negative_suppression_context`
- `post_move_terms.white_king_and_rook_split_rank_side_after_move` (king_support): count=93, status=`candidate_hard_negative_suppression_context`
- `post_move_terms.white_king_and_rook_split_file_side_after_move` (king_support): count=84, status=`candidate_hard_negative_suppression_context`

## Blocked Next Steps

- runtime_repair
- stage7_promotion
- stage8_training
- support_adapter
- score_bonus_or_provider_penalty
- runtime_dtm_or_tablebase
- gameplay_topology_mutation
