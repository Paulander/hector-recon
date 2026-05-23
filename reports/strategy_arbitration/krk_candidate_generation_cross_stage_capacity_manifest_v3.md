# KRK Candidate-Generation Cross-Stage Capacity Manifest v3

This manifest proposes a capped protected-only offline label slice targeted at stage-family capacity cells that block cross-stage candidate-generation refresh.

## Decision

- status: `cross_stage_capacity_manifest_ready_partial_target_coverage`
- labels_run_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `review_or_run_bounded_cross_stage_capacity_labels`

## Summary

- target_cell_count: 9
- candidate_pool_count: 11
- job_count: 8
- job_cap: 12
- job_count_by_stage: `{'stage4': 2, 'stage5': 4, 'stage6': 2}`
- job_count_by_provider_family: `{'edge_trap': 3, 'stage0_basin': 5}`
- job_count_by_target_cell_maturity: `{'mixed_capacity_cell': 2, 'positive_only_cell': 6}`
- unavailable_target_cells: `['stage4|edge_trap', 'stage5|fence_established', 'stage6|drive_to_edge', 'stage6|edge_trap', 'stage6|fence_established']`
- stage7_job_count: 0

## Jobs

- `job.krk.cg_cross_stage_v3.072671d3e877` cell=`stage5|edge_trap` maturity=`positive_only_cell` provider=`krk.edge_trap_close` move=`h7c7`
- `job.krk.cg_cross_stage_v3.23625c938438` cell=`stage5|stage0_basin` maturity=`positive_only_cell` provider=`krk.stage0_basin` move=`f2g3`
- `job.krk.cg_cross_stage_v3.d2fe4fcb2c63` cell=`stage6|stage0_basin` maturity=`positive_only_cell` provider=`krk.stage0_basin` move=`a1d1`
- `job.krk.cg_cross_stage_v3.7db3d70b3f8f` cell=`stage5|edge_trap` maturity=`positive_only_cell` provider=`krk.edge_trap_enemy_between` move=`h7c7`
- `job.krk.cg_cross_stage_v3.9f8c28df5da4` cell=`stage6|stage0_basin` maturity=`positive_only_cell` provider=`krk.stage0_basin` move=`a1g1`
- `job.krk.cg_cross_stage_v3.d68549c922ff` cell=`stage5|edge_trap` maturity=`positive_only_cell` provider=`krk.edge_trap_wrong_tempo` move=`h7c7`
- `job.krk.cg_cross_stage_v3.87de57e39c2f` cell=`stage4|stage0_basin` maturity=`mixed_capacity_cell` provider=`krk.stage0_basin` move=`b7b1`
- `job.krk.cg_cross_stage_v3.8b1329430dc1` cell=`stage4|stage0_basin` maturity=`mixed_capacity_cell` provider=`krk.stage0_basin` move=`d2a2`

## Boundary

This artifact does not run labels. Jobs are offline forced-provider capacity checks only; they are not selector labels, runtime inputs, score updates, guardrails, or promotion evidence.
