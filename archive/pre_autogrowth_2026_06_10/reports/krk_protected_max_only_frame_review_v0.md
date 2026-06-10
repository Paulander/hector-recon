# KRK Protected Max-Only Frame Review v0

Status: `protected_max_only_frames_block_runtime_selector`

Replay-free review of protected strategy-arbitration frames that have no labeled converting provider proposal.

## Summary

- strategy_benchmark_frame_count: `24`
- frames_with_labeled_mate_provider: `12`
- frames_with_only_labeled_max_plies_providers: `12`
- max_only_by_stage: `{'stage5': 4, 'stage6': 5, 'stage4': 3}`
- max_only_provider_counts: `{'krk.edge_trap_close': 8, 'krk.edge_trap_enemy_between': 8, 'krk.edge_trap_wrong_tempo': 8, 'krk.stage0_basin': 4}`
- baseline_selected_status: `strategy_arbitration_promising`
- runtime_work_allowed: `False`

## Interpretation

- The protected strategy selector can only choose among materialized/labeled provider proposals.
- Current selectors recover mate when a labeled converting provider is present, but half of protected benchmark frames have no labeled mate provider.
- This makes the next broader bottleneck a missing-provider / continuation-capacity / label-coverage problem, not a selector-score problem.

## Max-Only Frames

- `cp.krk.state.02feb8593cc6` stage=`stage5` label=`fence_established` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.326222aefdf1` stage=`stage5` label=`fence_established` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.3dca34326fca` stage=`stage5` label=`fence_established` providers=`{'krk.stage0_basin': 1}`
- `cp.krk.state.02feb8593cc6` stage=`stage5` label=`fence_established` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.699f0003a511` stage=`stage6` label=`drive_to_edge` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.699f0003a511` stage=`stage6` label=`drive_to_edge` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.699f0003a511` stage=`stage6` label=`drive_to_edge` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.699f0003a511` stage=`stage6` label=`drive_to_edge` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.699f0003a511` stage=`stage6` label=`drive_to_edge` providers=`{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.edge_trap_wrong_tempo': 1}`
- `cp.krk.state.256a3da30f0f` stage=`stage4` label=`wrong_tempo_control` providers=`{'krk.stage0_basin': 1}`
- `cp.krk.state.b11124d658cf` stage=`stage4` label=`wrong_tempo_control` providers=`{'krk.stage0_basin': 1}`
- `cp.krk.state.256a3da30f0f` stage=`stage4` label=`wrong_tempo_control` providers=`{'krk.stage0_basin': 1}`

Recommended next step: `define_protected_missing_provider_capacity_audit`
