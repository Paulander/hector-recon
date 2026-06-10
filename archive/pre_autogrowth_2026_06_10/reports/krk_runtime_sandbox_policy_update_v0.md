# KRK Runtime Sandbox Policy Update v0

## Decision

The prior absolute `no runtime changes` rule has completed its diagnostic role. The updated short-term rule is:

```text
No unreviewed runtime changes.
No default-policy changes.
No broad runtime changes.

Allow one narrowly scoped, default-off, reversible runtime sandbox when a review packet reaches runtime-review-ready.
```

## Immediate Scope

The only newly approved implementation class is:

```text
default-off progress-window selected-owner reconsideration sandbox
```

This is not:

- a general KRK arbiter,
- an initial pre-decision selector,
- a Stage 7 repair,
- Stage 7 promotion,
- Stage 8 training,
- runtime DTM/tablebase use,
- gameplay-time topology mutation,
- a hidden Python controller.

## Why This Is Allowed

`krk_state_local_paired_selector_runtime_proxy_review_packet_v1` is review-ready for a narrow progress-window monitor/reconsideration scope. Its evidence passes independent protected validation inside that scope, but all-row performance remains weak. Therefore the only appropriate runtime test is post-selection reconsideration after visible progress failure, not broad provider selection.

## Immediate Plan

1. Implement the sandbox default-off with explicit flags.
2. Preserve default-off equivalence.
3. Require visible progress-window source terms.
4. Require safety / safe-preservation evidence on any supported move.
5. Trace every firing and selected-supported case.
6. Run protected Stage 4/5/6 guardrails.
7. Use Stage 7 only as held-out challenge diagnostics.
8. Quarantine or keep sandboxed unless guardrails and target validation justify a later review.

## Runtime-Test Result

The first implementation slice is recorded in:

```text
reports/krk_progress_window_reconsideration_runtime_smoke_v0.md
reports/krk_progress_window_reconsideration_runtime_test_review_v0.md
```

Result:

```text
default_off_equivalence_passed: true
activation_observed: true
target_improvement_observed: false
status: runtime_test_scaffold_wired_but_policy_insufficient
```

This means the sandbox can remain as a default-off runtime-test scaffold, but it is not guardrail-ready. The current support rule is too broad inside the progress-window scope and should not be scaled, promoted, or enabled by default.

## Short-Term Plan

- Complete one default-off progress-window reconsideration runtime test.
- Do not tune broad selector scores.
- Do not promote or scale if the sandbox does not improve its scoped cases.
- If default-off equivalence fails, stop and diagnose.

## Long-Term Plan

The broader architecture remains:

```text
visible evidence -> structural candidate -> default-off sandbox -> guardrails -> promote/quarantine
```

KRK should proceed through:

- protected Stage 1/4/5/6 stack preservation,
- strategy ownership and sequence-policy separation,
- held-out Stage 7 boundary cases,
- full KRK integration,
- later KPK/KQK transfer using the same monitor/candidate/sandbox/guardrail loop.
