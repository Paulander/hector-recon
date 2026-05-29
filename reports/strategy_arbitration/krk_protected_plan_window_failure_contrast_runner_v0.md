# KRK Protected Plan-Window Failure Contrast Runner v0

Status: `protected_plan_window_failure_contrast_runner_blocked`

Default mode is dry-run only. Executing collection requires explicit user approval, the `--execute-reviewed-collection` flag, and a matching approval receipt. Runtime defaults, selector training, Stage 7 promotion, and Stage 8 training remain blocked.

## Summary

- job_count: `6`
- manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- manifest_declared_job_count: `6`
- manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- processed_job_count: `0`
- executed_job_count: `0`
- skipped_existing_output_count: `0`
- failed_job_count: `0`
- timed_out_job_count: `0`
- dry_run: `True`
- max_jobs: `None`
- job_timeout_seconds: `900`
- overwrite_existing_outputs: `False`
- execution_readiness_status: `protected_plan_window_failure_contrast_execution_readiness_blocked_pending_control_plane_gate_review`
- execution_readiness_current_control_plane_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- execution_readiness_current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'review_protected_plan_window_failure_contrast_manifest']`
- execution_readiness_protected_failure_contrast_collection_option_available: `False`
- execution_readiness_protected_failure_contrast_collection_command_available: `False`
- execution_readiness_protected_failure_contrast_collection_option_id: `None`
- execution_readiness_protected_failure_contrast_collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`
- execution_readiness_jobs_passing: `6`
- execution_readiness_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- execution_readiness_fingerprint: `0a9fe46170cb062d4a12db0b4ddf3bb9348142c9e2f575ee946afc30960acfbe`
- execution_readiness_all_jobs_pass: `True`
- execution_readiness_protected_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- execution_readiness_protected_stack_ready: `True`
- execution_readiness_protected_stack_rollback_paths_preserved: `True`
- execution_readiness_protected_stack_active_paths_safe: `True`
- execution_readiness_protected_stack_active_paths_exist: `True`
- execution_readiness_protected_stack_rollback_paths_safe: `True`
- execution_readiness_protected_stack_rollback_paths_exist: `True`
- execution_readiness_protected_stack_rollback_common_paths_distinct: `True`
- execution_readiness_protected_stack_filesystem_snapshots_replaced: `False`
- execution_readiness_protected_stack_hard_blockers: `[]`
- execution_readiness_checked_flag_count: `2912`
- execution_readiness_boundary_violation_count: `0`
- execution_readiness_source_artifact_count: `408`
- approval_receipt_required_for_execution: `True`
- approval_receipt_present: `True`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_readiness_fingerprint_mismatch', 'approval_receipt_readiness_status_mismatch', 'approval_receipt_current_control_plane_approval_option_ids_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_command_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_id_mismatch', 'approval_receipt_protected_failure_contrast_collection_blocked_by_option_id_mismatch']`
- output_validation_status: `protected_plan_window_failure_contrast_outputs_valid_ready_for_integration`
- output_exists_count: `6`
- output_valid_count: `6`
- invalid_existing_output_count: `0`
- refresh_after_run_requested: `True`
- refresh_after_run_performed: `False`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Jobs

- `protected_plan_failure.01.planwin.a8dd289c75b7` output_exists=`True` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.02.planwin.6ffab60fb0d0` output_exists=`True` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.03.planwin.4f9789a608c4` output_exists=`True` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.04.planwin.e09fb2b8a021` output_exists=`True` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.05.planwin.23c0bb760d87` output_exists=`True` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.06.planwin.d90d6f3d623a` output_exists=`True` would_execute=`False` would_skip_existing=`False`

## Decision

- recommended_next_step: `review_current_control_plane_gate_for_protected_failure_contrast_collection`
- collection_run_allowed: `False`
- label_run_allowed: `False`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
