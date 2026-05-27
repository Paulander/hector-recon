# KRK Full Suite Readiness Audit v0

## Decision

- status: `krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection`
- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- stage7_promotion_allowed: `false`
- stage8_training_allowed: `false`

## Protected Stack

- active status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- clean_stack_adopted: `True`
- filesystem_snapshots_replaced: `False`
- clean_stack_adopted_and_validated: `True`
- post_adoption_validation_required: `True`
- rollback_paths_preserved: `True`
- active_stack_paths_safe: `True`
- active_stack_paths_exist: `True`
- rollback_stack_paths_safe: `True`
- rollback_stack_paths_exist: `True`
- rollback_common_paths_distinct: `True`
- stage5_conversion_preservation_passed: `True`
- stage6_drive_validation_passed: `True`
- m1_m4_preservation_passed: `True`
- kpk_kqk_bridge_preservation_passed: `True`

## Clean Curriculum Run Lineage

- passive_lineage_ready: `True`
- checkpoint_plan_status: `clean_curriculum_checkpoint_plan_ready_full_run_requires_review`
- execution_manifest_status: `clean_retrain_execution_manifest_ready_not_run`
- execution_manifest_full_run_authorized: `False`
- stage6_compose_manifest_status: `stage6_overlay_compose_manifest_ready_not_run`
- stage6_compose_manifest_run_authorized: `False`
- preflight_status: `clean_retrain_preflight_ready_for_run_review`
- preflight_blocker_count: `0`
- smoke_result_status: `clean_retrain_smoke_plumbing_passed_semantic_smoke_too_tiny`
- smoke_command_plumbing_validated: `True`
- smoke_curriculum_semantics_validated: `False`
- initial_run_status: `clean_retrain_full_run_incomplete_stage2a_no_promotable_checkpoint`
- initial_run_full_clean_retrain_complete: `False`
- retry1_status: `clean_retrain_retry1_completed_through_stage6_overlay_compose_basic_checks_passed`
- retry1_complete_through_stage6: `True`
- retry1_promoted_by_this_artifact: `False`
- guardrail_status: `clean_retrain_retry1_stage6_overlay_quarantined_guardrails_partial`
- stage6_gap_status: `stage6_gap_explained_by_validation_profile_mismatch`
- stage5_control_debt_status: `stage5_one_ply_guardrail_control_debt_confirmed`
- stage5_semantics_status: `stage5_guardrail_semantics_split_defined`
- stage4_caveat_diagnostic_matrix_ready: `True`
- stage4_caveat_diagnostic_status: `stage4_caveat_diagnostic_matrix_ready`
- stage4_caveat_diagnostic_max_plies_count: `32`
- stage4_caveat_diagnostic_candidate_gap_confidence: `high`
- stage4_caveat_diagnostic_candidate_gap_next_test: `approve_stage4_observation_only_trace_collection_max_6_rows`
- stage4_caveat_decision_passive_ready: `True`
- stage4_caveat_decision_status: `stage4_candidate_generation_gap_with_known_residual_guardrail`
- stage4_caveat_decision_next_action: `explicit_approval_for_stage4_observation_only_trace_collection_or_keep_as_known_guardrail`
- stage4_caveat_runtime_or_training_authorized: `False`
- stage4_caveat_control_status: `stage4_caveat_reproduces_in_base_control_no_overlay_regression`
- curriculum_stage7_status: `stage7_unlock_path_identified_broader_sequence_control_not_micro_repair`
- curriculum_stage8_status: `stage8_remains_blocked_with_review`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Sequence Architecture

- passive_architecture_ready: `True`
- architecture_review_status: `broader_krk_strategy_sequence_review_ready`
- architecture_runtime_work_allowed: `False`
- architecture_recommended_next_slice_id: `krk_strategy_sequence_evidence_plan_v0`
- evidence_plan_status: `strategy_sequence_evidence_plan_defined`
- evidence_plan_runtime_work_allowed: `False`
- inventory_status: `replay_free_inventory_state_holdout_gap_blocks_runtime`
- inventory_runtime_work_allowed: `False`
- inventory_sequence_policy_clean_gate_closed: `True`
- inventory_sequence_policy_has_clean_success_gap: `False`
- inventory_state_holdout_gap_blocks_runtime: `True`
- inventory_strategy_ownership_has_some_signal: `True`
- inventory_strategy_ownership_state_holdout_ready: `False`
- inventory_stage7_is_held_out: `True`
- inventory_stage7_clean_review_recommendation: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- runtime_selector_implemented: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Owner Contrast

- passive_probe_ready: `True`
- label_plan_status: `protected_strategy_owner_contrast_label_plan_defined_execution_review_required`
- label_plan_job_count: `12`
- label_plan_stage7_job_count: `0`
- label_plan_labels_generated: `False`
- label_plan_review_status: `contrast_label_plan_review_passed_binding_required`
- execution_manifest_status: `contrast_execution_manifest_bound_review_required`
- execution_manifest_all_bindings_valid: `True`
- execution_manifest_review_status: `contrast_execution_manifest_review_passed_labels_allowed`
- control_label_count: `12`
- control_label_stage7_count: `0`
- dataset_status: `strategy_owner_contrast_dataset_ready_for_non_causal_probe_selector_sandbox_blocked`
- dataset_row_count: `13`
- dataset_stage7_training_rows: `0`
- readiness_selector_sandbox_ready: `False`
- probe_status: `strategy_owner_contrast_signal_present_selector_sandbox_blocked`
- probe_training_row_count: `9`
- probe_heldout_row_count: `4`
- probe_readiness_blockers: `['insufficient_selected_provider_family_diversity']`
- runtime_arbiter_implemented: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Arbiter Trace Observability

- passive_trace_observability_ready: `True`
- status: `labeled_controls_mixed_no_sandbox`
- sandbox_design_status: `proposed_for_review`
- sandbox_default_enabled: `False`
- smoke_status: `observability_skeleton_smoke_passed`
- smoke_runtime_arbiter_allowed: `False`
- smoke_selected_behavior_metrics_match: `True`
- smoke_observation_is_only_expected_delta: `True`
- smoke_direct_request: `False`
- smoke_score_delta: `0.0`
- observation_frames_status: `observation_frames_collected`
- observation_frame_count: `12`
- observation_stage_counts: `{'stage4': 2, 'stage5': 1, 'stage7': 9}`
- separability_status: `observation_frames_ready_for_non_causal_selector_probe`
- separability_sandbox_ready: `False`
- selector_probe_status: `observation_selector_probe_underlabeled`
- selector_probe_underlabeled: `True`
- selector_probe_selected_unknown_count: `10`
- labeled_controls_status: `labeled_observation_controls_collected`
- labeled_controls_record_count: `21`
- labeled_controls_selected_label_counts: `{'negative': 5, 'positive': 9, 'unknown': 7}`
- labeled_probe_status: `labeled_controls_mixed_no_sandbox`
- labeled_probe_sandbox_ready: `False`
- labeled_probe_stage7_unknown_count: `6`
- protected_matrix_status: `protected_control_matrix_passed`
- protected_matrix_default_off_equivalence_passed: `True`
- protected_matrix_stage7_rows: `0`
- runtime_arbiter_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Arbiter Semantics Blocker

- passive_semantics_blocker_ready: `True`
- status: `selector_objective_and_label_semantics_review_required`
- risk_review_status: `runtime_sandbox_blocked_pending_semantics_review`
- risk_review_runtime_sandbox_allowed: `False`
- risk_review_benchmark_frame_count: `28`
- risk_review_max_only_frame_count: `14`
- stratified_probe_status: `protected_forced_controls_promising_stage7_gap_confirmed`
- stratified_probe_selected_provider_hit_rate: `1.0`
- stratified_probe_forced_control_hit_rate: `1.0`
- stratified_probe_stage7_forced_provider_hit_rate: `0.5`
- architecture_review_status: `trace_only_observability_skeleton_allowed`
- architecture_runtime_arbiter_allowed: `False`
- architecture_allowed_next_scope: `default_off_trace_only`
- architecture_allowed_next_default_enabled: `False`
- sandbox_readiness_decision_status: `readiness_criteria_defined_sandbox_still_blocked`
- sandbox_readiness_selector_sandbox_ready: `False`
- sandbox_readiness_out_of_sample_controls_status: `missing`
- control_plane_observability_skeleton: `implemented_default_off_trace_only`
- control_plane_labeled_controls: `mixed`
- control_plane_stage7: `held_out_unlabeled_challenge`
- control_plane_runtime_arbiter_allowed: `False`
- control_plane_sandbox_ready: `False`
- control_plane_recommended_next_step_id: `krk_selector_objective_label_semantics_v0`
- control_plane_blocked_next_work: `['runtime_arbiter', 'default_off_selector_sandbox', 'score_bonus_or_provider_penalty', 'provider_support_adapter', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation', 'm3_m4_arbitration_update']`
- runtime_arbiter_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Arbiter Out-Of-Sample Controls

- passive_out_of_sample_ready: `True`
- plan_status: `out_of_sample_control_plan_defined_execution_blocked`
- plan_execute_collection_now: `False`
- manifest_status: `execution_manifest_ready_for_review`
- manifest_execute_labels_now: `False`
- manifest_job_count: `12`
- manifest_job_count_by_stage: `{'stage4': 4, 'stage5': 4, 'stage6': 4}`
- manifest_stage7_training_rows: `0`
- manifest_review_status: `execution_manifest_review_passed_bounded_label_run_allowed`
- manifest_review_execute_labels_now: `False`
- label_count: `12`
- label_stage7_training_rows: `0`
- label_selected_result_counts: `{'mate': 11, 'max_plies': 1}`
- probe_status: `out_of_sample_controls_guardrail_positive_selector_sandbox_blocked`
- probe_sandbox_blockers: `['class_imbalance', 'selected_provider_dominance']`
- probe_selected_provider_dominance: `1.0`
- architecture_review_status: `selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse`
- architecture_selector_signal_status: `not_ready_due_to_class_imbalance_and_provider_dominance`
- blocked_next_steps: `['runtime_arbiter', 'selector_sandbox', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation']`
- runtime_arbiter_allowed: `False`
- selector_sandbox_ready: `False`
- runtime_arbiter_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Arbiter Runtime No-Scale Review

