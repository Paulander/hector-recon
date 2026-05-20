# KRK Control-Plane Filtered Frames v0

This replay-free export adds non-causal dedupe and benchmark-role metadata to the control-plane frames. It does not change runtime behavior or authorize a sandbox.

## Summary

- Frames: `33`
- Unique states: `24`
- Duplicate state IDs: `['state.02feb8593cc6', 'state.256a3da30f0f', 'state.2c1d6da27ea1', 'state.69711173114a', 'state.699f0003a511', 'state.d1f052d2cab2']`
- Benchmark role counts: `{'internal_monitor_quality_analysis': 33, 'plan_window_context_only_stage7': 4, 'stage7_boundary_heldout_challenge': 7, 'sequence_policy_context_only_stage7': 3, 'strategy_arbitration_benchmark': 24}`
- Strategy-ready frames: `24`
- Strategy-ready by stage: `{'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Stage 7 boundary held-out frames: `7`
- Context-only frames: `5`
- Dropped duplicate monitors: `0`
- Dropped duplicate plan windows: `9`
- New playouts added: `0`

## Readiness

- `offline_strategy_arbitration_probe`: `ready_on_strategy_arbitration_benchmark_frames`
- `offline_sequence_policy_benchmark`: `blocked_general_krk_stage7_only`
- `runtime_sandbox`: `blocked`
- `stage7_promotion`: `blocked`
- `stage8_training`: `blocked`

## Recommended Next Slice

`offline_strategy_arbitration_probe_filtered_v0`
