# KRK Protected Plan-Window Failure Contrast Approval Request v0

Status: `protected_plan_window_failure_contrast_approval_request_ready`

This is a passive request packet only. It does not create the approval receipt, execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.

## Summary

- request_ready: `True`
- request_blockers: `[]`
- job_count: `6`
- manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- readiness_status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- readiness_checked_flag_count: `507`
- readiness_boundary_violation_count: `0`
- readiness_source_artifact_count: `55`
- runner_status: `protected_plan_window_failure_contrast_runner_dry_run_ready`
- runner_execution_requested: `False`
- runner_processed_job_count: `0`
- runner_executed_job_count: `0`
- runner_max_jobs_option: `None`
- runner_job_timeout_seconds: `900`
- runner_overwrite_existing_outputs: `False`
- runner_refresh_after_run_requested: `True`
- post_success_refresh_required: `True`
- post_success_refresh_script: `scripts/advance_krk_suite_from_current_gates_v0.py`
- post_success_refresh_scope: `full_passive_krk_suite_gate_stack`
- pre_collection_sequence_policy_after_protected_failure_contrast_refresh_status: `sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs`
- pre_collection_sequence_policy_after_protected_failure_contrast_boundaries_preserved: `True`
- pre_collection_sequence_policy_after_protected_failure_contrast_boundary_violation_count: `0`
- pre_collection_sequence_policy_after_protected_failure_contrast_rows: `0`
- pre_collection_sequence_policy_after_protected_failure_contrast_stage7_training_row_count: `0`
- manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- readiness_fingerprint: `14d8cecf5201a4f378aa8a602897cdd338ff66caea550ac26377eef9cdb11886`
- protected_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- protected_stack_ready: `True`
- protected_stack_rollback_paths_preserved: `True`
- protected_stack_filesystem_snapshots_replaced: `False`
- current_control_plane_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'approve_protected_plan_window_failure_contrast_collection']`
- protected_failure_contrast_collection_option_available: `True`
- protected_failure_contrast_collection_command_available: `True`
- protected_failure_contrast_collection_option_id: `approve_protected_plan_window_failure_contrast_collection`
- protected_failure_contrast_collection_blocked_by_option_id: `None`
- approval_receipt_required: `True`
- approval_receipt_missing: `True`

## Protected Stack Safety

- status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- ready: `True`
- rollback_paths_preserved: `True`
- active_paths_safe: `True`
- active_paths_exist: `True`
- rollback_paths_safe: `True`
- rollback_paths_exist: `True`
- rollback_common_paths_distinct: `True`
- filesystem_snapshots_replaced: `False`
- hard_blockers: `[]`

## Approval Receipt Status

- approval_receipt_path: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- approval_receipt_present: `False`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_missing']`
- approval_receipt_created: `False`

## Required Receipt If Explicitly Approved

```json
{
  "approval_id": "approve_protected_plan_window_failure_contrast_collection",
  "approval_scope": {
    "current_control_plane_approval_option_ids": [
      "approve_stage4_first_move_contrast_sandbox",
      "approve_protected_plan_window_failure_contrast_collection"
    ],
    "current_control_plane_gate_status": "krk_control_plane_waiting_on_explicit_gate_choice",
    "job_count": 6,
    "job_timeout_seconds": 900,
    "manifest_fingerprint": "5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038",
    "manifest_status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
    "max_jobs": null,
    "overwrite_existing_outputs": false,
    "post_success_refresh_required": true,
    "post_success_refresh_scope": "full_passive_krk_suite_gate_stack",
    "post_success_refresh_script": "scripts/advance_krk_suite_from_current_gates_v0.py",
    "protected_failure_contrast_collection_blocked_by_option_id": null,
    "protected_failure_contrast_collection_command_available": true,
    "protected_failure_contrast_collection_option_available": true,
    "protected_failure_contrast_collection_option_id": "approve_protected_plan_window_failure_contrast_collection",
    "protected_stack_active_paths_exist": true,
    "protected_stack_active_paths_safe": true,
    "protected_stack_filesystem_snapshots_replaced": false,
    "protected_stack_hard_blockers": [],
    "protected_stack_ready": true,
    "protected_stack_rollback_common_paths_distinct": true,
    "protected_stack_rollback_paths_exist": true,
    "protected_stack_rollback_paths_preserved": true,
    "protected_stack_rollback_paths_safe": true,
    "protected_stack_status": "retry1_protected_stage5_6_stack_adopted_manifest_only",
    "readiness_boundary_violation_count": 0,
    "readiness_checked_flag_count": 507,
    "readiness_fingerprint": "14d8cecf5201a4f378aa8a602897cdd338ff66caea550ac26377eef9cdb11886",
    "readiness_source_artifact_count": 55,
    "readiness_status": "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval",
    "refresh_after_run": true
  },
  "decision": {
    "gameplay_topology_mutation": false,
    "hidden_python_controller": false,
    "label_run_allowed": false,
    "runtime_behavior_changed": false,
    "runtime_changes_allowed": false,
    "runtime_defaults_changed": false,
    "runtime_direct_routing": false,
    "runtime_dtm_or_tablebase_lookup": false,
    "runtime_score_changes": false,
    "runtime_selector_implemented": false,
    "selector_allowed": false,
    "selector_training_allowed": false,
    "single_execution_only": true,
    "stage7_promotion_allowed": false,
    "stage8_training_allowed": false,
    "status": "approved_for_single_bounded_observation_collection"
  },
  "receipt_path": "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json",
  "schema_version": "krk_protected_plan_window_failure_contrast_collection_approval.v0"
}
```

## Decision

- recommended_next_step: `user_may_create_matching_approval_receipt_only_if_collection_is_explicitly_approved`
- collection_run_allowed: `False`
- label_run_allowed: `False`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
