# KRK Strategy Arbiter Protected Control Matrix v1

This runtime-test matrix compares baseline, flag-present default-off, and enabled bounded support on protected Stage 4/5/6 labels only.

## Summary

- `default_off_equivalence_passed`: `True`
- `enabled_has_no_no_move_or_draw_spike`: `True`
- `enabled_conversion_not_worse`: `True`
- `enabled_support_total`: `15`

## Rows

- `edge_trap_wrong_tempo` default_off=`True` enabled_mate=`0` baseline_mate=`0` support=`5`
- `fence_established` default_off=`True` enabled_mate=`1` baseline_mate=`1` support=`5`
- `drive_to_edge` default_off=`True` enabled_mate=`1` baseline_mate=`1` support=`5`

## Decision

- Status: `protected_control_matrix_passed`
- Recommended next step: `run_small_protected_control_matrix_or_guardrail_smoke`
