# Stage 7 Clean Control Sampling Review v0

Status: `clean_success_collection_blocked_by_sampling_overlap`

Non-causal review of clean Stage 7 control collection after the bounded h40 label job.

## Summary

- clean_sequence_success_controls_have: `2`
- clean_sequence_success_controls_required: `5`
- clean_sequence_hard_negatives_have: `8`
- bounded_label_run_mates: `3`
- bounded_label_run_novel_controls: `0`
- sampling_overlap_detected: `True`
- runtime_work_allowed: `False`

## Interpretation

- Current replay-free clean artifacts provide enough h40 hard negatives but too few unique clean mate controls.
- The single bounded current-default h40 label job produced mates but no novel de-duplicated clean controls.
- Blindly running more Stage 7 current-default labels risks spending time on duplicate curriculum positions rather than resolving the architecture question.

## Allowed Next Options

- `reviewed_diverse_clean_sampling_manifest`: Design a new manifest with explicit disjoint source-stage/position diversity and a hard cap before any additional labels.
- `stage7_curriculum_boundary_review`: Stop clean-control collection and review whether box_shrink should remain a held-out boundary/challenge rather than a standalone stage.

## Blocked Next Steps

- `unreviewed additional Stage 7 label runs`
- `runtime selector or arbiter changes`
- `Stage 7 repair, support adapter, score bonus, or provider penalty`
- `Stage 7 promotion`
- `Stage 8 training`

Recommended next step: `architecture_review_before_more_stage7_clean_labels`
