# KRK Strategy Owner Contrast Control Labels v0

This is an offline non-causal label run. It forced each configured provider only for the first White move, then released to the normal topology.

## Summary

- Label count: `12`
- Result counts: `{'mate': 10, 'max_plies': 2}`
- Result counts by stage: `{'stage4:mate': 2, 'stage4:max_plies': 2, 'stage5:mate': 4, 'stage6:mate': 4}`
- Result counts by provider: `{'krk.drive_to_edge:mate': 2, 'krk.edge_trap_close:mate': 2, 'krk.edge_trap_close:max_plies': 1, 'krk.edge_trap_enemy_between:mate': 1, 'krk.edge_trap_wrong_tempo:mate': 2, 'krk.edge_trap_wrong_tempo:max_plies': 1, 'krk.fence_established:mate': 3}`
- Stage 7 labels: `0`
- Wall time seconds: `35.217`

## Labels

- `job.krk.strategy_owner_contrast.6ca3b85ce53a` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` forced_move=`b7b6` result=`max_plies` plies=`40`
- `job.krk.strategy_owner_contrast.14c4d6d395bb` stage=`stage4` provider=`krk.edge_trap_close` forced_move=`b7b6` result=`max_plies` plies=`40`
- `job.krk.strategy_owner_contrast.1a9dfe565e76` stage=`stage4` provider=`krk.fence_established` forced_move=`b7b1` result=`mate` plies=`7`
- `job.krk.strategy_owner_contrast.d1744cd54930` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` forced_move=`d3e3` result=`mate` plies=`9`
- `job.krk.strategy_owner_contrast.eae6955cdd41` stage=`stage5` provider=`krk.edge_trap_close` forced_move=`f2f3` result=`mate` plies=`9`
- `job.krk.strategy_owner_contrast.fca927c317d8` stage=`stage5` provider=`krk.edge_trap_enemy_between` forced_move=`f2f3` result=`mate` plies=`9`
- `job.krk.strategy_owner_contrast.40d0a6e04b05` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` forced_move=`f2f3` result=`mate` plies=`9`
- `job.krk.strategy_owner_contrast.829c9b9fe98b` stage=`stage5` provider=`krk.fence_established` forced_move=`f2g3` result=`mate` plies=`9`
- `job.krk.strategy_owner_contrast.e14d23798e77` stage=`stage6` provider=`krk.drive_to_edge` forced_move=`e6f6` result=`mate` plies=`5`
- `job.krk.strategy_owner_contrast.5e053ab0baa8` stage=`stage6` provider=`krk.fence_established` forced_move=`a1g1` result=`mate` plies=`3`
- `job.krk.strategy_owner_contrast.4dcd4cc180e8` stage=`stage6` provider=`krk.edge_trap_close` forced_move=`a1g1` result=`mate` plies=`3`
- `job.krk.strategy_owner_contrast.82e91a823777` stage=`stage6` provider=`krk.drive_to_edge` forced_move=`f6f7` result=`mate` plies=`5`

## Recommended Next Step

`merge_contrast_labels_and_rebuild_strategy_owner_contrast_dataset`
