# KRK Progress-Window Reconsideration Runtime-Test Review v0

This review covers the first approved default-off runtime-test sandbox for selected-owner progress-window reconsideration.

## Status

The sandbox is wired, opt-in, traceable, and reversible. Runtime defaults remain unchanged.

```text
sandbox_id: sandbox.krk.progress_window_reconsideration_v0
status: runtime_test_scaffold_wired_but_policy_insufficient
default_off_equivalence_passed: true
activation_observed: true
target_improvement_observed: false
guardrails_allowed_now: false
```

## Evidence

Source smoke:

```text
reports/krk_progress_window_reconsideration_runtime_smoke_v0.json
reports/krk_progress_window_reconsideration_runtime_smoke_v0.md
```

Smoke summary:

```text
protected_label_count: 3
targeted_row_count: 2
enabled_supported_total: 518
enabled_selected_supported_total: 14
targeted_monitor_confirmed_events: 14
targeted_candidate_intersection_events: 20
target_failure_row_count: 1
improved_target_failure_count: 0
safe_regression_count: 0
```

Default-off equivalence passed on protected controls and targeted rows. The enabled sandbox also activated on the intended progress-window failure row.

However, the activated sandbox did not improve the target failure:

```text
cp.krk.state.ea634c29ece7:
  baseline: max_plies/40
  enabled:  max_plies/40
```

The safe row did not regress:

```text
cp.krk.state.c732b2d6dc56:
  baseline: mate/7
  enabled:  mate/7
```

## Diagnosis

The failure is not flag wiring. The runtime flags now reach the scoring path and produce visible `krk_progress_window_reconsideration` metadata.

The blocker is policy specificity. The current rule supports visible loop-breaking/progress moves, but that set includes moves that can still be selected inside non-converting trajectories. In the targeted failure row, support is applied and selected, yet closed-loop play remains max-plies.

This means the progress-window monitor is useful as a runtime-test scaffold, but the current support rule is not a validated reconsideration policy.

## Decision

Do not advance this sandbox to guardrails yet.

Do not:

- enable it by default
- promote Stage 7
- train Stage 8
- run broad guardrails as if target improvement had passed
- expand this into a general pre-decision selector
- use runtime DTM/tablebase

Allowed future work requires review:

- design a narrower alternative-selection policy inside progress-window scope
- improve visible candidate/proposal coverage for true reconsideration alternatives
- return to the broader KRK strategy-arbitration / sequence-policy track with Stage 7 as held-out challenge
