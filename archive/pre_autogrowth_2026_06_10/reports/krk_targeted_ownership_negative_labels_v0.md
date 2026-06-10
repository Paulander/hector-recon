# KRK Targeted Ownership Negative Labels v0

Bounded non-causal h40 labels for false-positive ownership risk cells. No selector was trained or run.

## Summary

- `label_count`: `6`
- `wall_time_sec`: `170.045602`
- `selected_result_counts`: `{'mate': 4, 'max_plies': 2}`
- `provider_result_counts`: `{'krk.stage0_basin:mate': 4, 'krk.stage0_basin:max_plies': 2}`
- `target_cell_result_counts`: `{'stage4_stage0_wrong_tempo_like:mate': 3, 'stage4_stage0_wrong_tempo_like:max_plies': 1, 'stage5_stage0_fence_like:mate': 1, 'stage5_stage0_fence_like:max_plies': 1}`
- `targeted_owner_failed_count`: `2`
- `targeted_owner_converted_count`: `4`
- `preselection_preserved_count`: `6`
- `trace_failures_only`: `True`
- `stage7_training_rows`: `0`

## Labels

- `state.1d2ebedbbb30` cell=`stage4_stage0_wrong_tempo_like` provider=`krk.stage0_basin` result=`mate`
- `state.7501312e20f8` cell=`stage4_stage0_wrong_tempo_like` provider=`krk.stage0_basin` result=`mate`
- `state.b09c954a787e` cell=`stage4_stage0_wrong_tempo_like` provider=`krk.stage0_basin` result=`max_plies`
- `state.6b3211a9a90f` cell=`stage4_stage0_wrong_tempo_like` provider=`krk.stage0_basin` result=`mate`
- `state.6e84c77a4520` cell=`stage5_stage0_fence_like` provider=`krk.stage0_basin` result=`mate`
- `state.0b1f2153179b` cell=`stage5_stage0_fence_like` provider=`krk.stage0_basin` result=`max_plies`

## Decision

- `status`: `targeted_ownership_negative_labels_collected`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `merge_targeted_ownership_negative_labels_and_reprobe`
