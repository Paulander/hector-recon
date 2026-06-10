# Role-Provider Support Edge Proposal

Schema: `role_provider_support_proposal.v1`
Causal status: `non_causal`
Target role: `krk.box_shrink_to_drive_repair`
Target provider: `krk.drive_to_edge`
Source probe result: `blocked_no_candidate_provider_eligibility`
Proposal status: `sandbox_ready`
Proposed relation count: `1`
Sandbox compile strategy: `compile_gated_support_adapter_not_direct_sub_edge`
Unsafe direct graph edges emitted: `False`

## Proposed Support Relations

- `script.krk.successor.box_shrink_to_drive_repair_affordance` --support/w=0.0--> `skill.krk.drive_to_edge` (visible_role_provider_support, adapter required)

## Required Validation

- `compile_sandbox_topology_with_gated_support_adapter`
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
