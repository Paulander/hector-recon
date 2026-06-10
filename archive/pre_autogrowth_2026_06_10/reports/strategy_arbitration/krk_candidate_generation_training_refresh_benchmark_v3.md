# KRK Candidate-Generation Training Refresh Benchmark v3

This offline benchmark evaluates candidate-generation policies over protected forced-provider capacity labels. It does not train or authorize a selector.

## Decision

- status: `candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed`
- runtime_implementation_allowed_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `write_candidate_generation_refresh_runtime_review_packet_only`

## Summary

- capacity_row_count: `36`
- positive_capacity_count: `26`
- negative_capacity_count: `10`
- runtime_trace_feature_row_count: `44`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- best_policy: `trace_stage_family_context`
- best_policy_metrics: `{'row_count': 36, 'positive_count': 26, 'negative_count': 10, 'predicted_count': 20, 'true_positive': 20, 'false_positive': 0, 'false_negative': 6, 'true_negative': 10, 'positive_capacity_recall': 0.7692307692307693, 'positive_precision': 1.0, 'negative_capacity_suppression': 1.0, 'balanced_recall_risk': 0.8846153846153846}`
- best_policy_leave_stage_out_metrics: `{'row_count': 36, 'positive_count': 26, 'negative_count': 10, 'predicted_count': 20, 'true_positive': 20, 'false_positive': 0, 'false_negative': 6, 'true_negative': 10, 'positive_capacity_recall': 0.7692307692307693, 'positive_precision': 1.0, 'negative_capacity_suppression': 1.0, 'balanced_recall_risk': 0.8846153846153846}`
- thresholds_met: `True`

## Policy Metrics

- `emit_all_capacity_candidates`: recall=`1.000` precision=`0.722` negative_suppression=`0.000` balanced=`0.500`
- `trace_exact_context`: recall=`0.308` precision=`1.000` negative_suppression=`1.000` balanced=`0.654`
- `trace_state_provider_context`: recall=`0.308` precision=`1.000` negative_suppression=`1.000` balanced=`0.654`
- `trace_stage_family_context`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `trace_provider_context`: recall=`1.000` precision=`0.743` negative_suppression=`0.100` balanced=`0.550`
- `trace_active_family_context`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `learned_family_positive_rate_at_least_half`: recall=`1.000` precision=`0.743` negative_suppression=`0.100` balanced=`0.550`
- `learned_provider_positive_rate_at_least_half`: recall=`1.000` precision=`0.743` negative_suppression=`0.100` balanced=`0.550`
- `learned_stage_family_pure_positive_support_2`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `learned_active_family_pure_positive_support_2`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `learned_stage_active_family_pure_positive_support_2`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `learned_stage_family_positive_rate_at_least_0_75`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `hybrid_trace_stage_family_or_learned_stage_family_pure`: recall=`0.769` precision=`1.000` negative_suppression=`1.000` balanced=`0.885`
- `oracle_positive_capacity_ceiling`: recall=`1.000` precision=`1.000` negative_suppression=`1.000` balanced=`1.000`

## Boundary

Capacity labels are candidate-generation labels only. Runtime trace rows are context features only. Stage 7 remains held out. This artifact does not authorize runtime implementation, selector training, score changes, routing, guardrails, promotion, or Stage 8 training.
