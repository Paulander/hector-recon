# KRK Protected Plan-Window Failure Contrast Runner v0

Status: `protected_plan_window_failure_contrast_runner_dry_run_ready`

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
- execution_readiness_status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- execution_readiness_current_control_plane_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- execution_readiness_current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'approve_protected_plan_window_failure_contrast_collection']`
- execution_readiness_protected_failure_contrast_collection_option_available: `True`
- execution_readiness_protected_failure_contrast_collection_command_available: `True`
- execution_readiness_protected_failure_contrast_collection_option_id: `approve_protected_plan_window_failure_contrast_collection`
- execution_readiness_protected_failure_contrast_collection_blocked_by_option_id: `None`
- execution_readiness_jobs_passing: `6`
- execution_readiness_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- execution_readiness_fingerprint: `7322af51693bcc4d48d49609522d88e533e714a42be2135f8ab9a69a77649b9b`
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
- execution_readiness_checked_flag_count: `1913`
- execution_readiness_boundary_violation_count: `0`
- execution_readiness_source_artifact_count: `234`
- approval_receipt_required_for_execution: `True`
- approval_receipt_present: `False`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_missing']`
- output_validation_status: `protected_plan_window_failure_contrast_outputs_validation_pending`
- output_exists_count: `0`
- output_valid_count: `0`
- invalid_existing_output_count: `0`
- refresh_after_run_requested: `True`
- refresh_after_run_performed: `False`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Jobs

- `protected_plan_failure.01.planwin.a8dd289c75b7` output_exists=`False` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.02.planwin.6ffab60fb0d0` output_exists=`False` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.03.planwin.4f9789a608c4` output_exists=`False` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.04.planwin.e09fb2b8a021` output_exists=`False` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.05.planwin.23c0bb760d87` output_exists=`False` would_execute=`False` would_skip_existing=`False`
- `protected_plan_failure.06.planwin.d90d6f3d623a` output_exists=`False` would_execute=`False` would_skip_existing=`False`

## Decision

- recommended_next_step: `obtain_matching_approval_receipt_then_run_with_explicit_execute_flag`
- collection_run_allowed: `False`
- label_run_allowed: `False`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
