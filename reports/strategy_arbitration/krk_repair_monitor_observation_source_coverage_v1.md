# KRK Repair-Monitor Observation Source Coverage v1

This analyzes emitted repair-monitor observation frames. It does not authorize selection or guardrails.

## Decision

- status: `repair_monitor_observation_source_coverage_ready_for_guarded_analysis`
- selector_allowed: `False`
- recommended_next_step: `broaden_repair_monitor_observation_sample_non_causal`

## Summary

- repair_monitor_frame_count: 3
- frame_count_by_stage: `{'stage4': 1, 'stage5': 1, 'stage6': 1}`
- risk_term_counts: `{'post_fence_conversion_needed': 3, 'repair_or_reestablish_cut_available': 3, 'rook_safe': 3}`
- invariant_failure_count: 0
- stage7_case_count: 0
- selected_move_provider_delta_count: 0
