# Stage 7 Counterfactual Candidate Update

Schema: `stage7_counterfactual_candidate_update.v1`
Causal status: `non_causal`
State count: `4`
States with any forced mate: `1`
States without any forced mate: `3`

## Forced Outcomes

- `krk.drive_to_edge:mate`: 1
- `krk.drive_to_edge:max_plies`: 3
- `krk.edge_trap_close:max_plies`: 4
- `krk.stage0_basin:max_plies`: 4

## Candidate Updates

### krk.box_shrink_to_drive_repair

- Status: `counterfactual_supported`
- Support: `1`
- Proposed next action: `sandbox_visible_drive_repair_role`

### krk.box_shrink_post_reply_continuation

- Status: `insufficient_existing_successor_capacity_in_quick_sweep`
- Support: `3`
- Proposed next action: `run_targeted_legal_first_or_longer_horizon_sweep`

### krk.stage0_basin_after_box_shrink

- Status: `negative_counterfactual_evidence`
- Support: `4`
- Proposed next action: `avoid_sandboxing_stage0_as_default_box_shrink_continuation`

Recommended next action: `sandbox_visible_drive_repair_role`
