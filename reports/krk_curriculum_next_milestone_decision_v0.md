# KRK Curriculum Next Milestone Decision v0

Status: `krk_curriculum_next_milestone_review_ready`

- Decision states: `['clean_stack_adoption_rejected_or_deferred', 'stage4_caveat_reduction_path_identified', 'stage7_unlock_path_identified', 'stage8_remains_blocked_with_review']`
- Protected stack status: `current_protected_stack_unchanged_retry1_review_ready_only`
- Stage 4 status: `stage4_candidate_generation_gap_with_known_residual_guardrail`
- Stage 7 status: `stage7_unlock_path_identified_broader_sequence_control_not_micro_repair`
- Stage 8 status: `stage8_remains_blocked_with_review`

Recommended path forward:

- Choose whether to explicitly approve rollback-aware retry1 protected Stage 5/6 adoption.
- If approval is not granted, keep current protected stack and continue non-causal Stage 4/7 evidence work.
- For Stage 4, the next useful evidence is the already-reviewed observation-only trace collection scope, capped and non-causal.
- For Stage 7, stop micro-repairs and build broader sequence-policy/strategy-arbitration evidence with Stage 7 held out.

Still forbidden:

- protected-stack replacement without explicit approval
- Stage 7 promotion
- Stage 8 training
- runtime selector implementation
- runtime DTM/tablebase
- gameplay topology mutation
- capacity labels as ownership labels
