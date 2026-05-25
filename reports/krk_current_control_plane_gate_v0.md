# KRK Current Control-Plane Gate v0

Status: `krk_control_plane_waiting_on_explicit_gate_choice`

## Current State

- protected_stack: `retry1_stage5_6_active_manifest_validated`
- stage4: `first_move_contrast_runtime_review_ready_pending_explicit_approval`
- stage7: `heldout_clean_success_controls_insufficient_sampling_manifest_ready`
- sequence_policy: `sequence_policy_benchmark_blocked_pending_clean_stage7_controls`
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
- status: `stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval`
- allows: run 8 bounded h40 clean Stage 7 label jobs, 64 samples total
- recommended_if: you want to fill the Stage 7 clean success-control gap before broader sequence-policy benchmarking
- does_not_allow:
  - runtime behavior
  - selector training
  - Stage 7 promotion
  - Stage 8 training
  - Stage 7 repair flags

### defer_runtime_and_labels_review_cross_stage_plan_capsule_evidence

- artifact: `reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.md`
- status: `sequence_policy_benchmark_blocked_pending_clean_stage7_controls`
- allows: non-causal cross-stage PlanCapsule/source evidence design only
- recommended_if: you want to avoid both current gates and only design further non-causal evidence
- does_not_allow:
  - runtime selector
  - label execution
  - Stage 7 promotion
  - Stage 8 training

## Recommendation

- if_no_user_approval: `stop_at_gate_and_report`
- if_runtime_approved: `implement_stage4_default_off_first_move_contrast_sandbox`
- if_labels_approved: `run_stage7_diverse_clean_sampling_manifest_and_recover_controls`
- reason: The broader sequence-policy design is also blocked on clean Stage 7 success controls or cross-stage PlanCapsule evidence; immediate empirical progress crosses either a runtime sandbox approval gate or a Stage 7 label-run approval gate.
