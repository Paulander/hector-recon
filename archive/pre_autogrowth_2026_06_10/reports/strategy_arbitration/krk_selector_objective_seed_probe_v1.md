# KRK Selector Objective Seed Probe v1

This non-causal probe checks whether v1 seed rows encode switch-vs-preserve selector-objective semantics after bounded observation collection. It is not selector training.

## Decision

- status: `selector_objective_seed_ready_for_non_causal_feature_probe`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `design_non_causal_selector_feature_probe`

## Summary

- seed_row_count: `12`
- target_action_counts: `{'prefer_visible_alternative': 4, 'preserve_selected_owner': 8}`
- correct_count: `12`
- apparent_semantic_rule_accuracy: `1.0`
- semantics_consistent: `True`
- seed_balanced_enough_for_next_non_causal_probe: `True`
- benchmark_underpowered: `False`
- switch_preserve_contrast_better_represented: `True`
- runtime_feature_eligible_prediction_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Interpretation

- semantics_confirmed: `True`
- selector_training_supported: `False`
- runtime_selector_supported: `False`
- runtime_feature_eligible_prediction_possible_now: `False`
- reason: `V1 improves switch-vs-preserve representation enough for a future non-causal feature probe, but predictions still use offline selected-owner labels and do not authorize runtime selector behavior.`
