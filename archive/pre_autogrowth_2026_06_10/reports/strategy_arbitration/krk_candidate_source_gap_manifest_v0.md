# KRK Candidate Source Gap Manifest v0

This manifest lists positive-capacity candidate rows that are not exactly covered by candidate-generation refresh runtime-observation traces. It is non-causal and does not authorize selection or runtime changes.

## Decision

- status: `candidate_source_gap_manifest_ready_non_causal`
- runtime_changes_allowed: `False`
- selector_allowed: `False`
- recommended_next_step: `review_candidate_source_expansion_options_non_causal`

## Summary

- positive_capacity_count: `26`
- refresh_trace_count: `25`
- exact_covered_positive_capacity_count: `5`
- exact_missing_positive_capacity_count: `21`
- policy_cell_covered_exact_missing_count: `15`
- policy_cell_missing_count: `6`
- gap_count_by_stage: `{'stage4': 6, 'stage5': 12, 'stage6': 3}`
- gap_count_by_family: `{'edge_trap': 12, 'stage0_basin': 9}`

## First Gap Records

- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_close` move=`h7d7`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_wrong_tempo` move=`h7d7`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_enemy_between` move=`h7b7`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_close` move=`h7c7`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_enemy_between` move=`h7c7`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_wrong_tempo` move=`h7c7`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`stage0_basin` provider=`krk.stage0_basin` move=`a7a8`
- `policy_cell_covered_exact_missing` stage=`stage6` family=`stage0_basin` provider=`krk.stage0_basin` move=`a8f8`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`stage0_basin` provider=`krk.stage0_basin` move=`c6b6`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_close` move=`h7c7`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`stage0_basin` provider=`krk.stage0_basin` move=`f2g3`
- `policy_cell_covered_exact_missing` stage=`stage6` family=`stage0_basin` provider=`krk.stage0_basin` move=`a1d1`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_enemy_between` move=`h7c7`
- `policy_cell_covered_exact_missing` stage=`stage6` family=`stage0_basin` provider=`krk.stage0_basin` move=`a1g1`
- `policy_cell_covered_exact_missing` stage=`stage5` family=`edge_trap` provider=`krk.edge_trap_wrong_tempo` move=`h7c7`
- `policy_cell_missing` stage=`stage4` family=`edge_trap` provider=`krk.edge_trap_close` move=`d6d5`
- `policy_cell_missing` stage=`stage4` family=`edge_trap` provider=`krk.edge_trap_wrong_tempo` move=`d6d5`
- `policy_cell_missing` stage=`stage4` family=`edge_trap` provider=`krk.edge_trap_enemy_between` move=`d6d5`
- `policy_cell_missing` stage=`stage4` family=`stage0_basin` provider=`krk.stage0_basin` move=`f6f7`
- `policy_cell_missing` stage=`stage4` family=`stage0_basin` provider=`krk.stage0_basin` move=`b7b1`
- ... 1 additional gaps omitted

## Interpretation

- exact_candidate_source_coverage_incomplete: `True`
- policy_cell_context_covers_most_missing_exact_candidates: `True`
- capacity_rows_remain_non_causal: `True`
- not_selector_training_data: `True`
- scope_review_status: `candidate_generation_scope_gap_review_blocks_new_runtime_boundary`
