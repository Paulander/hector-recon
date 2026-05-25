# KRK Sequence-Policy Underpowered Pilot v0

Status: `sequence_policy_pilot_ready_for_full_benchmark_after_label_gate`

This is a non-causal pilot review over underpowered inputs. It preserves diagnostic signal but does not relax the full benchmark gate, authorize labels, train a selector, change runtime behavior, promote Stage 7, or train Stage 8.

## Summary

- benchmark_executed_as_ready: `False`
- input_row_count: `79`
- stage4_topk_signal: `True`
- stage4_binary_rule_insufficient: `True`
- protected_plan_window_failure_evidence_sparse: `True`
- stage7_success_controls: `2`
- stage7_failure_controls: `8`
- stage7_success_gap: `3`
- stage7_replay_free_backfill_exhausted: `True`
- stage7_backfillable_success_controls: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_training_row_count: `0`

## Findings

- `stage4_state_local_topk_signal_present`
- `stage4_one_term_binary_rule_insufficient`

## Blockers

- `protected_plan_window_failure_evidence_sparse`
- `stage7_clean_success_controls_missing`
- `stage7_replay_free_backfill_exhausted`

## Stage 4 Signal

- interpretation: `state_local_ranking_signal_present_but_one_term_binary_rule_insufficient`
- top1_conversion_positive_by_state: `0.75`
- top3_conversion_positive_by_state: `1.0`
- precision: `0.75`
- recall: `0.34615384615384615`
- negative_suppression: `0.8636363636363636`

## Decision

- recommended_next_step: `explicitly_approve_stage7_diverse_clean_label_execution_before_full_sequence_policy_benchmark`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
