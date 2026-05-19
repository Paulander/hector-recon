# KRK Internal Terminal Candidates v0

This report defines non-causal InternalTerminalSpec candidates. They are design/evidence objects only.

## Status

- Candidate count: `4`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Candidates

### terminal.krk.local_provider_competition_failed

- Monitor type: `internal_control_arbitration_failure_monitor`
- Maturity status: `internal_terminal_candidate`
- Promotion status: `monitoring_only`
- Source monitor candidates: `['local_provider_competition_failed', 'PlanSelectionNeededMonitor']`
- Source terms: `['local_provider_competition_failed', 'selected provider closed-loop failed', 'current_graph_h40 == max_plies', 'alternative provider/candidate conversion evidence']`
- Missing terms: `['current_owner', 'alternative_provider_known_mate', 'route_conflict']`
- Intended scope: KRK strategy arbitration diagnostics and structural-growth evidence
- Forbidden causal uses: `['choose_provider', 'penalize_provider', 'boost_plan', 'mutate_topology']`
- Potential future consumers: `['GrowthMonitor', 'StrategyArbiter training dataset', 'PlanCapsule entry/abort/handoff diagnostics', 'M3/M4 arbitration-weight evidence after later review']`

### terminal.krk.post_plan_stagnation

- Monitor type: `internal_plan_progress_stagnation_monitor`
- Maturity status: `internal_terminal_candidate`
- Promotion status: `monitoring_only`
- Source monitor candidates: `['post_plan_stagnation', 'PlanSelectionNeededMonitor']`
- Source terms: `['post_plan_stagnation', 'plan_capsule_context', 'max_plies after plan', 'no progress over owned moves']`
- Missing terms: `['handoff_success_after_plan', 'multi_step_progress_required', 'repeated_abstract_state']`
- Intended scope: PlanCapsule self-monitoring and strategy monitor datasets
- Forbidden causal uses: `['force_plan_exit', 'force_provider_selection', 'alter_ttl', 'mutate_topology']`
- Potential future consumers: `['PlanCapsule self-monitoring', 'GrowthMonitor', 'StrategyMonitor datasets']`

### terminal.krk.box_shrink_owner_exit_pressure

- Monitor type: `owner_exit_monitor_candidate`
- Maturity status: `needs_more_evidence`
- Promotion status: `proposed`
- Source monitor candidates: `['box_area_no_longer_decision_relevant', 'OwnerExitMonitor']`
- Source terms: `['active_landmark_label == box_shrink', 'box_area_no_longer_decision_relevant', 'phase boundary near edge', 'mate_basin_readiness or edge/fence/king-support context']`
- Missing terms: `['box_shrink_goal_satisfied', 'validated_handoff_target_available']`
- Intended scope: box_shrink owner-exit diagnostics
- Forbidden causal uses: `['select_next_owner', 'boost_edge_provider', 'boost_fence_provider', 'boost_stage0']`
- Potential future consumers: `['OwnerExitMonitor', 'StrategyArbiter training dataset', 'PlanCapsule handoff diagnostics']`

### terminal.krk.repair_needed_monitor

- Monitor type: `repair_risk_monitor`
- Maturity status: `monitoring_only`
- Promotion status: `monitoring_only`
- Source monitor candidates: `['cut_or_fence_restored_after_move', 'RepairNeededMonitor']`
- Source terms: `['fence_or_cut_repair_affordance', 'cut_or_fence_restored_after_move', 'repair_or_reestablish_cut_available', 'safe_repair_move_exists']`
- Missing terms: `['repair_needed_but_no_safe_repair_available', 'box_area_not_expanded_after_reply']`
- Intended scope: repair-risk and repair-pressure diagnostics
- Forbidden causal uses: `['boost_fence_established', 'play_repair_move', 'route_to_provider']`
- Potential future consumers: `['RepairNeededMonitor', 'GrowthMonitor', 'StrategyArbiter training dataset']`

## Boundaries

No runtime terminal, causal affordance, runtime arbiter, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, topology mutation, or monitor-to-provider routing is authorized.
