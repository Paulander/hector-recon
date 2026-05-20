# KRK Ownership Selection Label Dataset v0

Recovered non-causal ownership-selection labels from normal selected-playout evidence.

## Summary

- `candidate_row_count`: `22`
- `deduplicated_row_count`: `14`
- `target_label_counts`: `{'selected_owner_converted': 9, 'selected_owner_failed': 5}`
- `source_stage_counts`: `{'stage4': 5, 'stage5': 5, 'stage6': 4}`
- `provider_family_counts`: `{'stage0_basin': 11, 'edge_trap': 3}`
- `state_count`: `14`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Rows

- state=`state.02cfd843a2cf` stage=`stage4` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`f6f7`
- state=`state.1e4f48a672e8` stage=`stage4` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`b7b1`
- state=`state.256a3da30f0f` stage=`stage4` provider=`krk.stage0_basin` label=`selected_owner_failed` move=`d6c7`
- state=`state.2c1d6da27ea1` stage=`stage5` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`a7a8`
- state=`state.326222aefdf1` stage=`stage5` provider=`krk.edge_trap_close` label=`selected_owner_failed` move=`h7c7`
- state=`state.3dca34326fca` stage=`stage5` provider=`krk.stage0_basin` label=`selected_owner_failed` move=`c6b6`
- state=`state.52085d244e9d` stage=`stage6` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`a8f8`
- state=`state.69711173114a` stage=`stage6` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`a1d1`
- state=`state.699f0003a511` stage=`stage6` provider=`krk.edge_trap_close` label=`selected_owner_failed` move=`h7c7`
- state=`state.7bd8961882ad` stage=`stage5` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`f2g3`
- state=`state.87b1160e68b9` stage=`stage5` provider=`krk.edge_trap_close` label=`selected_owner_converted` move=`e7e8`
- state=`state.b11124d658cf` stage=`stage4` provider=`krk.stage0_basin` label=`selected_owner_failed` move=`b7b1`
- state=`state.d1f052d2cab2` stage=`stage6` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`a1g1`
- state=`state.f17117682948` stage=`stage4` provider=`krk.stage0_basin` label=`selected_owner_converted` move=`d2a2`

## Decision

- `status`: `ownership_selection_labels_recovered`
- `recommended_next_step`: `merge_ownership_labels_into_split_objective_dataset`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
