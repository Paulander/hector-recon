# KRK Strategy Arbiter Support Sensitivity v1

This one-ply runtime-test measures how much bounded support is needed to change selected ownership. It does not run conversion playouts.

## Summary

- `low_support_cap`: `5.0`
- `stage7_first_provider_change_support`: `None`
- `stage7_changes_under_low_support_cap`: `False`
- `protected_labels_with_provider_change`: `['drive_to_edge']`
- `protected_labels_with_low_support_change`: `[]`
- `support_scale_risk`: `high_support_changes_protected_ownership_before_safe_stage7_evidence`

## Rows

- `edge_trap_wrong_tempo` baseline=`krk.stage0_basin` first_change=`none`
- `fence_established` baseline=`krk.stage0_basin` first_change=`none`
- `drive_to_edge` baseline=`krk.stage0_basin` first_change=`support=50.0 provider=krk.edge_trap_close`
- `box_shrink` baseline=`krk.fence_established` first_change=`none`

## Decision

- Status: `support_sensitivity_measured`
- Recommended next step: `do_not_raise_support_without_arbitration_objective_review`
