# KRK Balanced Hard-Negative Labels v0

Bounded non-causal label run to improve protected hard-negative evidence balance.

## Summary

- `label_count`: `12`
- `result_counts`: `{'mate': 9, 'max_plies': 3}`
- `result_counts_by_stage`: `{'stage4:mate': 2, 'stage4:max_plies': 1, 'stage5:mate': 4, 'stage5:max_plies': 2, 'stage6:mate': 3}`
- `result_counts_by_provider_family`: `{'drive_to_edge:mate': 4, 'drive_to_edge:max_plies': 1, 'fence_established:mate': 1, 'fence_established:max_plies': 1, 'stage0_basin:mate': 4, 'stage0_basin:max_plies': 1}`
- `stage7_labels`: `0`
- `stage7_training_labels`: `0`
- `negative_capacity_count`: `3`
- `positive_capacity_count`: `9`
- `trace_failures_only`: `True`
- `full_failure_traces_elided`: `True`
- `wall_time_seconds`: `84.23`

## Labels

- `job.krk.balanced_hard_negative.d4d27a10d1c4` stage=`stage5` provider=`krk.stage0_basin` result=`mate` capacity=`positive_capacity` plies=`1` forced_move=`e7e8`
- `job.krk.balanced_hard_negative.fd95ab614799` stage=`stage5` provider=`krk.stage0_basin` result=`mate` capacity=`positive_capacity` plies=`31` forced_move=`c6b6`
- `job.krk.balanced_hard_negative.8c7944e4b11b` stage=`stage4` provider=`krk.stage0_basin` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`f6f7`
- `job.krk.balanced_hard_negative.0129b9fbfc65` stage=`stage4` provider=`krk.stage0_basin` result=`mate` capacity=`positive_capacity` plies=`7` forced_move=`b7b1`
- `job.krk.balanced_hard_negative.e3b51918de2d` stage=`stage4` provider=`krk.stage0_basin` result=`max_plies` capacity=`negative_capacity` plies=`40` forced_move=`d6c7`
- `job.krk.balanced_hard_negative.3ce9a363baff` stage=`stage5` provider=`krk.drive_to_edge` result=`mate` capacity=`positive_capacity` plies=`15` forced_move=`h7c7`
- `job.krk.balanced_hard_negative.02a926e18ae1` stage=`stage5` provider=`krk.drive_to_edge` result=`max_plies` capacity=`negative_capacity` plies=`40` forced_move=`e2f3`
- `job.krk.balanced_hard_negative.a8a2493398d4` stage=`stage5` provider=`krk.fence_established` result=`max_plies` capacity=`negative_capacity` plies=`40` forced_move=`e2f3`
- `job.krk.balanced_hard_negative.a89843f4f707` stage=`stage6` provider=`krk.drive_to_edge` result=`mate` capacity=`positive_capacity` plies=`5` forced_move=`f6f7`
- `job.krk.balanced_hard_negative.1f6a0b02f7b7` stage=`stage6` provider=`krk.fence_established` result=`mate` capacity=`positive_capacity` plies=`3` forced_move=`a8d8`
- `job.krk.balanced_hard_negative.91560b3a0090` stage=`stage6` provider=`krk.drive_to_edge` result=`mate` capacity=`positive_capacity` plies=`5` forced_move=`b6c6`
- `job.krk.balanced_hard_negative.c9f3bdbd81b4` stage=`stage5` provider=`krk.drive_to_edge` result=`mate` capacity=`positive_capacity` plies=`37` forced_move=`h7c7`

## Decision

- `status`: `balanced_hard_negative_labels_completed`
- `recommended_next_step`: `merge_balanced_labels_and_refresh_hard_negative_ablation`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
