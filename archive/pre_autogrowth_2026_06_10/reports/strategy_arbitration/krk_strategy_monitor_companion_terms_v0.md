# KRK Strategy Monitor Companion Terms v0

## Purpose

This report follows `krk_strategy_monitor_records_v0`. It proposes companion terms for the mixed or failure-oriented monitor candidates.

It is non-causal design only. It does not implement runtime terminals, a runtime arbiter, Stage 7 repair, Stage 7 promotion, Stage 8 training, runtime DTM/tablebase use, or gameplay-time topology mutation.

## Source Evidence

Input artifacts:

- `reports/strategy_arbitration/krk_feature_candidate_validation_v0.json`
- `reports/strategy_arbitration/krk_strategy_monitor_v0_plan.json`
- `reports/strategy_arbitration/krk_strategy_monitor_records_v0.json`

Current monitor extraction:

- `PhaseBoundaryMonitor`: 52 records, mixed outcomes.
- `OwnerExitMonitor`: 25 records, mixed outcomes.
- `RepairNeededMonitor`: 22 records, failure-oriented.
- `PlanSelectionNeededMonitor`: 9 records, Stage7-only failure-oriented.
- `king_support_conversion_affordance`: rejected as too broad.

Conclusion:

```text
The monitors need companion terms before any causal or sandbox use.
```

## Companion Term Sets

### Phase Boundary Companions

Target monitors:

- `PhaseBoundaryMonitor`
- `edge_net_affordance`
- `phase_boundary_near_edge`

Candidate companion terms:

- `current_owner`
- `successful_next_provider`
- `safe_edge_net_tighten_move_exists`
- `safe_check_or_cut_tighten_move_exists`
- `edge_net_pressure_increases_after_move`
- `draw_risk_absent_after_edge_net_move`
- `king_support_aligned_with_edge_net`

Purpose:

```text
Separate "near edge" as a neutral phase context from "near edge and edge-net ownership is productive."
```

Why this is needed:

The current near-edge/edge-net predicates match successful and failed states at roughly equal rates. They can monitor phase ambiguity, but they cannot yet identify a winning owner or move family.

Minimum next evidence:

- Replay-free extraction of current owner/provider for each matching record.
- Existing-label comparison of successful-next-provider versus failed current-owner cases.
- If replay-free labels are insufficient, add only a small h40 label set for owner-specific outcomes.

### Owner Exit Companions

Target monitor:

- `OwnerExitMonitor`
- `box_shrink_exit_condition`

Candidate companion terms:

- `active_landmark_label == box_shrink`
- `box_shrink_goal_satisfied`
- `box_area_no_longer_decision_relevant`
- `edge_net_affordance_scoped`
- `mate_basin_readiness`
- `validated_handoff_target_available`
- `box_shrink_owner_repeats_without_progress`

Purpose:

```text
Detect when box_shrink should release ownership without deciding which provider should take over.
```

Why this is needed:

`box_shrink_exit_condition` is a plausible owner-release signal, but it is not a provider-selection signal. It needs a separately validated next-owner/handoff label.

Minimum next evidence:

- Pair `box_shrink_exit_condition` with active owner and next selected provider.
- Track whether release/handoff would have gone to a provider with known successful continuation evidence.
- Keep the term as monitor-only until the next-provider relation is validated.

### Repair Needed Companions

Target monitor:

- `RepairNeededMonitor`
- `fence_or_cut_repair_affordance`

Candidate companion terms:

- `repair_or_reestablish_cut_available`
- `safe_repair_move_exists`
- `rook_safe_after_repair`
- `box_area_not_expanded_after_reply`
- `cut_or_fence_restored_after_move`
- `repair_preserves_mate_basin_progress`
- `repair_needed_but_no_safe_repair_available`

Purpose:

```text
Separate repair pressure from repair affordance.
```

Why this is needed:

The current repair term is failure-correlated. It says the current strategy is unstable, not that a particular repair move or provider should be boosted.

Minimum next evidence:

- Add move/post-move labels that distinguish safe repair availability from broken-fence risk.
- Audit whether existing providers can exploit safe repair opportunities when forced.
- Do not use this as move support until `safe_repair_move_exists` and post-reply preservation terms separate success from failure.

### Plan Selection Companions

Target monitor:

- `PlanSelectionNeededMonitor`
- `plan_selection_needed`

Candidate companion terms:

- `plan_capsule_context`
- `handoff_success_after_plan`
- `post_plan_stagnation`
- `local_provider_competition_failed`
- `selected_provider_closed_loop_failed`
- `multi_step_progress_required`
- `single_move_affordance_insufficient`
- `growth_pressure_repeated_family`

Purpose:

```text
Identify when local provider competition is insufficient and higher-level plan/strategy selection should be audited.
```

Why this is needed:

This monitor is Stage7-only in the current data and failure-oriented. It is useful as internal control/growth evidence, not as a runtime routing signal.

Minimum next evidence:

- Add cross-stage plan-selection examples before generalizing.
- Separate "plan entry was needed" from "current plan policy succeeded."
- Keep it non-causal and monitoring-only until cross-stage evidence exists.

### King Support Redesign

Rejected source:

- `king_support_conversion_affordance`

Replacement candidate concepts:

- `king_support_improvement_move_exists`
- `king_support_improves_after_move`
- `king_support_improves_after_reply`
- `king_support_aligned_with_cut_or_edge_net`
- `king_support_needed_for_current_phase`

Purpose:

```text
Replace static king-support availability with action-relevant king-support progress.
```

Why this is needed:

Static king-support availability matches almost all records and is too broad. It should not be kept as a feature definition.

Minimum next evidence:

- Move-level or post-move support-improvement labels.
- Companion phase labels showing when king support matters for edge-net/fence/mate-basin ownership.

## Non-Causal Extraction Proposal

If more evidence is needed, the next allowed diagnostic is:

```text
reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.json
reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.md
```

Scope:

- replay-free first,
- existing artifacts first,
- no runtime behavior changes,
- no h40 relabeling unless explicitly reviewed,
- no causal terminal implementation.

The audit should answer:

- Which companion terms already exist in the dataset?
- Which companions require new visible extraction?
- Which monitor records would be narrowed by each companion?
- Which companions are Stage7-only versus cross-stage?

## Stop Conditions

Stop before:

- runtime terminals,
- a runtime arbiter,
- Stage 7 repair,
- Stage 7 promotion,
- Stage 8 training,
- runtime DTM/tablebase,
- topology mutation,
- any monitor-to-provider routing path.

## Current Recommendation

Do not implement any companion term causally.

The safest next step is a replay-free companion-term availability audit. If availability is poor, pause for architecture review instead of adding new extraction code blindly.
