# KRK Balanced Hard-Negative Label Plan v0

Bounded non-causal plan to improve protected hard-negative label balance before any selector training or runtime work.

## Summary

- `job_count`: `12`
- `source_state_count`: `10`
- `stage_counts`: `{'stage5': 6, 'stage4': 3, 'stage6': 3}`
- `provider_family_counts`: `{'stage0_basin': 5, 'drive_to_edge': 5, 'fence_established': 2}`
- `stage7_jobs`: `0`
- `runtime_work_allowed`: `False`

## Label Budget

- `max_jobs`: `12`
- `horizon`: `40`
- `trace_failures_only`: `True`
- `diagnostic_caches`: `True`
- `stage7_jobs`: `0`
- `expensive_sweeps_allowed`: `False`

## Jobs

- `job.krk.balanced_hard_negative.d4d27a10d1c4` stage=`stage5` state=`state.87b1160e68b9` provider=`krk.stage0_basin` family=`stage0_basin`
- `job.krk.balanced_hard_negative.fd95ab614799` stage=`stage5` state=`state.3dca34326fca` provider=`krk.stage0_basin` family=`stage0_basin`
- `job.krk.balanced_hard_negative.8c7944e4b11b` stage=`stage4` state=`state.02cfd843a2cf` provider=`krk.stage0_basin` family=`stage0_basin`
- `job.krk.balanced_hard_negative.0129b9fbfc65` stage=`stage4` state=`state.1e4f48a672e8` provider=`krk.stage0_basin` family=`stage0_basin`
- `job.krk.balanced_hard_negative.e3b51918de2d` stage=`stage4` state=`state.256a3da30f0f` provider=`krk.stage0_basin` family=`stage0_basin`
- `job.krk.balanced_hard_negative.3ce9a363baff` stage=`stage5` state=`state.02feb8593cc6` provider=`krk.drive_to_edge` family=`drive_to_edge`
- `job.krk.balanced_hard_negative.02a926e18ae1` stage=`stage5` state=`state.2c1d6da27ea1` provider=`krk.drive_to_edge` family=`drive_to_edge`
- `job.krk.balanced_hard_negative.a8a2493398d4` stage=`stage5` state=`state.2c1d6da27ea1` provider=`krk.fence_established` family=`fence_established`
- `job.krk.balanced_hard_negative.a89843f4f707` stage=`stage6` state=`state.52085d244e9d` provider=`krk.drive_to_edge` family=`drive_to_edge`
- `job.krk.balanced_hard_negative.1f6a0b02f7b7` stage=`stage6` state=`state.52085d244e9d` provider=`krk.fence_established` family=`fence_established`
- `job.krk.balanced_hard_negative.91560b3a0090` stage=`stage6` state=`state.69711173114a` provider=`krk.drive_to_edge` family=`drive_to_edge`
- `job.krk.balanced_hard_negative.c9f3bdbd81b4` stage=`stage5` state=`state.326222aefdf1` provider=`krk.drive_to_edge` family=`drive_to_edge`

## Decision

- `status`: `balanced_hard_negative_label_plan_ready`
- `recommended_next_step`: `bind_and_review_balanced_hard_negative_execution_manifest`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
