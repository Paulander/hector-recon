# KRK Protected Plan-Window Failure Contrast Output Validation v0

Status: `protected_plan_window_failure_contrast_outputs_validation_pending`

This is a passive validation gate for already-created protected failure-contrast outputs. It does not execute collection, run labels, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.

## Summary

- job_count: `6`
- output_exists_count: `0`
- output_valid_count: `0`
- all_outputs_present: `False`
- all_present_outputs_valid: `True`
- all_outputs_valid: `False`
- parse_error_count: `0`
- h40_outcome_label_counts: `{}`
- unique_failure_candidate_count: `0`
- issue_counts: `{'output_missing': 6}`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- current_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'approve_protected_plan_window_failure_contrast_collection']`
- protected_failure_contrast_collection_option_available: `True`
- protected_failure_contrast_collection_command_available: `True`
- protected_failure_contrast_collection_option_id: `approve_protected_plan_window_failure_contrast_collection`
- protected_failure_contrast_collection_blocked_by_option_id: `None`

## Outputs

- `protected_plan_failure.01.planwin.a8dd289c75b7` exists=`False` valid=`False` issues=`['output_missing']`
- `protected_plan_failure.02.planwin.6ffab60fb0d0` exists=`False` valid=`False` issues=`['output_missing']`
- `protected_plan_failure.03.planwin.4f9789a608c4` exists=`False` valid=`False` issues=`['output_missing']`
- `protected_plan_failure.04.planwin.e09fb2b8a021` exists=`False` valid=`False` issues=`['output_missing']`
- `protected_plan_failure.05.planwin.23c0bb760d87` exists=`False` valid=`False` issues=`['output_missing']`
- `protected_plan_failure.06.planwin.d90d6f3d623a` exists=`False` valid=`False` issues=`['output_missing']`

## Decision

- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- collection_run_allowed: `false`
- label_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
