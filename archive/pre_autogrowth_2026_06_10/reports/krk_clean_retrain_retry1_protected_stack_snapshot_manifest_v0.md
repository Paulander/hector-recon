# KRK Retry1 Protected Stack Snapshot Manifest v0

Status: `retry1_protected_stack_snapshot_manifest_ready_no_replacement`

## Decision

- Manifest records current protected stack: `True`
- Manifest records retry1 candidate stack: `True`
- All referenced paths exist: `True`
- Clean stack replacement allowed by manifest: `False`
- Recommended next step: `write_clean_stack_replacement_review_packet_before_any_file_change`

## Current Protected Stack

- `stage5_fence`: topology=`snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json`, provider=`snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl`, run_manifest=`snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/run_manifest.json`
- `stage6_drive_overlay`: topology=`snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json`, promotion_eval=`snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json`, stage6_validation=`snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json`, stage5_guardrail=`snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json`, stage4_caveat_control=`snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_stage5_base_control_300_seed7_h40.json`

## Retry1 Candidate Stack

- `stage5_fence`: topology=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage5_fence_handoff/topology/krk_entry_topology.json`, provider=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage5_fence_handoff/baseline/best_by_stage/fence_established.pkl`, run_manifest=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage5_fence_handoff/baseline/curriculum_history.json`
- `stage6_drive_overlay`: topology=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json`, provider=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_drive_overlay_candidate/baseline/best_by_stage/drive_to_edge.pkl`, promotion_eval=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/promotion_eval_stage6_overlay_profile_bonus.json`, stage6_validation=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage6_drive_overlay_300_seed7_h40_profile_bonus.json`, stage5_guardrail=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40_profile_bonus.json`, stage4_caveat_control=`snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage4_wrong_tempo_stage5_base_control_300_seed7_h40_profile_bonus.json`

## Missing Paths

- none

## Rollback Requirements

- Record exact current protected topology/provider paths before any replacement.
- Do not delete or overwrite current protected snapshots.
- Any replacement packet must name the rollback source paths and candidate target paths explicitly.
- A rollback must restore the previous protected topology/provider pointers without retraining.
- Stage 7 remains held-out/quarantined and cannot be included in the replacement stack.

## Boundary

This manifest is reference-only. It does not copy, replace, delete, promote, train, route, score, mutate topology, or change runtime defaults.
