# KRK Protected Plan-Window Failure Contrast Integration v0

Status: `protected_plan_window_failure_contrast_integration_pending_outputs`

This is a passive integration gate for already-validated protected failure-contrast outputs. It does not execute collection, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.

## Summary

- validation_status: `protected_plan_window_failure_contrast_outputs_validation_pending`
- manifest_job_count: `6`
- output_exists_count: `0`
- output_valid_count: `0`
- validated_unique_failure_candidate_count: `0`
- existing_unique_failure_count: `1`
- minimum_required_unique_failures: `5`
- minimum_new_unique_failures_needed: `4`
- integrated_new_failure_count: `0`
- projected_unique_failure_count: `1`
- integration_ready: `False`
- source_stage_counts: `{}`
- source_family_counts: `{}`
- skipped_counts: `{'invalid_or_missing_output': 6}`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Integrated Failure Contrasts

- none

## Decision

- recommended_next_step: `explicitly_approve_protected_plan_window_failure_contrast_collection`
- collection_run_allowed: `false`
- label_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
