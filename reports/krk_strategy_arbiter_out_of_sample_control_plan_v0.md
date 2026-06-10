# KRK Strategy Arbiter Out-of-Sample Control Plan v0

This plan defines the next evidence slice required before any strategy-arbiter sandbox review.

It does not execute labels.

## Purpose

The balanced replay-free selector set shows a provider/provenance signal, but it was built from existing controls. A future sandbox review needs out-of-sample protected controls.

## Bounds

- Maximum states: `12`
- Per-stage maximum: `4`
- Stages: Stage 4 wrong-tempo controls, Stage 5 fence/handoff, Stage 6 drive-to-edge
- Horizon: `h40`
- Diagnostic caches: enabled
- Trace mode: failures only
- Parallel workers: allowed
- Stage 7 training rows: `0`
- Exhaustive legal-first sweeps: forbidden by default

## Required Labels

- `selected_playout_success`
- `forced_provider_conversion_for_selected_provider`
- `same_move_provider_compatibility_when_available`
- `guardrail_safe_ownership`
- `shadow_candidate_delta`

## State Selection Rules

- Exclude states already used in `reports/krk_selector_balanced_label_dataset_v1.json`.
- Prefer protected Stage 4/5/6 states from existing guardrail/sample artifacts.
- Keep Stage 7 residuals as held-out challenge cases only.
- Balance positive and negative selected-playout outcomes if replay-free labels are available.
- If new labels are required, generate an execution manifest first and stop for review.

## Future Execution Acceptance

- No runtime arbiter or selector sandbox.
- No Stage 7 promotion.
- No Stage 8 training.
- No runtime DTM/tablebase.
- No topology mutation.
- Every job cites topology/profile/checkpoint metadata.
- Outputs remain non-causal evidence.

## Decision

```text
out_of_sample_control_plan_defined_execution_blocked
```

Recommended next step:

```text
review_plan_then_generate_execution_manifest_if_needed
```

Do not execute collection without review.
