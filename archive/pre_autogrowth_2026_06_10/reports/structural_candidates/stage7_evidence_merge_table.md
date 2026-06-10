# Stage 7 Evidence Merge Table

This report is replay-free and non-causal. It merges existing Stage 7 artifacts without changing runtime behavior.

## Summary

- Rows: 9
- Hypothesis labels: `{'already_solved_by_existing_provider_if_arbitrated': 2, 'bad_curriculum_boundary_candidate': 6, 'continuation_capacity_candidate': 4, 'missing_feature_candidate': 4, 'phase_boundary_candidate': 4, 'strategy_arbitration_candidate': 2, 'training_objective_model_expression_candidate': 2, 'unresolved_without_new_continuation_policy': 4}`
- Missing evidence: `{'candidate_move_role_for_this_family': 2, 'hypothesis_specific_evidence': 2, 'legal_first_h40_label': 2, 'provider_best_h40_mating_label': 3, 'provider_internal_trainability_for_this_state': 2}`
- M3 trainability: `scripted_provider_selected_but_not_trainable_for_move_policy`
- Arbitration answers: `{'provider_selection_model_predicts_converting_provider': False, 'provider_local_normalization_outperforms_raw_global_score': False, 'box_area_relevance_explains_some_failures': False, 'failures_suggest_box_or_stage0_over_ownership': False}`

## Rows

### 1. state.069e81a609ed

- Family: `None`
- FEN: `8/8/8/8/7R/2k5/4K3/8 w - - 2 2`
- Sources: `['stage7_0926_move_shape_role_candidate_audit.json']`
- Context: edge=2 (central_or_midboard), box=21, relevance=high, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_available
- Selected provider/move: `None` / `None`
- Raw top provider/move: `None` / `None`
- Best forced provider: `None`
- Current graph h40: `None`
- Legal/DTM label: `None`
- Capsule result: `None`
- Teacher fidelity: `None`
- Labels: `['missing_feature_candidate']`
- Missing evidence: `[{'missing_cell': 'candidate_move_role_for_this_family', 'can_be_filled_replay_free': True, 'smallest_bounded_h40_label_needed': None}, {'missing_cell': 'hypothesis_specific_evidence', 'can_be_filled_replay_free': True, 'smallest_bounded_h40_label_needed': None}]`

### 2. state.0926f12f8e8f

- Family: `None`
- FEN: `8/8/8/8/4K3/8/R7/4k3 w - - 2 2`
- Sources: `['stage7_0926_move_shape_role_candidate_audit.json']`
- Context: edge=0 (at_edge), box=7, relevance=low, rook_safe=True, fence/cut=fence_exists_unstable, king_support=support_can_improve
- Selected provider/move: `None` / `None`
- Raw top provider/move: `None` / `None`
- Best forced provider: `None`
- Current graph h40: `None`
- Legal/DTM label: `None`
- Capsule result: `None`
- Teacher fidelity: `None`
- Labels: `['missing_feature_candidate']`
- Missing evidence: `[]`

### 3. state.4a464b782ecb

- Family: `None`
- FEN: `R7/8/8/8/8/2k5/8/3K4 w - - 4 3`
- Sources: `['stage7_unified_strategy_arbitration_dataset.json']`
- Context: edge=2 (central_or_midboard), box=49, relevance=high, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_available
- Selected provider/move: `None` / `None`
- Raw top provider/move: `krk.stage0_basin` / `a8d8`
- Best forced provider: `None`
- Current graph h40: `None`
- Legal/DTM label: `None`
- Capsule result: `None`
- Teacher fidelity: `None`
- Labels: `['missing_feature_candidate']`
- Missing evidence: `[{'missing_cell': 'provider_best_h40_mating_label', 'can_be_filled_replay_free': False, 'smallest_bounded_h40_label_needed': 'one bounded h40 label for provider-best shortlist'}, {'missing_cell': 'hypothesis_specific_evidence', 'can_be_filled_replay_free': True, 'smallest_bounded_h40_label_needed': None}]`

### 4. state.4e34ad0b2f29

