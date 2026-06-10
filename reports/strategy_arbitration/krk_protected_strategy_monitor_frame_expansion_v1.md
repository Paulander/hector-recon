# KRK Protected Strategy Monitor Frame Expansion v1

This replay-free expansion converts protected Stage 4/5/6 StrategyMonitor records into broader-strategy candidate frames. It is non-causal.

## Decision

- status: `protected_strategy_monitor_frames_expanded_non_causal`
- selector_allowed: `False`
- recommended_next_step: `probe_protected_strategy_monitor_frame_source_quality`

## Summary

- frame_count: 85
- frame_count_by_stage: `{'stage4': 20, 'stage5': 30, 'stage6': 35}`
- frame_count_by_strategy_family: `{'terminal.krk.owner_exit_monitor': 24, 'terminal.krk.phase_boundary_monitor': 48, 'terminal.krk.repair_needed_monitor': 13}`
- frame_count_by_associated_outcome: `{'mate': 39, 'max_plies': 46}`
- stage7_challenge_row_count: 0

## Boundary

These frames are source-review evidence only. They do not authorize runtime source expansion, selector training, score changes, guardrails, Stage 7 promotion, or Stage 8 training.
