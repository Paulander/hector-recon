# KRK Sequence-Policy Underpowered Pilot v0

Status: `sequence_policy_pilot_underpowered_pending_protected_failure_contrast_collection`

This is a non-causal pilot review over underpowered inputs. It preserves diagnostic signal but does not relax the full benchmark gate, authorize labels, train a selector, change runtime behavior, promote Stage 7, or train Stage 8.

## Summary

- benchmark_executed_as_ready: `True`
- benchmark_status: `sequence_policy_benchmark_ready_non_causal_results_available`
- benchmark_preflight_blockers: `[]`
- benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- benchmark_review_blockers: `['protected_plan_window_failure_evidence_sparse']`
- forbidden_training_or_runtime_input_blocked: `False`
- input_row_count: `118`
- stage4_topk_signal: `True`
- stage4_binary_rule_insufficient: `True`
- protected_plan_window_failure_evidence_sparse: `True`
- stage7_success_controls: `11`
- stage7_failure_controls: `39`
- stage7_success_gap: `0`
- stage7_replay_free_backfill_exhausted: `False`
- stage7_backfillable_success_controls: `0`
- protected_failure_contrast_ready_for_explicit_approval: `True`
- protected_failure_contrast_integration_ready: `False`
- protected_failure_contrast_runner_status: `protected_plan_window_failure_contrast_runner_dry_run_ready`
- protected_failure_contrast_runner_processed_job_count: `0`
- protected_failure_contrast_runner_executed_job_count: `0`
- protected_failure_contrast_command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py --execute-reviewed-collection --refresh-after-run --approval-receipt reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- protected_failure_contrast_approval_request_artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.json`
- protected_failure_contrast_approval_request_status: `protected_plan_window_failure_contrast_approval_request_ready`
- protected_failure_contrast_approval_receipt_created_by_request: `False`
- protected_failure_contrast_approval_receipt_blockers: `['approval_receipt_missing']`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_training_row_count: `0`

## Findings

- `stage4_state_local_topk_signal_present`
- `stage4_one_term_binary_rule_insufficient`

## Blockers

- `protected_plan_window_failure_contrast_collection_pending_explicit_approval`

## Stage 4 Signal

- interpretation: `state_local_ranking_signal_present_but_one_term_binary_rule_insufficient`
- top1_conversion_positive_by_state: `0.75`
- top3_conversion_positive_by_state: `1.0`
- precision: `0.75`
- recall: `0.34615384615384615`
- negative_suppression: `0.8636363636363636`

## Decision

- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
