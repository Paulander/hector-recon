# KRK Curriculum Next Milestone Decision v0

Status: `krk_curriculum_next_milestone_review_ready`

- Decision states: `['clean_stack_adopted_and_validated', 'stage4_caveat_reduction_path_identified', 'stage7_unlock_path_identified', 'stage8_remains_blocked_with_review']`
- Protected stack status: `retry1_protected_stage5_6_stack_adopted_manifest_only`
- Stage 4 status: `stage4_candidate_generation_gap_with_known_residual_guardrail`
- Stage 7 status: `stage7_unlock_path_identified_broader_sequence_control_not_micro_repair`
- Stage 8 status: `stage8_remains_blocked_with_review`

Recommended path forward:

- Use the active retry1 Stage 5/6 protected-stack manifest as the current protected reference.
- Keep rollback paths preserved; do not copy, delete, or overwrite snapshot files.
- For Stage 4, the next useful evidence is the already-reviewed observation-only trace collection scope, capped and non-causal.
- For Stage 7, stop micro-repairs and build broader sequence-policy/strategy-arbitration evidence with Stage 7 held out.

Still forbidden:

- destructive snapshot replacement without rollback review
- Stage 7 promotion
- Stage 8 training
- runtime selector implementation
- runtime DTM/tablebase
- gameplay topology mutation
- capacity labels as ownership labels
