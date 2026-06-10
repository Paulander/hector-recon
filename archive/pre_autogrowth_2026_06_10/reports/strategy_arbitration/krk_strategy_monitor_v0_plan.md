# KRK Strategy Monitor v0 Plan

## Purpose

The KRK missing-feature validation is accepted as a monitor/internal-terminal result, not as a causal affordance result.

Decision:

```text
Do not implement any of the six candidates as causal move-support affordances.
```

Interpretation:

```text
missing_feature_first
```

means the current ontology is under-specified, but the proposed terms are not clean enough to drive behavior. The next architecture step is a non-causal KRK Strategy Monitor design.

This plan does not implement runtime control, causal terminals, a runtime arbiter, Stage 7 repair, Stage 7 promotion, Stage 8 training, runtime DTM/tablebase use, or gameplay-time topology mutation.

## Candidate Typing Summary

### `edge_net_affordance`

- Status: `needs_companion_terms`
- Type: possible future affordance / phase context
- Causal status: not causal
- Interpretation: edge-net pressure appears in both mate and max-plies contexts, so it cannot yet license moves or providers.
- Needed companion terms: `safe_edge_net_tighten_move_exists`, `king_support_conversion_affordance`, `draw_risk_absent`.

### `phase_boundary_near_edge`

- Status: `needs_companion_terms`
- Type: phase-boundary monitor
- Causal status: not causal
- Interpretation: near-edge context is broad and mixed-outcome; it may monitor when local stage ownership is questionable.
- Needed companion terms: `box_area_relevance`, `edge_net_pressure_proxy`, `current_owner`, `successful_next_provider`.

### `king_support_conversion_affordance`

- Status: `reject_or_too_broad_as_defined`
- Type: rejected feature definition
- Causal status: not causal
- Interpretation: static king support is too common to identify a useful affordance.
- Replacement direction: split static support from action-relevant support improvement.

### `box_shrink_exit_condition`

- Status: `possible_exit_condition_needs_evidence`
- Type: owner-exit / handoff monitor
- Causal status: not causal
- Interpretation: this may identify when `box_shrink` should release control, but it does not identify the next provider.
- Needed companion terms: `active_landmark_label == box_shrink`, `edge_net_affordance`, `mate_basin_readiness`.

### `fence_or_cut_repair_affordance`

- Status: `risk_failure_monitor`
- Type: internal repair-needed monitor
- Causal status: not move-support affordance
- Interpretation: failure-correlated repair pressure should monitor instability, not boost a provider.
- Needed companion terms: `repair_or_reestablish_cut_available`, `rook_safe_after_repair`, `box_area_not_expanded_after_reply`.

### `plan_selection_needed`

- Status: `stage7_only_growth_pressure_internal_monitor`
- Type: plan/strategy-selection-needed monitor
- Causal status: not causal
- Interpretation: this is a Stage7-only internal control/growth-pressure signal; it says local provider competition is insufficient.
- Needed companion terms: `plan_capsule_context`, `handoff_success_after_plan`, `post_plan_stagnation`.

## Monitor Classes

### `PhaseBoundaryMonitor`

Detects when a local stage concept may no longer be the right owner.

Candidate sources:

- `phase_boundary_near_edge`
- scoped `edge_net_affordance`
- scoped `box_shrink_exit_condition`

Output meaning:

```text
current owner may be operating outside its stable phase
```

It must not choose the next provider.

### `OwnerExitMonitor`

Detects when the current skill should release ownership or hand off.

Candidate sources:

- `box_shrink_exit_condition`
- phase-boundary context
- successful-next-provider evidence, when available

Output meaning:

```text
current owner should be audited for release/handoff
```

It must not boost any provider unless a future sandbox separately validates the next provider.

### `RepairNeededMonitor`

Detects fence/cut/rook/king-support instability.

Candidate sources:

- `fence_or_cut_repair_affordance`
- future action-relevant repair availability terms

Output meaning:

```text
current strategy is unstable and repair or handoff may be needed
```

It is a risk monitor, not a move-support affordance.

### `PlanSelectionNeededMonitor`

Detects that local providers are insufficient and a higher-level plan selector should arbitrate.

Candidate sources:

- `plan_selection_needed`
- Plan Capsule owned-window failures
- repeated max-plies under selected provider ownership

