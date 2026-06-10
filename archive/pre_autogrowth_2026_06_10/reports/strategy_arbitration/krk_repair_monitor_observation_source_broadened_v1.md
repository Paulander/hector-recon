# KRK Repair-Monitor Observation Source Broadened Sample v1

This is a protected-only broader sample for the default-off repair-monitor observation source. It is not selector or guardrail evidence.

## Decision

- status: `repair_monitor_observation_source_broadened_default_off_equivalent`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `repair_monitor_observation_source_non_causal_quality_review`

## Summary

- case_count: 6
- case_count_by_stage: `{'stage4': 1, 'stage5': 4, 'stage6': 1}`
- repair_monitor_frame_count: 6
- candidate_count_by_source: `{'broader_strategy_candidate': 6, 'candidate_move_frame': 126, 'validated_provider_pack': 70}`
- risk_term_counts: `{'post_fence_conversion_needed': 6, 'repair_or_reestablish_cut_available': 6, 'rook_safe': 6}`
- selected_provider_counts: `{'krk.edge_trap_close': 2, 'krk.fence_established': 1, 'krk.stage0_basin': 3}`
- selected_move_provider_delta_count: 0
- baseline_repair_monitor_frame_count: 0
- invariant_failure_count: 0
- stage7_case_count: 0

## Boundary

The broadened sample only checks observability and invariants. It does not authorize selector behavior, score changes, routing, guardrails, Stage 7 promotion, or Stage 8 training.
