# KRK Sequence Policy After Protected Failure Contrast Refresh v0

Status: `sequence_policy_after_protected_failure_contrast_refresh_blocked_pending_protected_failure_contrast_control_plane_gate_review`

This passive refresh consumes integrated protected failure contrasts when available. It does not execute collection, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.

## Summary

- all_boundaries_preserved: `True`
- boundary_violation_count: `0`
- boundary_violations: `[]`
- integration_status: `protected_plan_window_failure_contrast_integration_underpowered_needs_more_valid_failures`
- integration_ready: `False`
- integrated_new_failure_count: `0`
- protected_failure_contrast_row_count: `0`
- sequence_policy_input_row_count: `118`
- sequence_policy_benchmark_status: `sequence_policy_benchmark_ready_non_causal_results_available`
- sequence_policy_benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered_blocked_pending_protected_failure_contrast_control_plane_gate_review`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- current_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`
- current_control_plane_approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'review_protected_plan_window_failure_contrast_manifest']`
- protected_failure_contrast_collection_option_available: `False`
- protected_failure_contrast_collection_command_available: `False`
- protected_failure_contrast_collection_option_id: `None`
- protected_failure_contrast_collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`

## Steps

- `sequence_policy_inputs` status=`sequence_policy_benchmark_inputs_ready_non_causal` labels=`False` runtime=`False`
- `sequence_policy_input_probe` status=`sequence_policy_input_probe_ready_for_full_non_causal_benchmark` labels=`False` runtime=`False`
- `sequence_policy_benchmark` status=`sequence_policy_benchmark_ready_non_causal_results_available` labels=`False` runtime=`False`
- `sequence_policy_benchmark_review` status=`sequence_policy_benchmark_mixed_plan_window_underpowered_blocked_pending_protected_failure_contrast_control_plane_gate_review` labels=`False` runtime=`False`

## Decision

- recommended_next_step: `review_current_control_plane_gate_for_protected_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
