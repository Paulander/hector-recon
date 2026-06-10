# KRK Stage-Conditioned Candidate-Generation Benchmark v3

This benchmark evaluates candidate-generation policies scoped by protected stage/family cells. It does not train or implement runtime behavior.

## Decision

- status: `stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked`
- selector_allowed: `False`
- runtime_candidate_generator_refresh_allowed: `False`
- recommended_next_step: `stage5_6_candidate_generation_refresh_review_packet_or_stage4_companion_audit`

## Summary

- capacity_row_count: 36
- capacity_label_counts: `{'negative_capacity': 10, 'positive_capacity': 26}`
- source_stage_counts: `{'stage4': 11, 'stage5': 16, 'stage6': 9}`
- positive_scope_cells: `['stage5|edge_trap', 'stage5|fence_established', 'stage5|stage0_basin', 'stage6|stage0_basin']`
- best_policy_metrics: `{'row_count': 36, 'positive_count': 26, 'negative_count': 10, 'predicted_count': 20, 'true_positive': 20, 'false_positive': 0, 'false_negative': 6, 'true_negative': 10, 'positive_recall': 0.7692307692307693, 'positive_precision': 1.0, 'negative_suppression': 1.0, 'balanced_recall_risk': 0.8846153846153846}`
- stage5_6_positive_scope_metrics: `{'row_count': 25, 'positive_count': 20, 'negative_count': 5, 'predicted_count': 20, 'true_positive': 20, 'false_positive': 0, 'false_negative': 0, 'true_negative': 5, 'positive_recall': 1.0, 'positive_precision': 1.0, 'negative_suppression': 1.0, 'balanced_recall_risk': 1.0}`
- stage4_positive_scope_metrics: `{'row_count': 11, 'positive_count': 6, 'negative_count': 5, 'predicted_count': 0, 'true_positive': 0, 'false_positive': 0, 'false_negative': 6, 'true_negative': 5, 'positive_recall': 0.0, 'positive_precision': 0.0, 'negative_suppression': 1.0, 'balanced_recall_risk': 0.5}`

## Policy Metrics

- `emit_all_capacity_candidates`: recall=`1.000` precision=`0.722` negative_suppression=`0.000` balanced=`0.500`
- `global_family_positive_rate_at_least_half`: recall=`1.000` precision=`0.743` negative_suppression=`0.100` balanced=`0.550`
- `stage_conditioned_positive_scope`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `stage5_6_positive_scope_only`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`

## Interpretation

- stage_conditioned_candidate_generation_supported: `True`
- stage5_6_scope_promising: `True`
- stage4_scope_blocked_without_companion_terms: `True`
- selector_supported: `False`
- runtime_refresh_supported_now: `False`
- capacity_labels_are_not_ownership_labels: `True`

## Boundary

This is candidate-generation evidence only. It cannot select, suppress, score, route, promote Stage 7, or train Stage 8.
