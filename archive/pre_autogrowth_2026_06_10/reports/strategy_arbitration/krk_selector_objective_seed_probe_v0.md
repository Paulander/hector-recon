# KRK Selector Objective Seed Probe v0

This non-causal probe checks whether the seed manifest encodes the intended switch-vs-preserve selector-objective semantics. It is not a runtime-feature probe and not selector training.

## Decision

- status: `selector_objective_seed_probe_underpowered_semantics_confirmed`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `collect_more_joined_trace_ownership_evidence_non_causal`

## Summary

- seed_row_count: `4`
- target_action_counts: `{'prefer_visible_alternative': 2, 'preserve_selected_owner': 2}`
- correct_count: `4`
- apparent_semantic_rule_accuracy: `1.0`
- has_switch_and_preserve_seeds: `True`
- benchmark_underpowered: `True`
- runtime_feature_eligible_prediction_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Interpretation

- semantics_confirmed: `True`
- selector_training_supported: `False`
- runtime_selector_supported: `False`
- reason: `The seed rows encode the intended switch-vs-preserve contrast, but the probe uses offline selected-owner outcome labels and is too small for runtime feature training or selector authorization.`
