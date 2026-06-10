# KRK Strategy Arbiter Observation Separability Review v0

This is a replay-free review of trace-only observation frames.

## Summary

- Records: `12`
- Stage counts: `{'stage4': 2, 'stage5': 1, 'stage7': 9}`
- Selected provider counts: `{'krk.fence_established': 1, 'krk.stage0_basin': 11}`
- Source-term count distribution: `{'13': 1, '16': 7, '20': 2, '21': 2}`
- Proposal-provider count distribution: `{'7': 12}`
- Under-instrumented records: `0`
- Single-provider records: `0`

## Findings

- Stage7 holdout rows are visible and mostly selected by krk.stage0_basin.
- Trace-only KRK context terms are now present in observation source terms.
- Provider summaries expose multiple provider families for selector analysis.
- The current observation export is useful for auditability but is not a causal sandbox.

## Decision

Status: `observation_frames_ready_for_non_causal_selector_probe`
Sandbox ready: `False`
Runtime arbiter allowed: `False`
Recommended next step: `run_replay_free_observation_selector_probe`

The next step should remain trace-only. Do not add provider support, score changes, Stage 7 repair, Stage 7 promotion, or Stage 8 training.
