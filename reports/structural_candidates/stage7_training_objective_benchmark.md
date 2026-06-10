# Stage 7 Training-Objective Benchmark

This benchmark is offline-only and non-causal. It does not implement a runtime repair, promote Stage 7, train Stage 8, or use DTM/tablebase at runtime.

## Decision

- Candidate status: `model_expression_gap_persists`
- Next action: design stronger ranked sequence-policy candidate
- Ranked top-1 improvement over current: `-0.167`
- Visible top-1 improvement over current: `0.126`
- Internal-monitor top-1 improvement over visible: `0.000`
- Internal-monitor features improve offline: `False`

## Dataset

- Trajectories: `18`
- White training steps: `195`
- Legal move labels: `3838`
- Train/test: `137` / `58`
- Target classes: `{'winning_nonoptimal_move': 2922, 'optimal_dtm_move': 431, 'non_winning_move': 485}`
- Benchmark underpowered: `False`

## Internal-Terminal Diagnostic Features

- Causal status: `non_causal_diagnostic_features`
- FENs with features: `24`
- Feature support counts: `{'terminal.krk.repair_needed_monitor': 15, 'terminal.krk.box_shrink_owner_exit_pressure': 2, 'terminal.krk.post_plan_stagnation': 4, 'terminal.krk.local_provider_competition_failed': 2}`

## Model Metrics

### current_learned_post_box_scorer

- Train top1/top3 DTM-positive: `0.364` / `1.000`
- Test top1/top3 DTM-positive: `0.357` / `0.643`
- Test optimal top1/top3: `0.357` / `0.643`
- Test draw/stalemate top1 rate: `0.000`
- Test hard-negative-above-positive rate: `0.286`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a8', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': None, 'top_moves': [{'move': 'a6a8', 'score': 1.418431847000122, 'skill_id': None, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28}, {'move': 'a6f6', 'score': 0.020982536690394897, 'skill_id': None, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30}, {'move': 'a6h6', 'score': 0.01880987303654353, 'skill_id': None, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28}]}`

### visible_term_log_odds_scorer

- Train top1/top3 DTM-positive: `0.555` / `0.723`
- Test top1/top3 DTM-positive: `0.483` / `0.759`
- Test optimal top1/top3: `0.483` / `0.759`
- Test draw/stalemate top1 rate: `0.034`
- Test hard-negative-above-positive rate: `0.500`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'd1c2', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 2, 'top_moves': [{'move': 'd1c2', 'score': 7.585219148419794, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'd1d2', 'score': 6.948418652164079, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}, {'move': 'd1e2', 'score': 6.948418652164079, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a4', 'score': 2.80707442185436, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a5', 'score': 2.156992479637883, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}]}`

### pairwise_ranked_preference_scorer