- Family: `cand.krk.box_shrink.family_4e34ad0b2f29.post_box_continuation_overlay_probe.v1`
- FEN: `8/8/8/R7/4k3/8/3K4/8 w - - 2 2`
- Sources: `['stage7_remaining_dtm_candidate_summary.json', 'stage7_unified_strategy_arbitration_dataset.json', 'stage7_capsule_trajectory_fidelity_audit.json', 'stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json']`
- Context: edge=3 (central_or_midboard), box=28, relevance=high, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_available
- Selected provider/move: `None` / `None`
- Raw top provider/move: `krk.stage0_basin` / `a5h5`
- Best forced provider: `None`
- Current graph h40: `None`
- Legal/DTM label: `{'source_terms': ['current_graph_legal_first_failed', 'forced_existing_providers_failed', 'krk_dtm_oracle_winning_position', 'dtm_within_validation_horizon'], 'trigger_failure_classes': ['selected_successor_miscalibrated', 'no_legal_first_conversion_under_current_graph', 'unresolved_by_existing_forced_providers']}`
- Capsule result: `{'result': 'max_plies', 'plies': 40, 'selected_skill': 'krk.post_box_shrink_continuation', 'selected_move': 'd2e2', 'selected_target_class': 'winning_nonoptimal_move', 'selected_is_dtm_positive': False, 'teacher_move': 'd2c3', 'positive_moves': ['d2c3'], 'first_divergence': {'ply': 0, 'fen': '8/8/8/R7/4k3/8/3K4/8 w - - 2 2', 'selected_move': 'd2e2', 'positive_moves': ['d2c3'], 'optimal_moves': ['d2c3']}}`
- Teacher fidelity: `{'teacher_move_top1_rate': 0.2, 'dtm_positive_top1_rate': 0.36, 'dtm_positive_top3_rate': 0.8, 'top_level_diagnosis': 'trajectory_ranking_and_closed_loop_gap'}`
- Labels: `['continuation_capacity_candidate', 'training_objective_model_expression_candidate', 'unresolved_without_new_continuation_policy', 'bad_curriculum_boundary_candidate']`
- Missing evidence: `[{'missing_cell': 'provider_internal_trainability_for_this_state', 'can_be_filled_replay_free': True, 'smallest_bounded_h40_label_needed': None}, {'missing_cell': 'provider_best_h40_mating_label', 'can_be_filled_replay_free': False, 'smallest_bounded_h40_label_needed': 'one bounded h40 label for provider-best shortlist'}]`

### 5. state.b6796dfb62ff

- Family: `cand.krk.box_shrink.family_b6796dfb62ff.post_box_continuation_overlay_probe.v1`
- FEN: `8/8/R7/8/2k5/8/8/3K4 w - - 2 2`
- Sources: `['stage7_remaining_dtm_candidate_summary.json', 'stage7_0926_move_shape_role_candidate_audit.json', 'stage7_2cc_candidate_move_dtm_alignment.json', 'stage7_unified_strategy_arbitration_dataset.json', 'stage7_capsule_trajectory_fidelity_audit.json', 'stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json']`
- Context: edge=2 (central_or_midboard), box=35, relevance=high, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_can_improve
- Selected provider/move: `None` / `None`
- Raw top provider/move: `krk.stage0_basin` / `a6a8`
- Best forced provider: `None`
- Current graph h40: `None`
- Legal/DTM label: `{'source_terms': ['current_graph_legal_first_failed', 'forced_existing_providers_failed', 'krk_dtm_oracle_winning_position', 'dtm_within_validation_horizon'], 'trigger_failure_classes': ['selected_successor_miscalibrated', 'no_legal_first_conversion_under_current_graph', 'unresolved_by_existing_forced_providers']}`
- Capsule result: `{'result': 'max_plies', 'plies': 40, 'selected_skill': 'krk.post_box_shrink_continuation', 'selected_move': 'a6a8', 'selected_target_class': 'winning_nonoptimal_move', 'selected_is_dtm_positive': False, 'teacher_move': 'a6a5', 'positive_moves': ['a6a5', 'a6d6', 'd1d2'], 'first_divergence': {'ply': 0, 'fen': '8/8/R7/8/2k5/8/8/3K4 w - - 2 2', 'selected_move': 'a6a8', 'positive_moves': ['a6a5', 'a6d6', 'd1d2'], 'optimal_moves': ['a6a5', 'a6d6', 'd1d2']}}`
- Teacher fidelity: `{'teacher_move_top1_rate': 0.2, 'dtm_positive_top1_rate': 0.36, 'dtm_positive_top3_rate': 0.8, 'top_level_diagnosis': 'trajectory_ranking_and_closed_loop_gap'}`
- Labels: `['continuation_capacity_candidate', 'training_objective_model_expression_candidate', 'unresolved_without_new_continuation_policy', 'bad_curriculum_boundary_candidate', 'missing_feature_candidate']`
- Missing evidence: `[{'missing_cell': 'provider_internal_trainability_for_this_state', 'can_be_filled_replay_free': True, 'smallest_bounded_h40_label_needed': None}, {'missing_cell': 'candidate_move_role_for_this_family', 'can_be_filled_replay_free': True, 'smallest_bounded_h40_label_needed': None}, {'missing_cell': 'provider_best_h40_mating_label', 'can_be_filled_replay_free': False, 'smallest_bounded_h40_label_needed': 'one bounded h40 label for provider-best shortlist'}]`

