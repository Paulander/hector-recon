# KRK Sequence-Policy Benchmark Inputs v0

Status: `sequence_policy_benchmark_inputs_ready_non_causal`

This artifact assembles currently available non-causal inputs for a future sequence-policy benchmark. It does not run labels, train a model, implement runtime behavior, promote Stage 7, or train Stage 8.

## Summary

- row_count: `118`
- input_group_counts: `{'stage4_first_move_contrast': 48, 'protected_plan_window': 20, 'stage7_clean_heldout_control': 50}`
- source_stage_counts: `{'stage4': 58, 'stage5': 6, 'stage6': 4, 'stage7': 50}`
- target_label_counts: `{'conversion_failure': 62, 'conversion_positive': 56}`
- protected_plan_window_evidence_met: `True`
- stage7_clean_success_controls: `11`
- stage7_clean_success_controls_required: `5`
- stage7_clean_success_controls_met: `True`
- stage7_clean_failure_controls: `39`
- stage7_clean_failure_controls_required: `5`
- stage7_clean_failure_controls_met: `True`
- stage7_diverse_outputs_present: `True`
- stage7_diverse_new_controls: `0`
- protected_failure_contrast_integration_status: `protected_plan_window_failure_contrast_integration_pending_outputs`
- protected_failure_contrast_integration_ready: `False`
- protected_failure_contrast_row_count: `0`
- protected_failure_contrast_skipped_counts: `{}`
- current_benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- current_benchmark_review_next_step: `explicitly_approve_protected_plan_window_failure_contrast_collection`
- current_benchmark_review_available: `True`
- stage7_heldout_row_count: `50`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- benchmark_input_ready: `True`

## Label Semantics

- stage4_forced_first_move_rows_are_capacity_contrast: `True`
- protected_plan_window_rows_are_replay_free_context: `True`
- stage7_rows_are_heldout_challenge_only: `True`
- capacity_labels_are_not_runtime_ownership_labels: `True`
- benchmark_inputs_do_not_authorize_runtime_or_training: `True`

## Decision

- recommended_next_step: `explicitly_approve_protected_plan_window_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
