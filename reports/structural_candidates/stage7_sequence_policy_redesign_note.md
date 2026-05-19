# Stage 7 Sequence-Policy Redesign Note

This is a non-causal architecture design note for future review. It does not train, sandbox, or change runtime behavior.

## Scope

- Design scope: future ranked sequence-policy / model-expression redesign only
- Recommended next status: `architecture_review_required_before_implementation`
- Stage 7 status: `local_valid_composition_quarantined`

## Not Authorized

- `training_new_model_in_this_slice`
- `runtime_sandbox`
- `runtime_repair`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`

## Design Principles

- optimize multi-step sequence behavior rather than one-ply local score only
- train against state-local hard negatives that share broad visible terms
- separate move ranking from ownership/routing decisions
- keep DTM/tablebase labels offline-only
- preserve frozen Stage 5/6 providers and M1-M4 semantics
- require default-off sandbox plus guardrails before any future causal use

## Candidate Objective Classes

- `state_local_contrastive_sequence_ranking`: rank DTM-positive or conversion-positive continuation moves above winning-nonoptimal hard negatives within the same state family
- `closed_loop_sequence_loss`: penalize compounding drift across a bounded plan window, not just first-move mismatch
- `hard_negative_curriculum`: explicitly contrast positive moves with safe-looking but slow/stagnating moves
- `handoff_exit_supervision`: label when a sequence policy should hand off to validated providers rather than continue owning

## Minimum Future Data Requirements

- `more_family_held_out_post_box_trajectories`
- `successful_post_box_control_trajectories`
- `closed_loop_labels_beyond_stage7`
- `hard_negative_contrast_sets`

## Future Review Questions

- Can a state-local contrastive objective improve top-1 without increasing hard-negative ranking?
- Does sequence-level supervision reduce closed-loop drift on held-out families?
- Which data should be collected outside Stage 7 so the model is not overfit to the post-box residual set?
- What default-off sandbox and guardrails would be required before any future causal evaluation?
