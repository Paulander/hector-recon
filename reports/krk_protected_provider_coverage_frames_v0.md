# KRK Protected Provider Coverage Frames v0

These rows materialize protected forced-provider capacity labels as non-causal evidence frames. They are not runtime proposals and are not training rows.

## Summary

- `row_count`: `16`
- `capacity_label_counts`: `{'positive_capacity': 11, 'negative_capacity': 5}`
- `forced_result_counts`: `{'mate': 11, 'max_plies': 5}`
- `source_stage_counts`: `{'stage5': 7, 'stage6': 3, 'stage4': 6}`
- `provider_family_counts`: `{'stage0_basin': 3, 'fence_established': 3, 'edge_trap': 9, 'drive_to_edge': 1}`
- `stage7_row_count`: `0`
- `training_row_count`: `0`
- `runtime_proposal_row_count`: `0`

## Rows

- `job.krk.protected_missing_provider.75babbcc6000` stage=`stage5` provider=`krk.stage0_basin` capacity=`positive_capacity` forced_move=`b6c7` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.5f9c11521077` stage=`stage5` provider=`krk.fence_established` capacity=`positive_capacity` forced_move=`h7c7` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.38d0a11daf0c` stage=`stage5` provider=`krk.stage0_basin` capacity=`positive_capacity` forced_move=`a6b7` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.9df1f2680cbc` stage=`stage5` provider=`krk.fence_established` capacity=`positive_capacity` forced_move=`h7c7` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.8d58e5a5f72c` stage=`stage5` provider=`krk.edge_trap_close` capacity=`positive_capacity` forced_move=`h7d7` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.a306768e24a0` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` capacity=`positive_capacity` forced_move=`h7d7` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.9a4cc895c68d` stage=`stage5` provider=`krk.edge_trap_enemy_between` capacity=`positive_capacity` forced_move=`h7b7` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.4dca16fc81b3` stage=`stage6` provider=`krk.stage0_basin` capacity=`positive_capacity` forced_move=`a5b6` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.abcf6fafb467` stage=`stage6` provider=`krk.drive_to_edge` capacity=`negative_capacity` forced_move=`h7c7` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.54fd6c4dd136` stage=`stage6` provider=`krk.fence_established` capacity=`negative_capacity` forced_move=`h7c7` existing_frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.01f7ab28aca7` stage=`stage4` provider=`krk.edge_trap_close` capacity=`positive_capacity` forced_move=`d6d5` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.ac1e25bed37b` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` capacity=`positive_capacity` forced_move=`d6d5` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.8bd0028955fa` stage=`stage4` provider=`krk.edge_trap_enemy_between` capacity=`positive_capacity` forced_move=`d6d5` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.6262bf8a2534` stage=`stage4` provider=`krk.edge_trap_close` capacity=`negative_capacity` forced_move=`c8c7` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.104cb87db2f9` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` capacity=`negative_capacity` forced_move=`c8c7` existing_frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.8343f8b595ba` stage=`stage4` provider=`krk.edge_trap_enemy_between` capacity=`negative_capacity` forced_move=`c8c7` existing_frame_providers=`['krk.stage0_basin']`

## Decision

- `status`: `protected_provider_coverage_frames_built`
- `recommended_next_step`: `review_capacity_frame_training_semantics_before_selector_use`
- `runtime_work_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
