# KRK Forced Provider Control Labels v0

This is an offline non-causal label run. It forced each configured provider only for the first White move, then released control to the normal topology.

## Summary

- Label count: `12`
- Result counts: `{'mate': 9, 'max_plies': 3}`
- Result counts by stage: `{'stage5:mate': 6, 'stage6:mate': 3, 'stage6:max_plies': 3}`

## Labels

- `job.krk.forced_provider_control.c715487480c5` stage=`stage5` provider=`krk.stage0_basin` forced_move=`f2g3` result=`mate` plies=`9`
- `job.krk.forced_provider_control.150c41c3b1ad` stage=`stage5` provider=`krk.edge_trap_close` forced_move=`e7e8` result=`mate` plies=`1`
- `job.krk.forced_provider_control.7ab58d03a5bc` stage=`stage5` provider=`krk.edge_trap_enemy_between` forced_move=`e7e8` result=`mate` plies=`1`
- `job.krk.forced_provider_control.adde0e92f3a3` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` forced_move=`e7e8` result=`mate` plies=`1`
- `job.krk.forced_provider_control.7474bd7cf9de` stage=`stage5` provider=`krk.stage0_basin` forced_move=`a7a8` result=`mate` plies=`17`
- `job.krk.forced_provider_control.cd9c093a0c99` stage=`stage5` provider=`krk.edge_trap_close` forced_move=`h7c7` result=`mate` plies=`15`
- `job.krk.forced_provider_control.6a22ba706f91` stage=`stage6` provider=`krk.stage0_basin` forced_move=`a1g1` result=`mate` plies=`3`
- `job.krk.forced_provider_control.5b9da3b441ec` stage=`stage6` provider=`krk.stage0_basin` forced_move=`a8f8` result=`mate` plies=`3`
- `job.krk.forced_provider_control.772216e525ec` stage=`stage6` provider=`krk.stage0_basin` forced_move=`a1d1` result=`mate` plies=`3`
- `job.krk.forced_provider_control.c732438d4ceb` stage=`stage6` provider=`krk.edge_trap_close` forced_move=`h7c7` result=`max_plies` plies=`40`
- `job.krk.forced_provider_control.1f5da08ca8bb` stage=`stage6` provider=`krk.edge_trap_enemy_between` forced_move=`h7c7` result=`max_plies` plies=`40`
- `job.krk.forced_provider_control.c25eb5d2cfe9` stage=`stage6` provider=`krk.edge_trap_wrong_tempo` forced_move=`h7c7` result=`max_plies` plies=`40`

## Recommended Next Step

`merge_forced_provider_control_labels_and_rerun_stratified_probe`
