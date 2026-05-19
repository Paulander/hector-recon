# KRK Provider Label Coverage Plan v0

This is a non-causal plan. It does not run provider labels, add playouts, change runtime behavior, train Stage 8, or promote Stage 7.

## Current Coverage

- Benchmark frames: `28`
- Proposal count by stage: `{'stage7': 24, 'stage5': 16, 'stage6': 20, 'stage4': 6}`
- Known provider labels by stage: `{'stage7': 24, 'stage5': 16, 'stage6': 20, 'stage4': 6}`
- Unknown provider labels by stage: `{}`
- Provider-labeled frames: `28`
- Frames with known provider mate: `14`
- Coverage status: `sufficient_for_current_small_probe`

## Bounded Labeling Plan

The current filtered frames already contain provider-level labels for the small offline probe. The bounded labeling plan remains as a future fallback, but no p0 label run is needed before the next non-causal arbitration baseline.

### p0_protected_success_controls

- Purpose: Add provider-level h40 labels to protected Stage 5/6 success frames so arbitration has positive controls outside Stage 7.
- Max frames: `8`
- Max provider suggestions per frame: `2`
- Target stages: `['stage5', 'stage6']`
- Horizon: `40`
- Trace mode: `failures_only`
- New runtime behavior: `False`

### p1_stage4_caveat_controls

- Purpose: Label Stage 4 caveat provider suggestions to separate guardrail-definition debt from provider-selection failure.
- Max frames: `4`
- Max provider suggestions per frame: `2`
- Target stages: `['stage4']`
- Horizon: `40`
- Trace mode: `failures_only`
- New runtime behavior: `False`

### p2_stage7_challenge_balance

- Purpose: Only after protected controls exist, add balanced labels for Stage 7 challenge frames without reopening Stage 7 repair.
- Max frames: `4`
- Max provider suggestions per frame: `2`
- Target stages: `['stage7']`
- Horizon: `40`
- Trace mode: `failures_only`
- New runtime behavior: `False`

## Acceptance For Future Label Run

- `no_runtime_behavior_change`
- `no_stage7_promotion`
- `no_stage8_training`
- `no_runtime_dtm_or_tablebase`
- `no_exhaustive_legal_first_sweeps`
- `provider_labels_are_written_as_non_causal_outcome_labels`
- `run_stops_if_projected_to_hours`

## Recommended Next Slice

`offline_strategy_arbitration_baseline_v1`