- passive_no_scale_ready: `True`
- status: `runtime_sandbox_safe_but_additive_support_not_ready_to_scale`
- default_off_design_status: `default_off_strategy_arbiter_design_ready_for_external_review`
- default_off_design_implementation_allowed: `False`
- default_off_design_runtime_arbiter_allowed: `False`
- default_off_design_selector_sandbox_ready: `False`
- default_off_future_contract_default_enabled: `False`
- runtime_review_packet_status: `runtime_review_packet_ready`
- runtime_review_packet_implementation_allowed: `False`
- runtime_review_packet_selector_sandbox_ready: `False`
- runtime_review_packet_blocked_until_review: `True`
- runtime_sandbox_smoke_status: `runtime_sandbox_smoke_passed`
- runtime_sandbox_default_off_equivalence_passed: `True`
- runtime_sandbox_enabled_support_trace_visible: `True`
- runtime_sandbox_direct_request: `False`
- runtime_sandbox_support_was_applied: `True`
- protected_control_matrix_status: `protected_control_matrix_v2_passed`
- protected_control_no_conversion_regression: `True`
- protected_control_no_no_move_or_draw_spike: `True`
- protected_control_stage7_rows: `0`
- stage7_holdout_status: `stage7_holdout_lock_passed`
- stage7_holdout_support_blocked: `True`
- stage7_holdout_allow_stage7_challenge: `False`
- stage7_challenge_status: `stage7_challenge_probe_no_regression`
- stage7_challenge_conversion_delta: `0`
- stage7_challenge_selected_supported_count: `0`
- support_sensitivity_status: `support_sensitivity_measured`
- support_sensitivity_scale_risk: `high_support_changes_protected_ownership_before_safe_stage7_evidence`
- runtime_test_review_runtime_promotion_allowed: `False`
- runtime_test_review_small_support_stage7_effective: `False`
- runtime_test_review_high_support_scale_risk: `True`
- runtime_test_blocked_path: `raise_additive_support_bonus`
- blocked_next_steps: `['increase_broad_additive_support', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation']`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Provider Identity Maturity Blocker

- passive_provider_identity_maturity_ready: `True`
- status: `provider_identity_signal_requires_provenance_decomposition`
- row_count: `42`
- provider_prior_accuracy: `0.8333333333333334`
- best_feature_probe_baseline: `provider_prior_loo`
- best_feature_probe_accuracy: `0.8333333333333334`
- provider_identity_signal: `strong_but_not_causal_ready`
- raw_provider_id_is_principled_runtime_signal: `False`
- stage0_basin_positive_rate: `0.7333333333333333`
- edge_trap_positive_rates: `[0.1111111111111111, 0.1111111111111111, 0.1111111111111111]`
- required_future_features: `['provider_maturity', 'provider_version', 'source_stage', 'validated_profile', 'frozen_provider', 'overlay_provider', 'guardrail_status', 'plasticity_scope', 'promotion_status', 'protected_provider']`
- blocked_next_work: `['runtime_arbiter', 'selector_sandbox', 'raw_provider_id_runtime_prior', 'provider_support_adapter', 'score_bonus_or_penalty', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation']`
- runtime_arbiter_allowed: `False`
- selector_sandbox_ready: `False`
- stage7_repair_allowed: `False`
- runtime_arbiter_implemented: `False`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Directed Fix Blocker

- passive_selector_directed_fix_ready: `True`
- status: `directed_fix_review_complete_runtime_blocked`
- geometry_audit_status: `geometry_terms_partially_informative_not_sufficient`
- geometry_audit_row_count: `16`
- geometry_audit_stage7_row_count: `0`
- geometry_audit_capacity_label_counts: `{'negative_capacity': 5, 'positive_capacity': 11}`
- geometry_probe_status: `geometry_augmented_features_underpowered`
- geometry_probe_row_count: `16`
- geometry_probe_state_count: `6`
- geometry_probe_underpowered: `True`
- geometry_probe_best_objective: `provider_family`
- geometry_probe_best_negative_suppression: `0.0`
- directed_fix_recommended_next_step: `design_hard_negative_selector_target_dataset_v0`
- directed_fix_recommended_class: `non_causal_hard_negative_selector_target_design`
- directed_fix_recommended_not_runtime: `True`
- directed_fix_rejected_fixes: `['runtime_selector_now', 'runtime_candidate_generator_now', 'train_selector_on_forced_capacity_as_positive', 'add_simple_geometry_terms_only', 'return_to_stage7_patch']`
- directed_fix_requirements: `['keep candidate generation and selection as separate channels', 'create a hard-negative selector target dataset from protected capacity negatives', 'keep forced-capacity labels distinct from selected-playout labels', 'add move/post-move geometry only as non-causal scoring features', 'evaluate leave-state-out suppression before any sandbox', 'keep Stage 7 held out']`
- runtime_work_allowed: `False`
- candidate_generator_runtime_allowed: `False`
- selector_training_allowed: `False`
- runtime_selector_implemented: `False`
- runtime_candidate_generator_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Forced Provider Control Label Lineage

- passive_forced_provider_control_lineage_ready: `True`
- status: `merge_forced_provider_control_labels_and_rerun_stratified_probe`
- plan_causal_status: `non_causal_label_plan`
- plan_selected_job_count: `12`
- plan_selected_job_count_by_stage: `{'stage5': 6, 'stage6': 6}`
- plan_current_label_result_counts: `{'mate': 8, 'max_plies': 4}`
- plan_target_stages: `['stage5', 'stage6']`
- manifest_causal_status: `non_causal_execution_manifest`
- manifest_all_bindings_valid: `True`
- manifest_job_count: `12`
- manifest_missing_path_count: `0`
- labels_causal_status: `non_causal_label_run`
- label_count: `12`
- label_stage_counts: `{'stage4': 0, 'stage5': 6, 'stage6': 6, 'stage7': 0}`
- result_counts: `{'mate': 9, 'max_plies': 3}`
- result_counts_by_stage: `{'stage5:mate': 6, 'stage6:mate': 3, 'stage6:max_plies': 3}`
- trace_failures_only: `True`
- trace_included_count: `0`
- forced_successor_available_count: `12`
- provider_ids: `['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo', 'krk.stage0_basin']`
- blocked_next_steps: `['runtime_arbiter', 'runtime_internal_terminal', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation']`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Provenance Prior Blocker

- passive_provenance_prior_blocker_ready: `True`
- status: `provider_prior_remains_best_no_selector_sandbox`
- target_dataset_status: `selector_target_dataset_built`
- target_dataset_training_row_count: `42`
- target_dataset_stage7_training_rows: `0`
- target_probe_heldout_training_row_count: `0`
- baseline_probe_best_baseline: `provider_prior_loo`
- baseline_probe_best_accuracy: `0.8333333333333334`
- feature_baseline_status: `provider_prior_remains_best_non_causal_baseline`
- feature_baseline_improved_over_provider_prior: `False`
- provenance_dataset_rows_with_provider_provenance: `54`
- provenance_probe_status: `provenance_features_explain_provider_prior_non_causal`
- provenance_probe_raw_provider_id_runtime_prior_allowed: `False`
- provenance_probe_selector_sandbox_ready: `False`
- provenance_probe_best_name: `provider_id_loo`
- architecture_review_status: `provider_prior_remains_best_no_selector_sandbox`
- architecture_observation_features_improved_over_provider_prior: `False`
- architecture_must_remain_non_causal: `True`
- after_contrast_status: `selector_sandbox_blocked_selected_provider_evidence_missing`
- after_contrast_selector_sandbox_ready: `False`
- after_contrast_readiness_blockers: `['insufficient_selected_provider_family_diversity']`
- runtime_arbiter_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Objective Normalization

- passive_objective_ready: `True`
- arbitration_objective_status: `additive_support_objective_rejected_design_normalized_selector_objective`
- normalized_objective_status: `normalized_selector_objective_design_ready_for_offline_probe`
- normalized_probe_status: `normalized_objective_probe_underpowered_fields_available`
- normalized_probe_benchmark_underpowered: `True`
- normalized_probe_review_status: `normalized_selector_signal_promising_more_ranked_frames_required`
- normalized_probe_review_stage7_training_leakage: `False`
- selector_architecture_status: `selector_objective_needs_stratified_label_expansion_before_sandbox`
- selector_architecture_sandbox_ready: `False`
- selector_label_semantics_sandbox_ready: `False`
- split_dataset_status: `split_selector_objective_channels_with_ownership_labels`
- split_dataset_objective_row_count: `136`
- split_dataset_selector_training_row_count: `0`
- split_dataset_stage7_row_count: `0`
- split_readiness_status: `ownership_labels_recovered_but_underpowered`
- split_readiness_selector_training_allowed: `False`
- split_readiness_ownership_probe_underpowered: `True`
- runtime_selector_implemented: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Replay-Free Label Lineage

- passive_replay_free_label_lineage_ready: `True`
- plan_status: `bounded_selector_stratified_label_plan_ready`
- plan_execute_labels_now: `False`
- plan_job_count: `11`
- plan_job_stage_counts: `{'stage4': 4, 'stage5': 4, 'stage6': 3, 'stage7': 0}`
- review_status: `planned_labels_replay_free_fillable`
- review_execute_labels_now: `False`
- review_missing_replay_free_label_count: `0`
- review_fill_status_counts: `{'compatible_target_label_available': 11}`
- negative_control_status: `negative_protected_controls_identified_replay_free`
- negative_control_count: `9`
- negative_control_stage_counts: `{'stage4': 2, 'stage5': 4, 'stage6': 3}`
- negative_control_provider_counts: `{'krk.edge_trap_close': 3, 'krk.edge_trap_enemy_between': 2, 'krk.edge_trap_wrong_tempo': 2, 'krk.stage0_basin': 2}`
- stratified_dataset_status: `stratified_selector_label_dataset_built_replay_free`
- stratified_dataset_row_count: `11`
- stratified_dataset_label_counts: `{'negative': 1, 'positive': 10}`
- stratified_dataset_stage7_training_rows: `0`
- balanced_dataset_status: `balanced_selector_label_dataset_built_replay_free`
- balanced_dataset_row_count: `18`
- balanced_dataset_label_counts: `{'negative': 9, 'positive': 9}`
- balanced_dataset_stage7_training_rows: `0`
- balanced_probe_status: `balanced_labels_support_non_causal_selector_signal`
- balanced_probe_best_baseline: `provider_id_loo`
- balanced_probe_best_accuracy: `0.7777777777777778`
- architecture_status: `selector_signal_promising_sandbox_blocked_pending_readiness_criteria`
- architecture_selector_sandbox_ready: `False`
- architecture_runtime_arbiter_allowed: `False`
- architecture_stage7_repair_allowed: `False`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_arbiter_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Label Balance

