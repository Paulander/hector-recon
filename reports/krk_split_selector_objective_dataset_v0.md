# KRK Split Selector Objective Dataset v0

This artifact fixes the hard-negative label semantics issue by separating capacity recall, capacity risk, safe preservation, and ownership selection.

## Summary

- `source_row_count`: `40`
- `objective_row_count`: `103`
- `objective_channel_counts`: `{'capacity_recall': 31, 'capacity_risk': 40, 'safe_preservation': 31, 'ownership_selection': 1}`
- `target_label_counts`: `{'include_validated_provider_candidate': 31, 'risk_path_converted_h40': 31, 'risk_path_failed_h40': 9, 'preserve_validated_conversion_capacity': 31, 'missing_runtime_ownership_label': 1}`
- `offline_probe_row_count`: `102`
- `selector_training_row_count`: `0`
- `stage7_row_count`: `0`
- `ownership_selection_available`: `False`

## Objective Definitions

- `capacity_recall`: means `validated provider has conversion capacity and should be present in candidate set`; does not mean `provider should own runtime decision`
- `capacity_risk`: means `forced provider path failed or converted under h40, useful as risk evidence`; does not mean `global provider suppression rule`
- `safe_preservation`: means `known converting capacity that future suppressors must preserve`; does not mean `positive ownership selection`
- `ownership_selection`: means `which provider should own normal runtime selection`; does not mean `derivable from forced-provider labels alone`

## Decision

- `status`: `split_selector_objective_channels_built`
- `recommended_next_step`: `review_split_objective_readiness_before_any_selector_training`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
