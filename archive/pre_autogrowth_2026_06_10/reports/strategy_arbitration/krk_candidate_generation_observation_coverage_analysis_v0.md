# KRK Candidate-Generation Observation Coverage Analysis v0

This analyzes emitted observation-only candidate frames. It does not authorize selection or further runtime changes.

## Summary

- generated_candidate_count: 93
- sampled_frame_count: 93
- candidate_count_by_source: `{'candidate_move_frame': 58, 'validated_provider_pack': 35}`
- capacity_evidence_counts: `{'held_out_challenge': 27, 'negative_capacity': 2, 'positive_capacity': 3, 'unknown_capacity': 61}`
- protected_status_counts: `{'held_out_stage7_challenge': 27, 'protected_control': 5, 'protected_or_unknown': 61}`
- invariant_failure_count: 0
- selected_move_or_provider_changed: `False`
- playout_result_or_plies_changed: `False`

## Interpretation

- candidate_generation_visible: `True`
- protected_and_heldout_status_visible: `True`
- positive_and_negative_capacity_visible: `True`
- candidate_move_hypotheses_visible: `True`
- selector_still_blocked: `True`
- guardrails_still_blocked: `True`

## Decision

- status: `observation_frames_usable_for_non_causal_coverage_analysis`
- recommended_next_step: `broaden_observation_sample_before_selector_review`
- selector_allowed: `False`
- guardrails_allowed: `False`
