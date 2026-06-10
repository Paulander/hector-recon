# KRK Strategy Arbiter Protected Control Matrix v2

This runtime-test matrix scales the protected Stage 4/5/6 smoke to three samples per label. Stage 7 remains excluded.

## Summary

- `default_off_equivalence_passed`: `True`
- `enabled_has_no_no_move_or_draw_spike`: `True`
- `enabled_has_no_conversion_regression`: `True`
- `enabled_support_total`: `45`

## Rows

- `edge_trap_wrong_tempo` default_off=`True` conversion_delta=`0` baseline_playouts=`{'mate': 3}` enabled_playouts=`{'mate': 3}` support=`15`
- `fence_established` default_off=`True` conversion_delta=`0` baseline_playouts=`{'mate': 2, 'max_plies': 1}` enabled_playouts=`{'mate': 2, 'max_plies': 1}` support=`15`
- `drive_to_edge` default_off=`True` conversion_delta=`0` baseline_playouts=`{'max_plies': 3}` enabled_playouts=`{'max_plies': 3}` support=`15`

## Decision

- Status: `protected_control_matrix_v2_passed`
- Recommended next step: `architecture_review_before_stage7_challenge_or_scale_guardrails`
