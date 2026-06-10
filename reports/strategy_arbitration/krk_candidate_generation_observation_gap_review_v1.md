# KRK Candidate-Generation Observation Gap Review v1

This review uses broadened observation-only runtime frames. It remains non-causal and does not authorize selection.

## Decision

- status: `observation_gap_review_blocks_selector_recommends_capacity_annotation`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `non_causal_candidate_move_capacity_annotation_review`

## Summary

- frame_count: 569
- source_counts: `{'candidate_move_frame': 363, 'validated_provider_pack': 206}`
- capacity_evidence_counts: `{'held_out_challenge': 111, 'negative_capacity': 5, 'positive_capacity': 11, 'unknown_capacity': 442}`
- protected_status_counts: `{'held_out_stage7_challenge': 111, 'protected_control': 16, 'protected_or_unknown': 442}`
- unknown_capacity_ratio: `0.777`
- negative_capacity_ratio: `0.009`
- missing_expected_sources: `['broader_strategy_candidate', 'plan_capsule_sequence_candidate']`
- invariant_failure_count: 0

## Selector Blockers

- `candidate_capacity_mostly_unknown`
- `generated_set_contains_negative_capacity_candidates`
- `plan_capsule_sequence_candidates_not_observed`
- `broader_strategy_candidates_not_observed`

## Interpretation

- candidate_generation_visible: `True`
- validated_provider_pack_visible: `True`
- candidate_move_frames_visible: `True`
- plan_capsule_sequence_candidates_visible: `False`
- broader_strategy_candidates_visible: `False`
- candidate_move_capacity_annotation_needed: `True`
- provider_pack_contains_positive_capacity: `True`
- provider_pack_contains_negative_capacity: `True`

## Boundary

The next step is capacity/quality annotation for visible candidate frames, not selector implementation or guardrails.
