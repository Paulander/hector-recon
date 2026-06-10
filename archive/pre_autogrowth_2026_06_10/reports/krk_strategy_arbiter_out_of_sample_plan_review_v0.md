# KRK Strategy Arbiter Out-of-Sample Plan Review v0

This review checks whether the out-of-sample control plan can be satisfied from existing artifacts before any new h40 label run.

## Summary

- Plan status: `out_of_sample_control_plan_defined_execution_blocked`
- Replay-free candidates: `2`
- Replay-free unique states: `2`
- Counts by stage: `{'stage5': 1, 'stage6': 1}`
- Counts by label: `{'negative': 1, 'positive': 1}`
- Missing replay-free stages: `['stage4']`
- Decision: `plan_review_passed_execution_manifest_needed`

## Replay-Free Candidates

- `state.3dca34326fca` stage=`stage5` provider=`krk.stage0_basin` result=`max_plies`
- `state.69711173114a` stage=`stage6` provider=`krk.stage0_basin` result=`mate`

## Gaps

- Replay-free out-of-sample coverage does not span Stage4/5/6 after excluding balanced-label states.
- Replay-free candidate count is below the planned max-state target.
- A concrete execution manifest is needed before any new h40 labels are run.

## Manifest Requirements

- Max states: `12`
- Per-stage max: `4`
- Horizon: `h40`
- Excluded balanced states: `13`
- Jobs must bind topology/profile/checkpoint metadata.
- Stage 7 training rows must remain `0`.

## Recommended Next Step

`generate_out_of_sample_control_execution_manifest`

Do not execute labels until the execution manifest is reviewed.
