# KRK Selector Continuation Scope Audit v0

## Summary

- regression_row_id: `joined_trace_ownership_4`
- regression_ply: `4`
- regression_is_initial_owner_choice: `False`
- successful_initial_switch_count: `2`
- safe_preservation_row_count: `6`
- continuation_preserve_abstain_row_count: `17`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- safe_regression_count: `1`
- target_improvement_count: `2`

## Regression Row

- row_id: `joined_trace_ownership_4`
- state_id: `state.2c1d6da27ea1`
- ply: `4`
- fen_at_ply: `4R3/5k2/8/8/8/8/4K3/8 w - - 6 4`
- active_selected_owner_before_switch: `krk.fence_established`
- raw_selected_provider: `krk.fence_established`
- raw_selected_move: `e8a8`
- selector_replacement_provider: `krk.edge_trap_close`
- selector_replacement_move: `e8b8`
- recommendation_class: `prefer_visible_alternative`
- active_landmark: `fence_established`
- plan_context: `active_h40_continuation_after_initial_owner_choice`
- continuation_context: `{'white_ply': 4, 'is_initial_owner_choice': False, 'control_provider': 'krk.fence_established', 'control_move': 'e8a8', 'enabled_provider': 'krk.edge_trap_close', 'enabled_move': 'e8b8', 'recommendation_reason': 'near_edge_or_medium_box_relevance', 'why_selected_alternative': 'first_current_suggestion_matching_runtime_visible_alternative'}`
- source_terms: `['candidate_generation_only', 'edge_trap', 'fence_established', 'positive_capacity_scope', 'stage_conditioned_candidate_generation_refresh', 'stage_conditioned_capacity_scope_not_ownership_label']`
- explanation_terms: `['selector_model.combined_simple_rule', 'positive_trace_provider_candidate_count.7', 'positive_trace_count_bucket.medium', 'edge_bucket.near_edge', 'support_bucket.far', 'box_area_relevance.medium', 'selected_piece.rook', 'source_stage.stage5', 'active_landmark_label.fence_established']`
- baseline_continuation_outcome: `{'engine_decision_count': 9, 'plies': 17, 'result': 'mate'}`
- enabled_continuation_outcome: `{'engine_decision_count': 20, 'plies': 40, 'result': 'max_plies'}`
- observability_only_outcome: `{'engine_decision_count': 9, 'plies': 17, 'result': 'mate'}`

## Scope Rule Evaluations

- selector allowed only at initial decision / ply 0: `supported_for_future_review`; evidence: Both observed target improvements are initial single-decision switches; the protected regression switch occurs at ply 4.
- selector blocked when current provider is in an active continuation window: `supported_but_needs_monitor_definition`; evidence: The regression overrides an active fence-established continuation. A runtime-safe continuation-window monitor must be defined without offline owner labels.
- selector blocked when selected owner has recent progress: `promising_but_requires_runtime_progress_proxy`; evidence: The raw e8a8 continuation has positive goal_progress while e8b8 has negative goal_progress, but the exact safe progress proxy needs review.
- selector blocked when plan/edge/fence continuation is active: `supported_but_broader_than_ply0_only`; evidence: The regression switches away from fence_established to edge_trap_close inside an h40 continuation. Broad plan-family gates risk suppressing valid future switches unless scoped.
- selector may only recommend abstain during continuation unless failure-risk monitor fires: `needs_more_evidence`; evidence: This is compatible with quarantine, but the failure-risk monitor is not yet proven on continuation states.
- current quarantined selector_behavior path: `unsafe_as_implemented`; evidence: Protected validation has safe_regression_count=1.

## Evaluation

- would_ply0_only_preserve_prior_target_improvements: `True`
- would_ply0_only_eliminate_safe_control_regression: `True`
- does_ply0_only_preserve_safe_owners: `True`
- does_ply0_only_avoid_switching_away_from_active_fence_edge_continuations: `True`
- is_ply0_only_runtime_feature_eligible: `True`
- runtime_feature_eligibility_notes: `A future sandbox can use a runtime decision-window signal such as current_ply/white decision index where available. It must remain default-off and must not use offline ownership labels.`
- decision_recommendation: `selector_scope_initial_owner_only_supported`
