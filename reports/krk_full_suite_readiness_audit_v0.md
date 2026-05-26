# KRK Full Suite Readiness Audit v0

## Decision

- status: `krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection`
- recommended_next_step: `explicitly_approve_protected_plan_window_failure_contrast_collection`
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
- benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
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
- command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py --execute-reviewed-collection --refresh-after-run`

## Blockers

- `protected_plan_window_failure_contrast_collection_pending_explicit_approval`

## Approval Gates

- `stage7_diverse_clean_label_execution`: The Stage 7 clean success-control gate is already closed; additional Stage 7 labels are not the primary current unblocker.
- `protected_plan_window_failure_contrast_collection`: The sequence-policy benchmark is mixed/underpowered on protected plan-window failures; bounded observation-only collection is the current explicit gate.
- `stage4_first_move_contrast_sandbox`: Stage 4 has a reviewed default-off first-move contrast sandbox scope, but implementation still requires explicit sandbox approval.
- `stage8_training`: Protected plan-window failure-contrast evidence is not integrated; Stage 8 training remains blocked even though Stage 7 held-out controls are balanced.

## Boundary Check

- checked_flag_count: `155`
- violation_count: `0`
