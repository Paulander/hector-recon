# KRK Candidate-Generation Capacity Evidence Labels v2

Bounded protected-only offline forced-provider capacity labels. These labels are not runtime inputs and not ownership labels.

## Decision

- status: `candidate_generation_capacity_evidence_labels_completed`
- selector_allowed: `False`
- recommended_next_step: `merge_capacity_evidence_labels_v2_and_rerun_refresh_probe`

## Summary

- label_count: `12`
- result_counts: `{'mate': 8, 'max_plies': 4}`
- result_counts_by_stage: `{'stage4:mate': 2, 'stage4:max_plies': 1, 'stage5:mate': 5, 'stage6:mate': 1, 'stage6:max_plies': 3}`
- result_counts_by_provider_family: `{'edge_trap:mate': 3, 'edge_trap:max_plies': 3, 'stage0_basin:mate': 5, 'stage0_basin:max_plies': 1}`
- stage7_label_count: `0`
- stage7_training_label_count: `0`
- trace_failures_only: `True`
- full_failure_traces_elided: `True`
- wall_time_seconds: `112.966`

## Labels

- `job.krk.cg_capacity_v2.75ae33a275f1` stage=`stage4` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`3` forced_move=`f6f7`
- `job.krk.cg_capacity_v2.205639284e23` stage=`stage5` provider=`krk.edge_trap_close` family=`edge_trap` result=`mate` plies=`15` forced_move=`h7c7`
- `job.krk.cg_capacity_v2.36f95a84102d` stage=`stage6` provider=`krk.edge_trap_close` family=`edge_trap` result=`max_plies` plies=`40` forced_move=`h7c7`
- `job.krk.cg_capacity_v2.a1d20c18ea0f` stage=`stage4` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`7` forced_move=`b7b1`
- `job.krk.cg_capacity_v2.4c4a0a90354b` stage=`stage5` provider=`krk.edge_trap_enemy_between` family=`edge_trap` result=`mate` plies=`15` forced_move=`h7c7`
- `job.krk.cg_capacity_v2.89cb2ec1f824` stage=`stage6` provider=`krk.edge_trap_enemy_between` family=`edge_trap` result=`max_plies` plies=`40` forced_move=`h7c7`
- `job.krk.cg_capacity_v2.141862dde05b` stage=`stage4` provider=`krk.stage0_basin` family=`stage0_basin` result=`max_plies` plies=`40` forced_move=`d6c7`
- `job.krk.cg_capacity_v2.2285c6bdb5ce` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` family=`edge_trap` result=`mate` plies=`15` forced_move=`h7c7`
- `job.krk.cg_capacity_v2.2557dcb9229f` stage=`stage6` provider=`krk.edge_trap_wrong_tempo` family=`edge_trap` result=`max_plies` plies=`40` forced_move=`h7c7`
- `job.krk.cg_capacity_v2.a4bbf1706a56` stage=`stage5` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`17` forced_move=`a7a8`
- `job.krk.cg_capacity_v2.8df03270eb29` stage=`stage6` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`3` forced_move=`a8f8`
- `job.krk.cg_capacity_v2.a29804da547d` stage=`stage5` provider=`krk.stage0_basin` family=`stage0_basin` result=`mate` plies=`31` forced_move=`c6b6`
