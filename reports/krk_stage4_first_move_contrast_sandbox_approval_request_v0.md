# KRK Stage 4 First-Move Contrast Sandbox Approval Request v0

Status: `stage4_first_move_contrast_sandbox_approval_request_ready`

This is a passive request packet only. It does not approve or implement runtime behavior, change defaults, train selectors, promote Stage 7, or train Stage 8.

## Exact Approval Request

> Approve default-off Stage 4 first-move contrast sandbox implementation only within krk_stage4_first_move_contrast_runtime_review_packet_v0: CandidateMoveFrame legal first-move hypotheses in KRK Stage 4 edge_trap_wrong_tempo contexts; no default enablement, no exact-state or exact-move exception, no runtime DTM/tablebase lookup, no hidden controller, no selector training, no provider suppression, no broad stage0 penalty, no gameplay topology mutation, no Stage 7 promotion, and no Stage 8 training.

## Summary

- runtime_review_ready: `True`
- runtime_review_status: `stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval`
- evidence_passed: `True`
- implementation_authorized_by_runtime_packet: `False`
- requires_explicit_approval_before_implementation: `True`
- default_off: `True`
- default_enabled: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- hidden_python_controller: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Required Scope If User Approves

- approval_id: `approve_stage4_first_move_contrast_sandbox`
- review_packet: `reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json`
- review_packet_status: `stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval`
- sandbox_id: `sandbox.krk.stage4_first_move_contrast_v0`
- default_off: `True`

## Blockers

- none

## Decision

- recommended_next_step: `user_may_explicitly_approve_stage4_sandbox_only_if_runtime_work_is_intended`
- implementation_allowed_by_this_request: `False`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- stage7_promotion_allowed: `false`
- stage8_training_allowed: `false`