- passive_label_balance_ready: `True`
- stratified_dataset_status: `stratified_selector_label_dataset_built_replay_free`
- stratified_dataset_row_count: `11`
- stratified_dataset_stage7_training_rows: `0`
- stratified_probe_status: `stratified_labels_underbalanced_no_selector_probe`
- stratified_probe_label_counts: `{'negative': 1, 'positive': 10}`
- stratified_probe_underbalanced: `True`
- balanced_dataset_status: `balanced_selector_label_dataset_built_replay_free`
- balanced_dataset_row_count: `18`
- balanced_dataset_stage7_training_rows: `0`
- balanced_dataset_provider_family_counts: `{'edge_trap': 9, 'stage0_basin': 9}`
- balanced_probe_status: `balanced_labels_support_non_causal_selector_signal`
- balanced_probe_label_counts: `{'negative': 9, 'positive': 9}`
- balanced_probe_best_baseline: `provider_id_loo`
- balanced_probe_best_accuracy: `0.7777777777777778`
- architecture_status: `selector_signal_promising_sandbox_blocked_pending_readiness_criteria`
- architecture_recommended_next_step: `define_strategy_arbiter_sandbox_readiness_criteria`
- architecture_runtime_arbiter_allowed: `False`
- architecture_selector_sandbox_ready: `False`
- blocked_next_work: `['runtime_arbiter', 'selector_sandbox_implementation', 'provider_support_adapter', 'score_bonus_or_penalty', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation', 'm3_m4_arbitration_update']`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Ownership Selection Context

- passive_context_ready: `True`
- label_dataset_status: `ownership_selection_labels_expanded_with_targeted_false_positive_risk_cells`
- label_dataset_merged_row_count: `41`
- label_dataset_target_label_counts: `{'selected_owner_converted': 31, 'selected_owner_failed': 10}`
- label_dataset_targeted_added_row_count: `6`
- label_dataset_selector_training_row_count: `0`
- label_dataset_stage7_row_count: `0`
- context_dataset_status: `ownership_selection_context_dataset_ready_for_non_causal_probe`
- context_dataset_row_count: `41`
- context_dataset_exact_move_context_count: `41`
- context_dataset_label_counts: `{'selected_owner_converted': 31, 'selected_owner_failed': 10}`
- context_dataset_provider_family_counts: `{'edge_trap': 3, 'fence_established': 1, 'stage0_basin': 37}`
- context_dataset_selector_training_row_count: `0`
- context_dataset_stage7_row_count: `0`
- context_probe_status: `context_features_underpowered`
- context_probe_underpowered: `True`
- context_probe_positive_owner_count: `31`
- context_probe_negative_owner_count: `10`
- source_diversity_status: `source_diversity_gap_blocks_runtime`
- source_diversity_non_stage0_ownership_row_count: `4`
- source_diversity_provider_counts: `{'krk.edge_trap_close': 3, 'krk.fence_established': 1, 'krk.stage0_basin': 31}`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Negative-Suppression Blocker

- passive_blocker_ready: `True`
- protected_max_only_status: `protected_max_only_frames_block_runtime_selector`
- protected_max_only_frame_count: `24`
- protected_max_only_frames_with_only_max_plies: `12`
- protected_max_only_frames_with_mate_provider: `12`
- protected_max_only_runtime_work_allowed: `False`
- negative_suppression_status: `selector_negative_suppression_failure_confirmed`
- negative_suppression_recommended_next_step: `design_non_causal_negative_suppression_feature_and_label_balance_fix`
- negative_suppression_runtime_work_allowed: `False`
- negative_suppression_selector_training_allowed: `False`
- negative_suppression_candidate_generator_runtime_allowed: `False`
- runtime_selector_readiness_status: `runtime_selector_not_ready_collect_better_contrast_labels`
- runtime_selector_readiness_runtime_test_allowed_next: `False`
- runtime_selector_readiness_recommended_next_step: `design_small_diverse_state_local_contrast_label_plan`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Abstention Selector Safety

- passive_safety_ready: `True`
- runtime_architecture_lineage_ready: `True`
- runtime_architecture_review_status: `design_abstention_first_selector_objective`
- runtime_architecture_implementation_allowed: `design_only`
- runtime_architecture_selector_ready: `False`
- runtime_architecture_stage7_repair_ready: `False`
- runtime_architecture_internal_terminal_ready: `False`
- runtime_architecture_blocked_next_steps: `['runtime_selector', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation', 'm3_m4_arbitration_update']`
- first_objective_status: `abstention_first_selector_objective_defined`
- safe_preservation_review_status: `safe_preservation_requires_two_stage_label_semantics`
- training_dataset_status: `abstention_training_dataset_ready_for_probe`
- training_dataset_row_count: `51`
- training_dataset_stage7_training_rows: `0`
- training_probe_status: `abstention_signal_underpowered_no_runtime`
- context_dataset_status: `abstention_context_feature_dataset_ready_for_non_causal_probe`
- context_probe_status: `context_features_help_but_runtime_blocked`
- context_probe_improved_negative_suppression: `True`
- context_error_audit_status: `context_signal_overrejects_safe_owners_runtime_blocked`
- context_error_false_positive_count: `12`
- feature_gap_next_step_status: `join_abstention_labels_with_control_plane_context`
- feature_gap_implementation_allowed: `non_causal_replay_free_only`
- feature_gap_runtime_ready: `False`
- blocked_next_steps: `['runtime_selector', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation', 'm3_m4_arbitration_update']`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Two-Stage Abstention No-Go

- passive_no_go_ready: `True`
- objective_probe_status: `two_stage_abstention_signal_present_runtime_review_required`
- objective_probe_row_count: `51`
- objective_probe_threshold_passing_objective_count: `12`
- runtime_review_status: `two_stage_abstention_review_ready_implementation_blocked`
- runtime_review_implementation_allowed: `False`
- runtime_review_runtime_test_allowed_next: `False`
- default_off_status: `default_off_equivalent`
- default_off_same_core_metrics: `True`
- enabled_smoke_status: `enabled_tiny_smoke_no_behavior_delta`
- enabled_smoke_total_penalized_count: `24`
- enabled_smoke_total_selected_penalized_count: `0`
- stage7_challenge_status: `stage7_challenge_no_target_improvement`
- stage7_challenge_conversion_delta_mates: `0`
- stage7_challenge_target_improved: `False`
- status: `no_go_for_scaling_or_promotion`
- go_no_go_allowed_status: `keep_default_off_runtime_test_code_and_artifacts`
- rollback_tag: `pre-two-stage-abstention-runtime`
- runtime_defaults_changed: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- runtime_repair_not_promoted: `True`
- stage7_remains_quarantined: `True`
- stage8_remains_blocked: `True`
- no_hidden_controller: `True`

## Targeted Ownership Recovery

- passive_recovery_ready: `True`
- non_stage0_manifest_status: `targeted_non_stage0_manifest_ready`
- non_stage0_manifest_job_count: `4`
- non_stage0_manifest_stage7_job_count: `0`
- non_stage0_labels_status: `current_profile_preserves_some_historical_non_stage0_ownership`
- non_stage0_label_count: `4`
- non_stage0_preserved_count: `4`
- non_stage0_stage0_collapse_count: `0`
- non_stage0_stage7_training_rows: `0`
- negative_manifest_status: `targeted_ownership_negative_manifest_ready`
- negative_manifest_job_count: `6`
- negative_manifest_stage7_job_count: `0`
- negative_labels_status: `targeted_ownership_negative_labels_collected`
- negative_label_count: `6`
- negative_targeted_owner_converted_count: `4`
- negative_targeted_owner_failed_count: `2`
- negative_stage7_training_rows: `0`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Balanced Hard-Negative Evidence

- passive_evidence_ready: `True`
- label_plan_status: `balanced_hard_negative_label_plan_v1_ready`
- label_plan_job_count: `12`
- label_plan_stage7_jobs: `0`
- execution_manifest_status: `balanced_hard_negative_execution_manifest_bound`
- execution_manifest_labels_allowed_now: `False`
- execution_manifest_stage7_jobs: `0`
- execution_manifest_review_status: `balanced_hard_negative_manifest_review_passed_labels_allowed`
- labels_status: `balanced_hard_negative_labels_completed`
- label_count: `12`
- positive_capacity_count: `11`
- negative_capacity_count: `1`
- stage7_labels: `0`
- stage7_training_labels: `0`
- evidence_review_status: `balanced_hard_negative_signal_promising_but_underpowered`
- evidence_underpowered: `True`
- evidence_expanded_row_count: `40`
- evidence_expanded_hard_negative_count: `9`
- evidence_best_negative_suppression: `0.2222222222222222`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Hard-Negative Label Semantics

- passive_semantics_ready: `True`
- status: `capacity_labels_not_direct_selector_targets`
- recommended_next_step: `run_stronger_capacity_risk_feature_review_non_causal`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- row_count: `40`
- state_count: `14`
- stage7_row_count: `0`
- capacity_negative_count: `9`
- capacity_positive_count: `31`
- state_local_contrast_state_count: `2`
- best_ablation_negative_suppression: `0.2222222222222222`
- blocked_use_by_label_channel: `{'forced_provider_capacity_label': 'direct_runtime_owner_selection_or_suppression', 'state_local_capacity_contrast': 'global provider-family suppression', 'hard_negative_capacity': 'selector training target until safe-owner preservation is separately validated'}`
- stronger_feature_review_consumes_semantics: `True`
- runtime_selector_implemented: `False`
- runtime_candidate_generator_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Stronger Selector Feature Review

