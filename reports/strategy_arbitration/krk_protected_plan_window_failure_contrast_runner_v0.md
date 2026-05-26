# KRK Protected Plan-Window Failure Contrast Runner v0

Status: `protected_plan_window_failure_contrast_runner_dry_run_ready`

Default mode is dry-run only. Executing collection requires explicit user approval, the `--execute-reviewed-collection` flag, and a matching approval receipt. Runtime defaults, selector training, Stage 7 promotion, and Stage 8 training remain blocked.

## Summary

- job_count: `6`
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
- execution_readiness_jobs_passing: `6`
- execution_readiness_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- execution_readiness_fingerprint: `2a1b10fb7e14001a58397f74fbce3fb68941305b01378c14676a0f1948d5889d`
- execution_readiness_all_jobs_pass: `True`
- approval_receipt_required_for_execution: `True`
- approval_receipt_present: `False`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_missing']`
- output_validation_status: `protected_plan_window_failure_contrast_outputs_validation_pending`
- output_exists_count: `0`
- output_valid_count: `0`
- invalid_existing_output_count: `0`
- refresh_after_run_requested: `False`
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
