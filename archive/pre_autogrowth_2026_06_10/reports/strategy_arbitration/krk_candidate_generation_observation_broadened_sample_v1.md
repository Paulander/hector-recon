# KRK Candidate-Generation Observation Broadened Sample v1

This is a bounded observation-only runtime sample. Generated frames remain non-causal and are not used for selection.

## Decision

- status: `broadened_observation_sample_supports_coverage_analysis`
- default_off_equivalence_passed: `True`
- observation_frames_emitted: `True`
- frame_invariants_passed: `True`
- selector_allowed: `False`
- guardrails_allowed: `False`

## Summary

- case_count: 19
- case_count_by_stage: `{'stage4': 5, 'stage5': 6, 'stage6': 4, 'stage7': 4}`
- emitted_frame_count: 569
- frame_count_by_candidate_source: `{'candidate_move_frame': 363, 'validated_provider_pack': 206}`
- capacity_evidence_counts: `{'held_out_challenge': 111, 'negative_capacity': 5, 'positive_capacity': 11, 'unknown_capacity': 442}`
- protected_status_counts: `{'held_out_stage7_challenge': 111, 'protected_control': 16, 'protected_or_unknown': 442}`
- stage7_heldout_case_count: 4
- stage7_readiness_training_row_count: 0
- selected_move_or_provider_delta_count: 0
- default_off_observation_case_count: 0
- invariant_failure_count: 0

## Stage / Source Coverage

- frame_count_by_stage_and_candidate_source: `{'stage4': {'candidate_move_frame': 89, 'validated_provider_pack': 56}, 'stage5': {'candidate_move_frame': 124, 'validated_provider_pack': 67}, 'stage6': {'candidate_move_frame': 79, 'validated_provider_pack': 43}, 'stage7': {'candidate_move_frame': 71, 'validated_provider_pack': 40}}`
- case_count_by_source_artifact: `{'reports/krk_protected_provider_coverage_frames_v0.json': 6, 'reports/krk_ranked_strategy_proposal_frames_v1.json': 13}`

## Boundary

This artifact does not authorize selector implementation, score changes, guardrails, promotion, or Stage 8 training.
