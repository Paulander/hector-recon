# KRK Sequence-Policy Benchmark Inputs v0

Status: `sequence_policy_benchmark_inputs_blocked_pending_stage7_success_controls`

This artifact assembles currently available non-causal inputs for a future sequence-policy benchmark. It does not run labels, train a model, implement runtime behavior, promote Stage 7, or train Stage 8.

## Summary

- row_count: `79`
- input_group_counts: `{'stage4_first_move_contrast': 48, 'protected_plan_window': 21, 'stage7_clean_heldout_control': 10}`
- source_stage_counts: `{'stage4': 59, 'stage5': 6, 'stage6': 4, 'stage7': 10}`
- target_label_counts: `{'conversion_failure': 32, 'conversion_positive': 47}`
- protected_plan_window_evidence_met: `True`
- stage7_clean_success_controls: `2`
- stage7_clean_success_controls_required: `5`
- stage7_clean_success_controls_met: `False`
- stage7_clean_failure_controls: `8`
- stage7_clean_failure_controls_required: `5`
- stage7_clean_failure_controls_met: `True`
- stage7_heldout_row_count: `10`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- benchmark_input_ready: `False`

## Label Semantics

- stage4_forced_first_move_rows_are_capacity_contrast: `True`
- protected_plan_window_rows_are_replay_free_context: `True`
- stage7_rows_are_heldout_challenge_only: `True`
- capacity_labels_are_not_runtime_ownership_labels: `True`
- benchmark_inputs_do_not_authorize_runtime_or_training: `True`

## Decision

- recommended_next_step: `approve_stage7_diverse_clean_label_run_to_fill_success_controls`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
