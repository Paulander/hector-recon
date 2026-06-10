# KRK Exact Trace Enrichment Sandbox v0

This report validates the approved default-off exact trace enrichment sandbox. The sandbox emits candidate-generation frames only; it does not select, score, route, suppress, mutate topology, promote Stage 7, or train Stage 8.

## Decision

- status: `exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis`
- selector_allowed: `False`
- recommended_next_step: `non_causal_coverage_analysis_over_exact_trace_enrichment_frames`

## Summary

- case_count: `1`
- default_off_equivalence_passed: `True`
- enabled_smoke_status: `passed`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- selected_score_delta_count: `0`
- score_delta_count: `0`
- baseline_exact_frame_count: `0`
- generated_frame_count: `3`
- generated_frame_count_by_stage: `{'stage5': 3}`
- generated_frame_count_by_provider_family: `{'edge_trap': 3}`
- protected_frame_count: `3`
- stage7_held_out_frame_count: `0`
- direct_request_false_count: `3`
- score_delta_zero_count: `3`
- truncation_count: `0`
- truncated_frame_count: `0`
- invalid_frame_count: `0`
- runtime_behavior_changed: `False`

## Boundary

Frames use `causal_status = candidate_generation_only`, `direct_request = false`, and `score_delta = 0.0`. The approved scope is Stage 5/6 exact trace enrichment only; Stage 4 remains excluded pending separate review and Stage 7 remains held-out challenge only.
