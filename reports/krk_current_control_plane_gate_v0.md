# KRK Current Control-Plane Gate v0

Status: `krk_control_plane_waiting_on_explicit_gate_choice`

## Current State

- protected_stack: `retry1_stage5_6_active_manifest_validated`
- stage4: `first_move_contrast_runtime_review_ready_pending_explicit_approval`
- stage7: `heldout_clean_success_controls_insufficient_sampling_manifest_ready`
- stage7_label_execution_readiness: `stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval`
- stage7_label_output_integration: `stage7_diverse_clean_sampling_outputs_pending`
- stage7_label_runner: `stage7_diverse_clean_sampling_runner_dry_run_ready`
- stage7_label_runner_output_validation_status: `stage7_diverse_clean_sampling_outputs_validation_pending`
- stage7_label_runner_invalid_existing_output_count: `0`
- stage7_label_runner_processed_job_count: `0`
- stage7_label_runner_executed_job_count: `0`
- stage7_label_runner_skipped_existing_output_count: `0`
- stage7_post_label_outcome: `post_label_outcome_pending_explicit_label_outputs`
- protected_plan_window_evidence: `available_non_causal`
- sequence_policy: `sequence_policy_benchmark_blocked_pending_clean_stage7_controls`
- sequence_policy_inputs: `sequence_policy_benchmark_inputs_blocked_pending_stage7_success_controls`
- stage8: `blocked`
- runtime_selector: `blocked`

## Approval Options

### approve_stage4_first_move_contrast_sandbox

- artifact: `reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.md`
- status: `stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval`
- allows: default-off Stage 4 CandidateMoveFrame first-move contrast sandbox only
- recommended_if: you want to reduce the known Stage 4 h40 caveat now
- does_not_allow:
  - default enablement
  - exact-state or exact-move runtime exception
  - selector training
  - broad stage0 penalty
  - provider suppression
  - Stage 7 promotion
  - Stage 8 training

### approve_stage7_diverse_clean_label_run

- artifact: `reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.md`
- status: `stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval`
- allows: run 8 bounded h40 clean Stage 7 label jobs, 64 samples total
- recommended_if: you want to fill the Stage 7 clean success-control gap before broader sequence-policy benchmarking
- safety_scope:
  - resume_safe: `True`
  - skip_existing_outputs_by_default: `True`
  - invalid_existing_outputs_block_without_overwrite: `True`
  - stage7_training_rows: `0`
- does_not_allow:
  - runtime behavior
  - selector training
  - Stage 7 promotion
  - Stage 8 training
  - Stage 7 repair flags

### defer_runtime_and_labels_review_cross_stage_plan_capsule_evidence

- artifact: `reports/strategy_arbitration/krk_protected_plan_window_frames_v0.md`
- status: `sequence_policy_benchmark_blocked_pending_clean_stage7_controls`
- allows: non-causal protected Stage 4/5/6 plan-window evidence review only
- recommended_if: already executed replay-free; remaining sequence-policy gap is Stage 7 clean success controls
- does_not_allow:
  - runtime selector
  - label execution
  - Stage 7 promotion
  - Stage 8 training

## Recommendation

- if_no_user_approval: `stop_at_gate_or_design_non_causal_sequence_policy_only`
- if_runtime_approved: `implement_stage4_default_off_first_move_contrast_sandbox`
- if_labels_approved: `run_stage7_diverse_clean_sampling_manifest_and_recover_controls`
- reason: Replay-free protected plan-window evidence now satisfies the Stage 4/5/6 cross-stage side. The remaining empirical blocker for the sequence-policy benchmark is clean Stage 7 success controls, while Stage 4 runtime work still requires explicit sandbox approval.
