# KRK Selector Objective Seed Probe v2

This non-causal probe checks whether the expanded seed manifest encodes switch-vs-preserve semantics after adding Stage 4 observation rows. It is not selector training.

## Decision

- status: `selector_objective_seed_probe_v2_ready_for_non_causal_benchmark`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `design_non_causal_selector_objective_benchmark`

## Summary

- seed_row_count: `18`
- target_action_counts: `{'abstain_context_only': 5, 'prefer_visible_alternative': 5, 'preserve_selected_owner': 8}`
- source_stage_counts: `{'stage4': 6, 'stage5': 8, 'stage6': 4}`
- correct_count: `18`
- apparent_semantic_rule_accuracy: `1.0`
- has_switch_and_preserve_seeds: `True`
- benchmark_underpowered: `False`
- runtime_feature_eligible_prediction_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Interpretation

- semantics_confirmed: `True`
- stage4_switch_contrast_added: `True`
- selector_training_supported: `False`
- runtime_selector_supported: `False`
- reason: `The seed rows now include Stage 4 switch-context evidence and enough switch/preserve/abstain contrast for a non-causal objective benchmark, but the probe still uses offline labels and is not selector training.`
