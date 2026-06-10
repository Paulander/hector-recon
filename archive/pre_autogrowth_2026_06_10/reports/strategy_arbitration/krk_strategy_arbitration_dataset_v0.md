# KRK Strategy Arbitration Dataset v0

This dataset is replay-free and non-causal. It normalizes existing Stage 5/6/7 evidence into StrategyProposalFrame records.

## Status

- Causal status: `non_causal_dataset`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Summary

- Record count: `33`
- Proposal count: `87`
- Records by source stage: `{'stage7': 9, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Result label counts: `{'None': 5, 'max_plies': 16, 'mate': 12}`
- New h40 labels: `0`

## Sample Records

- `state.069e81a609ed` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': None, 'dtm': None, 'closed_loop_capsule': None}` proposals=0 edge_bucket=`central_or_midboard` box_relevance=`high`
- `state.0926f12f8e8f` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': None, 'dtm': None, 'closed_loop_capsule': None}` proposals=0 edge_bucket=`at_edge` box_relevance=`low`
- `state.4a464b782ecb` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': None, 'dtm': None, 'closed_loop_capsule': None}` proposals=7 edge_bucket=`central_or_midboard` box_relevance=`high`
- `state.4e34ad0b2f29` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': None, 'dtm': {'best_dtm_plies': 21, 'best_moves': ['d2c3', 'a5b5', 'a5c5', 'a5g5', 'a5h5', 'd2c2', 'd2d1', 'd2e1'], 'diagnosis': 'dtm_won_within_validation_horizon_but_current_continuation_failed', 'legal_move_count': 20, 'state_dtm': 21, 'winning_move_count': 17}, 'closed_loop_capsule': {'first_divergence': {'fen': '8/8/8/R7/4k3/8/3K4/8 w - - 2 2', 'optimal_moves': ['d2c3'], 'ply': 0, 'positive_moves': ['d2c3'], 'selected_move': 'd2e2'}, 'plies': 40, 'positive_moves': ['d2c3'], 'result': 'max_plies', 'selected_is_dtm_positive': False, 'selected_move': 'd2e2', 'selected_skill': 'krk.post_box_shrink_continuation', 'selected_target_class': 'winning_nonoptimal_move', 'teacher_move': 'd2c3'}}` proposals=7 edge_bucket=`central_or_midboard` box_relevance=`high`
- `state.b6796dfb62ff` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': None, 'dtm': {'all_legal_moves_win': True, 'best_child_dtm': 26, 'best_moves': ['a6a5', 'a6d6', 'd1d2', 'a6a1', 'a6a2', 'a6a3', 'a6a4', 'a6a7', 'a6a8', 'a6h6'], 'legal_move_count': 19, 'state_dtm': 27, 'winning_move_count': 19}, 'closed_loop_capsule': {'first_divergence': {'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'optimal_moves': ['a6a5', 'a6d6', 'd1d2'], 'ply': 0, 'positive_moves': ['a6a5', 'a6d6', 'd1d2'], 'selected_move': 'a6a8'}, 'plies': 40, 'positive_moves': ['a6a5', 'a6d6', 'd1d2'], 'result': 'max_plies', 'selected_is_dtm_positive': False, 'selected_move': 'a6a8', 'selected_skill': 'krk.post_box_shrink_continuation', 'selected_target_class': 'winning_nonoptimal_move', 'teacher_move': 'a6a5'}}` proposals=7 edge_bucket=`central_or_midboard` box_relevance=`high`
- `state.0afbf11aa123` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': 'max_plies', 'dtm': None, 'closed_loop_capsule': None}` proposals=6 edge_bucket=`near_edge` box_relevance=`medium`
- `state.38aed2f35911` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': 'max_plies', 'dtm': None, 'closed_loop_capsule': None}` proposals=6 edge_bucket=`central_or_midboard` box_relevance=`high`
- `state.ac0b7ed500ea` stage=`stage7` label=`box_shrink` result=`{'current_graph_h40': 'max_plies', 'dtm': None, 'closed_loop_capsule': None}` proposals=6 edge_bucket=`central_or_midboard` box_relevance=`high`

## Hard Constraints

- do_not_train_stage8
- do_not_promote_stage7
- do_not_make_arbitration_causal
- do_not_use_dtm_or_tablebase_at_runtime
- do_not_mutate_topology_during_gameplay
