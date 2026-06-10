# Stage 7 Ranking Calibration Audit

This audit is offline-only and non-causal. It explains ranking failures from existing benchmark/trajectory artifacts.

## Status

- Candidate status: `term_collision_and_state_local_ranking_gap`
- Recommended next step: Do not add runtime behavior. If continuing Stage 7, design the next offline benchmark around state-local contrastive ranking or interaction features that separate optimal DTM moves from winning-nonoptimal hard negatives; otherwise pause Stage 7 and ask for architecture review.
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Dataset

- Steps: `195`
- Train/test: `137` / `58`
- Target classes: `{'winning_nonoptimal_move': 2922, 'optimal_dtm_move': 431, 'non_winning_move': 485}`
- Hard-negative/positive ratio: `6.780`

## Findings

- Winning-nonoptimal hard negatives heavily outnumber optimal positives, so global term scorers are biased toward broad progress/safety terms shared by both classes.
- At least one visible-term scorer improves top-1 but leaves hard-negative ranking too high, indicating calibration rather than missing signal alone.
- The simple ranked objective overweights ambiguous terms and performs worse than the current learned scorer.
- Several visible terms are shared by positives and winning-nonoptimal hard negatives; state-local contrast or interaction terms are needed before another runtime sandbox.

## Model Error Profiles

- `current_learned_post_box_scorer`: top1=0.35714285714285715, top3=0.6428571428571429, hard_neg_rate=0.2857142857142857, diagnosis=`partial_signal_or_inconclusive`
- `visible_term_log_odds_scorer`: top1=0.4827586206896552, top3=0.7586206896551724, hard_neg_rate=0.5, diagnosis=`candidate_set_contains_signal_but_hard_negative_calibration_fails`
- `pairwise_ranked_preference_scorer`: top1=0.1896551724137931, top3=0.3103448275862069, hard_neg_rate=0.7931034482758621, diagnosis=`objective_overweights_ambiguous_hard_negative_terms`
- `pairwise_ranked_preference_with_coordinate_terms`: top1=0.27586206896551724, top3=0.3448275862068966, hard_neg_rate=0.7241379310344828, diagnosis=`partial_signal_or_inconclusive`
- `heuristic_king_support_improvement`: top1=0.1896551724137931, top3=0.41379310344827586, hard_neg_rate=0.7413793103448276, diagnosis=`unsafe_draw_prone_objective`
- `heuristic_fence_cut_preservation`: top1=0.1724137931034483, top3=0.3103448275862069, hard_neg_rate=0.7758620689655172, diagnosis=`objective_overweights_ambiguous_hard_negative_terms`
- `heuristic_edge_corner_net_pressure`: top1=0.05172413793103448, top3=0.1896551724137931, hard_neg_rate=0.9482758620689655, diagnosis=`unsafe_draw_prone_objective`
- `heuristic_box_area_relevance`: top1=0.5172413793103449, top3=0.6724137931034483, hard_neg_rate=0.39655172413793105, diagnosis=`top1_improves_but_hard_negatives_remain_too_high`
- `heuristic_safety_non_draw_rook_safe`: top1=0.1206896551724138, top3=0.3793103448275862, hard_neg_rate=0.8793103448275862, diagnosis=`objective_overweights_ambiguous_hard_negative_terms`
- `oracle_dtm_positive_topk_ceiling`: top1=1.0, top3=1.0, hard_neg_rate=0.0, diagnosis=`oracle_ceiling_not_runtime_candidate`
- `oracle_teacher_forced_trajectory_ceiling`: top1=1.0, top3=1.0, hard_neg_rate=0.0, diagnosis=`oracle_ceiling_not_runtime_candidate`

## High-Collision Terms

- `post_move_terms.black_king_escape_count_decreases_after_move`: pos=165, hard_neg=249, nonwin=112, diagnosis=`ambiguous_king_support_term`
- `move_shape_terms.king_moves_toward_enemy`: pos=99, hard_neg=54, nonwin=36, diagnosis=`weak_or_neutral_term`
- `post_move_terms.white_king_distance_to_enemy_decreases`: pos=99, hard_neg=54, nonwin=36, diagnosis=`weak_or_neutral_term`
- `post_move_terms.box_area_decreases_after_move`: pos=182, hard_neg=508, nonwin=224, diagnosis=`overbroad_box_progress_term`
- `post_move_terms.white_king_file_opposition_distance_two_after_move`: pos=66, hard_neg=189, nonwin=15, diagnosis=`ambiguous_king_support_term`
- `post_move_terms.white_king_and_rook_split_file_side_after_move`: pos=119, hard_neg=406, nonwin=145, diagnosis=`ambiguous_king_support_term`

## First Miss By Model

- `current_learned_post_box_scorer`: move `a6a8` as `winning_nonoptimal_move`, positive_rank=`None`
- `visible_term_log_odds_scorer`: move `d1c2` as `winning_nonoptimal_move`, positive_rank=`2`
- `pairwise_ranked_preference_scorer`: move `d1c2` as `winning_nonoptimal_move`, positive_rank=`4`
- `pairwise_ranked_preference_with_coordinate_terms`: move `a6h6` as `winning_nonoptimal_move`, positive_rank=`9`
- `heuristic_king_support_improvement`: move `d1c2` as `winning_nonoptimal_move`, positive_rank=`2`
- `heuristic_fence_cut_preservation`: move `a6a4` as `winning_nonoptimal_move`, positive_rank=`6`
- `heuristic_edge_corner_net_pressure`: move `a6a4` as `winning_nonoptimal_move`, positive_rank=`6`
- `heuristic_box_area_relevance`: move `a6a4` as `winning_nonoptimal_move`, positive_rank=`2`
- `heuristic_safety_non_draw_rook_safe`: move `a6a1` as `winning_nonoptimal_move`, positive_rank=`5`

## Blocked Next Steps

- runtime_repair
- stage7_promotion
- stage8_training
- support_adapter
- score_bonus_or_provider_penalty
- runtime_dtm_or_tablebase
- gameplay_topology_mutation
