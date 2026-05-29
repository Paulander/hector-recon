# KRK Full Suite Unblocker Packet v0

## Decision

- status: `krk_suite_protected_failure_contrast_unblocker_ready_pending_explicit_collection_approval`
- recommended_next_step: `review_current_control_plane_gate_for_protected_failure_contrast_collection`
- implementation_allowed_by_this_packet: `False`
- label_run_allowed: `False`
- runtime_changes_allowed: `False`

## Current State

- readiness_checked_flag_count: `2912`
- readiness_boundary_violation_count: `0`
- readiness_source_artifact_count: `408`
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
- sequence_policy_benchmark_design_status: `sequence_policy_benchmark_design_ready_non_causal`
- sequence_policy_passive_design_without_new_labels_status: `non_causal_sequence_policy_design_review_needed`
- sequence_policy_passive_design_current_evidence_limit: `None`
- sequence_policy_cross_stage_requirements_status: `cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark`
- sequence_policy_replay_free_protected_cross_stage_evidence: `True`
- sequence_policy_cross_stage_sequence_evidence_met: `True`
- current_control_plane_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'review_protected_plan_window_failure_contrast_manifest']`
- protected_plan_window_failure_contrast_collection_option_available: `False`
- protected_plan_window_failure_contrast_collection_command_available: `False`
- protected_plan_window_failure_contrast_collection_option_id: `None`
- protected_plan_window_failure_contrast_collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`
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
- protected_plan_window_failure_contrast_manifest_review_status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_control_plane_gate_review`
- protected_plan_window_failure_contrast_execution_readiness_status: `protected_plan_window_failure_contrast_execution_readiness_blocked_pending_control_plane_gate_review`
- protected_plan_window_failure_contrast_execution_jobs_passing: `6`
- protected_plan_window_failure_contrast_runner_status: `protected_plan_window_failure_contrast_runner_blocked`
- protected_plan_window_failure_contrast_runner_manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- protected_plan_window_failure_contrast_runner_manifest_declared_job_count: `6`
- protected_plan_window_failure_contrast_runner_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- protected_plan_window_failure_contrast_runner_collection_run_allowed: `False`
- protected_plan_window_failure_contrast_runner_processed_job_count: `0`
- protected_plan_window_failure_contrast_runner_executed_job_count: `0`
- protected_plan_window_failure_contrast_approval_request_status: `protected_plan_window_failure_contrast_approval_request_blocked`
- protected_plan_window_failure_contrast_approval_request_blockers: `['protected_failure_contrast_execution_scope_not_ready']`
- protected_plan_window_failure_contrast_approval_receipt_created: `False`
- protected_plan_window_failure_contrast_approval_receipt_blockers: `['approval_receipt_readiness_fingerprint_mismatch', 'approval_receipt_readiness_status_mismatch', 'approval_receipt_current_control_plane_approval_option_ids_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_command_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_id_mismatch', 'approval_receipt_protected_failure_contrast_collection_blocked_by_option_id_mismatch']`
- protected_plan_window_failure_contrast_output_validation_status: `protected_plan_window_failure_contrast_outputs_valid_ready_for_integration`
- protected_plan_window_failure_contrast_output_exists_count: `6`
- protected_plan_window_failure_contrast_output_valid_count: `6`
- protected_plan_window_failure_contrast_integration_status: `protected_plan_window_failure_contrast_integration_underpowered_needs_more_valid_failures`
- protected_plan_window_failure_contrast_integrated_new_failure_count: `0`
- protected_plan_window_failure_contrast_integration_ready: `False`
- sequence_policy_after_protected_failure_contrast_refresh_status: `sequence_policy_after_protected_failure_contrast_refresh_blocked_pending_protected_failure_contrast_control_plane_gate_review`
- sequence_policy_after_protected_failure_contrast_rows: `0`
- sequence_policy_after_protected_failure_contrast_boundaries_preserved: `True`
- sequence_policy_after_protected_failure_contrast_boundary_violation_count: `0`
- sequence_policy_after_protected_failure_contrast_stage7_training_row_count: `0`
- sequence_policy_after_protected_failure_contrast_selector_training_row_count: `0`
- sequence_policy_after_protected_failure_contrast_runtime_authorization_row_count: `0`

## Why Work Stops At This Gate

- The Stage 7 held-out clean label gate is closed; the remaining non-causal benchmark review identifies protected plan-window failure-contrast sparsity.
- Runtime changes, Stage 7 promotion, and Stage 8 training remain gated by repository reports and architecture policy.
- The current /goal does not by itself authorize runtime behavior, Stage 7 promotion, or Stage 8 training.

## Primary Unblocker

- id: `protected_plan_window_failure_contrast_collection`
- status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_control_plane_gate_review`
- purpose: Review the bounded protected plan-window failure-contrast manifest before any explicitly approved collection run.
- command_if_explicitly_approved: `None`
- max_jobs: `6`
- manifest_job_count: `6`
- runner_max_jobs_option: `None`
- horizon: `h40`
- stage: `protected_plan_window_failure_contrast_evidence_only`
- protected_stack_readiness_required: `True`
- protected_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- protected_stack_ready: `True`
- protected_stack_rollback_paths_preserved: `True`
- protected_stack_active_paths_safe: `True`
- protected_stack_active_paths_exist: `True`
- protected_stack_rollback_paths_safe: `True`
- protected_stack_rollback_paths_exist: `True`
- protected_stack_rollback_common_paths_distinct: `True`
- protected_stack_filesystem_snapshots_replaced: `False`
- source_stage_counts: `{'stage4': 2, 'stage5': 2, 'stage6': 2}`
- stop_after_unique_failures: `4`
- observation_only: `True`
- resume_safe: `True`
- skip_existing_outputs_by_default: `True`
- invalid_existing_outputs_block_without_overwrite: `True`
- execution_readiness_recomputed_live: `True`
- per_job_timeout_seconds: `900`
- refresh_after_run: `True`
- approval_receipt_required: `True`
- approval_receipt_path: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- approval_receipt_present: `True`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_readiness_fingerprint_mismatch', 'approval_receipt_readiness_status_mismatch', 'approval_receipt_current_control_plane_approval_option_ids_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_command_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_id_mismatch', 'approval_receipt_protected_failure_contrast_collection_blocked_by_option_id_mismatch']`
- approval_request_artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.json`
- approval_request_status: `protected_plan_window_failure_contrast_approval_request_blocked`
- approval_request_blockers: `['protected_failure_contrast_execution_scope_not_ready']`
- approval_request_ready_for_collection: `False`
- collection_option_available: `False`
- collection_command_available: `False`
- collection_option_id: `None`
- collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`
- approval_receipt_created_by_request: `False`
- expected_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- expected_readiness_fingerprint: `0a9fe46170cb062d4a12db0b4ddf3bb9348142c9e2f575ee946afc30960acfbe`
- timed_out_job_count: `0`
- post_success_refresh: `full_passive_krk_suite_gate_stack`
- runtime_behavior_changed: `False`
- runtime_direct_routing: `False`
- hidden_python_controller: `False`
- stage7_training_rows: `0`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- approval_required: `True`
- implementation_allowed_by_this_packet: `False`