- passive_feature_review_ready: `True`
- feature_ablation_status: `hard_negative_feature_ablation_promising_underpowered`
- feature_ablation_underpowered: `True`
- feature_ablation_row_count: `40`
- feature_ablation_stage7_row_count: `0`
- feature_ablation_best_objective: `provider_piece_king_delta@0.5`
- feature_ablation_best_negative_suppression: `0.2222222222222222`
- feature_review_status: `stronger_features_review_ready_runtime_still_blocked`
- feature_review_recommended_next_step: `architecture_review_before_selector_training_or_runtime`
- feature_review_improved_over_v2_ablation: `True`
- feature_review_row_count: `40`
- feature_review_stage7_row_count: `0`
- feature_review_previous_best_negative_suppression: `0.2222222222222222`
- feature_review_best_negative_suppression: `0.7777777777777778`
- feature_review_best_positive_recall: `0.9032258064516129`
- feature_review_best_objective: `piece_motion@0.5`
- runtime_selector_implemented: `False`
- runtime_candidate_generator_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selected-Provider Diversity

- passive_diversity_review_ready: `True`
- evidence_plan_status: `selected_provider_diversity_evidence_plan_defined`
- replay_free_scan_status: `selected_provider_diversity_replay_free_insufficient`
- replay_free_selected_record_count: `23`
- observation_manifest_status: `selected_provider_diversity_sampling_manifest_review_required`
- observation_manifest_review_status: `selected_provider_diversity_sampling_manifest_review_passed`
- observation_scan_status: `selected_provider_diversity_observation_insufficient`
- observation_scan_count: `20`
- manifest_status: `fresh_seed_selected_provider_diversity_manifest_ready_for_bounded_labels`
- manifest_observations_allowed_now: `False`
- manifest_bounded_labels_allowed_by_script: `True`
- manifest_job_count: `18`
- manifest_stage7_jobs: `0`
- labels_status: `fresh_seed_selected_provider_diversity_ownership_labels_collected`
- label_count: `18`
- ownership_label_counts: `{'selected_owner_converted': 15, 'selected_owner_failed': 3}`
- selected_result_counts_by_stage: `{'stage4:mate': 6, 'stage4:max_plies': 2, 'stage5:mate': 6, 'stage6:mate': 3, 'stage6:max_plies': 1}`
- selected_provider_counts: `{'krk.stage0_basin': 18}`
- stage7_training_rows: `0`
- architecture_status: `selected_provider_diversity_requirement_should_be_reframed`
- architecture_recommended_next_step: `define_selector_readiness_v3_proposal_diversity_criteria`
- architecture_runtime_arbiter_allowed: `False`
- runtime_selector_implemented: `False`
- runtime_candidate_generator_implemented: `False`
- runtime_arbiter_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Readiness v3 Design

- passive_design_review_ready: `True`
- status: `selector_readiness_v3_sandbox_design_review_allowed`
- recommended_next_step: `design_default_off_strategy_arbiter_sandbox_for_review`
- runtime_arbiter_allowed: `False`
- selector_sandbox_ready: `False`
- hard_blocker_count: `0`
- passed_checks: `['proposal_family_diversity', 'conversion_positive_provider_diversity', 'label_balance', 'protected_stage_coverage', 'stage7_heldout_boundary']`
- diagnostic_only_checks: `['current_selected_provider_diversity']`
- label_balance: `{'negative': 11, 'positive': 13}`
- stage_coverage: `{'stage4': 2, 'stage5': 4, 'stage6': 3, 'stage7': 4}`
- stage7_training_rows: `0`
- conversion_positive_provider_family_count: `3`
- conversion_positive_provider_families: `['drive_to_edge', 'edge_trap', 'fence_established']`
- default_off_design_status: `default_off_strategy_arbiter_design_ready_for_external_review`
- default_off_design_implementation_allowed: `False`
- runtime_review_packet_readiness_v3_status: `selector_readiness_v3_sandbox_design_review_allowed`
- runtime_arbiter_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## State-Local Contrast

- passive_contrast_ready: `True`
- labels_status: `state_local_contrast_labels_v2_joined`
- labels_row_count: `20`
- labels_training_contrast_label_counts: `{'negative': 3, 'positive': 9}`
- labels_stage7_challenge_row_count: `8`
- labels_stage7_contrast_label_counts: `{'negative': 8}`
- labels_usable_training_row_count: `12`
- probe_status: `state_local_contrast_signal_not_ready`
- probe_training_row_count: `12`
- probe_stage7_eval_row_count: `8`
- probe_stage7_training_leakage: `False`
- readiness_status: `runtime_selector_blocked_negative_suppression_zero`
- readiness_recommended_next_step: `architecture_review_before_more_runtime_tests`
- readiness_runtime_test_allowed_next: `False`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## State-Local Paired Ownership

- passive_semantic_gate_ready: `True`
- hard_negative_target_dataset_status: `hard_negative_selector_target_dataset_expanded_v2`
- hard_negative_target_row_count: `40`
- hard_negative_training_row_count: `0`
- hard_negative_stage7_row_count: `0`
- ownership_context_status: `context_features_review_ready_but_not_runtime_ready`
- ownership_context_runtime_threshold_passed: `False`
- ownership_architecture_status: `ownership_objective_requires_state_local_pairing_review`
- objective_plan_status: `state_local_paired_ownership_objective_plan_ready`
- work_package_status: `work_package_ready`
- inventory_status: `paired_inventory_ready_for_non_causal_probe`
- inventory_pair_count: `40`
- inventory_same_state_conflict_pair_count: `9`
- inventory_selector_training_row_count: `0`
- inventory_stage7_row_count: `0`
- probe_status: `semantic_gate_review_ready_runtime_feature_translation_needed`
- probe_threshold_passing_model_count: `2`
- probe_runtime_feature_passing_model_count: `0`
- error_audit_status: `safe_preservation_false_positives_are_outcome_semantics_errors`
- review_status: `semantic_gate_review_ready_runtime_feature_translation_needed`
- review_best_objective: `safe_preservation_gated_model`
- review_runtime_feature_passing_model_count: `0`
- review_stage7_row_count: `0`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selected-Owner Failure-Risk Proxy

- passive_proxy_review_ready: `True`
- runtime_proxy_design_status: `proxy_design_ready_for_replay_free_validation`
- runtime_proxy_dataset_row_count: `40`
- runtime_proxy_dataset_selector_training_row_count: `0`
- runtime_proxy_dataset_stage7_row_count: `0`
- runtime_proxy_review_status: `runtime_proxy_translation_still_blocked`
- runtime_review_packet_v0_translation_blocker: `True`
- failure_risk_evidence_status: `failure_risk_evidence_v1_built`
- failure_risk_evidence_row_count: `48`
- visible_proxy_precision: `1.0`
- visible_proxy_recall: `1.0`
- visible_proxy_probe_v0_status: `visible_failure_risk_proxy_candidate_needs_out_of_sample_validation`
- independent_validation_v0_status: `independent_proxy_validation_failed_or_underpowered`
- independent_validation_v0_threshold_met: `False`
- independent_validation_v0_safe_preservation_recall: `0.42857142857142855`
- blocker_review_v0_status: `failed_proxy_closed_next_evidence_v1_required`
- blocker_review_v0_threshold_met: `False`
- blocker_review_v0_false_positive_count: `4`
- proxy_v1_probe_status: `proxy_v1_independent_candidate_found`
- proxy_v1_independent_passing_proxy_count: `3`
- independent_label_count: `8`
- independent_label_stage7_training_rows: `0`
- independent_validation_status: `independent_proxy_validation_passed`
- independent_validation_threshold_met: `True`
- independent_validation_runtime_scope: `progress_window_monitor_or_reconsideration_only`
- runtime_proxy_review_packet_v1_status: `runtime_review_ready_progress_window_scope_only`
- runtime_proxy_review_packet_v1_implementation_allowed: `False`
- runtime_proxy_review_packet_v1_stage7_row_count: `0`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- runtime_terminals_added: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Progress-Window Reconsideration

- passive_review_ready: `True`
- runtime_test_review_status: `runtime_test_scaffold_wired_but_policy_insufficient`
- runtime_test_guardrails_allowed_now: `False`
- runtime_test_promotion_allowed_now: `False`
- runtime_test_default_off_equivalence_passed: `True`
- runtime_test_activation_observed: `True`
- runtime_test_target_improvement_observed: `False`
- runtime_test_safe_regression_observed: `False`
- smoke_status: `runtime_smoke_activation_observed_no_target_improvement`
- smoke_default_off_equivalence_passed: `True`
- smoke_improved_target_failure_count: `0`
- smoke_safe_regression_count: `0`
- smoke_target_failure_row_count: `1`
- smoke_protected_label_count: `3`
- smoke_enabled_supported_total: `518`
- smoke_enabled_selected_supported_total: `14`
- post_activation_status: `post_activation_failure_classified`
- post_activation_implement_next_fix_now: `False`
- post_activation_recommended_next_step: `return_to_candidate_generation_or_broader_strategy_sequence_track`
- classification_primary: `candidate_set_missing_good_alternative`
- classification_labels: `['candidate_set_missing_good_alternative', 'visible_support_terms_overbroad']`
- promotion_status: `quarantined_or_analysis_only`
- sandbox_status: `wired_but_policy_insufficient`
- runtime_defaults_changed: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Runtime Sandbox Policy Update

