# KRK Targeted Non-Stage0 Ownership Labels v0

This is a bounded offline label run. It asks whether the current handoff profile preserves historical non-stage0 selected ownership. It does not train a selector, change runtime defaults, or alter topology.

## Summary

- Label count: `4`
- Wall time sec: `80.710077`
- Historical provider counts: `{'krk.edge_trap_close': 3, 'krk.fence_established': 1}`
- Current provider counts: `{'krk.edge_trap_close': 3, 'krk.fence_established': 1}`
- Historical preservation counts: `{'preserved': 4}`
- Stage0 collapse counts: `{'non_stage0_current': 4}`
- Selected result counts: `{'mate': 3, 'max_plies': 1}`
- Current provider/result counts: `{'krk.edge_trap_close:mate': 2, 'krk.edge_trap_close:max_plies': 1, 'krk.fence_established:mate': 1}`
- Stage 7 training rows: `0`

## Labels

- `state.326222aefdf1` stage=`stage5` historical=`krk.edge_trap_close` current=`krk.edge_trap_close` preserved=`True` stage0_collapse=`False` result=`mate`
- `state.87b1160e68b9` stage=`stage5` historical=`krk.edge_trap_close` current=`krk.edge_trap_close` preserved=`True` stage0_collapse=`False` result=`mate`
- `state.02feb8593cc6` stage=`stage5` historical=`krk.fence_established` current=`krk.fence_established` preserved=`True` stage0_collapse=`False` result=`mate`
- `state.699f0003a511` stage=`stage6` historical=`krk.edge_trap_close` current=`krk.edge_trap_close` preserved=`True` stage0_collapse=`False` result=`max_plies`

## Decision

- Status: `current_profile_preserves_some_historical_non_stage0_ownership`
- Recommended next step: `merge_preserved_non_stage0_labels_then_reprobe_selector_features`

