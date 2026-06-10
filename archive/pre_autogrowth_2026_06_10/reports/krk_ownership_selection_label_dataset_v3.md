# KRK Ownership Selection Label Dataset v3

Adds replay-free supplemental selected-owner labels from selected-playout groups where the actual selected provider was not present as a target row.

## Summary

- `input_v2_row_count`: `34`
- `supplemental_row_count`: `1`
- `merged_row_count`: `35`
- `target_label_counts`: `{'selected_owner_converted': 25, 'selected_owner_failed': 10}`
- `source_stage_counts`: `{'stage4': 15, 'stage5': 12, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 31, 'fence_established': 1, 'edge_trap': 3}`
- `label_source_counts`: `{'normal_selected_playout': 14, 'selected_provider_group_recovery': 1, 'selected_provider_diversity_normal_routing_h40': 20}`
- `state_count`: `35`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Decision

- `status`: `ownership_selection_labels_supplemented_from_selected_provider_groups`
- `recommended_next_step`: `rerun_context_enriched_ownership_probe`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