### 6. state.0afbf11aa123

- Family: `stage7.post_box.family_0afbf11aa123`
- FEN: `8/8/8/8/4K3/4R3/3k4/8 w - - 2 2`
- Sources: `['stage7_post_box_family_diagnosis.json']`
- Context: edge=1 (near_edge), box=8, relevance=medium, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_available
- Selected provider/move: `krk.stage0_basin` / `a3e3`
- Raw top provider/move: `None` / `None`
- Best forced provider: `None`
- Current graph h40: `max_plies`
- Legal/DTM label: `{'tested_move_count': 7, 'outcome_counts': {'h40:max_plies': 5, 'h40:draw': 2}, 'mating_moves': [], 'any_mate': False}`
- Capsule result: `None`
- Teacher fidelity: `None`
- Labels: `['continuation_capacity_candidate', 'unresolved_without_new_continuation_policy', 'phase_boundary_candidate', 'bad_curriculum_boundary_candidate']`
- Missing evidence: `[]`

### 7. state.38aed2f35911

- Family: `stage7.post_box.family_38aed2f35911`
- FEN: `8/8/8/R7/4k3/8/8/3K4 w - - 2 2`
- Sources: `['stage7_post_box_family_diagnosis.json']`
- Context: edge=3 (central_or_midboard), box=28, relevance=high, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_can_improve
- Selected provider/move: `krk.stage0_basin` / `a3a5`
- Raw top provider/move: `None` / `None`
- Best forced provider: `None`
- Current graph h40: `max_plies`
- Legal/DTM label: `{'tested_move_count': 17, 'outcome_counts': {'h40:max_plies': 14, 'h40:draw': 3}, 'mating_moves': [], 'any_mate': False}`
- Capsule result: `None`
- Teacher fidelity: `None`
- Labels: `['continuation_capacity_candidate', 'unresolved_without_new_continuation_policy', 'phase_boundary_candidate', 'bad_curriculum_boundary_candidate']`
- Missing evidence: `[]`

### 8. state.ac0b7ed500ea

- Family: `stage7.post_box.family_ac0b7ed500ea`
- FEN: `8/8/8/4k3/R7/8/3K4/8 w - - 2 2`
- Sources: `['stage7_post_box_family_diagnosis.json']`
- Context: edge=3 (central_or_midboard), box=28, relevance=high, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_can_improve
- Selected provider/move: `krk.stage0_basin` / `a1a4`
- Raw top provider/move: `None` / `None`
- Best forced provider: `krk.fence_established`
- Current graph h40: `max_plies`
- Legal/DTM label: `None`
- Capsule result: `None`
- Teacher fidelity: `None`
- Labels: `['already_solved_by_existing_provider_if_arbitrated', 'strategy_arbitration_candidate', 'phase_boundary_candidate', 'bad_curriculum_boundary_candidate']`
- Missing evidence: `[{'missing_cell': 'legal_first_h40_label', 'can_be_filled_replay_free': False, 'smallest_bounded_h40_label_needed': 'one bounded h40 legal-first/provider-best label if this family remains decision-critical'}]`

### 9. state.ff6652c8832c

- Family: `stage7.post_box.family_ff6652c8832c`
- FEN: `8/8/8/8/4R3/2k5/4K3/8 w - - 2 2`
- Sources: `['stage7_post_box_family_diagnosis.json']`
- Context: edge=2 (central_or_midboard), box=12, relevance=high, rook_safe=True, fence/cut=fence_or_cut_not_preserved, king_support=support_available
- Selected provider/move: `krk.stage0_basin` / `a4e4`
- Raw top provider/move: `None` / `None`
- Best forced provider: `krk.drive_to_edge`
- Current graph h40: `max_plies`
- Legal/DTM label: `None`
- Capsule result: `None`
- Teacher fidelity: `None`
- Labels: `['already_solved_by_existing_provider_if_arbitrated', 'strategy_arbitration_candidate', 'phase_boundary_candidate', 'bad_curriculum_boundary_candidate']`
- Missing evidence: `[{'missing_cell': 'legal_first_h40_label', 'can_be_filled_replay_free': False, 'smallest_bounded_h40_label_needed': 'one bounded h40 legal-first/provider-best label if this family remains decision-critical'}]`
