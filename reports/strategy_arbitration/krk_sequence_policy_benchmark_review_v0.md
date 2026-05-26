# KRK Sequence-Policy Benchmark Review v0

Status: `sequence_policy_benchmark_mixed_plan_window_underpowered`

This review is non-causal. It does not train a sequence policy, implement a selector, change runtime behavior, promote Stage 7, or train Stage 8.

## Preflight

- benchmark_input_ready: `True`
- blockers: `[]`
- row_count: `118`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_heldout_row_count: `50`

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
- row_count: `20`
- target_label_counts: `{'conversion_failure': 1, 'conversion_positive': 19}`
- failure_evidence_sparse: `True`
- interpretation: `needs_more_failure_contrasts`

### stage7_heldout
- row_count: `50`
- target_label_counts: `{'conversion_failure': 39, 'conversion_positive': 11}`
- success_controls_met: `True`
- failure_controls_met: `True`
- interpretation: `balanced_heldout_controls`

## Findings

- `stage4_topk_sequence_signal_present`
- `stage4_binary_rule_insufficient`
- `stage4_negative_suppression_reasonable`
- `protected_plan_window_failure_evidence_sparse`
- `stage7_heldout_controls_balanced`

## Blockers

- `protected_plan_window_failure_evidence_sparse`

## Decision

- recommended_next_step: `explicitly_approve_protected_plan_window_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
