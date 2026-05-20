# KRK Protected Missing-Provider Capacity Labels v0

Bounded non-causal label run over protected max-only frames.

## Summary

- label_count: `16`
- result_counts: `{'mate': 11, 'max_plies': 5}`
- result_counts_by_stage: `{'stage4:mate': 3, 'stage4:max_plies': 3, 'stage5:mate': 7, 'stage6:mate': 1, 'stage6:max_plies': 2}`
- result_counts_by_provider: `{'krk.drive_to_edge:max_plies': 1, 'krk.edge_trap_close:mate': 2, 'krk.edge_trap_close:max_plies': 1, 'krk.edge_trap_enemy_between:mate': 2, 'krk.edge_trap_enemy_between:max_plies': 1, 'krk.edge_trap_wrong_tempo:mate': 2, 'krk.edge_trap_wrong_tempo:max_plies': 1, 'krk.fence_established:mate': 2, 'krk.fence_established:max_plies': 1, 'krk.stage0_basin:mate': 3}`
- stage7_labels: `0`
- stage7_training_labels: `0`
- trace_failures_only: `True`
- full_failure_traces_elided: `True`
- wall_time_seconds: `175.079`

## Labels

- `job.krk.protected_missing_provider.75babbcc6000` stage=`stage5` provider=`krk.stage0_basin` result=`mate` plies=`27` forced_move=`b6c7`
- `job.krk.protected_missing_provider.5f9c11521077` stage=`stage5` provider=`krk.fence_established` result=`mate` plies=`15` forced_move=`h7c7`
- `job.krk.protected_missing_provider.38d0a11daf0c` stage=`stage5` provider=`krk.stage0_basin` result=`mate` plies=`27` forced_move=`a6b7`
- `job.krk.protected_missing_provider.9df1f2680cbc` stage=`stage5` provider=`krk.fence_established` result=`mate` plies=`37` forced_move=`h7c7`
- `job.krk.protected_missing_provider.8d58e5a5f72c` stage=`stage5` provider=`krk.edge_trap_close` result=`mate` plies=`31` forced_move=`h7d7`
- `job.krk.protected_missing_provider.a306768e24a0` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` result=`mate` plies=`31` forced_move=`h7d7`
- `job.krk.protected_missing_provider.9a4cc895c68d` stage=`stage5` provider=`krk.edge_trap_enemy_between` result=`mate` plies=`31` forced_move=`h7b7`
- `job.krk.protected_missing_provider.4dca16fc81b3` stage=`stage6` provider=`krk.stage0_basin` result=`mate` plies=`27` forced_move=`a5b6`
- `job.krk.protected_missing_provider.abcf6fafb467` stage=`stage6` provider=`krk.drive_to_edge` result=`max_plies` plies=`40` forced_move=`h7c7`
- `job.krk.protected_missing_provider.54fd6c4dd136` stage=`stage6` provider=`krk.fence_established` result=`max_plies` plies=`40` forced_move=`h7c7`
- `job.krk.protected_missing_provider.01f7ab28aca7` stage=`stage4` provider=`krk.edge_trap_close` result=`mate` plies=`9` forced_move=`d6d5`
- `job.krk.protected_missing_provider.ac1e25bed37b` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` result=`mate` plies=`9` forced_move=`d6d5`
- `job.krk.protected_missing_provider.8bd0028955fa` stage=`stage4` provider=`krk.edge_trap_enemy_between` result=`mate` plies=`9` forced_move=`d6d5`
- `job.krk.protected_missing_provider.6262bf8a2534` stage=`stage4` provider=`krk.edge_trap_close` result=`max_plies` plies=`40` forced_move=`c8c7`
- `job.krk.protected_missing_provider.104cb87db2f9` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` result=`max_plies` plies=`40` forced_move=`c8c7`
- `job.krk.protected_missing_provider.8343f8b595ba` stage=`stage4` provider=`krk.edge_trap_enemy_between` result=`max_plies` plies=`40` forced_move=`c8c7`

Recommended next step: `merge_missing_provider_labels_and_refresh_strategy_sequence_inventory`
