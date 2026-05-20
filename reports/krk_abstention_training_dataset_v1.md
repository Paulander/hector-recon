# KRK Abstention Training Dataset v0

This replay-free dataset reconstructs protected-control abstention labels from existing forced-provider outcomes. It is non-causal and does not run playouts.

## Summary

- `row_count`: `51`
- `state_count`: `15`
- `label_counts`: `{'safe_owner': 34, 'unsafe_owner': 17}`
- `stage_counts`: `{'stage5': 24, 'stage6': 18, 'stage4': 9}`
- `provider_family_counts`: `{'stage0_basin': 19, 'edge_trap': 27, 'fence_established': 3, 'drive_to_edge': 2}`
- `provider_maturity_counts`: `{'foundation_frozen': 19, 'validated_low_plasticity': 30, 'settling_medium_plasticity': 2}`
- `source_artifact_counts`: `{'reports/krk_forced_provider_control_labels_v0.json': 12, 'reports/krk_strategy_owner_contrast_control_labels_v0.json': 12, 'reports/krk_diverse_contrast_labels_v1.json': 4, 'reports/krk_selector_target_dataset_v0.json': 23}`
- `stage7_training_rows`: `0`
- `minimum_training_rows_required`: `40`
- `minimum_negative_rows_required`: `12`

## Decision

- Status: `abstention_training_dataset_ready_for_probe`
- Recommended next step: `probe_abstention_dataset_v1_non_causal`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
