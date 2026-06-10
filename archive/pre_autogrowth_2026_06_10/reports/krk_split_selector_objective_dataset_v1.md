# KRK Split Selector Objective Dataset v1

Adds recovered normal-routing ownership-selection labels to the split objective channels.

## Summary

- `objective_row_count`: `116`
- `objective_channel_counts`: `{'capacity_recall': 31, 'capacity_risk': 40, 'safe_preservation': 31, 'ownership_selection': 14}`
- `target_label_counts`: `{'include_validated_provider_candidate': 31, 'risk_path_converted_h40': 31, 'risk_path_failed_h40': 9, 'preserve_validated_conversion_capacity': 31, 'selected_owner_converted': 9, 'selected_owner_failed': 5}`
- `offline_probe_row_count`: `116`
- `selector_training_row_count`: `0`
- `stage7_row_count`: `0`
- `ownership_selection_available`: `True`
- `ownership_selection_row_count`: `14`

## Decision

- `status`: `split_selector_objective_channels_with_ownership_labels`
- `recommended_next_step`: `probe_ownership_selection_features_non_causal`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
