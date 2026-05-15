# Role-Provider Support Edge Proposal

Schema: `role_provider_support_proposal.v1`
Causal status: `non_causal`
Target role: `krk.box_shrink_to_drive_repair`
Target provider: `krk.drive_to_edge`
Source probe result: `blocked_no_candidate_provider_eligibility`
Proposal status: `sandbox_ready`
Proposed edge count: `1`

## Proposed Edges

- `script.krk.successor.box_shrink_to_drive_repair_affordance` --`SUB`/w=0.0--> `skill.krk.drive_to_edge` (visible_role_provider_support)

## Required Validation

- `compile_sandbox_topology_with_support_edges`
- `stage7_target_smoke`
- `stage6_drive_guardrail`
- `stage5_fence_guardrail`
- `stage1_backchain_guardrail`
- `m1_m4_preservation`

## Hard Blocks

- `do_not_insert_into_default_topology`
- `do_not_train_stage8`
- `do_not_promote_stage7_without_guardrails`
- `do_not_make_probe_or_candidate_causal`