- passive_policy_update_ready: `True`
- status: `reviewed_default_off_runtime_sandbox_allowed`
- allowed_scope: `progress_window_selected_owner_reconsideration`
- broad_runtime_changes_allowed: `False`
- default_policy_changes_allowed: `False`
- test_result_status: `runtime_test_scaffold_wired_but_policy_insufficient`
- test_result_default_off_equivalence_passed: `True`
- test_result_activation_observed: `True`
- test_result_target_improvement_observed: `False`
- test_result_guardrails_allowed_now: `False`
- source_review_packet: `reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.json`
- progress_window_passive_review_ready: `True`
- hidden_python_controller: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`
- general_predecision_selector: `False`
- stage7_repair_or_promotion: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Clean Replacement Review

- passive_review_ready: `True`
- replacement_readiness_status: `retry1_ready_for_remaining_preservation_checks_not_replacement`
- replacement_readiness_clean_stack_replacement_allowed: `False`
- snapshot_manifest_status: `retry1_protected_stack_snapshot_manifest_ready_no_replacement`
- snapshot_manifest_all_referenced_paths_exist: `True`
- snapshot_manifest_replacement_allowed: `False`
- review_packet_status: `retry1_clean_stack_replacement_review_ready_explicit_approval_required`
- review_packet_replacement_review_ready: `True`
- review_packet_implementation_allowed: `False`
- deferred_review_status: `clean_stack_adoption_deferred_explicit_approval_required`
- deferred_review_explicit_approval_detected: `False`
- deferred_review_implementation_allowed: `False`
- protected_stage_reference_mode: `retry1_manifest_active`
- protected_stage_active_stack_status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- protected_stage_stage4_status: `protected_profile_solved_with_overlay_guardrail_caveat`
- protected_stage_stage7_status: `local_valid_composition_quarantined`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Stage Status

- `stage1`: `protected_component_from_current_brief`
- `stage4`: `stage4_caveat_unblocker_ready_pending_explicit_runtime_approval`
  - approval_request_artifact: `reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json`
  - approval_request_status: `stage4_first_move_contrast_sandbox_approval_request_ready`
  - approval_request_created: `False`
- `stage5`: `protected_retry1_stack_validated`
- `stage6`: `protected_retry1_overlay_validated`
- `stage7`: `held_out_challenge_quarantined`
- `stage8`: `blocked`

## Stage 7 Sampling Gate

- runner_status: `stage7_diverse_clean_sampling_runner_executed_success`
- runner_dry_run: `False`
- runner_job_count: `8`
- processed_job_count: `0`
- executed_job_count: `0`
- skipped_existing_output_count: `0`
- overwrite_existing_outputs: `False`
- output_validation_status: `stage7_diverse_clean_sampling_outputs_valid_ready_for_integration`
- execution_readiness_source: `live_recomputed`
- execution_readiness_status: `not_applicable_stage7_success_gate_closed`
- execution_readiness_jobs_passing: `8`
- invalid_existing_output_count: `0`
- job_timeout_seconds: `900`
- timed_out_job_count: `0`
- integration_status: `stage7_diverse_clean_sampling_integration_success_controls_met`
- outputs_present_count: `8`
- combined_success_controls: `11`
- success_controls_required: `5`
- success_controls_ready: `True`

## Sequence Policy

- pipeline_status: `sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review`
- input_probe_status: `sequence_policy_input_probe_ready_for_full_non_causal_benchmark`
- input_probe_row_count: `118`
- input_probe_benchmark_input_ready: `True`
- input_probe_stage4_topk_signal: `True`
- input_probe_protected_plan_window_failure_sparse: `True`
- input_probe_selector_training_row_count: `0`
- input_probe_runtime_authorization_row_count: `0`
- benchmark_status: `sequence_policy_benchmark_ready_non_causal_results_available`
- benchmark_design_status: `sequence_policy_benchmark_design_ready_non_causal`
- benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- post_failure_contrast_refresh_status: `sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs`
- post_failure_contrast_refresh_boundaries_preserved: `True`
- post_failure_contrast_refresh_boundary_violation_count: `0`
- post_failure_contrast_refresh_row_count: `0`
- post_failure_contrast_refresh_stage7_training_row_count: `0`
- passive_design_without_new_labels_status: `non_causal_sequence_policy_design_without_new_labels_ready`
- passive_design_current_evidence_limit: `protected_plan_window_failure_evidence_sparse`
- passive_design_depends_on_new_label_execution: `False`
- passive_design_depends_on_protected_failure_contrast_collection: `False`
- cross_stage_requirements_status: `cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark`
- replay_free_protected_cross_stage_evidence: `True`
- cross_stage_sequence_evidence_met: `True`
- input_row_count: `118`
- inputs_ready: `True`
- benchmark_ready: `True`
- selector_training_row_count: `0`

## Protected Failure Contrast Gate

- plan_status: `protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval`
- unique_failure_count: `1`
- minimum_new_failures_needed: `4`
- manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- manifest_job_count: `6`
- manifest_review_status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval`
- execution_readiness_status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`
- execution_jobs_passing: `6`
- runner_status: `protected_plan_window_failure_contrast_runner_dry_run_ready`
- runner_manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- runner_manifest_declared_job_count: `6`
- runner_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- runner_collection_run_allowed: `False`
- runner_processed_job_count: `0`
- runner_executed_job_count: `0`
- output_validation_status: `protected_plan_window_failure_contrast_outputs_validation_pending`
- output_exists_count: `0`
- output_valid_count: `0`
- integration_status: `protected_plan_window_failure_contrast_integration_pending_outputs`
- integrated_new_failure_count: `0`
- integration_ready: `False`
- ready_for_explicit_approval: `True`
- current_artifact_allows_collection: `False`
- approval_receipt_required: `True`
- approval_receipt_path: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- approval_receipt_present: `False`
- approval_receipt_valid: `False`
- approval_receipt_blockers: `['approval_receipt_missing']`
- approval_request_artifact: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.json`
- approval_request_status: `protected_plan_window_failure_contrast_approval_request_ready`
- approval_receipt_created_by_request: `False`
- post_success_refresh_required: `True`
- post_success_refresh_script: `scripts/advance_krk_suite_from_current_gates_v0.py`
- post_success_refresh_scope: `full_passive_krk_suite_gate_stack`
- expected_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- expected_readiness_fingerprint: `a9b4f2849f2b862370c045cf8a3f4aaef741533188608d8658ae15727084eec0`
- command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py --execute-reviewed-collection --refresh-after-run --approval-receipt reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_selector_implemented: `False`
- runtime_score_changes: `False`
- runtime_direct_routing: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- gameplay_topology_mutation: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Protected Missing-Provider Evidence

- audit_plan_ready: `True`
- audit_plan_status: `protected_missing_provider_capacity_audit_plan_ready`
- audit_plan_job_count: `16`
- audit_plan_source_frame_count: `6`
- audit_plan_stage_counts: `{'stage4': 6, 'stage5': 7, 'stage6': 3}`
- audit_plan_runtime_work_allowed: `False`
- execution_manifest_status: `protected_missing_provider_capacity_execution_manifest_bound`
- execution_manifest_job_count: `16`
- execution_manifest_stage7_job_count: `0`
- execution_manifest_labels_allowed_now: `False`
- execution_manifest_runtime_work_allowed: `False`
- execution_manifest_review_passive_ready: `True`
- execution_manifest_review_status: `protected_missing_provider_capacity_manifest_review_passed_labels_allowed`
- execution_manifest_review_labels_allowed: `True`
- execution_manifest_review_runtime_work_allowed: `False`
- execution_manifest_review_violation_count: `0`
- labels_status: `protected_missing_provider_capacity_labels_completed`
- labels_next_step: `merge_missing_provider_labels_and_refresh_strategy_sequence_inventory`
- label_count: `16`
- label_result_counts: `{'mate': 11, 'max_plies': 5}`
- stage7_label_count: `0`
- stage7_training_label_count: `0`
- merge_status: `protected_missing_provider_labels_unmatched_by_current_proposal_frames`
- merge_next_step: `review_ranked_proposal_frame_coverage_for_protected_missing_provider_states`
- matched_label_count: `0`
- unmatched_label_count: `16`
- coverage_status: `proposal_provider_coverage_gap_blocks_selector_training`
- coverage_next_step: `design_non_causal_proposal_coverage_expansion_for_protected_states`
- coverage_label_count: `16`
- coverage_frames_present_count: `16`
- provider_present_in_frame_count: `0`
- provider_missing_from_frame_count: `16`
- missing_provider_mate_label_count: `11`
- current_gap_blocks_selector_training: `True`
- coverage_expansion_plan_status: `protected_proposal_coverage_expansion_plan_ready`
- coverage_expansion_rows_to_create: `16`
- coverage_expansion_training_allowed_initially: `False`
- coverage_frames_status: `protected_provider_coverage_frames_built`
- coverage_frame_row_count: `16`
- coverage_frame_training_row_count: `0`
- coverage_frame_runtime_proposal_row_count: `0`
- training_semantics_review_status: `capacity_frames_diagnostic_not_selector_training_ready`
- training_semantics_selector_training_allowed: `False`
- training_semantics_runtime_work_allowed: `False`
- training_semantics_training_row_count: `0`
- training_semantics_runtime_proposal_row_count: `0`
- candidate_generator_coverage_status: `candidate_generator_recall_gap_confirmed`
- candidate_generator_positive_recall_rate: `0.0`
- candidate_generator_missing_positive_capacity_count: `11`
- validated_candidate_set_status: `validated_provider_candidate_set_recall_promising_requires_selector_semantics`
- validated_candidate_set_added_positive_capacity_count: `11`
- validated_candidate_set_added_negative_capacity_count: `5`
- two_stage_review_status: `two_stage_non_causal_benchmark_design_needed`
- two_stage_benchmark_plan_status: `two_stage_candidate_selection_benchmark_plan_ready`
- two_stage_benchmark_status: `candidate_generation_recall_improves_selection_not_ready`
- two_stage_benchmark_current_positive_recall_rate: `0.0`
- two_stage_benchmark_expanded_positive_recall_rate: `1.0`
- two_stage_benchmark_selector_ready: `False`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Sequence Candidate-Source Evidence

