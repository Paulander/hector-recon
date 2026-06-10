# Stage 7 Selected Failure Path Audit v0

Decision: `mixed_selected_path_gap_no_runtime_patch`

This is a replay-free audit. It does not change runtime behavior, train Stage 8, promote Stage 7, use DTM/tablebase at runtime, or mutate topology.

## Summary

- selected_failure_state_count: `4`
- selected_provider_counts: `{'krk.stage0_basin': 4}`
- selected_failure_path_class_counts: `{'continuation_capacity_or_sequence_policy_gap': 2, 'strategy_ownership_gap_existing_provider_can_convert': 2}`
- internal_terminal_hit_counts: `{'terminal.krk.post_plan_stagnation': 2, 'terminal.krk.box_shrink_owner_exit_pressure': 1, 'terminal.krk.repair_needed_monitor': 4, 'terminal.krk.local_provider_competition_failed': 2}`
- strategy_monitor_type_counts: `{'PhaseBoundaryMonitor': 2, 'RepairNeededMonitor': 4, 'PlanSelectionNeededMonitor': 4}`
- abstention_stage7_penalized_count: `12`
- abstention_stage7_selected_penalized_count: `0`
- abstention_target_conversion_delta_mates: `0`

## Selected Failure Rows

| State | Selected provider | Selected move | Path class | Forced mating provider | Internal terminals | Strategy monitors |
| --- | --- | --- | --- | --- | --- | --- |
| `state.0afbf11aa123` | `krk.stage0_basin` | `a3e3` | `continuation_capacity_or_sequence_policy_gap` | `None` | terminal.krk.post_plan_stagnation, terminal.krk.box_shrink_owner_exit_pressure, terminal.krk.repair_needed_monitor | PhaseBoundaryMonitor, PhaseBoundaryMonitor, RepairNeededMonitor, PlanSelectionNeededMonitor |
| `state.38aed2f35911` | `krk.stage0_basin` | `a3a5` | `continuation_capacity_or_sequence_policy_gap` | `None` | terminal.krk.post_plan_stagnation, terminal.krk.repair_needed_monitor | RepairNeededMonitor, PlanSelectionNeededMonitor |
| `state.ac0b7ed500ea` | `krk.stage0_basin` | `a1a4` | `strategy_ownership_gap_existing_provider_can_convert` | `krk.fence_established` | terminal.krk.local_provider_competition_failed, terminal.krk.repair_needed_monitor | RepairNeededMonitor, PlanSelectionNeededMonitor |
| `state.ff6652c8832c` | `krk.stage0_basin` | `a4e4` | `strategy_ownership_gap_existing_provider_can_convert` | `krk.drive_to_edge` | terminal.krk.local_provider_competition_failed, terminal.krk.repair_needed_monitor | RepairNeededMonitor, PlanSelectionNeededMonitor |

## Interpretation

The actual selected Stage 7 max-plies path is mostly stage0_basin ownership, but it splits into two different problem classes: some states have an existing forced provider that converts, while others remain unresolved even under forced providers/legal-first h40 evidence.

The runtime selector penalized suggestions in the Stage 7 smoke, but selected_penalized_count stayed 0. It therefore did not target the move/provider that actually won selection in the sampled failure path.

## Recommended Next Step

`do_not_tune_abstention; build a non-causal selected-path target spec that separately models strategy ownership gaps and sequence/continuation gaps`

## Forbidden Next Steps

- `increase abstention penalty`
- `scale runtime selector validation`
- `promote Stage 7`
- `train Stage 8`
- `add support adapter or provider penalty`
- `make internal terminals causal`
