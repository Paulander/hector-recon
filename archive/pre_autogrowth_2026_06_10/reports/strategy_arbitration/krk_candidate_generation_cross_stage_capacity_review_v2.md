# KRK Candidate-Generation Cross-Stage Capacity Review v2

This review explains why the candidate-generation refresh signal is useful in-sample but weak under leave-stage-out evaluation.

## Decision

- status: `cross_stage_capacity_review_recommends_stratified_capacity_manifest`
- selector_allowed: `False`
- runtime_candidate_generator_refresh_allowed: `False`
- recommended_next_step: `build_targeted_cross_stage_capacity_manifest_non_causal`

## Summary

- capacity_row_count: 28
- stage_counts: `{'stage4': 9, 'stage5': 12, 'stage6': 7}`
- family_counts: `{'drive_to_edge': 1, 'edge_trap': 15, 'fence_established': 3, 'stage0_basin': 9}`
- stage_family_cell_count: 9
- stage7_readiness_training_row_count: 0

## Findings

- positive_only_cells: `['stage5|edge_trap', 'stage5|fence_established', 'stage5|stage0_basin', 'stage6|stage0_basin']`
- negative_only_cells: `['stage6|edge_trap']`
- mixed_capacity_cells: `['stage4|edge_trap', 'stage4|stage0_basin']`
- underpowered_cells: `['stage6|drive_to_edge', 'stage6|fence_established']`
- leave_stage_out_positive_recall: 0.5789473684210527
- leave_stage_out_negative_suppression: 0.1111111111111111
- main_blocker: `stage_family_capacity_is_not_uniform_across_protected_stages`

## Stage-Family Cells

- `stage4|edge_trap`: support=6 positive=3 negative=3 maturity=`mixed_capacity_cell`
- `stage4|stage0_basin`: support=3 positive=2 negative=1 maturity=`mixed_capacity_cell`
- `stage5|edge_trap`: support=6 positive=6 negative=0 maturity=`positive_only_cell`
- `stage5|fence_established`: support=2 positive=2 negative=0 maturity=`positive_only_cell`
- `stage5|stage0_basin`: support=4 positive=4 negative=0 maturity=`positive_only_cell`
- `stage6|drive_to_edge`: support=1 positive=0 negative=1 maturity=`underpowered_cell`
- `stage6|edge_trap`: support=3 positive=0 negative=3 maturity=`negative_only_cell`
- `stage6|fence_established`: support=1 positive=0 negative=1 maturity=`underpowered_cell`
- `stage6|stage0_basin`: support=2 positive=2 negative=0 maturity=`positive_only_cell`

## Boundary

This is a candidate-generation capacity review only. Forced-provider capacity labels remain offline evidence, not selector labels or runtime ownership authority.
