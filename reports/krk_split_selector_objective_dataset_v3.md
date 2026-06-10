# KRK Split Selector Objective Dataset v3

Adds recovered normal-routing ownership-selection labels to the split objective channels.

## Summary

- `objective_row_count`: `136`
- `objective_channel_counts`: `{'capacity_recall': 31, 'capacity_risk': 40, 'safe_preservation': 31, 'ownership_selection': 34}`
- `target_label_counts`: `{'include_validated_provider_candidate': 31, 'risk_path_converted_h40': 31, 'risk_path_failed_h40': 9, 'preserve_validated_conversion_capacity': 31, 'selected_owner_converted': 25, 'selected_owner_failed': 9}`
- `offline_probe_row_count`: `136`
- `selector_training_row_count`: `0`
- `stage7_row_count`: `0`
- `ownership_selection_available`: `True`
- `ownership_selection_row_count`: `34`

## Decision

- `status`: `split_selector_objective_channels_with_ownership_labels`
- `recommended_next_step`: `probe_twice_expanded_ownership_selection_features_non_causal`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
