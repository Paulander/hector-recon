# KRK Candidate-Generation Cross-Stage Capacity Labels v3

Bounded protected-only offline forced-provider capacity labels for cross-stage candidate-generation review. These labels are not runtime inputs and not ownership labels.

## Decision

- status: `cross_stage_capacity_labels_completed`
- selector_allowed: `False`
- recommended_next_step: `merge_cross_stage_capacity_labels_and_rerun_refresh_probe`

## Summary

- label_count: `8`
- result_counts: `{'mate': 7, 'max_plies': 1}`
- result_counts_by_stage_family_cell: `{'stage4|stage0_basin:mate': 1, 'stage4|stage0_basin:max_plies': 1, 'stage5|edge_trap:mate': 3, 'stage5|stage0_basin:mate': 1, 'stage6|stage0_basin:mate': 2}`
- stage7_label_count: `0`
- stage7_training_label_count: `0`
- trace_failures_only: `True`
- full_failure_traces_elided: `True`
- wall_time_seconds: `54.499`

## Labels

- `job.krk.cg_cross_stage_v3.072671d3e877` cell=`stage5|edge_trap` provider=`krk.edge_trap_close` family=`edge_trap` result=`mate` plies=`37` forced_move=`h7c7`
- `job.krk.cg_cross_stage_v3.23625c938438` cell=`stage5|stage0_basin` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`9` forced_move=`f2g3`
- `job.krk.cg_cross_stage_v3.d2fe4fcb2c63` cell=`stage6|stage0_basin` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`3` forced_move=`a1d1`
- `job.krk.cg_cross_stage_v3.7db3d70b3f8f` cell=`stage5|edge_trap` provider=`krk.edge_trap_enemy_between` family=`edge_trap` result=`mate` plies=`37` forced_move=`h7c7`
- `job.krk.cg_cross_stage_v3.9f8c28df5da4` cell=`stage6|stage0_basin` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`3` forced_move=`a1g1`
- `job.krk.cg_cross_stage_v3.d68549c922ff` cell=`stage5|edge_trap` provider=`krk.edge_trap_wrong_tempo` family=`edge_trap` result=`mate` plies=`37` forced_move=`h7c7`
- `job.krk.cg_cross_stage_v3.87de57e39c2f` cell=`stage4|stage0_basin` provider=`krk.stage0_basin` family=`stage0_basin` result=`max_plies` plies=`40` forced_move=`b7b1`
- `job.krk.cg_cross_stage_v3.8b1329430dc1` cell=`stage4|stage0_basin` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`9` forced_move=`d2a2`
