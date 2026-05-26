# KRK Full Suite Readiness Audit v0

## Decision

- status: `krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection`
- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- stage7_promotion_allowed: `false`
- stage8_training_allowed: `false`

## Protected Stack

- active status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- clean_stack_adopted: `True`
- filesystem_snapshots_replaced: `False`
- clean_stack_adopted_and_validated: `True`
- post_adoption_validation_required: `True`
- rollback_paths_preserved: `True`
- active_stack_paths_safe: `True`
- active_stack_paths_exist: `True`
- rollback_stack_paths_safe: `True`
- rollback_stack_paths_exist: `True`
- rollback_common_paths_distinct: `True`
- stage5_conversion_preservation_passed: `True`
- stage6_drive_validation_passed: `True`
- m1_m4_preservation_passed: `True`
- kpk_kqk_bridge_preservation_passed: `True`

## Stage Status

- `stage1`: `protected_component_from_current_brief`
- `stage4`: `stage4_caveat_unblocker_ready_pending_explicit_runtime_approval`
  - approval_request_artifact: `reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json`
  - approval_request_status: `stage4_first_move_contrast_sandbox_approval_request_ready`
  - approval_request_created: `False`
- `stage5`: `protected_retry1_stack_validated`
- `stage6`: `protected_retry1_overlay_validated`
- `stage7`: `held_out_challenge_quarantined`
- `stage8`: `blocked`

## Stage 7 Sampling Gate

- runner_status: `stage7_diverse_clean_sampling_runner_executed_success`
- runner_dry_run: `False`
- runner_job_count: `8`
- processed_job_count: `0`
- executed_job_count: `0`
- skipped_existing_output_count: `0`
- overwrite_existing_outputs: `False`
- output_validation_status: `stage7_diverse_clean_sampling_outputs_valid_ready_for_integration`
- execution_readiness_source: `live_recomputed`
- execution_readiness_status: `not_applicable_stage7_success_gate_closed`
- execution_readiness_jobs_passing: `8`
- invalid_existing_output_count: `0`
- job_timeout_seconds: `900`
- timed_out_job_count: `0`
- integration_status: `stage7_diverse_clean_sampling_integration_success_controls_met`
- outputs_present_count: `8`
- combined_success_controls: `11`
- success_controls_required: `5`
- success_controls_ready: `True`

## Sequence Policy

- pipeline_status: `sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review`
- benchmark_status: `sequence_policy_benchmark_ready_non_causal_results_available`
- benchmark_design_status: `sequence_policy_benchmark_design_ready_non_causal`
- benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- post_failure_contrast_refresh_status: `sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs`
- post_failure_contrast_refresh_boundaries_preserved: `True`
- post_failure_contrast_refresh_boundary_violation_count: `0`
- post_failure_contrast_refresh_row_count: `0`
- post_failure_contrast_refresh_stage7_training_row_count: `0`
- passive_design_without_new_labels_status: `non_causal_sequence_policy_design_without_new_labels_ready`
- passive_design_current_evidence_limit: `protected_plan_window_failure_evidence_sparse`
- passive_design_depends_on_new_label_execution: `False`
- passive_design_depends_on_protected_failure_contrast_collection: `False`
- cross_stage_requirements_status: `cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark`
- replay_free_protected_cross_stage_evidence: `True`
- cross_stage_sequence_evidence_met: `True`
- input_row_count: `118`
- inputs_ready: `True`
- benchmark_ready: `True`
- selector_training_row_count: `0`

## Protected Failure Contrast Gate

- plan_status: `protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval`
- unique_failure_count: `1`
- minimum_new_failures_needed: `4`
- manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- manifest_job_count: `6`
- manifest_review_status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval`
- execution_readiness_status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- execution_jobs_passing: `6`
- runner_status: `protected_plan_window_failure_contrast_runner_dry_run_ready`
- runner_manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- runner_manifest_declared_job_count: `6`
- runner_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- runner_collection_run_allowed: `False`
- runner_processed_job_count: `0`
- runner_executed_job_count: `0`
- output_validation_status: `protected_plan_window_failure_contrast_outputs_validation_pending`
- output_exists_count: `0`
- output_valid_count: `0`
- integration_status: `protected_plan_window_failure_contrast_integration_pending_outputs`
- integrated_new_failure_count: `0`
- integration_ready: `False`
- ready_for_explicit_approval: `True`
- current_artifact_allows_collection: `False`
- approval_receipt_required: `True`
- approval_receipt_path: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- approval_receipt_present: `False`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_missing']`
- approval_request_artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.json`
- approval_request_status: `protected_plan_window_failure_contrast_approval_request_ready`
- approval_receipt_created_by_request: `False`
- post_success_refresh_required: `True`
- post_success_refresh_script: `scripts/advance_krk_suite_from_current_gates_v0.py`
- post_success_refresh_scope: `full_passive_krk_suite_gate_stack`
- expected_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- expected_readiness_fingerprint: `3d8481218b7f46804e054090e7bd83b4a8a39d341a3290a537068a0a7b586987`
- command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py --execute-reviewed-collection --refresh-after-run --approval-receipt reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_selector_implemented: `False`
- runtime_score_changes: `False`
- runtime_direct_routing: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- gameplay_topology_mutation: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Blockers

- `protected_plan_window_failure_contrast_collection_pending_explicit_approval`

## Approval Gates

- `stage7_diverse_clean_label_execution`: The Stage 7 clean success-control gate is already closed; additional Stage 7 labels are not the primary current unblocker.
- `protected_plan_window_failure_contrast_collection`: The sequence-policy benchmark is mixed/underpowered on protected plan-window failures; bounded observation-only collection is the current explicit gate.
- `stage4_first_move_contrast_sandbox`: Stage 4 has a reviewed default-off first-move contrast sandbox scope, but implementation still requires explicit sandbox approval.
- `stage8_training`: Protected plan-window failure-contrast evidence is not integrated; Stage 8 training remains blocked even though Stage 7 held-out controls are balanced.

## Boundary Check

- checked_flag_count: `430`
- violation_count: `0`
