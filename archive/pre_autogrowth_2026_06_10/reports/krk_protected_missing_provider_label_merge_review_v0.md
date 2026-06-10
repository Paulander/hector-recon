# KRK Protected Missing-Provider Label Merge Review v0

This replay-free review checks whether the protected missing-provider labels joined to ranked proposal frames.

## Summary

- `protected_label_count`: `16`
- `matched_protected_label_count`: `0`
- `unmatched_protected_label_count`: `16`
- `matched_result_counts`: `{}`
- `unmatched_result_counts`: `{'mate': 11, 'max_plies': 5}`
- `unmatched_stage_counts`: `{'stage5': 7, 'stage6': 3, 'stage4': 6}`
- `unmatched_provider_counts`: `{'krk.stage0_basin': 3, 'krk.fence_established': 3, 'krk.edge_trap_close': 3, 'krk.edge_trap_wrong_tempo': 3, 'krk.edge_trap_enemy_between': 3, 'krk.drive_to_edge': 1}`
- `stage7_label_count`: `0`

## Decision

- `status`: `protected_missing_provider_labels_unmatched_by_current_proposal_frames`
- `recommended_next_step`: `review_ranked_proposal_frame_coverage_for_protected_missing_provider_states`
- `runtime_work_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`

## Unmatched Labels

- `job.krk.protected_missing_provider.75babbcc6000` stage=`stage5` provider=`krk.stage0_basin` result=`mate` plies=`27`
- `job.krk.protected_missing_provider.5f9c11521077` stage=`stage5` provider=`krk.fence_established` result=`mate` plies=`15`
- `job.krk.protected_missing_provider.38d0a11daf0c` stage=`stage5` provider=`krk.stage0_basin` result=`mate` plies=`27`
- `job.krk.protected_missing_provider.9df1f2680cbc` stage=`stage5` provider=`krk.fence_established` result=`mate` plies=`37`
- `job.krk.protected_missing_provider.8d58e5a5f72c` stage=`stage5` provider=`krk.edge_trap_close` result=`mate` plies=`31`
- `job.krk.protected_missing_provider.a306768e24a0` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` result=`mate` plies=`31`
- `job.krk.protected_missing_provider.9a4cc895c68d` stage=`stage5` provider=`krk.edge_trap_enemy_between` result=`mate` plies=`31`
- `job.krk.protected_missing_provider.4dca16fc81b3` stage=`stage6` provider=`krk.stage0_basin` result=`mate` plies=`27`
- `job.krk.protected_missing_provider.abcf6fafb467` stage=`stage6` provider=`krk.drive_to_edge` result=`max_plies` plies=`40`
- `job.krk.protected_missing_provider.54fd6c4dd136` stage=`stage6` provider=`krk.fence_established` result=`max_plies` plies=`40`
- `job.krk.protected_missing_provider.01f7ab28aca7` stage=`stage4` provider=`krk.edge_trap_close` result=`mate` plies=`9`
- `job.krk.protected_missing_provider.ac1e25bed37b` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` result=`mate` plies=`9`
- `job.krk.protected_missing_provider.8bd0028955fa` stage=`stage4` provider=`krk.edge_trap_enemy_between` result=`mate` plies=`9`
- `job.krk.protected_missing_provider.6262bf8a2534` stage=`stage4` provider=`krk.edge_trap_close` result=`max_plies` plies=`40`
- `job.krk.protected_missing_provider.104cb87db2f9` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` result=`max_plies` plies=`40`
- `job.krk.protected_missing_provider.8343f8b595ba` stage=`stage4` provider=`krk.edge_trap_enemy_between` result=`max_plies` plies=`40`
