# KRK Protected Plan-Window Failure Contrast Plan v0

Status: `protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval`

This is a non-causal collection plan only. It does not execute labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.

## Summary

- benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- benchmark_objective_row_count: `20`
- benchmark_failure_evidence_sparse: `True`
- input_row_count: `20`
- unique_row_count: `20`
- duplicate_row_count: `0`
- unique_success_count: `19`
- unique_failure_count: `1`
- minimum_required_unique_failures: `5`
- minimum_new_unique_failures_needed: `4`
- failure_source_stage_counts: `{'stage4': 1}`
- failure_source_family_counts: `{'wrong_tempo_plan_window': 1}`
- success_source_stage_counts: `{'stage4': 9, 'stage5': 6, 'stage6': 4}`
- success_source_family_counts: `{'wrong_tempo_plan_window': 9, 'fence_handoff_plan_window': 6, 'drive_to_edge_plan_window': 4}`
- protected_window_frame_count: `20`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_training_row_count: `0`
- forbidden_training_or_runtime_input_row_count: `0`
- forbidden_input_flag_counts: `{'runtime_behavior_changed': 0, 'runtime_defaults_changed': 0, 'runtime_selector_implemented': 0, 'runtime_score_changes': 0, 'runtime_direct_routing': 0, 'runtime_dtm_or_tablebase_lookup': 0, 'hidden_python_controller': 0, 'gameplay_topology_mutation': 0, 'runtime_changes_allowed': 0, 'label_run_allowed': 0, 'selector_allowed': 0, 'selector_training_allowed': 0, 'usable_for_selector_training': 0, 'usable_for_runtime_authorization': 0, 'stage7_heldout_challenge': 0, 'stage7_promotion_allowed': 0, 'stage8_training_allowed': 0}`

## Existing Failure Examples

- `seq_input.planwin.7302462fcb01` stage=`stage4` family=`wrong_tempo_plan_window` move=`b8h8` outcome=`max_plies` abort_terms=`['provider_selected_without_role_license', 'max_plies']`

## Collection Units

- `protected_plan_window_failure_contrast_minimum` purpose=Raise unique protected plan-window failure contrasts to the non-causal benchmark minimum.
- `cross_stage_failure_balance` purpose=Avoid a Stage 4-only failure slice by adding Stage 5/6 protected-window failures if available.

## Decision

- recommended_next_step: `review_protected_plan_window_failure_contrast_plan_before_explicit_collection_approval`
- approval_required_before_label_execution: `True`
- implementation_allowed_by_this_packet: `false`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
