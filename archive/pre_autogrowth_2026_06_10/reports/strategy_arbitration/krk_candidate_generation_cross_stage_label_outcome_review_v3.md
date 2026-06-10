# KRK Candidate-Generation Cross-Stage Label Outcome Review v3

This review checks whether the targeted cross-stage capacity labels changed the candidate-generation refresh decision.

## Decision

- status: `cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked`
- selector_allowed: `False`
- runtime_candidate_generator_refresh_allowed: `False`
- recommended_next_step: `review_stage_conditioned_candidate_generation_scope`

## Label Run

- label_count: 8
- result_counts: `{'mate': 7, 'max_plies': 1}`
- stage7_label_count: 0
- stage7_training_label_count: 0

## Before / After

- before: `{'capacity_row_count': 28, 'capacity_label_counts': {'negative_capacity': 9, 'positive_capacity': 19}, 'best_policy': 'stage_family_pure_positive_with_support_2', 'best_positive_recall': 0.7368421052631579, 'best_positive_precision': 1.0, 'best_negative_suppression': 1.0, 'best_balanced_recall_risk': 0.868421052631579, 'leave_stage_positive_recall': 0.5789473684210527, 'leave_stage_negative_suppression': 0.1111111111111111, 'leave_stage_balanced_recall_risk': 0.3450292397660819}`
- after: `{'capacity_row_count': 36, 'capacity_label_counts': {'negative_capacity': 10, 'positive_capacity': 26}, 'best_policy': 'stage_family_pure_positive_with_support_2', 'best_positive_recall': 0.7692307692307693, 'best_positive_precision': 1.0, 'best_negative_suppression': 1.0, 'best_balanced_recall_risk': 0.8846153846153846, 'leave_stage_positive_recall': 0.5769230769230769, 'leave_stage_negative_suppression': 0.1, 'leave_stage_balanced_recall_risk': 0.3384615384615384}`
- deltas: `{'capacity_row_count': 8, 'best_positive_recall': 0.03238866396761142, 'best_negative_suppression': 0.0, 'best_balanced_recall_risk': 0.0161943319838056, 'leave_stage_positive_recall': -0.002024291497975783, 'leave_stage_negative_suppression': -0.0111111111111111, 'leave_stage_balanced_recall_risk': -0.006567701304543483}`

## Interpretation

- in_sample_candidate_generation_signal_improved: `True`
- cross_stage_generalization_improved: `False`
- selector_supported: `False`
- capacity_labels_are_not_ownership_labels: `True`
- more_blind_capacity_labels_recommended: `False`
- main_blocker: `stage_family_scope_and_candidate_source_coverage`

## Boundary

The labels improve candidate-generation capacity evidence only. They are not selector labels, runtime inputs, score updates, guardrails, or promotion evidence.
