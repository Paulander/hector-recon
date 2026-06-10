# KRK Candidate-Generation Observation Sandbox v0

This runtime smoke exercises the approved default-off observation-only candidate-generation sandbox.

## Decision

- status: `observation_sandbox_ready_for_non_causal_coverage_analysis`
- default_off_equivalence_passed: `True`
- observation_frames_emitted: `True`
- frame_invariants_passed: `True`
- selector_allowed: `False`

## Summary

- generated_candidate_count: 93
- generated_candidate_count_by_source: `{'candidate_move_frame': 58, 'validated_provider_pack': 35}`
- protected_candidate_count: 5
- stage7_heldout_candidate_count: 27
- capacity_evidence_counts: `{'held_out_challenge': 27, 'negative_capacity': 2, 'positive_capacity': 3, 'unknown_capacity': 61}`
- selected_move_or_provider_changed: `False`
- playout_result_or_plies_changed: `False`

## Cases

### protected_stage5

- source_stage: `stage5`
- held_out: `False`
- selected_move_provider_score_equivalent: `True`
- playout_equivalent: `True`
- enabled_candidate_count: 34

### protected_stage6

- source_stage: `stage6`
- held_out: `False`
- selected_move_provider_score_equivalent: `True`
- playout_equivalent: `True`
- enabled_candidate_count: 32

### heldout_stage7

- source_stage: `stage7`
- held_out: `True`
- selected_move_provider_score_equivalent: `True`
- playout_equivalent: `True`
- enabled_candidate_count: 27

