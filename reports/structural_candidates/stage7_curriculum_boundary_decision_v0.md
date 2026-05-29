# Stage 7 Curriculum Boundary Decision v0

Status: `box_shrink_reclassified_as_local_evidence_handoff_trigger`

Stage 7 `box_shrink` is no longer treated as a standalone repair target. It remains useful as local evidence, handoff pressure, and a held-out challenge set for broader KRK strategy/sequence learning.

## Motivation

- Stage 7 box_shrink can be locally useful, but repeated local, arbitration, support, candidate-move, Plan Capsule, and training-objective work did not produce reliable conversion.
- Selected-path evidence split the residuals into strategy-ownership gaps and sequence/continuation gaps, which means the failure is not one local move-shape defect.
- Clean-control evidence now meets the Stage 7 held-out sequence threshold; this closes the local clean-control collection branch without authorizing Stage 7 promotion or Stage 8 training.
- Continuing to crack Stage 7 as a standalone problem risks overfitting the lab to a noisy curriculum boundary; the active sequence-policy gap is protected plan-window failure-contrast evidence.
- The better abstraction is to treat box_shrink as local evidence that can help trigger owner exit, handoff, or broader KRK strategy/sequence selection.

## Current Evidence State

- stage7_clean_review_status: `stage7_clean_control_collection_closed_heldout_only`
- stage7_clean_review_next_step: `review_current_control_plane_gate_for_protected_failure_contrast_collection`
- strategy_sequence_inventory_status: `replay_free_inventory_state_holdout_gap_blocks_runtime`
- strategy_sequence_inventory_next_step: `review_state_holdout_signal_before_runtime_or_continue_protected_failure_contrast_gate`
- stage7_clean_success_controls_met: `True`
- stage7_clean_hard_negatives_met: `True`

## New Role

- box_shrink_role: `local_evidence_handoff_trigger_phase_boundary_signal`
- stage7_residuals_role: `heldout_challenge_set`
- allowed_uses: `['diagnostic evidence for strategy-ownership failures', 'diagnostic evidence for sequence-policy failures', 'held-out challenge cases for broader KRK strategy/sequence learners', 'non-causal feature/monitor evaluation']`
- blocked_uses: `['standalone promotion target', 'Stage 8 training gate', 'justification for local box_shrink runtime patches', 'runtime selector tuning target without protected-stack evidence']`

## Architecture Implication

- next_level_problem: `learn_when_each_KRK_strategy_or_sequence_should_own`
- protected_base: `['stage1', 'stage4_with_h40_caveat', 'stage5', 'stage6']`
- next_tracks: `['strategy_ownership', 'sequence_policy', 'curriculum_boundary']`
- stage7_training_rows_allowed: `False`
- stage7_evaluation_rows_allowed: `True`

## Explicitly Rejected Next Steps

- `more Stage 7 local move-shape tuning`
- `more Stage 7 support adapters or score bonuses`
- `more Plan Capsule micro-tuning as a Stage 7 repair`
- `promoting Stage 7`
- `training Stage 8 from unresolved Stage 7`
- `runtime DTM/tablebase selector`
- `unreviewed additional Stage 7 labels`

Recommended next step: `review_current_control_plane_gate_for_protected_failure_contrast_collection`
