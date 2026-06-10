# KRK Ranked Proposal Frame Protected Provider Coverage Review v0

This replay-free review checks whether protected forced-provider labels have corresponding proposal-frame rows.

## Summary

- `label_count`: `16`
- `frames_present_count`: `16`
- `states_present_count`: `16`
- `provider_present_in_frame_count`: `0`
- `provider_missing_from_frame_count`: `16`
- `missing_provider_mate_label_count`: `11`
- `result_counts`: `{'mate': 11, 'max_plies': 5}`
- `missing_result_counts`: `{'mate': 11, 'max_plies': 5}`
- `missing_stage_counts`: `{'stage5': 7, 'stage6': 3, 'stage4': 6}`
- `missing_provider_counts`: `{'krk.stage0_basin': 3, 'krk.fence_established': 3, 'krk.edge_trap_close': 3, 'krk.edge_trap_wrong_tempo': 3, 'krk.edge_trap_enemy_between': 3, 'krk.drive_to_edge': 1}`
- `stage7_label_count`: `0`

## Decision

- `status`: `proposal_provider_coverage_gap_blocks_selector_training`
- `recommended_next_step`: `design_non_causal_proposal_coverage_expansion_for_protected_states`
- `runtime_work_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`

## Missing Provider Records

- `job.krk.protected_missing_provider.75babbcc6000` stage=`stage5` provider=`krk.stage0_basin` result=`mate` frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.5f9c11521077` stage=`stage5` provider=`krk.fence_established` result=`mate` frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.38d0a11daf0c` stage=`stage5` provider=`krk.stage0_basin` result=`mate` frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.9df1f2680cbc` stage=`stage5` provider=`krk.fence_established` result=`mate` frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.8d58e5a5f72c` stage=`stage5` provider=`krk.edge_trap_close` result=`mate` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.a306768e24a0` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` result=`mate` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.9a4cc895c68d` stage=`stage5` provider=`krk.edge_trap_enemy_between` result=`mate` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.4dca16fc81b3` stage=`stage6` provider=`krk.stage0_basin` result=`mate` frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.abcf6fafb467` stage=`stage6` provider=`krk.drive_to_edge` result=`max_plies` frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.54fd6c4dd136` stage=`stage6` provider=`krk.fence_established` result=`max_plies` frame_providers=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `job.krk.protected_missing_provider.01f7ab28aca7` stage=`stage4` provider=`krk.edge_trap_close` result=`mate` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.ac1e25bed37b` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` result=`mate` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.8bd0028955fa` stage=`stage4` provider=`krk.edge_trap_enemy_between` result=`mate` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.6262bf8a2534` stage=`stage4` provider=`krk.edge_trap_close` result=`max_plies` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.104cb87db2f9` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` result=`max_plies` frame_providers=`['krk.stage0_basin']`
- `job.krk.protected_missing_provider.8343f8b595ba` stage=`stage4` provider=`krk.edge_trap_enemy_between` result=`max_plies` frame_providers=`['krk.stage0_basin']`
