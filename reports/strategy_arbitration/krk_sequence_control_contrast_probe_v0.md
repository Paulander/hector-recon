# KRK Sequence-Control Contrast Probe v0

## Decision

- status: `sequence_control_stage4_review_ready_stage7_success_controls_insufficient`
- recommended_next_step: `choose_stage4_sandbox_approval_or_design_diverse_stage7_sampling_manifest`
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
- stage7_success_control_count: `2`
- stage7_failure_control_count: `8`

## Readiness

- stage4_first_move_contrast_sandbox_review_ready: `True`
- stage7_sequence_policy_benchmark_ready: `False`
- broader_runtime_selector_ready: `False`
- stage8_training_ready: `False`

## Blockers

- Stage 4 first-move contrast sandbox still requires explicit approval before implementation.
- Stage 7 clean success controls remain below the minimum threshold for sequence-policy benchmarking.
- No row in this dataset is an ownership-training row or runtime-authorization row.
