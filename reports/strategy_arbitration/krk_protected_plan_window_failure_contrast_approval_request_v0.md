# KRK Protected Plan-Window Failure Contrast Approval Request v0

Status: `protected_plan_window_failure_contrast_approval_request_ready`

This is a passive request packet only. It does not create the approval receipt, execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.

## Summary

- job_count: `6`
- manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- readiness_status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- runner_status: `protected_plan_window_failure_contrast_runner_dry_run_ready`
- runner_execution_requested: `False`
- runner_processed_job_count: `0`
- runner_executed_job_count: `0`
- manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- readiness_fingerprint: `9e3760e042b380429e8c2b1b7c533296cb98bb59fbf31b287e2bfdae30abdc0d`
- protected_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- protected_stack_ready: `True`
- protected_stack_rollback_paths_preserved: `True`
- protected_stack_filesystem_snapshots_replaced: `False`
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
    "job_count": 6,
    "manifest_fingerprint": "5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038",
    "manifest_status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
    "readiness_fingerprint": "9e3760e042b380429e8c2b1b7c533296cb98bb59fbf31b287e2bfdae30abdc0d",
    "readiness_status": "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
  },
  "decision": {
    "label_run_allowed": false,
    "runtime_changes_allowed": false,
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