Output meaning:

```text
local provider competition is not enough here
```

It must not become a hidden runtime controller.

### `GrowthPressureMonitor`

Records repeated failure patterns as structural-growth evidence only.

Candidate sources:

- repeated Stage7 residual failures
- repair-needed monitor repetition
- plan-selection-needed monitor repetition

Output meaning:

```text
this context may justify future structural candidate generation
```

It remains non-causal unless later compiled/promoted through explicit visible topology.

## StrategyMonitorRecord Schema

Proposed non-causal record:

```text
StrategyMonitorRecord:
  schema_version = strategy_monitor_record.v1
  monitor_id
  monitor_type
  source_candidate_id
  active_landmark_label
  state_id
  fen
  source_terms
  missing_terms
  confidence
  associated_outcome
  suggested_action_class
  causal_status = non_causal
  promotion_status = proposed / monitoring_only / rejected
  notes
```

Field semantics:

- `monitor_id`: stable identifier for the monitor instance or definition.
- `monitor_type`: one of `PhaseBoundaryMonitor`, `OwnerExitMonitor`, `RepairNeededMonitor`, `PlanSelectionNeededMonitor`, `GrowthPressureMonitor`.
- `source_candidate_id`: original StructuralCandidate or feature-candidate source.
- `source_terms`: visible terms supporting monitor activation.
- `missing_terms`: visible companion terms still needed before sandbox consideration.
- `confidence`: evidence-level confidence from replay-free labels, not a runtime score.
- `associated_outcome`: mate/max-plies/unknown or richer failure class.
- `suggested_action_class`: non-causal recommendation such as `audit_owner_exit`, `collect_companion_terms`, `record_growth_pressure`.
- `causal_status`: must remain `non_causal`.
- `promotion_status`: monitor proposal status, not topology promotion.

This is evidence only. It is not runtime routing.

## Stage 7 Interpretation

Stage 7 is not currently blocked because one missing move-affordance terminal is absent.

It is blocked because the system needs better strategy-level self-monitoring:

- when `box_shrink` should exit,
- when plan selection is needed,
- when fence/cut repair is needed,
- when near-edge phase boundaries change which strategy should own.

Stage 7 residuals should remain challenge cases for monitor validation and future strategy arbitration. They should not be patched one-by-one.

## Relationship To ReCoN Self-Monitoring

These monitor candidates are a step toward internal terminals:

- They observe graph/environment/control state.
- They do not choose moves.
- They can later become visible TERMINAL/SCRIPT nodes.
- They may eventually feed GrowthMonitor or PlanCapsule abort/exit/handoff logic.
- They may only influence behavior after default-off sandbox validation and guardrail checks.

The key distinction is:

```text
failure-correlated monitor != action affordance
```

This avoids turning risk signals into broad provider boosts.

## Immediate Next Non-Causal Experiment

Recommended next diagnostic:

```text
Build a small StrategyMonitorRecord extraction over existing Stage 7 + Stage 5/6 artifacts.
```

Proposed outputs:

```text
reports/strategy_arbitration/krk_strategy_monitor_records_v0.json
reports/strategy_arbitration/krk_strategy_monitor_records_v0.md
```

Scope:

- replay-free,
- cheap,
- uses existing `krk_strategy_arbitration_dataset_v0` and feature validation artifacts,
- no h40 relabeling unless a later review explicitly requests it,
- no runtime behavior changes.

The extraction should answer:

- Which records activate each monitor class?
- Are monitor activations mostly Stage7-only or cross-stage?
- Do repair/plan monitors correlate with max-plies without being mistaken for action affordances?
- Which companion terms are most often missing?

## Stop Conditions

Stop before any runtime terminal or sandbox implementation.

Stop if:

- any monitor would need to influence routing,
- monitor source terms are not visible/explainable,
- the work becomes another Stage 7 patch,
- the extraction requires expensive new labels,
- the mechanism starts acting as a hidden controller,
- DTM/tablebase would be needed at runtime,
- topology mutation during gameplay would be required.

## Current Recommendation

Proceed only with non-causal StrategyMonitorRecord extraction if it can be done replay-free and cheaply.

Do not implement a runtime arbiter.

Do not add causal terminals.

Do not add Stage 7 repair.

Do not train Stage 8.

Do not promote Stage 7.
