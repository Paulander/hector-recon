# KRK Sequence-Policy Benchmark Review v0

Status: `sequence_policy_benchmark_review_blocked_pending_ready_inputs`

This review is non-causal. It does not train a sequence policy, implement a selector, change runtime behavior, promote Stage 7, or train Stage 8.

## Preflight

- benchmark_input_ready: `False`
- blockers: `['stage7_clean_success_controls_missing']`
- row_count: `79`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_heldout_row_count: `10`

## Objective Review

### stage4
- row_count: `48`
- state_count: `4`
- top1_conversion_positive_by_state: `0.75`
- top3_conversion_positive_by_state: `1.0`
- recall: `0.34615384615384615`
- negative_suppression: `0.8636363636363636`
- interpretation: `topk_signal_present_binary_rule_insufficient`

### protected_plan_window
- row_count: `21`
- target_label_counts: `{'conversion_failure': 2, 'conversion_positive': 19}`
- failure_evidence_sparse: `True`
- interpretation: `needs_more_failure_contrasts`

### stage7_heldout
- row_count: `10`
- target_label_counts: `{'conversion_failure': 8, 'conversion_positive': 2}`
- success_controls_met: `False`
- failure_controls_met: `True`
- interpretation: `success_controls_missing`

## Findings

- `stage4_topk_sequence_signal_present`
- `stage4_binary_rule_insufficient`
- `stage4_negative_suppression_reasonable`
- `protected_plan_window_failure_evidence_sparse`
- `stage7_success_controls_missing`

## Blockers

- `stage7_clean_success_controls_missing`

## Decision

- recommended_next_step: `fill_stage7_clean_success_controls_and_rerun_passive_gate_advancement`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
