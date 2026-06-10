# Stage 7 Post-Box Plan Capsule Sandbox Protocol

Schema: `stage7_post_box_plan_capsule_sandbox_protocol.v1`
Causal status: `non_causal`
Runtime behavior changed: `False`
Capsule: `krk.post_box_shrink_continuation`
TTL white moves: `3`
Reference support: `2/2`

This is a non-causal protocol check. It does not compile a runtime plan owner.

## Interpretation

reference trajectories support a bounded commitment protocol

Next action: `compile_default_off_visible_capsule_sandbox`

## Trajectories

- `8/8/R7/8/2k5/8/8/3K4 w - - 2 2`
  start DTM `27` -> after TTL `22`
  supported: `True`
  progress terms: `box_area_decreases_or_does_not_expand, corner_net_pressure_increases, enemy_king_mobility_decreases, mate_basin_proximity_improves, stagnation_avoided, white_king_support_improves`
- `8/8/8/R7/4k3/8/3K4/8 w - - 2 2`
  start DTM `21` -> after TTL `16`
  supported: `True`
  progress terms: `box_area_decreases_or_does_not_expand, corner_net_pressure_increases, enemy_king_mobility_decreases, mate_basin_proximity_improves, stagnation_avoided, white_king_support_improves`

## Hard Blocks

- `do_not_train_stage8`
- `do_not_promote_stage7`
- `do_not_enable_runtime_capsule_by_default`
- `do_not_mutate_topology_during_gameplay`
