# KRK Targeted Ownership Negative Manifest v0

This manifest targets known false-positive ownership risk cells. It is non-causal and does not implement or train a selector.

## Summary

- Job count: `6`
- Jobs by stage: `{'stage4': 4, 'stage5': 2}`
- Jobs by target cell: `{'stage4_stage0_wrong_tempo_like': 4, 'stage5_stage0_fence_like': 2}`
- Scan summary: `{'scanned_by_target_cell': {'stage4_stage0_wrong_tempo_like': 7, 'stage5_stage0_fence_like': 4}, 'matched_by_target_cell': {'stage4_stage0_wrong_tempo_like': 4, 'stage5_stage0_fence_like': 2}, 'selected_by_target_cell': {'stage4_stage0_wrong_tempo_like': 4, 'stage5_stage0_fence_like': 2}}`
- Decision: `targeted_ownership_negative_manifest_ready`

## Jobs

- `state.1d2ebedbbb30` stage=`stage4` cell=`stage4_stage0_wrong_tempo_like` selected=`krk.stage0_basin` move=`h1h8`
- `state.7501312e20f8` stage=`stage4` cell=`stage4_stage0_wrong_tempo_like` selected=`krk.stage0_basin` move=`d2c2`
- `state.b09c954a787e` stage=`stage4` cell=`stage4_stage0_wrong_tempo_like` selected=`krk.stage0_basin` move=`e2e8`
- `state.6b3211a9a90f` stage=`stage4` cell=`stage4_stage0_wrong_tempo_like` selected=`krk.stage0_basin` move=`c5g5`
- `state.6e84c77a4520` stage=`stage5` cell=`stage5_stage0_fence_like` selected=`krk.stage0_basin` move=`g2f1`
- `state.0b1f2153179b` stage=`stage5` cell=`stage5_stage0_fence_like` selected=`krk.stage0_basin` move=`c7a7`

## Recommended Next Step

`run_bounded_targeted_ownership_negative_labels`
