# KRK Cross-Stage PlanCapsule Evidence Requirements v0

Status: `cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark`

This is a non-causal requirements artifact. It does not implement PlanCapsule runtime behavior, collect labels, train a selector, promote Stage 7, or train Stage 8.

## Current Readiness

- plan_capsule_stage7_only_evidence: `True`
- source_review_protected_cross_stage_evidence: `False`
- replay_free_protected_cross_stage_evidence: `True`
- cross_stage_sequence_evidence_met: `True`
- plan_capsule_policy_succeeded: `False`
- stage7_clean_success_controls_met: `True`
- stage7_clean_failure_controls_met: `True`
- sequence_policy_benchmark_ready: `True`
- sequence_policy_current_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered_blocked_pending_protected_failure_contrast_control_plane_gate_review`
- sequence_policy_passive_design_status: `non_causal_sequence_policy_design_review_needed`
- remaining_evidence_gap: `None`
- protected_failure_contrast_approval_request_status: `protected_plan_window_failure_contrast_approval_request_blocked`
- protected_failure_contrast_approval_request_blockers: `['protected_failure_contrast_execution_scope_not_ready']`
- protected_failure_contrast_approval_request_ready_for_collection: `False`
- protected_failure_contrast_collection_option_available: `False`
- protected_failure_contrast_collection_command_available: `False`
- protected_failure_contrast_collection_option_id: `None`
- protected_failure_contrast_collection_blocked_by_option_id: `review_protected_plan_window_failure_contrast_manifest`
- protected_failure_contrast_approval_receipt_blockers: `['approval_receipt_readiness_fingerprint_mismatch', 'approval_receipt_readiness_status_mismatch', 'approval_receipt_current_control_plane_approval_option_ids_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_command_available_mismatch', 'approval_receipt_protected_failure_contrast_collection_option_id_mismatch', 'approval_receipt_protected_failure_contrast_collection_blocked_by_option_id_mismatch']`
- control_plane_gate_status: `krk_control_plane_waiting_on_explicit_gate_choice`

## Required Evidence Frames

### stage4.first_move_or_wrong_tempo_plan_window

- source_stage: `stage4`
- purpose: test whether short plan windows can distinguish wrong-tempo first-move contrast from drift
- minimum_examples: `{'success': 4, 'failure': 4}`
- required_fields:
  - `plan_candidate_id`
  - `entry_terms_confirmed`
  - `first_move_candidate_terms`
  - `progress_terms_after_first_reply`
  - `abort_terms`
  - `handoff_target_if_any`
  - `h40_outcome_label`
  - `causal_status=non_causal`

### stage5.fence_handoff_plan_window

- source_stage: `stage5`
- purpose: verify that plan-window evidence preserves validated fence/handoff behavior
- minimum_examples: `{'success': 4, 'failure': 2}`
- required_fields:
  - `fence_contract_terms`
  - `handoff_packet_trace`
  - `plan_entry_or_abstain`
  - `safe_preservation_label`
  - `h40_outcome_label`
  - `causal_status=non_causal`

### stage6.drive_to_edge_plan_window

- source_stage: `stage6`
- purpose: verify that plan-window evidence does not override protected drive-to-edge overlay behavior
- minimum_examples: `{'success': 4, 'failure': 2}`
- required_fields:
  - `drive_progress_terms`
  - `owner_preservation_terms`
  - `candidate_handoff_terms`
  - `h40_outcome_label`
  - `causal_status=non_causal`

### stage7.heldout_post_box_plan_window

- source_stage: `stage7`
- purpose: held-out challenge only; evaluate whether cross-stage plan evidence explains post-box failures
- minimum_examples: `{'success': 5, 'failure': 5}`
- required_fields:
  - `post_box_entry_terms`
  - `progress_terms`
  - `exit_or_handoff_terms`
  - `stagnation_terms`
  - `h40_outcome_label`
  - `heldout_challenge=true`
  - `causal_status=non_causal`

## Acceptance Before Sequence-Policy Benchmark

- protected_stage4_5_6_frame_count_min: `20`
- stage7_heldout_success_min: `5`
- stage7_heldout_failure_min: `5`
- stage7_training_rows: `0`
- selector_training_rows: `0`
- runtime_authorization_rows: `0`
- plan_capsule_spec_causal: `False`
- dtm_runtime_lookup: `False`
- topology_mutation: `False`

## Non-Causal Collection Options

- `replay_free_protected_window_extraction`: recover plan-window terms from existing protected Stage 4/5/6 traces if available requires_approval=`False`
- `bounded_protected_trace_collection`: collect trace-only protected Stage 4/5/6 plan-window metadata with no score/routing effect requires_approval=`True`
- `approved_stage7_diverse_clean_label_run`: run the existing Stage 7 diverse clean sampling manifest to fill held-out success controls requires_approval=`True`

## Decision

- recommended_next_step: `review_non_causal_sequence_policy_benchmark_results`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
