# KRK Strategy Arbiter Observation Separability Review v0

This is a replay-free review of trace-only observation frames.

## Summary

- Records: `12`
- Stage counts: `{'stage4': 2, 'stage5': 1, 'stage7': 9}`
- Selected provider counts: `{'krk.fence_established': 1, 'krk.stage0_basin': 11}`
- Source-term count distribution: `{'1': 12}`
- Proposal-provider count distribution: `{'1': 11, '4': 1}`
- Under-instrumented records: `12`
- Single-provider records: `11`

## Findings

- Stage7 holdout rows are visible and mostly selected by krk.stage0_basin.
- Observation source terms are under-instrumented; most records expose only active_landmark_label.
- Several rows expose only one provider in the retained top suggestions, limiting strategy separability.
- The current observation export is useful for auditability but not enough for sandbox arbiter design.

## Decision

Status: `observation_context_underinstrumented`
Sandbox ready: `False`
Runtime arbiter allowed: `False`
Recommended next step: `enrich_trace_only_observation_with_existing_context_terms`

The next step should remain trace-only. Do not add provider support, score changes, Stage 7 repair, Stage 7 promotion, or Stage 8 training.
