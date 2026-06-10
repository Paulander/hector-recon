# KRK Protected Plan-Window Failure Contrast Collection Result v0

Status: `collection_complete_underpowered`

The approved bounded observation collection produced valid outputs, but no new protected plan-window failure contrasts. Runtime behavior, routing, scoring, selector training, Stage 7 promotion, and Stage 8 training remain blocked.

## Summary

- approved_collection_scope: `approve_protected_plan_window_failure_contrast_collection`
- approval_status: `approved_for_single_bounded_observation_collection`
- single_execution_only: `True`
- manifest_job_count: `6`
- collection_output_count: `6`
- output_valid_count: `6`
- h40_outcome_label_counts: `{'conversion_positive': 6}`
- conversion_failure_count: `0`
- conversion_positive_count: `6`
- integrated_new_failure_count: `0`
- validated_unique_failure_candidate_count: `0`
- existing_unique_failure_count: `1`
- minimum_required_unique_failures: `5`
- minimum_new_unique_failures_needed: `4`
- integration_ready: `False`
- sequence_policy_replay_free_recovery_row_count: `0`
- sequence_policy_boundaries_preserved: `True`
- sequence_policy_boundary_violation_count: `0`
- benchmark_protected_plan_window_row_count: `20`
- benchmark_protected_plan_window_target_label_counts: `{'conversion_failure': 1, 'conversion_positive': 19}`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- runtime_behavior_unchanged: `True`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- output_load_issue_counts: `{}`
- output_forbidden_issue_counts: `{}`
- non_causal_feature_probe_possible: `False`
- runtime_review_packet_possible: `False`
- next_step_requires_new_explicit_approval: `True`

## Decision

- recommended_next_step: `review_followup_packet_before_any_additional_protected_plan_window_collection`
- collection_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
