# KRK Protected Missing-Provider Capacity Audit Plan v0

Status: `protected_missing_provider_capacity_audit_plan_ready`

This is a non-causal label plan for protected Stage 4/5/6 frames that currently have only max-plies provider labels.

## Summary

- job_count: `16`
- source_frame_count: `6`
- provider_counts: `{'krk.drive_to_edge': 1, 'krk.edge_trap_close': 3, 'krk.edge_trap_enemy_between': 3, 'krk.edge_trap_wrong_tempo': 3, 'krk.fence_established': 3, 'krk.stage0_basin': 3}`
- stage_counts: `{'stage4': 6, 'stage5': 7, 'stage6': 3}`
- runtime_work_allowed: `False`

## Label Budget

- max_frames: `12`
- max_jobs: `36`
- horizon: `40`
- trace_failures_only: `True`
- diagnostic_caches: `True`
- stage7_jobs: `0`

## Jobs

- `job.krk.protected_missing_provider.75babbcc6000` frame=`cp.krk.state.02feb8593cc6` stage=`stage5` provider=`krk.stage0_basin`
- `job.krk.protected_missing_provider.5f9c11521077` frame=`cp.krk.state.02feb8593cc6` stage=`stage5` provider=`krk.fence_established`
- `job.krk.protected_missing_provider.38d0a11daf0c` frame=`cp.krk.state.326222aefdf1` stage=`stage5` provider=`krk.stage0_basin`
- `job.krk.protected_missing_provider.9df1f2680cbc` frame=`cp.krk.state.326222aefdf1` stage=`stage5` provider=`krk.fence_established`
- `job.krk.protected_missing_provider.8d58e5a5f72c` frame=`cp.krk.state.3dca34326fca` stage=`stage5` provider=`krk.edge_trap_close`
- `job.krk.protected_missing_provider.a306768e24a0` frame=`cp.krk.state.3dca34326fca` stage=`stage5` provider=`krk.edge_trap_wrong_tempo`
- `job.krk.protected_missing_provider.9a4cc895c68d` frame=`cp.krk.state.3dca34326fca` stage=`stage5` provider=`krk.edge_trap_enemy_between`
- `job.krk.protected_missing_provider.4dca16fc81b3` frame=`cp.krk.state.699f0003a511` stage=`stage6` provider=`krk.stage0_basin`
- `job.krk.protected_missing_provider.abcf6fafb467` frame=`cp.krk.state.699f0003a511` stage=`stage6` provider=`krk.drive_to_edge`
- `job.krk.protected_missing_provider.54fd6c4dd136` frame=`cp.krk.state.699f0003a511` stage=`stage6` provider=`krk.fence_established`
- `job.krk.protected_missing_provider.01f7ab28aca7` frame=`cp.krk.state.256a3da30f0f` stage=`stage4` provider=`krk.edge_trap_close`
- `job.krk.protected_missing_provider.ac1e25bed37b` frame=`cp.krk.state.256a3da30f0f` stage=`stage4` provider=`krk.edge_trap_wrong_tempo`
- `job.krk.protected_missing_provider.8bd0028955fa` frame=`cp.krk.state.256a3da30f0f` stage=`stage4` provider=`krk.edge_trap_enemy_between`
- `job.krk.protected_missing_provider.6262bf8a2534` frame=`cp.krk.state.b11124d658cf` stage=`stage4` provider=`krk.edge_trap_close`
- `job.krk.protected_missing_provider.104cb87db2f9` frame=`cp.krk.state.b11124d658cf` stage=`stage4` provider=`krk.edge_trap_wrong_tempo`
- `job.krk.protected_missing_provider.8343f8b595ba` frame=`cp.krk.state.b11124d658cf` stage=`stage4` provider=`krk.edge_trap_enemy_between`

## Blocked Actions

- `execute labels without review`
- `runtime selector changes`
- `Stage 7 repair or promotion`
- `Stage 8 training`
- `runtime DTM/tablebase use`
- `gameplay topology mutation`

Recommended next step: `review_manifest_before_any_label_execution`
