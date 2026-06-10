# KRK Sequence-Policy Underpowered Pilot v0

Status: `sequence_policy_pilot_blocked_pending_protected_failure_contrast_control_plane_gate_review`

This is a non-causal pilot review over underpowered inputs. It preserves diagnostic signal but does not relax the full benchmark gate, authorize labels, train a selector, change runtime behavior, promote Stage 7, or train Stage 8.

## Summary

- benchmark_executed_as_ready: `True`
- benchmark_status: `sequence_policy_benchmark_ready_non_causal_results_available`
- benchmark_preflight_blockers: `[]`
- benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered_blocked_pending_protected_failure_contrast_control_plane_gate_review`
- benchmark_review_blockers: `['protected_plan_window_failure_evidence_sparse']`
- readiness_checked_flag_count: `2912`
- readiness_boundary_violation_count: `0`
- readiness_source_artifact_count: `408`
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
- protected_failure_contrast_ready_for_explicit_approval: `False`
- protected_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- protected_stack_ready: `True`
- protected_stack_rollback_paths_preserved: `True`
- protected_stack_active_paths_safe: `True`
- protected_stack_active_paths_exist: `True`
- protected_stack_rollback_paths_safe: `True`
- protected_stack_rollback_paths_exist: `True`
- protected_stack_rollback_common_paths_distinct: `True`
- protected_stack_filesystem_snapshots_replaced: `False`
- protected_failure_contrast_integration_ready: `False`
- protected_failure_contrast_runner_status: `protected_plan_window_failure_contrast_runner_blocked`
- protected_failure_contrast_runner_manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- protected_failure_contrast_runner_manifest_declared_job_count: `6`
- protected_failure_contrast_runner_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- protected_failure_contrast_runner_collection_run_allowed: `False`
- protected_failure_contrast_runner_processed_job_count: `0`
- protected_failure_contrast_runner_executed_job_count: `0`
- protected_failure_contrast_command_if_explicitly_approved: `None`
- protected_failure_contrast_collection_option_available: `False`
- protected_failure_contrast_collection_command_available: `False`
- protected_failure_contrast_collection_option_id: `None`
- protected_failure_contrast_collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`
- protected_failure_contrast_approval_request_artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.json`
- protected_failure_contrast_approval_request_status: `protected_plan_window_failure_contrast_approval_request_blocked`
- protected_failure_contrast_approval_request_blockers: `['protected_failure_contrast_execution_scope_not_ready']`
- protected_failure_contrast_approval_request_ready_for_collection: `False`
- protected_failure_contrast_approval_receipt_created_by_request: `False`
- protected_failure_contrast_approval_receipt_present: `True`
- protected_failure_contrast_approval_receipt_valid: `False`
- protected_failure_contrast_approval_receipt_blockers: `['approval_receipt_readiness_fingerprint_mismatch', 'approval_receipt_readiness_status_mismatch', 'approval_receipt_current_control_plane_approval_option_ids_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_command_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_id_mismatch', 'approval_receipt_protected_failure_contrast_collection_blocked_by_option_id_mismatch']`
- protected_failure_contrast_post_success_refresh_required: `True`
- protected_failure_contrast_post_success_refresh_script: `scripts/advance_krk_suite_from_current_gates_v0.py`
- protected_failure_contrast_post_success_refresh_scope: `full_passive_krk_suite_gate_stack`
- protected_failure_contrast_runtime_behavior_changed: `False`
- protected_failure_contrast_runtime_defaults_changed: `False`
- protected_failure_contrast_runtime_selector_implemented: `False`
- protected_failure_contrast_runtime_score_changes: `False`
- protected_failure_contrast_runtime_direct_routing: `False`
- protected_failure_contrast_runtime_dtm_or_tablebase_lookup: `False`
- protected_failure_contrast_hidden_python_controller: `False`
- protected_failure_contrast_gameplay_topology_mutation: `False`
- protected_failure_contrast_selector_training_allowed: `False`
- protected_failure_contrast_stage7_promotion_allowed: `False`
- protected_failure_contrast_stage8_training_allowed: `False`
- sequence_policy_after_protected_failure_contrast_refresh_status: `sequence_policy_after_protected_failure_contrast_refresh_blocked_pending_protected_failure_contrast_control_plane_gate_review`
- sequence_policy_after_protected_failure_contrast_boundaries_preserved: `True`
- sequence_policy_after_protected_failure_contrast_boundary_violation_count: `0`
- sequence_policy_after_protected_failure_contrast_rows: `0`
- sequence_policy_after_protected_failure_contrast_stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_training_row_count: `0`

## Findings

- `stage4_state_local_topk_signal_present`
- `stage4_one_term_binary_rule_insufficient`

## Blockers

- `protected_plan_window_failure_contrast_underpowered_after_collection`

## Stage 4 Signal

- interpretation: `state_local_ranking_signal_present_but_one_term_binary_rule_insufficient`
- top1_conversion_positive_by_state: `0.75`
- top3_conversion_positive_by_state: `1.0`
- precision: `0.75`
- recall: `0.34615384615384615`
- negative_suppression: `0.8636363636363636`

## Decision

- recommended_next_step: `review_current_control_plane_gate_for_protected_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