- Train top1/top3 DTM-positive: `0.234` / `0.343`
- Test top1/top3 DTM-positive: `0.190` / `0.310`
- Test optimal top1/top3: `0.190` / `0.310`
- Test draw/stalemate top1 rate: `0.017`
- Test hard-negative-above-positive rate: `0.793`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'd1c2', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 4, 'top_moves': [{'move': 'd1c2', 'score': 1.7277227668269923, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a1', 'score': 1.455862442945279, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6h6', 'score': 1.1565296587458147, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'd1d2', 'score': 1.099446557149573, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}, {'move': 'd1e2', 'score': 1.099446557149573, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### pairwise_ranked_preference_with_coordinate_terms

- Train top1/top3 DTM-positive: `0.285` / `0.328`
- Test top1/top3 DTM-positive: `0.276` / `0.345`
- Test optimal top1/top3: `0.276` / `0.345`
- Test draw/stalemate top1 rate: `0.017`
- Test hard-negative-above-positive rate: `0.724`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6h6', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 9, 'top_moves': [{'move': 'a6h6', 'score': 2.3019175064007835, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'd1c2', 'score': 2.041711412166916, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a2', 'score': 1.898398879132755, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a1', 'score': 1.8765878144552488, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6f6', 'score': 1.6944991076657727, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### internal_monitor_augmented_visible_term_scorer

- Train top1/top3 DTM-positive: `0.562` / `0.723`
- Test top1/top3 DTM-positive: `0.483` / `0.759`
- Test optimal top1/top3: `0.483` / `0.759`
- Test draw/stalemate top1 rate: `0.034`
- Test hard-negative-above-positive rate: `0.500`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'd1c2', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 2, 'top_moves': [{'move': 'd1c2', 'score': 22.62256573126468, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'd1d2', 'score': 20.519428166215537, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}, {'move': 'd1e2', 'score': 20.519428166215537, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a4', 'score': 13.678238888392656, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6c6', 'score': 6.641676816352016, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### heuristic_king_support_improvement

- Train top1/top3 DTM-positive: `0.175` / `0.343`
- Test top1/top3 DTM-positive: `0.190` / `0.414`
- Test optimal top1/top3: `0.190` / `0.414`
- Test draw/stalemate top1 rate: `0.103`
- Test hard-negative-above-positive rate: `0.741`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'd1c2', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 2, 'top_moves': [{'move': 'd1c2', 'score': 5.5, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'd1d2', 'score': 5.5, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}, {'move': 'd1e2', 'score': 5.5, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a1', 'score': 2.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a2', 'score': 2.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### heuristic_fence_cut_preservation

- Train top1/top3 DTM-positive: `0.153` / `0.321`
- Test top1/top3 DTM-positive: `0.172` / `0.310`
- Test optimal top1/top3: `0.172` / `0.310`
- Test draw/stalemate top1 rate: `0.069`
- Test hard-negative-above-positive rate: `0.776`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a4', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 6, 'top_moves': [{'move': 'a6a4', 'score': 4.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6c6', 'score': 4.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a1', 'score': 0.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a2', 'score': 0.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a3', 'score': 0.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### heuristic_edge_corner_net_pressure

- Train top1/top3 DTM-positive: `0.051` / `0.292`
- Test top1/top3 DTM-positive: `0.052` / `0.190`
- Test optimal top1/top3: `0.052` / `0.190`
- Test draw/stalemate top1 rate: `0.172`
- Test hard-negative-above-positive rate: `0.948`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a4', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 6, 'top_moves': [{'move': 'a6a4', 'score': 2.5, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6c6', 'score': 1.5, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a1', 'score': 1.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a2', 'score': 1.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a3', 'score': 1.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### heuristic_box_area_relevance

- Train top1/top3 DTM-positive: `0.431` / `0.540`
- Test top1/top3 DTM-positive: `0.517` / `0.672`
- Test optimal top1/top3: `0.517` / `0.672`
- Test draw/stalemate top1 rate: `0.293`
- Test hard-negative-above-positive rate: `0.397`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a4', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 2, 'top_moves': [{'move': 'a6a4', 'score': 4.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a5', 'score': 4.0, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}, {'move': 'a6b6', 'score': 4.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6c6', 'score': 4.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6d6', 'score': 4.0, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}]}`

### heuristic_safety_non_draw_rook_safe

- Train top1/top3 DTM-positive: `0.153` / `0.372`
- Test top1/top3 DTM-positive: `0.121` / `0.379`
- Test optimal top1/top3: `0.121` / `0.379`
- Test draw/stalemate top1 rate: `0.000`
- Test hard-negative-above-positive rate: `0.879`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a1', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 5, 'top_moves': [{'move': 'a6a1', 'score': 2.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a2', 'score': 2.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a3', 'score': 2.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a4', 'score': 2.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a5', 'score': 2.0, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}]}`

### oracle_dtm_positive_topk_ceiling

- Train top1/top3 DTM-positive: `1.000` / `1.000`
- Test top1/top3 DTM-positive: `1.000` / `1.000`
- Test optimal top1/top3: `1.000` / `1.000`
- Test draw/stalemate top1 rate: `0.000`
- Test hard-negative-above-positive rate: `0.000`
- First miss: `None`

### oracle_teacher_forced_trajectory_ceiling

- Train top1/top3 DTM-positive: `1.000` / `1.000`
- Test top1/top3 DTM-positive: `1.000` / `1.000`
- Test optimal top1/top3: `1.000` / `1.000`
- Test draw/stalemate top1 rate: `0.000`
- Test hard-negative-above-positive rate: `0.000`
- First miss: `None`

## Controls

- 0926 candidate-move summary: `{'states_with_matches': 1, 'total_matching_moves': 1}`
- 2cc DTM/current-graph summary: `{'dtm': {'state_dtm': 27, 'legal_move_count': 19, 'winning_move_count': 19, 'all_legal_moves_win': True, 'best_child_dtm': 26, 'best_moves': ['a6a5', 'a6d6', 'd1d2', 'a6a1', 'a6a2', 'a6a3', 'a6a4', 'a6a7', 'a6a8', 'a6h6'], 'optimal_move_count': 3}, 'legal_first_current_graph': {'probe_count': 19, 'outcome_counts': {'h50:max_plies': 19}, 'mating_moves': []}, 'candidate_diagnosis': 'multi_step_continuation_policy_gap_not_single_move_gap'}`

## Blocked Next Steps

- implement_runtime_repair
- promote_stage7
- train_stage8
- add_support_adapter
- add_score_bonus_or_provider_penalty
- use_runtime_dtm_or_tablebase
- mutate_topology_during_gameplay
- promote_internal_terminals
