# KRK Ownership Selection Label Dataset v2

Merges recovered ownership labels with two bounded selected-provider diversity h40 label slices.

## Summary

- `input_v1_row_count`: `34`
- `input_fresh_seed_label_count`: `18`
- `merged_row_count`: `34`
- `conflict_count`: `0`
- `target_label_counts`: `{'selected_owner_converted': 25, 'selected_owner_failed': 9}`
- `source_stage_counts`: `{'stage4': 15, 'stage5': 11, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 31, 'edge_trap': 3}`
- `label_source_counts`: `{'normal_selected_playout': 14, 'selected_provider_diversity_normal_routing_h40': 20}`
- `state_count`: `34`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Decision

- `status`: `ownership_selection_labels_expanded_with_second_diversity_slice`
- `recommended_next_step`: `rerun_ownership_selection_feature_probe`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
