# KRK Sequence-Control Contrast Probe v0

## Decision

- status: `sequence_control_dataset_ready_for_broader_sequence_policy_review`
- recommended_next_step: `review_current_sequence_policy_benchmark_and_protected_failure_contrast_gate`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`

## Summary

- row_count: `76`
- stage4_forced_candidate_count: `48`
- stage4_positive_count: `26`
- stage4_failure_count: `22`
- stage4_review_ready_pending_approval: `True`
- selector_switch_seed_count: `5`
- selector_preserve_seed_count: `8`
- stage7_dataset_success_control_count: `2`
- stage7_dataset_failure_control_count: `8`
- stage7_success_control_count: `11`
- stage7_success_controls_required: `5`
- stage7_failure_control_count: `39`
- stage7_failure_controls_required: `5`

## Readiness

- stage4_first_move_contrast_sandbox_review_ready: `True`
- stage7_sequence_policy_benchmark_ready: `True`
- broader_runtime_selector_ready: `False`
- stage8_training_ready: `False`

## Blockers

- Stage 4 first-move contrast sandbox still requires explicit approval before implementation.
- Stage 7 clean success controls are satisfied in the integrated current gate; Stage 7 remains held out and not promoted.
- No row in this dataset is an ownership-training row or runtime-authorization row.
