# KRK Protected Plan-Window Failure Contrast Execution Readiness v0

Status: `protected_plan_window_failure_contrast_execution_readiness_blocked_pending_control_plane_gate_review`

This is a dry-run preflight only. It does not execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.

## Summary

- job_count: `6`
- jobs_passing_readiness: `6`
- all_jobs_pass_readiness: `True`
- job_readiness_blocker_count: `0`
- manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- manifest_review_status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_control_plane_gate_review`
- current_control_plane_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'review_protected_plan_window_failure_contrast_manifest']`
- protected_failure_contrast_collection_option_available: `False`
- protected_failure_contrast_collection_command_available: `False`
- protected_failure_contrast_collection_option_id: `None`
- protected_failure_contrast_collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`
- manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- recorded_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- review_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- manifest_fingerprints_match: `True`
- execution_readiness_blockers: `['protected_plan_window_failure_contrast_control_plane_gate_review_required']`
- existing_output_count: `6`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_training_row_count: `0`
- protected_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- protected_stack_ready: `True`
- protected_stack_rollback_paths_preserved: `True`
- protected_stack_active_paths_safe: `True`
- protected_stack_active_paths_exist: `True`
- protected_stack_rollback_paths_safe: `True`
- protected_stack_rollback_paths_exist: `True`
- protected_stack_rollback_common_paths_distinct: `True`
- protected_stack_filesystem_snapshots_replaced: `False`
- protected_stack_hard_blockers: `[]`
- readiness_checked_flag_count: `2912`
- readiness_boundary_violation_count: `0`
- readiness_source_artifact_count: `408`
- readiness_fingerprint: `0a9fe46170cb062d4a12db0b4ddf3bb9348142c9e2f575ee946afc30960acfbe`

## Jobs

- `protected_plan_failure.01.planwin.a8dd289c75b7` ready=`True` output_exists=`True` blockers=`[]`
- `protected_plan_failure.02.planwin.6ffab60fb0d0` ready=`True` output_exists=`True` blockers=`[]`
- `protected_plan_failure.03.planwin.4f9789a608c4` ready=`True` output_exists=`True` blockers=`[]`
- `protected_plan_failure.04.planwin.e09fb2b8a021` ready=`True` output_exists=`True` blockers=`[]`
- `protected_plan_failure.05.planwin.23c0bb760d87` ready=`True` output_exists=`True` blockers=`[]`
- `protected_plan_failure.06.planwin.d90d6f3d623a` ready=`True` output_exists=`True` blockers=`[]`

## Decision

- recommended_next_step: `review_current_control_plane_gate_for_protected_failure_contrast_collection`
- collection_run_allowed: `false`
- label_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
