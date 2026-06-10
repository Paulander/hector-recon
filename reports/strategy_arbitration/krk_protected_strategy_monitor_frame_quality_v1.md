# KRK Protected Strategy Monitor Frame Quality v1

This probe summarizes protected broader-strategy monitor frames. It does not authorize runtime source expansion.

## Decision

- status: `protected_strategy_monitor_frames_have_monitor_signal`
- selector_allowed: `False`
- recommended_next_step: `protected_strategy_monitor_observation_source_review_packet`

## Summary

- frame_count: 85
- strong_failure_family_count: 1
- strong_success_family_count: 0
- ambiguous_family_count: 2

## Family Stats

- `terminal.krk.owner_exit_monitor`: count=24 success_precision=`0.500` failure_precision=`0.500` outcomes=`{'mate': 12, 'max_plies': 12}`
- `terminal.krk.phase_boundary_monitor`: count=48 success_precision=`0.500` failure_precision=`0.500` outcomes=`{'mate': 24, 'max_plies': 24}`
- `terminal.krk.repair_needed_monitor`: count=13 success_precision=`0.231` failure_precision=`0.769` outcomes=`{'mate': 3, 'max_plies': 10}`

## Boundary

Monitor frames are candidates, not actions. Runtime observation expansion still requires a separate review packet.
