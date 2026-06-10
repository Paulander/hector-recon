# KRK Ownership Selection Label Dataset v4

Refreshes historical non-stage0 ownership labels with bounded current-profile h40 observations. These labels remain offline evidence and do not authorize selector training or runtime behavior changes.

## Summary

- `input_v3_row_count`: `35`
- `targeted_label_count`: `4`
- `targeted_override_count`: `4`
- `targeted_label_change_count`: `2`
- `merged_row_count`: `35`
- `target_label_counts`: `{'selected_owner_converted': 27, 'selected_owner_failed': 8}`
- `source_stage_counts`: `{'stage4': 15, 'stage5': 12, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 31, 'fence_established': 1, 'edge_trap': 3}`
- `label_source_counts`: `{'normal_selected_playout': 11, 'targeted_non_stage0_current_profile_h40': 4, 'selected_provider_diversity_normal_routing_h40': 20}`
- `state_count`: `35`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Changed Labels

- `state.326222aefdf1` provider=`krk.edge_trap_close` `selected_owner_failed` -> `selected_owner_converted`
- `state.02feb8593cc6` provider=`krk.fence_established` `selected_owner_failed` -> `selected_owner_converted`

## Decision

- `status`: `ownership_selection_labels_refreshed_with_targeted_non_stage0_current_profile_h40`
- `recommended_next_step`: `rerun_context_enriched_probe_with_refreshed_non_stage0_labels`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
