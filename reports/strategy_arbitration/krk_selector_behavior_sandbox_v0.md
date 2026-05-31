# KRK Selector Behavior Sandbox v0

This report records the explicitly approved default-off narrow selector behavior sandbox smoke. The sandbox can switch only to an already-visible alternative when enabled and when the refined selector recommends `prefer_visible_alternative`.

## Decision

- status: `selector_behavior_sandbox_target_improved`
- promote: `False`
- make_default: `False`
- run_broad_guardrails: `True`
- train_anything: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- runtime_dtm_or_tablebase_allowed: `False`
- gameplay_topology_mutation_allowed: `False`

## Summary

- attempted_row_count: `14`
- default_off_equivalence_passed: `True`
- enabled_switch_count: `2`
- preserve_noop_count: `4`
- abstain_noop_count: `6`
- behavior_action_counts: `{'no_op': 12, 'switch_to_visible_alternative': 2}`
- recommendation_counts_by_class: `{'abstain_context_only': 6, 'prefer_visible_alternative': 4, 'preserve_selected_owner': 4}`
- flag_off_behavior_metadata_count: `0`
- selected_move_delta_count: `2`
- selected_provider_delta_count: `2`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- target_improvement_count: `2`
- safe_regression_count: `0`
- bad_switch_count: `0`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_dtm_or_tablebase: `False`
- topology_mutation: `False`
- enabled_behavior_changed: `True`

## Rows

- `stage4_joined_trace_ownership_1` stage=stage4 recommendation=`prefer_visible_alternative` action=`switch_to_visible_alternative` move_delta=True provider_delta=True target_improved=True safe_regression=False
- `stage4_joined_trace_ownership_2` stage=stage4 recommendation=`abstain_context_only` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `stage4_joined_trace_ownership_3` stage=stage4 recommendation=`abstain_context_only` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `stage4_joined_trace_ownership_4` stage=stage4 recommendation=`abstain_context_only` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `stage4_joined_trace_ownership_5` stage=stage4 recommendation=`abstain_context_only` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `stage4_joined_trace_ownership_6` stage=stage4 recommendation=`abstain_context_only` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `selector_objective_fresh_diversity.01` stage=stage5 recommendation=`prefer_visible_alternative` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `selector_objective_fresh_diversity.02` stage=stage5 recommendation=`abstain_context_only` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `selector_objective_fresh_diversity.03` stage=stage5 recommendation=`preserve_selected_owner` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `selector_objective_fresh_diversity.04` stage=stage6 recommendation=`prefer_visible_alternative` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `selector_objective_fresh_diversity.05` stage=stage6 recommendation=`prefer_visible_alternative` action=`switch_to_visible_alternative` move_delta=True provider_delta=True target_improved=True safe_regression=False
- `selector_objective_fresh_diversity.06` stage=stage6 recommendation=`preserve_selected_owner` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `selector_objective_fresh_diversity.07` stage=stage5 recommendation=`preserve_selected_owner` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
- `selector_objective_fresh_diversity.08` stage=stage6 recommendation=`preserve_selected_owner` action=`no_op` move_delta=False provider_delta=False target_improved=False safe_regression=False
