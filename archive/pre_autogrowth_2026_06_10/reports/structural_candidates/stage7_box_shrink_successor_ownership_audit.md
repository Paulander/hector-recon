# Stage 7 Successor Ownership Audit

Schema: `stage7_successor_ownership_audit.v1`
Causal status: `non_causal`
Source candidate ready: `True`

## Successor Outcomes

- `krk.edge_trap_close:mate`: 8
- `krk.stage0_basin:max_plies`: 31
- `none:mate`: 11

## Role Audits

### krk.box_shrink_to_edge_trap_handoff

- Audit status: `sandbox_candidate`
- Positive support: `8`
- Negative support: `0`
- Unsupported failure support: `0`
- Proposed visible terms: `box_area_not_increased_after_reply`, `rook_safe_after_reply`, `fence_or_cut_preserved`, `successor_edge_trap_close_available`

### krk.box_shrink_to_drive_repair

- Audit status: `needs_counterfactual_evidence`
- Positive support: `0`
- Negative support: `0`
- Unsupported failure support: `31`
- Proposed visible terms: `box_shrink_reward_confirmed`, `fence_or_cut_not_preserved`, `drive_to_edge_affordance_after_box_shrink`, `repair_or_reestablish_cut_available`

### krk.box_shrink_post_reply_continuation

- Audit status: `needs_role_split_or_successor_sweep`
- Positive support: `11`
- Negative support: `31`
- Unsupported failure support: `0`
- Proposed visible terms: `post_box_shrink_conversion_needed`, `stage0_basin_fallback_detected`, `stage0_basin_unlicensed_after_box_shrink`, `edge_or_drive_repair_not_selected`

Recommended next action: `sandbox_edge_trap_handoff_role_and_counterfactual_stage0_failures`
