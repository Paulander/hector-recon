# KRK Repair-Monitor Observation Source Smoke v1

This smoke tests the default-off observation-only broader-strategy source for `terminal.krk.repair_needed_monitor`.

## Decision

- status: `repair_monitor_observation_source_wired_default_off_equivalent`
- selector_allowed: `False`
- recommended_next_step: `repair_monitor_observation_source_coverage_analysis`

## Summary

- case_count: 3
- repair_monitor_frame_count: 3
- candidate_count_by_source: `{'broader_strategy_candidate': 3, 'candidate_move_frame': 63, 'validated_provider_pack': 36}`
- selected_move_provider_delta_count: 0
- baseline_repair_monitor_frame_count: 0
- invariant_failure_count: 0
- stage7_case_count: 0

## Boundary

The source emits observation frames only. It does not select, score, route, run guardrails, promote Stage 7, or train Stage 8.
