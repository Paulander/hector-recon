# KRK Balanced Hard-Negative Execution Manifest v0

Bound execution manifest for protected hard-negative label expansion. It does not execute labels.

## Binding Summary

- `job_count`: `12`
- `topology_path`: `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json`
- `topology_exists`: `True`
- `missing_provider_skill_ids`: `[]`
- `stage7_jobs`: `0`
- `all_bindings_valid`: `True`

## Jobs

- `job.krk.balanced_hard_negative.d4d27a10d1c4` stage=`stage5` provider=`krk.stage0_basin` version=`foundation_frozen_v1`
- `job.krk.balanced_hard_negative.fd95ab614799` stage=`stage5` provider=`krk.stage0_basin` version=`foundation_frozen_v1`
- `job.krk.balanced_hard_negative.8c7944e4b11b` stage=`stage4` provider=`krk.stage0_basin` version=`foundation_frozen_v1`
- `job.krk.balanced_hard_negative.0129b9fbfc65` stage=`stage4` provider=`krk.stage0_basin` version=`foundation_frozen_v1`
- `job.krk.balanced_hard_negative.e3b51918de2d` stage=`stage4` provider=`krk.stage0_basin` version=`foundation_frozen_v1`
- `job.krk.balanced_hard_negative.3ce9a363baff` stage=`stage5` provider=`krk.drive_to_edge` version=`stage6_overlay_v1`
- `job.krk.balanced_hard_negative.02a926e18ae1` stage=`stage5` provider=`krk.drive_to_edge` version=`stage6_overlay_v1`
- `job.krk.balanced_hard_negative.a8a2493398d4` stage=`stage5` provider=`krk.fence_established` version=`stage5_validated_v1`
- `job.krk.balanced_hard_negative.a89843f4f707` stage=`stage6` provider=`krk.drive_to_edge` version=`stage6_overlay_v1`
- `job.krk.balanced_hard_negative.1f6a0b02f7b7` stage=`stage6` provider=`krk.fence_established` version=`stage5_validated_v1`
- `job.krk.balanced_hard_negative.91560b3a0090` stage=`stage6` provider=`krk.drive_to_edge` version=`stage6_overlay_v1`
- `job.krk.balanced_hard_negative.c9f3bdbd81b4` stage=`stage5` provider=`krk.drive_to_edge` version=`stage6_overlay_v1`

## Decision

- `status`: `balanced_hard_negative_execution_manifest_bound`
- `recommended_next_step`: `review_balanced_hard_negative_execution_manifest`
- `labels_allowed_now`: `False`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
