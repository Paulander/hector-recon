# KRK Forced Provider Control Label Plan v0

This is a non-causal job plan. It does not run labels, force providers during gameplay, implement an arbiter, change defaults, promote Stage 7, or train Stage 8.

## Rationale

Stratified probe v2 found selected protected-control labels promising but forced Stage7 labels weak/sparse.

## Job Selection

- Target stages: `['stage5', 'stage6']`
- Selected jobs: `12`
- Jobs by stage: `{'stage5': 6, 'stage6': 6}`
- Current label result counts: `{'mate': 8, 'max_plies': 4}`

## Jobs

- `job.krk.forced_provider_control.c715487480c5` stage=`stage5` provider=`krk.stage0_basin` move=`f2g3` current=`selected_provider_playout:mate`
- `job.krk.forced_provider_control.150c41c3b1ad` stage=`stage5` provider=`krk.edge_trap_close` move=`e7e8` current=`selected_provider_playout:mate`
- `job.krk.forced_provider_control.7ab58d03a5bc` stage=`stage5` provider=`krk.edge_trap_enemy_between` move=`e7e8` current=`same_move_unselected_provider_playout:mate`
- `job.krk.forced_provider_control.adde0e92f3a3` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` move=`e7e8` current=`same_move_unselected_provider_playout:mate`
- `job.krk.forced_provider_control.7474bd7cf9de` stage=`stage5` provider=`krk.stage0_basin` move=`a7a8` current=`selected_provider_playout:mate`
- `job.krk.forced_provider_control.cd9c093a0c99` stage=`stage5` provider=`krk.edge_trap_close` move=`h7c7` current=`selected_provider_playout:max_plies`
- `job.krk.forced_provider_control.6a22ba706f91` stage=`stage6` provider=`krk.stage0_basin` move=`a1g1` current=`selected_provider_playout:mate`
- `job.krk.forced_provider_control.5b9da3b441ec` stage=`stage6` provider=`krk.stage0_basin` move=`a8f8` current=`selected_provider_playout:mate`
- `job.krk.forced_provider_control.772216e525ec` stage=`stage6` provider=`krk.stage0_basin` move=`a1d1` current=`selected_provider_playout:mate`
- `job.krk.forced_provider_control.c732438d4ceb` stage=`stage6` provider=`krk.edge_trap_close` move=`h7c7` current=`selected_provider_playout:max_plies`
- `job.krk.forced_provider_control.1f5da08ca8bb` stage=`stage6` provider=`krk.edge_trap_enemy_between` move=`h7c7` current=`same_move_unselected_provider_playout:max_plies`
- `job.krk.forced_provider_control.c25eb5d2cfe9` stage=`stage6` provider=`krk.edge_trap_wrong_tempo` move=`h7c7` current=`same_move_unselected_provider_playout:max_plies`

## Acceptance For Future Label Run

- `no_runtime_behavior_change`
- `no_stage7_promotion`
- `no_stage8_training`
- `no_runtime_dtm_or_tablebase`
- `no_exhaustive_legal_first_sweeps`
- `forced_provider_labels_are_non_causal_outcome_labels`
- `run_stops_if_projected_to_hours`

## Recommended Next Step

`run_bounded_forced_provider_control_labels_if_runner_available`
