# KRK Balanced Hard-Negative Labels v0

Bounded non-causal label run to improve protected hard-negative evidence balance.

## Summary

- `label_count`: `12`
- `result_counts`: `{'mate': 11, 'max_plies': 1}`
- `result_counts_by_stage`: `{'stage4:mate': 6, 'stage4:max_plies': 1, 'stage6:mate': 5}`
- `result_counts_by_provider_family`: `{'drive_to_edge:mate': 3, 'drive_to_edge:max_plies': 1, 'edge_trap:mate': 4, 'fence_established:mate': 4}`
- `stage7_labels`: `0`
- `stage7_training_labels`: `0`
- `negative_capacity_count`: `1`
- `positive_capacity_count`: `11`
- `trace_failures_only`: `True`
- `full_failure_traces_elided`: `True`
- `wall_time_seconds`: `30.721`

## Labels

- `job.krk.balanced_hard_negative.v1.f79f3b4d2c46` stage=`stage6` provider=`krk.edge_trap_close` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`a1g1`
- `job.krk.balanced_hard_negative.v1.e3b37b037793` stage=`stage6` provider=`krk.edge_trap_close` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`a8f8`
- `job.krk.balanced_hard_negative.v1.541c77a6b895` stage=`stage6` provider=`krk.edge_trap_close` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`a1d1`
- `job.krk.balanced_hard_negative.v1.7fedb9faad85` stage=`stage6` provider=`krk.edge_trap_enemy_between` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`a1g1`
- `job.krk.balanced_hard_negative.v1.05c7b9ebbed5` stage=`stage6` provider=`krk.fence_established` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`a1d1`
- `job.krk.balanced_hard_negative.v1.ab83a1469ea3` stage=`stage4` provider=`krk.drive_to_edge` result=`mate` capacity=`positive_capacity` plies=`7` forced_move=`b7b1`
- `job.krk.balanced_hard_negative.v1.7302037c73ad` stage=`stage4` provider=`krk.drive_to_edge` result=`mate` capacity=`positive_capacity` plies=`9` forced_move=`d2a2`
- `job.krk.balanced_hard_negative.v1.dd6af4d5f28d` stage=`stage4` provider=`krk.drive_to_edge` result=`mate` capacity=`positive_capacity` plies=`5` forced_move=`e5a5`
- `job.krk.balanced_hard_negative.v1.bc8f0a66fbdb` stage=`stage4` provider=`krk.drive_to_edge` result=`max_plies` capacity=`negative_capacity` plies=`40` forced_move=`d6c7`
- `job.krk.balanced_hard_negative.v1.48aca50a3a9f` stage=`stage4` provider=`krk.fence_established` result=`mate` capacity=`positive_capacity` plies=`7` forced_move=`b7b1`
- `job.krk.balanced_hard_negative.v1.448a86bb8c90` stage=`stage4` provider=`krk.fence_established` result=`mate` capacity=`positive_capacity` plies=`9` forced_move=`d2a2`
- `job.krk.balanced_hard_negative.v1.97960937a39a` stage=`stage4` provider=`krk.fence_established` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`f6f7`

## Decision

- `status`: `balanced_hard_negative_labels_completed`
- `recommended_next_step`: `merge_balanced_labels_and_refresh_hard_negative_ablation`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
