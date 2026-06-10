# KRK Selector Negative Control Manifest v1

This manifest identifies replay-free negative protected-control examples from existing selector labels.

## Summary

- Controls: `9`
- Stage counts: `{'stage4': 2, 'stage5': 4, 'stage6': 3}`
- Provider counts: `{'krk.edge_trap_close': 3, 'krk.edge_trap_enemy_between': 2, 'krk.edge_trap_wrong_tempo': 2, 'krk.stage0_basin': 2}`
- Runtime arbiter allowed: `False`
- Selector sandbox ready: `False`

## Controls

- `state.256a3da30f0f` stage=`stage4` provider=`krk.stage0_basin` landmark=`wrong_tempo_control`
- `state.b11124d658cf` stage=`stage4` provider=`krk.stage0_basin` landmark=`wrong_tempo_control`
- `state.02feb8593cc6` stage=`stage5` provider=`krk.edge_trap_close` landmark=`fence_established`
- `state.02feb8593cc6` stage=`stage5` provider=`krk.edge_trap_enemy_between` landmark=`fence_established`
- `state.02feb8593cc6` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` landmark=`fence_established`
- `state.326222aefdf1` stage=`stage5` provider=`krk.edge_trap_close` landmark=`fence_established`
- `state.699f0003a511` stage=`stage6` provider=`krk.edge_trap_close` landmark=`drive_to_edge`
- `state.699f0003a511` stage=`stage6` provider=`krk.edge_trap_enemy_between` landmark=`drive_to_edge`
- `state.699f0003a511` stage=`stage6` provider=`krk.edge_trap_wrong_tempo` landmark=`drive_to_edge`

## Decision

Status: `negative_protected_controls_identified_replay_free`
Recommended next step: `build_balanced_replay_free_selector_label_dataset`
