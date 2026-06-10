# KRK Protected Plan-Window Failure Contrast Manifest v0

Status: `protected_plan_window_failure_contrast_manifest_ready_for_review`

This is a bounded non-causal collection manifest for review. It does not execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.

## Summary

- job_count: `6`
- max_collection_jobs: `6`
- minimum_new_unique_failures_needed: `4`
- target_failure_label_goal: `conversion_failure`
- source_stage_counts: `{'stage5': 2, 'stage6': 2, 'stage4': 2}`
- source_family_counts: `{'fence_handoff_plan_window': 2, 'drive_to_edge_plan_window': 2, 'wrong_tempo_plan_window': 2}`
- missing_required_source_stages: `[]`
- all_bindings_valid: `True`
- topology_path: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json`
- topology_path_safe: `True`
- topology_exists: `True`
- output_paths_valid: `True`
- forbidden_job_flag_count: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_training_row_count: `0`
- manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`

## Jobs

- `protected_plan_failure.01.planwin.a8dd289c75b7` stage=`stage5` family=`fence_handoff_plan_window` seed=`planwin.a8dd289c75b7` target=`fence_handoff_abort_or_max_plies`
- `protected_plan_failure.02.planwin.6ffab60fb0d0` stage=`stage5` family=`fence_handoff_plan_window` seed=`planwin.6ffab60fb0d0` target=`fence_handoff_abort_or_max_plies`
- `protected_plan_failure.03.planwin.4f9789a608c4` stage=`stage6` family=`drive_to_edge_plan_window` seed=`planwin.4f9789a608c4` target=`drive_to_edge_abort_or_max_plies`
- `protected_plan_failure.04.planwin.e09fb2b8a021` stage=`stage6` family=`drive_to_edge_plan_window` seed=`planwin.e09fb2b8a021` target=`drive_to_edge_abort_or_max_plies`
- `protected_plan_failure.05.planwin.23c0bb760d87` stage=`stage4` family=`wrong_tempo_plan_window` seed=`planwin.23c0bb760d87` target=`wrong_tempo_stage0_or_handoff_abort`
- `protected_plan_failure.06.planwin.d90d6f3d623a` stage=`stage4` family=`wrong_tempo_plan_window` seed=`planwin.d90d6f3d623a` target=`wrong_tempo_stage0_or_handoff_abort`

## Decision

- recommended_next_step: `review_protected_plan_window_failure_contrast_manifest`
- collection_run_allowed: `false`
- label_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
