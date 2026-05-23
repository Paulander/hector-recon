# KRK Candidate-Generation Refresh Sandbox v0

This report validates the approved default-off candidate-generation refresh sandbox. The sandbox emits candidate-generation frames only; it does not select, score, route, suppress, mutate topology, promote Stage 7, or train Stage 8.

## Decision

- status: `candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis`
- selector_allowed: `False`
- recommended_next_step: `non_causal_coverage_analysis_over_emitted_candidate_generation_frames`

## Summary

- case_count: `3`
- default_off_equivalence_passed: `True`
- enabled_smoke_status: `passed`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- baseline_refresh_frame_count: `0`
- generated_frame_count: `25`
- generated_frame_count_by_stage: `{'stage5': 24, 'stage6': 1}`
- generated_frame_count_by_provider_family: `{'edge_trap': 19, 'fence_established': 3, 'stage0_basin': 3}`
- protected_frame_count: `25`
- stage7_held_out_frame_count: `0`
- direct_request_false_count: `25`
- score_delta_zero_count: `25`
- truncation_count: `2`
- truncated_frame_count: `24`
- invalid_frame_count: `0`
- runtime_behavior_changed: `False`

## Boundary

Frames use `causal_status = candidate_generation_only`, `direct_request = false`, and `score_delta = 0.0`. The approved scope is Stage 5/6 only; Stage 4 remains excluded pending separate review and Stage 7 remains held-out challenge only.
