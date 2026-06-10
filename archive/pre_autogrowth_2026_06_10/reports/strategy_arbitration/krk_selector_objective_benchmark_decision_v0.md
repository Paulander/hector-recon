# KRK Selector Objective Benchmark Decision v0

This artifact is non-causal. It does not train or authorize a runtime selector.

## Decision

- status: `selector_objective_benchmark_promising_non_causal`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `write_runtime_review_packet_not_implementation`

## Summary

- benchmark_status: `selector_objective_benchmark_promising_non_causal`
- seed_row_count: `21`
- target_action_counts: `{'abstain_context_only': 5, 'prefer_visible_alternative': 5, 'preserve_selected_owner': 11}`
- best_model: `combined_simple_rule`
- best_accuracy: `0.9523809523809523`
- best_safe_preservation_recall: `1.0`
- best_switch_contrast_recall: `0.8`
- best_abstain_recall: `1.0`
- promising_runtime_feature_model_count: `1`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`
