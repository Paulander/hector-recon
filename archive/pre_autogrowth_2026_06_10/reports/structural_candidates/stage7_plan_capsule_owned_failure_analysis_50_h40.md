# Stage 7 Plan Capsule Owned-Failure Analysis

Schema: `stage7_plan_capsule_owned_failure_analysis.v1`
Causal status: `non_causal`
Capsule: `krk.post_box_shrink_continuation`
Samples: `50`
Playouts: `{'max_plies': 25, 'mate': 25}`
Shadow candidates: `67`
Max-plies rows analyzed: `25`
Unique failure families: `3`

## Provider Buckets

- `krk.edge_trap_close`: 17
- `krk.fence_established`: 8

## Failure Families

- `state.069e81a609ed`: support=10, provider=`krk.edge_trap_close`, move=`h4g4`, semantic={'reward_contract_mismatch': 10}, failure={'successor_conflict': 10}
- `state.2cc0b3e1033a`: support=8, provider=`krk.fence_established`, move=`a6h6`, semantic={'reward_contract_mismatch': 8}, failure={'successor_conflict': 8}
- `state.0926f12f8e8f`: support=7, provider=`krk.edge_trap_close`, move=`e4d4`, semantic={'reward_visible_fence_aligned_survived': 7}, failure={'conversion_failure_unclassified': 7}

## Provider By Semantic Alignment

- `krk.edge_trap_close|reward_contract_mismatch`: 10
- `krk.fence_established|reward_contract_mismatch`: 8
- `krk.edge_trap_close|reward_visible_fence_aligned_survived`: 7

## Failure Classes

- `successor_conflict`: 18
- `conversion_failure_unclassified`: 7

## Diagnosis

- `capsule_owned_failures_are_provider_specific`
- `edge_trap_close_ownership_still_has_max_plies_residuals`
- `fence_established_ownership_still_has_max_plies_residuals`
- `owned_arbitration_overrode_stage0_basin_but_conversion_still_failed`
- `upstream_reward_contract_mismatch_remains_in_failure_set`

## Next Actions

- `do_not_promote_stage7_plan_capsule`
- `do_not_increase_broad_support_bonus`
- `derive provider-specific post-owned-window audits for edge_trap_close and fence_established residuals`
- `audit why edge_trap_close licensed moves fail despite visible progress terms`
- `audit whether fence_established is acting as repair, re-establish, or stale fallback`

## Boundary

This analysis is replay-free and non-causal. It must not promote Stage 7, mutate topology, or alter runtime routing.
