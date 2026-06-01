# KRK Refined Selector Initial Owner Observability Sandbox v0

This report records a default-off, recommendation-only refined selector observability sandbox scoped to the initial owner decision. It does not alter move, provider, score, routing, training, topology, or runtime defaults.

## Decision

- status: `refined_selector_initial_owner_observability_ready_for_recommendation_analysis`
- selector_runtime_ready: `False`
- runtime_changes_allowed: `False`
- behavior_changing_selector_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- recommended_next_step: `non_causal_initial_owner_recommendation_analysis`

## Scope

- selector_scope: `initial_owner_only`
- continuation_recommendations_allowed: `False`
- plan_capsule_continuation_influence_allowed: `False`
- progress_window_reconsideration_influence_allowed: `False`
- move_provider_selection_effect_allowed: `False`

## Summary

- attempted_row_count: `14`
- default_off_equivalence_passed: `True`
- enabled_recommendation_count: `14`
- default_off_selector_recommendation_count: `0`
- recommendation_counts_by_class: `{'preserve_selected_owner': 4, 'prefer_visible_alternative': 4, 'abstain_context_only': 6}`
- preserve_on_failure_count: `0`
- switch_on_safe_owner_count: `0`
- abstain_count: `6`
- abstain_target_count: `5`
- abstain_target_recalled_count: `5`
- abstain_recall: `1.0`
- continuation_recommendation_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- runtime_behavior_changed: `False`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_dtm_or_tablebase_use: `False`
- gameplay_topology_mutation: `False`
- hidden_python_controller: `False`
- capacity_label_used_as_ownership_label_count: `0`
- invalid_metadata_count: `0`
- initial_owner_only_scope_count: `14`
- direct_request_false_count: `14`
- score_delta_zero_count: `14`
- preserve_failure_risk_refinement_present_count: `14`
- abstain_guard_present_count: `14`

## Rows

- `stage4_joined_trace_ownership_1` recommendation=`prefer_visible_alternative` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `stage4_joined_trace_ownership_2` recommendation=`abstain_context_only` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `stage4_joined_trace_ownership_3` recommendation=`abstain_context_only` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `stage4_joined_trace_ownership_4` recommendation=`abstain_context_only` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `stage4_joined_trace_ownership_5` recommendation=`abstain_context_only` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `stage4_joined_trace_ownership_6` recommendation=`abstain_context_only` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.01` recommendation=`prefer_visible_alternative` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.02` recommendation=`abstain_context_only` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.03` recommendation=`preserve_selected_owner` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.04` recommendation=`prefer_visible_alternative` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.05` recommendation=`prefer_visible_alternative` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.06` recommendation=`preserve_selected_owner` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.07` recommendation=`preserve_selected_owner` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
- `selector_objective_fresh_diversity.08` recommendation=`preserve_selected_owner` scope=`initial_owner_only` move_delta=False provider_delta=False routing_delta=False
