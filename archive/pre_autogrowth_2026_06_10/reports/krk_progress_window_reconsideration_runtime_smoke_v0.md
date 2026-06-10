# KRK Progress-Window Reconsideration Runtime Smoke v0

This is a default-off runtime-test sandbox smoke. It is not a promotion or default policy change.

## Summary

- `default_off_equivalence_passed`: `True`
- `protected_label_count`: `3`
- `targeted_row_count`: `2`
- `enabled_supported_total`: `518`
- `enabled_selected_supported_total`: `14`
- `targeted_monitor_confirmed_events`: `14`
- `targeted_candidate_intersection_events`: `20`
- `target_failure_row_count`: `1`
- `improved_target_failure_count`: `0`
- `safe_regression_count`: `0`

## Protected Controls

- `edge_trap_wrong_tempo` default_off=`True` baseline=`{'max_plies': 1}` enabled=`{'max_plies': 1}` supported=`0`
- `fence_established` default_off=`True` baseline=`{'mate': 1}` enabled=`{'mate': 1}` supported=`0`
- `drive_to_edge` default_off=`True` baseline=`{'mate': 1}` enabled=`{'mate': 1}` supported=`0`

## Targeted Progress-Window Rows

- `cp.krk.state.ea634c29ece7` target_failure=`True` default_off=`True` baseline=`max_plies/40` enabled=`max_plies/40` selected_supported=`14` monitor_events=`14` candidate_intersections=`16`
- `cp.krk.state.c732b2d6dc56` target_failure=`False` default_off=`True` baseline=`mate/7` enabled=`mate/7` selected_supported=`0` monitor_events=`0` candidate_intersections=`4`

## Decision

- status: `runtime_smoke_activation_observed_no_target_improvement`
- next: `quarantine_or_refine_reconsideration_policy_before_guardrails`
