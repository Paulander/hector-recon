# KRK Sequence-Policy Benchmark v0

Status: `sequence_policy_benchmark_blocked_pending_stage7_success_controls`

This is a non-causal benchmark harness. It does not train a model, select moves, change runtime behavior, promote Stage 7, or train Stage 8.

## Preflight

- benchmark_input_ready: `False`
- blockers: `['stage7_clean_success_controls_missing']`
- row_count: `79`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_heldout_row_count: `10`

## Objectives

- `stage4_state_local_first_move_contrast` rows=`48` runtime_ready=`False`
- `protected_plan_window_entry_progress_exit_abort` rows=`21` runtime_ready=`False`
- `stage7_heldout_sequence_success_vs_hard_negative` rows=`10` runtime_ready=`False`

## Decision

- benchmark_executed_as_ready: `False`
- recommended_next_step: `fill_stage7_clean_success_controls_before_treating_benchmark_as_ready`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
