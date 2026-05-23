# KRK Stage 5/6 Candidate-Generation Refresh Quality Review v0

This quality review keeps the Stage 5/6 refresh source as trace/candidate-generation context only. It does not authorize selection, scoring, guardrails, or promotion.

## Decision

- status: `stage5_6_candidate_generation_refresh_quality_trace_only_retained`
- selector_allowed: `False`
- recommended_next_step: `fold_stage5_6_refresh_frames_into_strategy_sequence_dataset`

## Summary

- case_count: 4
- refresh_frame_count: 38
- stage7_case_count: 0
- invariant_failure_count: 0
- selected_move_provider_delta_count: 0
- baseline_refresh_frame_count: 0
- refresh_provider_counts: `{'krk.edge_trap_close': 6, 'krk.edge_trap_enemy_between': 11, 'krk.edge_trap_wrong_tempo': 5, 'krk.fence_established': 3, 'krk.stage0_basin': 13}`
- capacity_evidence_counts: `{'negative_capacity': 2, 'positive_capacity': 16, 'positive_capacity_scope': 30, 'unknown_capacity': 120}`
- trace_usable_for_candidate_generation_context: `True`

## Selector Blockers

- `capacity_evidence_not_runtime_ownership_label`
- `sample_size_small_for_selector_or_guardrails`
- `negative_capacity_absence_in_refresh_scope_does_not_prove_safe_selection`
- `stage4_stage7_stage8_explicitly_excluded`