## Secondary Unblocker

- id: `stage4_first_move_contrast_sandbox`
- status: `stage4_caveat_unblocker_ready_pending_explicit_runtime_approval`
- purpose: Address the separate Stage 4 h40 caveat through a reviewed default-off sandbox path.
- approval_request_artifact: `reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md`
- approval_request_status: `stage4_first_move_contrast_sandbox_approval_request_ready`
- approval_request_ready_for_runtime_approval: `True`
- approval_request_created: `False`
- implementation_authorized_by_approval_request: `False`
- sandbox_scope_id: `default_off_stage4_candidate_move_first_move_contrast_sandbox_only`
- default_off: `True`
- default_enabled: `False`
- runtime_change_class: `default_off_candidate_move_frame_sandbox_only`
- exact_state_or_exact_move_exception: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- selector_training_allowed: `False`
- provider_suppression_allowed: `False`
- broad_stage0_penalty_allowed: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- why_secondary: This may reduce Stage 4 debt, but it does not directly fill the protected plan-window failure-contrast sparsity now blocking sequence-policy review.

## Low-Value Safe Work Remaining

- Rerunning Stage 7 label commands without overwrite will skip existing outputs; the Stage 7 success-control gap is already closed.
- Passive benchmark and cross-stage design summaries are current; the next useful gate-moving work is explicit protected plan-window failure-contrast collection approval, or separately explicit Stage 4 runtime-sandbox approval.
