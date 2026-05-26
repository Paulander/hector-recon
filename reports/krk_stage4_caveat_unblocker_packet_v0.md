# KRK Stage 4 Caveat Unblocker Packet v0

Status: `stage4_caveat_unblocker_ready_pending_explicit_runtime_approval`

This packet is non-causal. It consolidates Stage 4 caveat evidence and the reviewed runtime-sandbox approval boundary, but it does not implement or authorize runtime behavior.

## Current Stage 4 Status

- control_plane_option_status: `stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval`
- control_plane_option_artifact: `reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.md`
- control_plane_approval_request_artifact: `reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md`
- runtime_review_ready: `True`
- approval_request_status: `stage4_first_move_contrast_sandbox_approval_request_ready`
- approval_request_blockers: `[]`
- approval_request_created: `False`
- implementation_authorized_by_approval_request: `False`
- approval_scope_id: `default_off_stage4_candidate_move_first_move_contrast_sandbox_only`
- approval_scope_default_off: `True`
- approval_scope_default_enabled: `False`
- approval_scope_runtime_dtm_or_tablebase_lookup: `False`
- approval_scope_hidden_python_controller: `False`
- approval_scope_selector_training_allowed: `False`
- implementation_authorized_by_review_packet: `False`
- requires_explicit_approval_before_implementation: `True`
- caveat_control_status: `stage4_caveat_reproduces_in_base_control_no_overlay_regression`
- sequence_review_status: `stage4_caveat_sequence_followup_gap_review_ready`
- stratified_validation_status: `stage4_stratified_contrast_validation_supports_first_move_ranking_gap`
- sequence_contrast_status: `sequence_control_dataset_ready_for_broader_sequence_policy_review`

## Evidence

- base_control_reproduces_failure: `True`
- single_unique_failure: `True`
- target_state_id: `state.44938ccb8ab7`
- target_fen: `1R6/1K6/8/k7/8/8/8/8 w - - 0 1`
- target_selected_move: `b8h8`
- stratified_gap_variant_count: `4`
- stratified_candidate_row_count: `48`
- stage4_forced_candidate_count: `48`
- stage4_positive_count: `26`
- stage4_failure_count: `22`

## Approved Scope If Explicitly Approved Later

- scope: `default_off_stage4_candidate_move_first_move_contrast_sandbox_only`
- candidate_source: `CandidateMoveFrame legal first-move hypotheses`
- direct_request: `False`
- score_delta: `0.0`
- default_enabled: `False`
- exact_state_or_exact_move_exception: `False`
- selector_training: `False`
- provider_suppression: `False`
- stage7_promotion: `False`
- stage8_training: `False`

## Forbidden Without Later Explicit Approval

- runtime sandbox implementation
- default enablement
- exact-state or exact-move runtime exception
- selector training
- broad stage0 penalty
- provider suppression
- Stage 7 promotion
- Stage 8 training

## Blockers

- none

## Decision

- recommended_next_step: `explicitly_approve_stage4_first_move_contrast_sandbox_or_defer_stage4_caveat`
- implementation_allowed_by_this_packet: `False`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- stage7_promotion_allowed: `false`
- stage8_training_allowed: `false`