- candidate_proposal_coverage_status: `candidate_generation_gap_confirmed`
- candidate_proposal_coverage_positive_capacity_recall: `0.0`
- candidate_proposal_coverage_missing_positive_capacity_count: `11`
- candidate_generation_strategy_review_status: `strategy_sequence_control_plane_v1_needed`
- candidate_generation_strategy_review_runtime_sandbox_allowed: `False`
- schema_status: `strategy_sequence_candidate_frame_schema_defined`
- schema_runtime_sandbox_allowed: `False`
- frames_status: `strategy_sequence_frames_populated_non_causal`
- frames_frame_count: `256`
- frames_frame_type_counts: `{'broader_krk_strategy_candidate': 13, 'candidate_move_hypothesis': 140, 'validated_provider_candidate': 103}`
- frames_stage7_challenge_row_count: `198`
- frames_stage7_readiness_training_row_count: `0`
- quality_status: `frame_quality_probe_supports_next_sequence_candidate_benchmark`
- quality_capacity_not_selector_label: `True`
- quality_sequence_candidate_mate_count: `0`
- source_benchmark_status: `candidate_generation_sources_promising_selector_blocked`
- source_benchmark_protected_positive_capacity_ratio: `0.6875`
- source_benchmark_protected_negative_capacity_ratio: `0.3125`
- source_benchmark_progress_window_sequence_candidate_mate_count: `0`
- control_plane_status: `candidate_generation_control_plane_ready_for_architecture_review`
- control_plane_runtime_sandbox_allowed: `False`
- sandbox_review_status: `candidate_generation_observation_sandbox_review_ready`
- sandbox_review_implementation_authorized: `False`
- observation_sandbox_status: `observation_sandbox_ready_for_non_causal_coverage_analysis`
- observation_sandbox_generated_candidate_count: `93`
- observation_sandbox_selected_move_or_provider_changed: `False`
- observation_coverage_status: `observation_frames_usable_for_non_causal_coverage_analysis`
- observation_coverage_sampled_frame_count: `93`
- observation_coverage_invariant_failure_count: `0`
- observation_broadened_status: `broadened_observation_sample_supports_coverage_analysis`
- observation_broadened_case_count: `19`
- observation_broadened_emitted_frame_count: `569`
- observation_broadened_selected_move_or_provider_delta_count: `0`
- observation_gap_review_status: `observation_gap_review_blocks_selector_recommends_capacity_annotation`
- observation_gap_review_unknown_capacity_ratio: `0.7768014059753954`
- capacity_annotation_v1_status: `candidate_move_capacity_annotation_partial_selector_blocked`
- capacity_annotation_v1_protected_annotation_recall: `0.03424657534246575`
- capacity_label_manifest_status: `bounded_candidate_move_capacity_manifest_ready`
- capacity_label_manifest_labels_run_by_this_artifact: `False`
- capacity_label_manifest_stage7_job_count: `0`
- capacity_labels_status: `bounded_candidate_move_capacity_labels_completed`
- capacity_labels_label_count: `12`
- capacity_labels_stage7_training_label_count: `0`
- capacity_annotation_v2_status: `candidate_move_capacity_annotation_improved_but_selector_blocked`
- capacity_annotation_v2_protected_annotation_recall: `0.07534246575342465`
- label_blocker_status: `candidate_generation_label_coverage_underpowered_selector_blocked`
- label_blocker_more_blind_label_farming_not_recommended: `True`
- quality_prioritization_review_status: `proposal_quality_prioritization_review_ready`
- quality_dataset_status: `candidate_proposal_quality_dataset_ready_for_probe`
- quality_dataset_row_count: `569`
- quality_dataset_quality_probe_row_count: `38`
- quality_probe_status: `proposal_quality_axes_insufficient_for_selector_review`
- quality_probe_best_probe: `candidate_move_frame_source`
- quality_probe_best_positive_recall: `0.6333333333333333`
- quality_probe_best_negative_suppression: `0.625`
- quality_probe_ready_for_selector_review: `False`
- quality_decision_status: `candidate_proposal_quality_not_selector_ready`
- quality_decision_more_blind_label_farming_allowed: `False`
- source_design_status: `broader_strategy_sequence_candidate_source_design_ready`
- source_design_implementation_allowed: `False`
- plan_capsule_source_status: `plan_capsule_sequence_observation_source_schema_ready_but_stage7_only`
- broader_strategy_source_status: `broader_strategy_observation_source_schema_ready_but_stage7_only`
- source_review_status: `source_reviews_complete_runtime_expansion_not_authorized`
- source_review_implementation_allowed: `False`
- protected_monitor_expansion_status: `protected_strategy_monitor_frames_expanded_non_causal`
- protected_monitor_expansion_frame_count: `85`
- protected_monitor_expansion_stage7_challenge_row_count: `0`
- protected_monitor_quality_status: `protected_strategy_monitor_frames_have_monitor_signal`
- protected_monitor_quality_strong_failure_family_count: `1`
- repair_monitor_review_status: `protected_repair_monitor_observation_source_review_ready`
- repair_monitor_review_implementation_authorized: `False`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Arbitration Missing-Feature Gate

- dataset_record_count: `33`
- dataset_proposal_count: `87`
- dataset_records_by_source_stage: `{'stage4': 6, 'stage5': 8, 'stage6': 10, 'stage7': 9}`
- dataset_records_with_terminal_context: `33`
- probe_status: `missing_feature_first`
- probe_next_step: `Propose non-causal terminal/affordance candidates and a separability audit.`
- probe_raw_global_provider_hit_rate: `0.9285714285714286`
- probe_visible_heuristic_hit_rate: `0.07142857142857142`
- probe_provider_local_rank1_coverage_rate: `1.0`
- probe_stage7_record_count: `9`
- probe_missing_terms_obvious: `True`
- probe_stage7_failures_cluster_by_phase_boundary: `True`
- decision_status: `missing_feature_first`
- decision_next_class: `non_causal_terminal_affordance_candidate_audit`
- decision_stop_after_next_class: `True`
- missing_feature_candidate_count: `6`
- missing_feature_challenge_family_count: `6`
- missing_feature_recommended_next_step: `stop_for_architecture_review_before_any_terminal_or_affordance_runtime_sandbox`
- runtime_work_allowed: `False`
- runtime_arbiter_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Strategy Monitor Maturity Evidence

- plan_do_not_implement_as_causal_affordances: `True`
- records_dataset_record_count: `33`
- records_monitor_definition_count: `5`
- records_monitor_record_count: `108`
- records_by_monitor_type: `{'OwnerExitMonitor': 25, 'PhaseBoundaryMonitor': 52, 'PlanSelectionNeededMonitor': 9, 'RepairNeededMonitor': 22}`
- companion_terms_causal_terms_authorized: `False`
- companion_terms_runtime_arbiter_authorized: `False`
- companion_terms_stage7_repair_authorized: `False`
- companion_audit_v0_all_terms_available: `False`
- visible_terms_record_count: `33`
- visible_terms_term_names: `['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'box_area_no_longer_decision_relevant', 'post_plan_stagnation', 'local_provider_competition_failed']`
- companion_audit_v1_all_terms_available: `False`
- companion_audit_v1_visible_terms_applied: `True`
- companion_audit_v1_visible_term_count: `6`
- companion_audit_v1_still_missing_term_count: `11`
- maturity_term_count: `6`
- maturity_status_counts: `{'context_feature': 2, 'internal_terminal_candidate': 2, 'monitor_candidate': 1, 'too_broad': 1}`
- maturity_causal_ready_terms: `[]`
- maturity_strongest_internal_terminal_candidates: `['post_plan_stagnation', 'local_provider_competition_failed']`
- maturity_recommended_next_step: `broader_evidence_collection_or_internal_monitor_design_review`
- runtime_work_allowed: `False`
- runtime_terminals_allowed: `False`
- runtime_arbiter_allowed: `False`
- monitor_to_provider_routing_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Internal Terminal Readiness Evidence

- feature_candidate_all_non_causal: `True`
- feature_candidate_count: `6`
- feature_candidate_sandbox_ready_candidate_ids: `[]`
- candidate_spec_count: `4`
- candidate_terminal_ids: `['terminal.krk.local_provider_competition_failed', 'terminal.krk.post_plan_stagnation', 'terminal.krk.box_shrink_owner_exit_pressure', 'terminal.krk.repair_needed_monitor']`
- candidate_maturity_statuses: `['internal_terminal_candidate', 'internal_terminal_candidate', 'needs_more_evidence', 'monitoring_only']`
- validation_terminal_count: `4`
- validation_record_count: `30`
- validation_causal_ready_terminals: `[]`
- validation_all_causal_use_blocked: `True`
- evidence_terminal_count: `4`
- evidence_combined_record_count: `24`
- evidence_causal_ready_terminals: `[]`
- evidence_monitoring_only_candidates: `['terminal.krk.box_shrink_owner_exit_pressure', 'terminal.krk.repair_needed_monitor']`
- evidence_stage7_only_candidates: `['terminal.krk.local_provider_competition_failed', 'terminal.krk.post_plan_stagnation', 'terminal.krk.box_shrink_owner_exit_pressure']`
- evidence_all_causal_ready_false: `True`
- design_review_causal_ready_terminals: `[]`
- design_review_all_causal_ready_false: `True`
- design_review_recommended_next_step: `broader_replay_free_monitor_evidence_collection_or_review`
- runtime_work_allowed: `False`
- runtime_terminals_allowed: `False`
- causal_affordances_allowed: `False`
- runtime_arbiter_allowed: `False`
- monitor_to_provider_routing_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Repair-Monitor Trace-Feature Evidence

