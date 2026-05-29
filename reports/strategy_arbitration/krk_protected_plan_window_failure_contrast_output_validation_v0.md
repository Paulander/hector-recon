# KRK Protected Plan-Window Failure Contrast Output Validation v0

Status: `protected_plan_window_failure_contrast_outputs_valid_ready_for_integration`

This is a passive validation gate for already-created protected failure-contrast outputs. It does not execute collection, run labels, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.

## Summary

- job_count: `6`
- output_exists_count: `6`
- output_valid_count: `6`
- all_outputs_present: `True`
- all_present_outputs_valid: `True`
- all_outputs_valid: `True`
- parse_error_count: `0`
- h40_outcome_label_counts: `{'conversion_positive': 6}`
- unique_failure_candidate_count: `0`
- issue_counts: `{}`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- current_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'review_protected_plan_window_failure_contrast_manifest']`
- protected_failure_contrast_collection_option_available: `False`
- protected_failure_contrast_collection_command_available: `False`
- protected_failure_contrast_collection_option_id: `None`
- protected_failure_contrast_collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`

## Outputs

- `protected_plan_failure.01.planwin.a8dd289c75b7` exists=`True` valid=`True` issues=`[]`
- `protected_plan_failure.02.planwin.6ffab60fb0d0` exists=`True` valid=`True` issues=`[]`
- `protected_plan_failure.03.planwin.4f9789a608c4` exists=`True` valid=`True` issues=`[]`
- `protected_plan_failure.04.planwin.e09fb2b8a021` exists=`True` valid=`True` issues=`[]`
- `protected_plan_failure.05.planwin.23c0bb760d87` exists=`True` valid=`True` issues=`[]`
- `protected_plan_failure.06.planwin.d90d6f3d623a` exists=`True` valid=`True` issues=`[]`

## Decision

- recommended_next_step: `integrate_protected_plan_window_failure_contrasts_passively`
- collection_run_allowed: `false`
- label_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
