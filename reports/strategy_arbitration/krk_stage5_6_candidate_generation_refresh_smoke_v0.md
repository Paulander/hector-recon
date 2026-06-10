# KRK Stage 5/6 Candidate-Generation Refresh Smoke v0

This smoke tests the default-off observation-only Stage 5/6 candidate-generation refresh source.

## Decision

- status: `stage5_6_candidate_generation_refresh_wired_default_off_equivalent`
- selector_allowed: `False`
- recommended_next_step: `stage5_6_candidate_generation_refresh_coverage_analysis`

## Summary

- case_count: 2
- refresh_frame_count: 13
- candidate_count_by_source: `{'candidate_move_frame': 41, 'stage_conditioned_candidate_generation_refresh': 13, 'validated_provider_pack': 25}`
- capacity_evidence_counts: `{'negative_capacity': 2, 'positive_capacity': 6, 'positive_capacity_scope': 10, 'unknown_capacity': 61}`
- selected_move_provider_delta_count: 0
- baseline_refresh_frame_count: 0
- invariant_failure_count: 0
- stage7_case_count: 0

## Boundary

The source emits observation frames only. It does not select, score, route, run guardrails, promote Stage 7, or train Stage 8.
