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
- expected_readiness_fingerprint: `ac2ce0ad75f392f73eb5b41cbc35b5a66661a01eb722963c2c1b6824124a9a25`
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

- checked_flag_count: `1338`
- violation_count: `0`
