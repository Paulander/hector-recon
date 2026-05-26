# KRK Full Suite Unblocker Packet v0

## Decision

- status: `krk_suite_protected_failure_contrast_unblocker_ready_pending_explicit_collection_approval`
- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- implementation_allowed_by_this_packet: `False`
- label_run_allowed: `False`
- runtime_changes_allowed: `False`

## Current State

- protected_stack_ready: `True`
- protected_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- protected_stack_rollback_paths_preserved: `True`
- protected_stack_active_paths_safe: `True`
- protected_stack_active_paths_exist: `True`
- protected_stack_rollback_paths_safe: `True`
- protected_stack_rollback_paths_exist: `True`
- protected_stack_rollback_common_paths_distinct: `True`
- protected_stack_filesystem_snapshots_replaced: `False`
- stage7_success_controls: `11`
- stage7_success_controls_required: `5`
- sequence_policy_inputs_ready: `True`
- sequence_policy_benchmark_ready: `True`
- stage8_training_ready: `False`
- stage7_output_validation_status: `stage7_diverse_clean_sampling_outputs_valid_ready_for_integration`
- stage7_invalid_existing_output_count: `0`
- stage7_overwrite_existing_outputs: `False`
- stage7_processed_job_count: `0`
- stage7_executed_job_count: `0`
- stage7_historical_processed_job_count: `8`
- stage7_historical_executed_job_count: `8`
- stage7_skipped_existing_output_count: `0`
- stage7_label_distribution_review_status: `stage7_label_distribution_review_success_gate_closed`
- stage7_label_distribution_unique_new_success: `2`
- stage7_label_distribution_duplicate_playouts: `50`
- stage7_additional_clean_sampling_manifest_status: `stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed`
- stage7_additional_clean_sampling_runner_status: `stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed`
- stage7_additional_clean_sampling_job_count: `0`
- protected_plan_window_failure_contrast_plan_status: `protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval`
- protected_plan_window_unique_failure_count: `1`
- protected_plan_window_minimum_new_failures_needed: `4`
- protected_plan_window_failure_contrast_manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- protected_plan_window_failure_contrast_manifest_job_count: `6`
- protected_plan_window_failure_contrast_manifest_review_status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval`
- protected_plan_window_failure_contrast_execution_readiness_status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- protected_plan_window_failure_contrast_execution_jobs_passing: `6`
- protected_plan_window_failure_contrast_runner_status: `protected_plan_window_failure_contrast_runner_dry_run_ready`
- protected_plan_window_failure_contrast_runner_processed_job_count: `0`
- protected_plan_window_failure_contrast_runner_executed_job_count: `0`
- protected_plan_window_failure_contrast_approval_request_status: `protected_plan_window_failure_contrast_approval_request_ready`
- protected_plan_window_failure_contrast_approval_receipt_created: `False`
- protected_plan_window_failure_contrast_approval_receipt_blockers: `['approval_receipt_missing']`
- protected_plan_window_failure_contrast_output_validation_status: `protected_plan_window_failure_contrast_outputs_validation_pending`
- protected_plan_window_failure_contrast_output_exists_count: `0`
- protected_plan_window_failure_contrast_output_valid_count: `0`
- protected_plan_window_failure_contrast_integration_status: `protected_plan_window_failure_contrast_integration_pending_outputs`
- protected_plan_window_failure_contrast_integrated_new_failure_count: `0`
- protected_plan_window_failure_contrast_integration_ready: `False`
- sequence_policy_after_protected_failure_contrast_refresh_status: `sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs`
- sequence_policy_after_protected_failure_contrast_rows: `0`

## Why Work Stops At This Gate

- The Stage 7 held-out clean label gate is closed; the remaining non-causal benchmark review identifies protected plan-window failure-contrast sparsity.
- Runtime changes, Stage 7 promotion, and Stage 8 training remain gated by repository reports and architecture policy.
- The current /goal does not by itself authorize runtime behavior, Stage 7 promotion, or Stage 8 training.

## Primary Unblocker

- id: `protected_plan_window_failure_contrast_collection`
- status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval`
- purpose: Review the bounded protected plan-window failure-contrast manifest before any explicitly approved collection run.
- command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py --execute-reviewed-collection --refresh-after-run --approval-receipt reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- max_jobs: `6`
- horizon: `h40`
- stage: `protected_plan_window_failure_contrast_evidence_only`
- stop_after_unique_failures: `4`
- observation_only: `True`
- resume_safe: `True`
- skip_existing_outputs_by_default: `True`
- invalid_existing_outputs_block_without_overwrite: `True`
- per_job_timeout_seconds: `900`
- approval_receipt_required: `True`
- approval_receipt_path: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- approval_receipt_present: `False`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_missing']`
- approval_request_artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.json`
- approval_request_status: `protected_plan_window_failure_contrast_approval_request_ready`
- approval_receipt_created_by_request: `False`
- expected_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- expected_readiness_fingerprint: `351a366042e7e888018897007e29e096afdb180a9c4f4eb02853940b82228c66`
- post_success_refresh: `full_passive_krk_suite_gate_stack`
- stage7_training_rows: `0`
- approval_required: `True`
- implementation_allowed_by_this_packet: `False`

## Secondary Unblocker

- id: `stage4_first_move_contrast_sandbox`
- status: `stage4_caveat_unblocker_ready_pending_explicit_runtime_approval`
- purpose: Address the separate Stage 4 h40 caveat through a reviewed default-off sandbox path.
- approval_request_artifact: `reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md`
- approval_request_status: `stage4_first_move_contrast_sandbox_approval_request_ready`
- approval_request_created: `False`
- implementation_authorized_by_approval_request: `False`
- why_secondary: This may reduce Stage 4 debt, but it does not directly fill the protected plan-window failure-contrast sparsity now blocking sequence-policy review.

## Low-Value Safe Work Remaining

- Rerunning Stage 7 label commands without overwrite will skip existing outputs; the Stage 7 success-control gap is already closed.
- More passive summaries can be written, but the next useful work is benchmark review or protected plan-window failure-contrast collection.
