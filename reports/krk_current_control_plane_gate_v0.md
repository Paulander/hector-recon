# KRK Current Control-Plane Gate v0

Status: `krk_control_plane_waiting_on_explicit_gate_choice`

## Current State

- protected_stack: `retry1_stage5_6_active_manifest_validated`
- protected_stack_ready: `True`
- protected_stack_hard_blockers: `[]`
- stage4: `first_move_contrast_runtime_review_ready_pending_explicit_approval`
- stage7: `heldout_clean_success_controls_ready_sequence_benchmark_available`
- stage7_success_controls_ready: `True`
- stage7_success_controls: `11`
- stage7_success_controls_required: `5`
- stage7_label_execution_readiness: `not_applicable_stage7_success_gate_closed`
- stage7_label_historical_execution_readiness: `stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval`
- stage7_label_output_integration: `stage7_diverse_clean_sampling_integration_success_controls_met`
- stage7_label_runner: `stage7_diverse_clean_sampling_runner_executed_success`
- stage7_label_runner_output_validation_status: `stage7_diverse_clean_sampling_outputs_valid_ready_for_integration`
- stage7_label_output_validation_status: `stage7_diverse_clean_sampling_outputs_valid_ready_for_integration`
- stage7_label_distribution_review: `stage7_label_distribution_review_success_gate_closed`
- stage7_additional_label_manifest: `stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed`
- stage7_additional_label_runner: `stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed`
- stage7_additional_label_runner_job_count: `0`
- stage7_label_runner_execution_readiness_source: `live_recomputed`
- stage7_label_runner_execution_readiness_status: `not_applicable_stage7_success_gate_closed`
- stage7_label_runner_historical_execution_readiness_status: `stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval`
- stage7_label_runner_execution_readiness_jobs_passing: `8`
- stage7_label_runner_invalid_existing_output_count: `0`
- stage7_label_runner_processed_job_count: `0`
- stage7_label_runner_executed_job_count: `0`
- stage7_label_runner_historical_processed_job_count: `8`
- stage7_label_runner_historical_executed_job_count: `8`
- stage7_label_runner_skipped_existing_output_count: `0`
- stage7_label_runner_job_timeout_seconds: `900`
- stage7_label_runner_timed_out_job_count: `0`
- stage7_post_label_outcome: `post_label_outcome_waiting_on_explicit_protected_failure_contrast_collection`
- protected_plan_window_evidence: `available_non_causal`
- sequence_policy: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- sequence_policy_forbidden_training_or_runtime_input_blocked: `False`
- sequence_policy_forbidden_training_or_runtime_input_blockers: `[]`
- protected_plan_window_failure_contrast_plan: `protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval`
- protected_plan_window_unique_failure_count: `1`
- protected_plan_window_minimum_new_failures_needed: `4`
- protected_plan_window_failure_contrast_manifest: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- protected_plan_window_failure_contrast_manifest_job_count: `6`
- protected_plan_window_failure_contrast_manifest_review: `protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval`
- protected_plan_window_failure_contrast_execution_readiness: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- protected_plan_window_failure_contrast_execution_jobs_passing: `6`
- protected_plan_window_failure_contrast_runner: `protected_plan_window_failure_contrast_runner_dry_run_ready`
- protected_plan_window_failure_contrast_runner_processed_job_count: `0`
- protected_plan_window_failure_contrast_runner_executed_job_count: `0`
- protected_plan_window_failure_contrast_approval_request: `protected_plan_window_failure_contrast_approval_request_ready`
- protected_plan_window_failure_contrast_approval_receipt_created: `False`
- protected_plan_window_failure_contrast_approval_receipt_blockers: `['approval_receipt_missing']`
- protected_plan_window_failure_contrast_output_validation: `protected_plan_window_failure_contrast_outputs_validation_pending`
- protected_plan_window_failure_contrast_output_exists_count: `0`
- protected_plan_window_failure_contrast_output_valid_count: `0`
- protected_plan_window_failure_contrast_integration: `protected_plan_window_failure_contrast_integration_pending_outputs`
- protected_plan_window_failure_contrast_integrated_new_failure_count: `0`
- protected_plan_window_failure_contrast_integration_ready: `False`
- sequence_policy_after_protected_failure_contrast_refresh: `sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs`
- sequence_policy_after_protected_failure_contrast_rows: `0`
- sequence_policy_inputs: `sequence_policy_benchmark_inputs_ready_non_causal`
- stage8: `blocked`
- runtime_selector: `blocked`

## Approval Options

### approve_stage4_first_move_contrast_sandbox

- artifact: `reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.md`
- status: `stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval`
- allows: default-off Stage 4 CandidateMoveFrame first-move contrast sandbox only
- recommended_if: you want to reduce the known Stage 4 h40 caveat now
- approval_request_artifact: `reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md`
- approval_request_status: `stage4_first_move_contrast_sandbox_approval_request_ready`
- does_not_allow:
  - default enablement
  - exact-state or exact-move runtime exception
  - selector training
  - broad stage0 penalty
  - provider suppression
  - Stage 7 promotion
  - Stage 8 training

### approve_protected_plan_window_failure_contrast_collection

- artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_review_v0.md`
- status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- allows: explicitly approved bounded observation-only protected plan-window failure-contrast collection
- recommended_if: manifest review passed and you want to collect bounded observation-only failure contrasts
- command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py --execute-reviewed-collection --refresh-after-run --approval-receipt reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- approval_request_artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.md`
- safety_scope:
  - max_jobs: `6`
  - horizon: `h40`
  - stage: `protected_plan_window_failure_contrast_evidence_only`
  - source_stage_counts: `{'stage4': 2, 'stage5': 2, 'stage6': 2}`
  - stop_after_unique_failures: `4`
  - observation_only: `True`
  - resume_safe: `True`
  - skip_existing_outputs_by_default: `True`
  - invalid_existing_outputs_block_without_overwrite: `True`
  - execution_readiness_recomputed_live: `True`
  - approval_receipt_required: `True`
  - approval_receipt_path: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
  - approval_receipt_present: `False`
  - approval_receipt_valid: `False`
  - approval_receipt_blockers: `['approval_receipt_missing']`
  - approval_request_status: `protected_plan_window_failure_contrast_approval_request_ready`
  - approval_receipt_created_by_request: `False`
  - expected_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
  - expected_readiness_fingerprint: `9e3760e042b380429e8c2b1b7c533296cb98bb59fbf31b287e2bfdae30abdc0d`
  - per_job_timeout_seconds: `900`
  - processed_job_count: `0`
  - executed_job_count: `0`
  - output_valid_count: `0`
  - runtime_authorization_row_count: `0`
  - stage7_training_row_count: `0`
- does_not_allow:
  - runtime selector
  - runtime default changes
  - runtime DTM or tablebase lookup
  - gameplay-time topology mutation
  - unreviewed or unbounded label execution
  - selector training
  - Stage 7 promotion
  - Stage 8 training

## Recommendation

- if_no_user_approval: `wait_for_explicit_protected_plan_window_failure_contrast_collection_approval`
- if_runtime_approved: `implement_stage4_default_off_first_move_contrast_sandbox`
- if_collection_approved: `create_matching_approval_receipt_then_execute_bounded_protected_plan_window_failure_contrast_collection_from_reviewed_manifest`
- if_labels_approved: `not_applicable_stage7_success_gate_closed`
- reason: Stage 7 held-out clean controls now satisfy the benchmark gate; the remaining work is non-causal benchmark review/protected plan-window contrast analysis, while Stage 4 runtime work still requires explicit sandbox approval.
