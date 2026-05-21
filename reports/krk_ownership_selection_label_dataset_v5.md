# KRK Ownership Selection Label Dataset v5

Adds targeted current-profile h40 labels from false-positive ownership risk cells. These remain non-causal offline evidence.

## Summary

- `input_v4_row_count`: `35`
- `targeted_label_count`: `6`
- `targeted_added_row_count`: `6`
- `targeted_added_label_counts`: `{'selected_owner_converted': 4, 'selected_owner_failed': 2}`
- `merged_row_count`: `41`
- `target_label_counts`: `{'selected_owner_converted': 31, 'selected_owner_failed': 10}`
- `source_stage_counts`: `{'stage4': 19, 'stage5': 14, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 37, 'fence_established': 1, 'edge_trap': 3}`
- `label_source_counts`: `{'normal_selected_playout': 11, 'targeted_non_stage0_current_profile_h40': 4, 'targeted_false_positive_risk_cell_h40': 6, 'selected_provider_diversity_normal_routing_h40': 20}`
- `state_count`: `41`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Decision

- `status`: `ownership_selection_labels_expanded_with_targeted_false_positive_risk_cells`
- `recommended_next_step`: `rerun_context_enriched_probe_with_targeted_negative_labels`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