- smoke_status: `repair_monitor_observation_source_wired_default_off_equivalent`
- smoke_case_count: `3`
- smoke_repair_monitor_frame_count: `3`
- smoke_selected_move_provider_delta_count: `0`
- smoke_invariant_failure_count: `0`
- smoke_stage7_case_count: `0`
- coverage_status: `repair_monitor_observation_source_coverage_ready_for_guarded_analysis`
- broadened_status: `repair_monitor_observation_source_broadened_default_off_equivalent`
- broadened_case_count: `6`
- broadened_repair_monitor_frame_count: `6`
- broadened_selected_move_provider_delta_count: `0`
- broadened_stage7_case_count: `0`
- quality_status: `repair_monitor_observation_source_quality_trace_only_retained`
- quality_source_stable: `True`
- quality_risk_term_set_count: `1`
- trace_features_status: `repair_monitor_trace_features_folded_non_causal`
- trace_features_trace_frame_count: `6`
- trace_features_stage7_trace_frame_count: `0`
- trace_features_selector_training_row_count: `0`
- integration_review_status: `strategy_sequence_trace_features_integrated_selector_still_blocked`
- integration_review_trace_integration_safe: `True`
- dataset_design_status: `strategy_sequence_dataset_design_v2_ready`
- dataset_design_implementation_allowed: `False`
- dataset_v2_status: `strategy_sequence_dataset_v2_refreshed_non_causal_selector_blocked`
- dataset_v2_row_count: `262`
- dataset_v2_runtime_trace_feature_row_count: `6`
- dataset_v2_selector_training_row_count: `0`
- dataset_v2_stage7_readiness_training_row_count: `0`
- dataset_v2_quality_status: `strategy_sequence_dataset_v2_quality_candidate_generation_ready_selector_blocked`
- dataset_v2_quality_runtime_flags_false: `True`
- dataset_v2_quality_selector_rows_absent: `True`
- refresh_probe_status: `candidate_generation_refresh_underpowered_selector_blocked`
- capacity_manifest_status: `candidate_generation_capacity_evidence_manifest_ready`
- capacity_manifest_labels_run_by_this_artifact: `False`
- capacity_manifest_stage7_job_count: `0`
- capacity_labels_status: `candidate_generation_capacity_evidence_labels_completed`
- capacity_labels_stage7_label_count: `0`
- dataset_v2_capacity_merged_status: `strategy_sequence_dataset_v2_capacity_merged_non_causal`
- refresh_after_labels_status: `candidate_generation_refresh_supported_selector_blocked`
- refresh_after_labels_positive_recall: `0.7368421052631579`
- refresh_after_labels_negative_suppression: `1.0`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Stage 5/6 Candidate-Generation Refresh Evidence

- review_status: `stage5_6_candidate_generation_refresh_review_ready`
- review_runtime_review_ready: `True`
- review_implementation_authorized: `False`
- review_runtime_candidate_generator_refresh_allowed: `False`
- smoke_status: `stage5_6_candidate_generation_refresh_wired_default_off_equivalent`
- smoke_case_count: `2`
- smoke_refresh_frame_count: `13`
- smoke_selected_move_provider_delta_count: `0`
- smoke_invariant_failure_count: `0`
- smoke_stage7_case_count: `0`
- coverage_status: `stage5_6_refresh_coverage_ready_for_broadened_analysis`
- coverage_refresh_frame_count: `13`
- coverage_stage7_case_count: `0`
- broadened_status: `stage5_6_candidate_generation_refresh_broadened_default_off_equivalent`
- broadened_case_count: `4`
- broadened_case_count_by_stage: `{'stage5': 3, 'stage6': 1}`
- broadened_refresh_frame_count: `38`
- broadened_selected_move_provider_delta_count: `0`
- broadened_invariant_failure_count: `0`
- broadened_stage7_case_count: `0`
- quality_status: `stage5_6_candidate_generation_refresh_quality_trace_only_retained`
- quality_trace_usable_for_candidate_generation_context: `True`
- quality_stage7_case_count: `0`
- trace_features_status: `stage5_6_refresh_trace_features_folded_non_causal`
- trace_features_trace_frame_count: `38`
- trace_features_stage_counts: `{'stage5': 37, 'stage6': 1}`
- trace_features_stage7_trace_frame_count: `0`
- trace_features_selector_training_row_count: `0`
- trace_features_candidate_generation_training_row_count: `0`
- dataset_design_v3_status: `strategy_sequence_dataset_design_v3_ready`
- dataset_design_v3_implementation_allowed: `False`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Cross-Stage Candidate-Generation Scope Evidence

- cross_stage_label_probe_status: `candidate_generation_refresh_supported_selector_blocked`
- cross_stage_label_probe_best_policy: `stage_family_pure_positive_with_support_2`
- cross_stage_label_probe_positive_recall: `0.7692307692307693`
- cross_stage_label_probe_negative_suppression: `1.0`
- cross_stage_label_probe_capacity_row_count: `36`
- cross_stage_label_probe_guardrails_allowed: `False`
- cross_stage_label_probe_selector_allowed: `False`
- cross_stage_label_probe_promotion_allowed: `False`
- capacity_review_status: `cross_stage_capacity_review_recommends_stratified_capacity_manifest`
- capacity_review_capacity_row_count: `28`
- capacity_manifest_status: `cross_stage_capacity_manifest_ready_partial_target_coverage`
- capacity_manifest_labels_run_by_this_artifact: `False`
- capacity_manifest_job_count: `8`
- capacity_manifest_stage7_job_count: `0`
- capacity_labels_status: `cross_stage_capacity_labels_completed`
- capacity_labels_label_count: `8`
- capacity_labels_stage7_label_count: `0`
- dataset_cross_stage_merged_status: `strategy_sequence_dataset_v2_cross_stage_capacity_merged_non_causal`
- dataset_cross_stage_merged_row_count: `282`
- dataset_cross_stage_merged_selector_training_row_count: `0`
- dataset_cross_stage_merged_stage7_readiness_training_row_count: `0`
- label_outcome_review_status: `cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked`
- scope_review_status: `stage_conditioned_candidate_generation_scope_review_ready`
- stage_conditioned_benchmark_status: `stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked`
- stage_conditioned_benchmark_best_policy: `stage_conditioned_positive_scope`
- stage_conditioned_benchmark_positive_recall: `0.7692307692307693`
- stage_conditioned_benchmark_negative_suppression: `1.0`
- stage_conditioned_benchmark_stage4_positive_recall: `0.0`
- stage_conditioned_benchmark_stage5_6_positive_recall: `1.0`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Objective Lineage Evidence

- ownership_recovery_status: `ownership_label_recovery_seed_manifest_ready_selector_blocked`
- ownership_recovery_joined_state_count: `4`
- ownership_recovery_selected_failure_with_visible_positive_count: `2`
- seed_manifest_v0_status: `selector_objective_seed_manifest_ready_non_causal`
- seed_manifest_v0_seed_row_count: `4`
- seed_probe_v0_status: `selector_objective_seed_probe_underpowered_semantics_confirmed`
- collection_manifest_status: `joined_trace_ownership_collection_manifest_ready_for_review`
- collection_review_status: `joined_trace_ownership_observation_collection_review_ready`
- collection_review_implementation_authorized: `False`
- joined_collection_status: `joined_trace_ownership_collection_complete_seed_improved`
- joined_collection_collected_row_count: `8`
- joined_collection_generated_frame_count: `80`
- joined_collection_selected_move_delta_count: `0`
- joined_collection_selected_provider_delta_count: `0`
- joined_collection_score_delta_count: `0`
- joined_collection_routing_delta_count: `0`
- seed_manifest_v1_status: `selector_objective_seed_manifest_v1_ready_non_causal`
- seed_manifest_v1_seed_row_count: `12`
- seed_probe_v1_status: `selector_objective_seed_ready_for_non_causal_feature_probe`
- feature_probe_status: `selector_objective_feature_probe_no_runtime_ready_features`
- feature_probe_runtime_threshold_passing_model_count: `0`
- feature_probe_review_status: `selector_feature_probe_blocks_runtime_needs_diverse_evidence`
- feature_probe_review_best_switch_recall: `0.75`
- feature_probe_review_best_preserve_recall: `1.0`
- diversity_gap_status: `selector_objective_diversity_gap_requires_stage4_scope_review`
- diversity_gap_remaining_stage4_selected_failure_count: `6`
- diversity_gap_remaining_stage5_6_selected_failure_count: `0`
- stage4_scope_review_status: `stage4_joined_trace_ownership_scope_review_ready`
- stage4_scope_review_implementation_authorized: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Selector Objective Evidence

- stage4_collection_status: `stage4_joined_trace_ownership_collection_complete`
- stage4_collection_collected_row_count: `6`
- stage4_collection_generated_frame_count: `170`
- stage4_collection_switch_contrast_with_positive_capacity_count: `1`
- stage4_collection_default_off_equivalence_passed: `True`
- stage4_collection_selected_move_delta_count: `0`
- stage4_collection_selected_provider_delta_count: `0`
- stage4_collection_score_delta_count: `0`
- stage4_collection_routing_delta_count: `0`
- seed_manifest_v2_status: `selector_objective_seed_manifest_v2_ready_non_causal`
- seed_manifest_v2_seed_row_count: `18`
- seed_manifest_v2_objective_channel_counts: `{'candidate_switch_contrast_seed': 5, 'failure_context_without_candidate_seed': 5, 'safe_preservation_contrast_seed': 8}`
- seed_probe_v2_status: `selector_objective_seed_probe_v2_ready_for_non_causal_benchmark`
- selector_benchmark_v2_status: `selector_objective_benchmark_v2_runtime_feature_review_ready`
- selector_benchmark_v2_best_runtime_model: `visible_failure_risk_heuristic_v2`
- selector_benchmark_v2_runtime_threshold_passing_model_count: `1`
- selector_benchmark_review_status: `selector_objective_benchmark_review_ready_for_independent_validation`
- independent_validation_manifest_status: `selector_objective_independent_validation_manifest_ready`
- independent_validation_manifest_job_count: `10`
- independent_validation_manifest_job_count_by_stage: `{'stage4': 7, 'stage6': 3}`
- independent_validation_manifest_stage7_training_rows: `0`
- independent_validation_labels_status: `selector_objective_independent_validation_labels_collected`
- independent_validation_labels_label_count: `10`
- independent_validation_labels_selector_training_row_count: `0`
- independent_validation_labels_stage7_training_row_count: `0`
- independent_validation_status: `selector_objective_independent_validation_underpowered`
- independent_validation_target_counts: `{'preserve': 10}`
- independent_validation_blocker_status: `selector_objective_runtime_blocked_pending_independent_switch_contrasts`
- independent_validation_runtime_selector_blocked: `True`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Stage 4 First-Move Diagnostic Evidence

