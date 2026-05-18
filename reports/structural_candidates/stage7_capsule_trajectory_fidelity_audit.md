# Stage 7 Capsule Trajectory Fidelity Audit

This is non-causal analysis. DTM labels are used only as offline supervision evidence.

## Summary

- teacher states: `25`
- teacher top-1: `0.160`
- DTM-positive top-1: `0.280`
- DTM-positive top-3: `0.800`
- DTM-optimal top-1: `0.280`
- DTM-optimal top-3: `0.800`
- diagnosis: `trajectory_ranking_and_closed_loop_gap`
- next_action: `expand_offline_dtm_seed_and_train_ranked_imitation_before_more_runtime_repair`

## Closed-Loop Families

- `8/8/R7/8/2k5/8/8/3K4 w - - 2 2` selected `a6a8` (winning_nonoptimal_move) -> `max_plies`: `teacher_fidelity_ranking_gap`
- `8/8/8/R7/4k3/8/3K4/8 w - - 2 2` selected `a5h5` (winning_nonoptimal_move) -> `max_plies`: `teacher_fidelity_ranking_gap`
- `8/8/R7/8/2k5/8/8/3K4 w - - 2 2` selected `a6a8` (winning_nonoptimal_move) -> `max_plies`: `teacher_fidelity_ranking_gap`
- `8/8/8/R7/4k3/8/3K4/8 w - - 2 2` selected `a5h5` (winning_nonoptimal_move) -> `max_plies`: `teacher_fidelity_ranking_gap`

## First Misses

- first_teacher_miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a8', 'teacher_move': 'a6a5', 'positive_moves': ['a6a5', 'a6d6', 'd1d2'], 'optimal_moves': ['a6a5', 'a6d6', 'd1d2']}`
- first_positive_miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a8', 'teacher_move': 'a6a5', 'positive_moves': ['a6a5', 'a6d6', 'd1d2'], 'optimal_moves': ['a6a5', 'a6d6', 'd1d2']}`
- first_optimal_miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a8', 'teacher_move': 'a6a5', 'positive_moves': ['a6a5', 'a6d6', 'd1d2'], 'optimal_moves': ['a6a5', 'a6d6', 'd1d2']}`
