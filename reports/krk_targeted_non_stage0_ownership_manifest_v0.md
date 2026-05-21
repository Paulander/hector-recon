# KRK Targeted Non-Stage0 Ownership Manifest v0

This manifest is a bounded non-causal source-diversity diagnostic. It replays historical protected-control states that selected non-stage0 owners and checks current-profile ownership without changing runtime behavior.

## Summary

- Job count: `4`
- Jobs by stage: `{'stage5': 3, 'stage6': 1}`
- Historical selected provider counts: `{'krk.edge_trap_close': 3, 'krk.fence_established': 1}`
- All bindings valid: `True`
- Stage 7 job count: `0`
- Decision: `targeted_non_stage0_manifest_ready`

## Jobs

- `state.326222aefdf1` stage=`stage5` historical_provider=`krk.edge_trap_close` historical_move=`h7c7`
- `state.87b1160e68b9` stage=`stage5` historical_provider=`krk.edge_trap_close` historical_move=`e7e8`
- `state.02feb8593cc6` stage=`stage5` historical_provider=`krk.fence_established` historical_move=`h7c7`
- `state.699f0003a511` stage=`stage6` historical_provider=`krk.edge_trap_close` historical_move=`h7c7`

## Recommended Next Step

`run_bounded_current_profile_labels_for_historical_non_stage0_owners`