- failure_discovery_status: `stage4_failure_discovery_collapsed_to_seed_state`
- failure_packet_count: `32`
- unique_failure_state_move_count: `1`
- sequence_review_status: `stage4_caveat_sequence_followup_gap_review_ready`
- sequence_review_primary_diagnosis: `stage4_sequence_followup_gap_single_state`
- sequence_candidate_status: `stage4_first_move_ranking_gap`
- sequence_candidate_converting_first_move_count: `7`
- feature_review_status: `stage4_first_move_feature_contrast_found_single_state`
- feature_review_positive_terms: `['king_destination_c_file', 'rook_mid_rank8_cut_candidate']`
- feature_review_failure_terms: `['king_destination_a7', 'rook_far_rank8_drift_candidate']`
- stratified_validation_status: `stage4_stratified_contrast_validation_supports_first_move_ranking_gap`
- stratified_validation_gap_variant_count: `4`
- runtime_review_status: `stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval`
- runtime_review_implementation_authorized: `False`
- sequence_control_dataset_status: `krk_sequence_control_contrast_dataset_ready_non_causal`
- sequence_control_dataset_row_count: `76`
- sequence_control_dataset_runtime_authorization_row_count: `0`
- sequence_control_probe_status: `sequence_control_dataset_ready_for_broader_sequence_policy_review`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Candidate Generation Training-Refresh Evidence

- dataset_v3_status: `strategy_sequence_dataset_v3_refreshed_non_causal_selector_blocked`
- dataset_v3_row_count: `320`
- dataset_v3_candidate_generation_training_row_count: `26`
- dataset_v3_selector_training_row_count: `0`
- context_benchmark_status: `candidate_generation_v3_context_useful_selector_still_blocked`
- context_benchmark_stage_family_positive_capacity_recall_from_trace: `0.7692307692307693`
- runtime_boundary_status: `candidate_generation_v3_runtime_boundary_context_ready_selector_blocked`
- runtime_boundary_new_runtime_behavior_allowed: `False`
- training_refresh_design_v2_status: `candidate_generation_training_refresh_design_ready`
- training_refresh_design_v2_runtime_candidate_generator_refresh_allowed: `False`
- training_refresh_design_v2_selector_allowed: `False`
- training_refresh_design_v2_guardrails_allowed: `False`
- training_refresh_design_v2_promotion_allowed: `False`
- training_refresh_design_status: `candidate_generation_training_refresh_v3_design_ready`
- training_refresh_design_implementation_allowed: `False`
- benchmark_status: `candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed`
- benchmark_best_policy: `trace_stage_family_context`
- benchmark_positive_capacity_recall: `0.7692307692307693`
- benchmark_negative_capacity_suppression: `1.0`
- benchmark_thresholds_met: `True`
- runtime_review_status: `candidate_generation_training_refresh_runtime_review_ready`
- runtime_review_ready: `True`
- runtime_review_candidate_generation_allowed_by_packet: `False`
- runtime_review_implementation_authorized: `False`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Candidate Generation Trace-Context Evidence

- refresh_sandbox_status: `candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis`
- refresh_sandbox_generated_frame_count: `25`
- refresh_sandbox_default_off_equivalence_passed: `True`
- refresh_coverage_status: `candidate_generation_refresh_coverage_ready_for_trace_dataset_refresh`
- refresh_coverage_exact_positive_capacity_recall: `1.0`
- refresh_trace_features_status: `candidate_generation_refresh_trace_features_folded_non_causal`
- refresh_trace_features_trace_frame_count: `25`
- refresh_trace_features_stage7_trace_frame_count: `0`
- refresh_trace_features_selector_training_row_count: `0`
- dataset_v4_status: `strategy_sequence_dataset_v4_refreshed_non_causal_selector_blocked`
- dataset_v4_row_count: `307`
- v4_boundary_status: `candidate_generation_v4_next_runtime_boundary_context_ready_selector_blocked`
- source_gap_manifest_status: `candidate_source_gap_manifest_ready_non_causal`
- source_gap_exact_missing_positive_capacity_count: `21`
- exact_trace_runtime_review_status: `exact_trace_enrichment_runtime_review_ready`
- exact_trace_runtime_review_implementation_authorized: `False`
- exact_trace_sandbox_status: `exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis`
- exact_trace_sandbox_generated_frame_count: `3`
- exact_trace_coverage_exact_gap_recall: `1.0`
- dataset_v5_status: `strategy_sequence_dataset_v5_refreshed_non_causal_selector_blocked`
- dataset_v5_row_count: `310`
- dataset_v5_selector_training_row_count: `0`
- v5_context_benchmark_status: `candidate_generation_v5_context_useful_selector_still_blocked`
- v5_exact_positive_capacity_recall_from_candidate_generation_trace: `0.3076923076923077`
- v5_boundary_status: `candidate_generation_v5_next_boundary_context_improved_selector_blocked`
- v5_boundary_implement_new_runtime_sandbox: `False`
- runtime_work_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Control Plane Contract Lineage

- passive_contract_lineage_ready: `True`
- architecture_goal_id: `krk_control_plane_evidence_contract_v0`
- architecture_goal_type: `non_causal_data_contract_and_review`
- architecture_must_remain_non_causal: `True`
- architecture_runtime_defaults_must_remain_unchanged: `True`
- contract_recommended_next_slice: `control_plane_manifest_from_existing_artifacts_v0`
- contract_causal_status: `non_causal_schema_contract`
- manifest_causal_status: `non_causal_manifest`
- manifest_records_from_existing_artifacts_only: `True`
- manifest_new_playouts_added: `0`
- manifest_missing_required_fields_after_manifest: `[]`
- manifest_recommended_next_slice: `stratified_control_plane_gap_report_v0`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Control Plane Frame Export

- passive_frame_export_ready: `True`
- gap_report_next_slice_id: `export_replay_free_control_plane_frames_v0`
- gap_report_new_playouts_allowed: `False`
- gap_report_new_playouts_added: `0`
- frame_export_frame_count: `33`
- frame_export_frames_by_source_stage: `{'stage4': 6, 'stage5': 8, 'stage6': 10, 'stage7': 9}`
- frame_export_new_playouts_added: `0`
- frame_quality_next_slice_id: `control_plane_frame_dedupe_and_quality_filters_v0`
- frame_quality_runtime_sandbox: `blocked`
- frame_quality_stage7_promotion: `blocked`
- frame_quality_stage8_training: `blocked`
- filtered_strategy_ready_frame_count: `24`
- filtered_stage7_boundary_heldout_frame_count: `7`
- forced_control_labels_attached: `12`
- forced_control_missing_label_job_ids: `[]`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Control Plane Strategy Baseline

- passive_strategy_baseline_ready: `True`
- provider_label_coverage_plan_ready: `True`
- provider_label_coverage_status: `sufficient_for_current_small_probe`
- provider_label_coverage_benchmark_frame_count: `28`
- provider_label_coverage_known_provider_mate_count: `14`
- provider_label_coverage_recommended_next_slice: `offline_strategy_arbitration_baseline_v1`
- probe_status: `provider_labels_sufficient_for_small_probe`
- probe_causal_next_step_allowed: `False`
- probe_recommended_next_slice: `offline_strategy_arbitration_baseline_v1`
- probe_strategy_benchmark_frame_count: `24`
- probe_provider_labeled_frame_count: `24`
- probe_frames_with_known_provider_mate: `12`
- baseline_status: `strategy_arbitration_promising`
- baseline_causal_next_step_allowed: `False`
- baseline_recommended_next_class: `non_causal_strategy_arbiter_sandbox_design`
- baseline_strategy_benchmark_frame_count: `24`
- baseline_frames_with_provider_mate: `12`
- baseline_frames_with_only_provider_max_plies: `12`
- baseline_stage_counts: `{'stage4': 6, 'stage5': 8, 'stage6': 10}`
- baseline_selector_names: `['raw_global_score', 'normalized_score', 'provider_local_rank', 'visible_context_heuristic', 'stage_prior_heuristic']`
- baseline_selector_hit_rates: `{'raw_global_score': 1.0, 'normalized_score': 1.0, 'provider_local_rank': 1.0, 'visible_context_heuristic': 0.0, 'stage_prior_heuristic': 1.0}`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Control Plane Stage 7 Boundary

- passive_stage7_boundary_ready: `True`
- boundary_decision_status: `box_shrink_reclassified_as_local_evidence_handoff_trigger`
- boundary_recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- stage7_clean_success_controls_met: `True`
- stage7_clean_hard_negatives_met: `True`
- stage7_clean_review_status: `stage7_clean_control_collection_closed_heldout_only`
- strategy_sequence_inventory_status: `replay_free_inventory_state_holdout_gap_blocks_runtime`
- strategy_ready_frame_count: `24`
- strategy_ready_by_stage: `{'stage4': 6, 'stage5': 8, 'stage6': 10}`
- stage7_boundary_heldout_frame_count: `7`
- strategy_probe_status: `provider_labels_sufficient_for_small_probe`
- strategy_baseline_status: `strategy_arbitration_promising`
- approval_receipt_present: `False`
- approval_receipt_valid: `False`
- runner_execution_requested: `False`
- runner_collection_run_allowed: `False`
- runner_processed_job_count: `0`
- runner_executed_job_count: `0`
- runtime_behavior_changed: `False`
- runtime_defaults_changed: `False`
- runtime_selector_implemented: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- gameplay_topology_mutation: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Current Control Plane Gate

- status: `krk_control_plane_waiting_on_explicit_gate_choice`
- approval_option_ids: `['approve_stage4_first_move_contrast_sandbox', 'approve_protected_plan_window_failure_contrast_collection']`
- protected_failure_contrast_collection_option_available: `True`
- protected_failure_contrast_collection_command_available: `True`
- protected_failure_contrast_collection_option_id: `approve_protected_plan_window_failure_contrast_collection`
- protected_failure_contrast_collection_blocked_by_option_id: `None`

## Blockers

- `protected_plan_window_failure_contrast_collection_pending_explicit_approval`

## Approval Gates

- `stage7_diverse_clean_label_execution`: The Stage 7 clean success-control gate is already closed; additional Stage 7 labels are not the primary current unblocker.
- `protected_plan_window_failure_contrast_collection`: The sequence-policy benchmark is mixed/underpowered on protected plan-window failures; bounded observation-only collection is the current explicit gate.
- `stage4_first_move_contrast_sandbox`: Stage 4 has a reviewed default-off first-move contrast sandbox scope, but implementation still requires explicit sandbox approval.
- `stage8_training`: Protected plan-window failure-contrast evidence is not integrated; Stage 8 training remains blocked even though Stage 7 held-out controls are balanced.

## Boundary Check

- checked_flag_count: `2669`
- violation_count: `0`
