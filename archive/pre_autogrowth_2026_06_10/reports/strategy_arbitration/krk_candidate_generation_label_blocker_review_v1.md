# KRK Candidate-Generation Label Blocker Review v1

This review closes the bounded candidate-move capacity-label slice. It remains non-causal.

## Decision

- status: `candidate_generation_label_coverage_underpowered_selector_blocked`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `design_candidate_proposal_quality_prioritization_review`

## Evidence

- broadened_frame_count: 569
- candidate_move_frame_count: 363
- protected_candidate_move_count: 292
- protected_annotated_candidate_move_count: 22
- protected_annotation_recall: `0.075`
- bounded_label_count: 12
- bounded_label_positive_capacity_count: 11
- bounded_label_negative_capacity_count: 1
- missing_expected_sources: `['broader_strategy_candidate', 'plan_capsule_sequence_candidate']`

## Blockers

- `candidate_capacity_mostly_unknown`
- `generated_set_contains_negative_capacity_candidates`
- `plan_capsule_sequence_candidates_not_observed`
- `broader_strategy_candidates_not_observed`
- `candidate_move_annotation_coverage_too_sparse`
- `blind_label_expansion_risk`

## Interpretation

- candidate_generation_observation_is_safe: `True`
- candidate_move_capacity_annotation_path_exists: `True`
- candidate_move_annotation_is_too_sparse_for_selector_review: `True`
- bounded_labels_found_positive_capacity: `True`
- bounded_labels_found_negative_capacity: `True`
- more_blind_label_farming_not_recommended: `True`
- capacity_labels_are_not_ownership_labels: `True`

## Boundary

The next step should improve candidate proposal quality/prioritization before further labels or selector review. Do not implement a selector, route, score change, guardrail campaign, Stage 7 promotion, or Stage 8 training.
