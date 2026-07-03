# Phase 1.1 Feature Audit
`white_king_file` | PERCEPT | direct white-king file coordinate.
`white_king_rank` | PERCEPT | direct white-king rank coordinate.
`white_rook_file` | PERCEPT | direct rook file coordinate.
`white_rook_rank` | PERCEPT | direct rook rank coordinate.
`black_king_file` | PERCEPT | direct black-king file coordinate.
`black_king_rank` | PERCEPT | direct black-king rank coordinate.
`side_white_to_move` | PERCEPT | direct side-to-move bit.
`white_king_to_black_king_distance` | PERCEPT | direct Chebyshev king distance.
`white_rook_to_black_king_distance` | PERCEPT | direct Chebyshev rook-king distance.
`white_king_to_rook_distance` | PERCEPT | direct Chebyshev king-rook distance.
`black_king_nearest_edge_distance` | PERCEPT | direct board-edge distance.
`legal_move_count` | COMPUTED-LOOKAHEAD REMOVE | enumerates legal moves.
`black_reply_mobility` | COMPUTED-LOOKAHEAD REMOVE | enumerates black legal replies.
`rook_present` | PERCEPT | direct rook presence bit.
`rook_attacked_by_black` | PERCEPT | current attack geometry on the rook.
`is_check` | PERCEPT | current king attack status.
`is_checkmate` | COMPUTED-LOOKAHEAD REMOVE | requires no legal check escape.
`is_stalemate` | COMPUTED-LOOKAHEAD REMOVE | requires no legal move and no check.
`king_delta_file_abs` | PERCEPT | direct absolute king file gap.
`king_delta_rank_abs` | PERCEPT | direct absolute king rank gap.
`king_support_l_shape` | PERCEPT | direct king-gap shape predicate.
`king_pair_knight_distance_like` | PERCEPT | direct king-gap shape predicate.
`king_support_chebyshev_distance` | PERCEPT | direct king Chebyshev distance.
`king_support_manhattan_distance` | PERCEPT | direct king Manhattan distance.
`rook_black_king_same_side_of_white_king_on_primary_axis` | PERCEPT | direct edge-axis side relation.
`rook_black_king_opposite_sides_of_white_king_on_primary_axis` | PERCEPT | direct edge-axis side relation.
`rook_distance_to_black_king_edge_line` | PERCEPT | direct rook distance to black-king edge line.
`rook_fence_depth_relative_to_black_king_edge` | PERCEPT | direct rook distance relative to black-king edge.
`rook_lateral_escape_available` | COMPUTED-LOOKAHEAD REMOVE | enumerates rook moves and pushes boards.
`black_king_on_edge` | PERCEPT | direct edge occupancy bit.
`black_king_corner_distance` | PERCEPT | direct corner distance.
`white_king_controls_escape_band` | COMPUTED-LOOKAHEAD REMOVE | projects escape-band squares and king control.
`feature_hub_opposition_status` | CONCEPT REMOVE | hand-authored opposition/parity concept.
`feature_hub_mobility` | COMPUTED-LOOKAHEAD REMOVE | counts legal moves.
`feature_hub_king_tropism` | CONCEPT REMOVE | hand-authored attack-potential score.
`feature_hub_mobility_restriction` | COMPUTED-LOOKAHEAD REMOVE | maps legal-move count to restriction.
`feature_hub_tempo_advantage` | CONCEPT REMOVE | hand-authored initiative/threat score.
`feature_hub_mating_net_present` | CONCEPT REMOVE | hand-authored mating-net heuristic.
`feature_hub_enemy_king_rank` | PERCEPT | direct enemy-king rank coordinate.
`feature_hub_enemy_king_file` | PERCEPT | direct enemy-king file coordinate.
`feature_hub_enemy_king_at_edge` | PERCEPT | direct enemy-king edge bit.
`feature_hub_enemy_king_in_corner` | PERCEPT | direct enemy-king corner geometry.
`feature_hub_enemy_king_mobility` | COMPUTED-LOOKAHEAD REMOVE | counts enemy king escape squares.
`feature_hub_enemy_king_mobility_raw` | COMPUTED-LOOKAHEAD REMOVE | raw enemy king escape-square count.
`feature_hub_stalemate_danger` | CONCEPT REMOVE | composite stalemate-risk heuristic.
`bk_neighbor_n_available` | PERCEPT | static attack geometry, same class as is_check.
`bk_neighbor_ne_available` | PERCEPT | static attack geometry, same class as is_check.
`bk_neighbor_e_available` | PERCEPT | static attack geometry, same class as is_check.
`bk_neighbor_se_available` | PERCEPT | static attack geometry, same class as is_check.
`bk_neighbor_s_available` | PERCEPT | static attack geometry, same class as is_check.
`bk_neighbor_sw_available` | PERCEPT | static attack geometry, same class as is_check.
`bk_neighbor_w_available` | PERCEPT | static attack geometry, same class as is_check.
`bk_neighbor_nw_available` | PERCEPT | static attack geometry, same class as is_check.

## Impact Inventory
Promoted refs mate1/mate2_first: `legal_move_count` 1/1; `black_reply_mobility` 3/5; `is_checkmate` 0/0; `is_stalemate` 0/0.
Promoted refs mate1/mate2_first: `rook_lateral_escape_available` 0/0; `white_king_controls_escape_band` 0/0; `feature_hub_opposition_status` 0/3; `feature_hub_mobility` 1/0.
Promoted refs mate1/mate2_first: `feature_hub_king_tropism` 0/0; `feature_hub_mobility_restriction` 0/0; `feature_hub_tempo_advantage` 2/1; `feature_hub_mating_net_present` 0/2.
Promoted refs mate1/mate2_first: `feature_hub_enemy_king_mobility` 0/3; `feature_hub_enemy_king_mobility_raw` 0/2; `feature_hub_stalemate_danger` 0/1.
Direct refs needing 1.2 update, autogrowth src: `candidate_generation.py`, `clean_edge_fence_stage.py`, `curriculum_reward_recovery.py`, `edge_fence_curriculum.py`, `edge_killbox_curriculum.py`, `features.py`, `fence_boundary_signal.py`, `foundation_curriculum.py`, `handoff_reachability_audit.py`, `mining.py`, `native_single_graph_curriculum.py`, `real_clean_slate_foundation.py`, `retry_diagnostics.py`, `suppressor.py`, `terminal_substrate.py`, `tg48a2_same_side_microstage.py`.
Direct refs needing 1.2 update, other src: `features/hub.py`, `features/integration.py`, `features/krk_features.py`, `features/sensors_v2.py`, `scripts/kqk.py`, `scripts/stalemate_detector.py`, `training/krk_landmarks.py`.
Direct refs needing 1.2 update, tests: `tests/autogrowth/test_autogrowth_experiment.py`, `tests/autogrowth/test_candidate_sandbox.py`, `tests/autogrowth/test_edge_killbox_curriculum.py`, `tests/autogrowth/test_local_arbitration.py`, `tests/autogrowth/test_local_suppressor.py`, `tests/autogrowth/test_terminal_substrate.py`, `tests/test_krk_landmarks.py`.
