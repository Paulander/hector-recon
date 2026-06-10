# KRK Strategy Missing-Feature Candidate Audit

This audit is non-causal. It proposes terminal/affordance candidates after the `missing_feature_first` decision gate, but implements none of them.

## Status

- Source decision: `missing_feature_first`
- Candidate count: `6`
- Recommended next step: stop_for_architecture_review_before_any_terminal_or_affordance_runtime_sandbox
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Candidates

### cand.krk.strategy.edge_net_affordance.v0

- Target concept: `edge_net_affordance`
- Suggested terms: `['black_king_edge_bucket == at_edge', 'edge_net_pressure_proxy', 'edge_trap_shape_available', 'corner_net_pressure_proxy', 'rook_safe']`
- Tests hypotheses: `['strategy_arbitration_phase_boundary', 'missing_feature_ontology']`
- Matching records: `26`
- Result counts: `{'unknown': 1, 'max_plies': 13, 'mate': 12}`
- Source stage counts: `{'stage7': 2, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Promotion status: `proposed`
- Causal status: `non_causal`

### cand.krk.strategy.king_support_conversion_affordance.v0

- Target concept: `king_support_conversion_affordance`
- Suggested terms: `['white_king_support_available', 'white_king_can_improve_support', 'king_support_improvement_move_exists', 'rook_safe']`
- Tests hypotheses: `['strategy_arbitration_phase_boundary', 'training_objective_model_expression']`
- Matching records: `33`
- Result counts: `{'unknown': 3, 'max_plies': 18, 'mate': 12}`
- Source stage counts: `{'stage7': 9, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Promotion status: `proposed`
- Causal status: `non_causal`

### cand.krk.strategy.box_shrink_exit_condition.v0

- Target concept: `box_shrink_exit_condition`
- Suggested terms: `['box_area_relevance == low', 'black_king_edge_bucket == at_edge', 'edge_net_pressure_proxy', 'mate_basin_readiness']`
- Tests hypotheses: `['bad_curriculum_boundary', 'strategy_arbitration_phase_boundary']`
- Matching records: `25`
- Result counts: `{'unknown': 1, 'mate': 12, 'max_plies': 12}`
- Source stage counts: `{'stage7': 1, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Promotion status: `proposed`
- Causal status: `non_causal`

### cand.krk.strategy.phase_boundary_near_edge.v0

- Target concept: `phase_boundary_near_edge`
- Suggested terms: `['black_king_edge_bucket in {at_edge, near_edge}', 'box_area_relevance in {low, medium}', 'edge_net_pressure_proxy or fence_exists']`
- Tests hypotheses: `['bad_curriculum_boundary', 'missing_feature_ontology']`
- Matching records: `26`
- Result counts: `{'unknown': 1, 'max_plies': 13, 'mate': 12}`
- Source stage counts: `{'stage7': 2, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Promotion status: `proposed`
- Causal status: `non_causal`

### cand.krk.strategy.fence_or_cut_repair_affordance.v0

- Target concept: `fence_or_cut_repair_affordance`
- Suggested terms: `['fence_exists', 'not fence_stable', 'not cut_stable', 'rook_safe']`
- Tests hypotheses: `['strategy_arbitration_phase_boundary', 'continuation_capacity']`
- Matching records: `22`
- Result counts: `{'unknown': 3, 'max_plies': 16, 'mate': 3}`
- Source stage counts: `{'stage7': 9, 'stage5': 6, 'stage6': 5, 'stage4': 2}`
- Promotion status: `proposed`
- Causal status: `non_causal`

### cand.krk.strategy.plan_selection_needed.v0

- Target concept: `plan_selection_needed`
- Suggested terms: `['stage7 residual', 'no visible heuristic hit', 'post_box continuation / capsule context', 'current_graph_h40 == max_plies']`
- Tests hypotheses: `['training_objective_model_expression', 'continuation_capacity']`
- Matching records: `9`
- Result counts: `{'unknown': 3, 'max_plies': 6}`
- Source stage counts: `{'stage7': 9}`
- Promotion status: `proposed`
- Causal status: `non_causal`

## Blocked Next Steps

- implement_runtime_arbiter
- add_causal_terminal
- add_stage7_repair
- train_stage8
- promote_stage7
- use_runtime_dtm_or_tablebase
- mutate_topology_during_gameplay
