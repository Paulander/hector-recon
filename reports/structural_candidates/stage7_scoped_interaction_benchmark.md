# Stage 7 Scoped Interaction Benchmark

This benchmark is offline-only and non-causal. It evaluates scoped interaction features before any runtime sandbox is considered.

## Decision

- Candidate status: `scoped_interaction_benchmark_inconclusive`
- Next action: do not patch; pause Stage 7 runtime work or request architecture review
- Best scoped model: `scoped_interaction_log_odds_scorer`
- Best top-1 improvement over current: `0.039`
- Best top-1 improvement over visible: `-0.086`
- Best hard-negative delta vs current: `0.300`
- Best hard-negative delta vs visible: `0.086`

## Dataset

- `{'step_count': 195, 'train_step_count': 137, 'test_step_count': 58, 'positive_term_count': 25, 'hard_context_term_count': 25, 'interaction_pair_count': 25}`

## Model Metrics

### scoped_interaction_log_odds_scorer

- Train top1/top3 DTM-positive: `0.358` / `0.526`
- Test top1/top3 DTM-positive: `0.397` / `0.569`
- Test optimal top1/top3: `0.397` / `0.569`
- Test draw/stalemate top1 rate: `0.069`
- Test hard-negative-above-positive rate: `0.586`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'd1c2', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 7, 'top_moves': [{'move': 'd1c2', 'score': 11.314747177580506, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6a4', 'score': 8.469712228336402, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6c6', 'score': 7.748512682912521, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6b6', 'score': 7.559845156242362, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6f6', 'score': 7.116420498134128, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### scoped_interaction_ranked_scorer

- Train top1/top3 DTM-positive: `0.321` / `0.533`
- Test top1/top3 DTM-positive: `0.397` / `0.690`
- Test optimal top1/top3: `0.397` / `0.690`
- Test draw/stalemate top1 rate: `0.017`
- Test hard-negative-above-positive rate: `0.586`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'd1c2', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 6, 'top_moves': [{'move': 'd1c2', 'score': 5.366207267532231, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6f6', 'score': 3.6481614330330023, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6g6', 'score': 3.6481614330330023, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6b6', 'score': 3.329448901442976, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6h6', 'score': 2.9347654858783114, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}]}`

### state_local_refinement_vote_scorer

- Train top1/top3 DTM-positive: `0.328` / `0.533`
- Test top1/top3 DTM-positive: `0.310` / `0.621`
- Test optimal top1/top3: `0.310` / `0.621`
- Test draw/stalemate top1 rate: `0.052`
- Test hard-negative-above-positive rate: `0.690`
- First miss: `{'trajectory_index': 0, 'step_index': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a4', 'selected_target_class': 'winning_nonoptimal_move', 'positive_rank': 5, 'top_moves': [{'move': 'a6a4', 'score': 33.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 28, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6c6', 'score': 24.8, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6f6', 'score': 23.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6g6', 'score': 23.0, 'target_class': 'winning_nonoptimal_move', 'label': 0, 'child_dtm': 30, 'is_positive': False, 'is_optimal': False, 'is_hard_negative': True, 'is_bad_safety': False}, {'move': 'a6d6', 'score': 22.4, 'target_class': 'optimal_dtm_move', 'label': 1, 'child_dtm': 26, 'is_positive': True, 'is_optimal': True, 'is_hard_negative': False, 'is_bad_safety': False}]}`

## Blocked Next Steps

- implement_runtime_repair
- promote_stage7
- train_stage8
- add_support_adapter
- add_score_bonus_or_provider_penalty
- use_runtime_dtm_or_tablebase
- mutate_topology_during_gameplay
