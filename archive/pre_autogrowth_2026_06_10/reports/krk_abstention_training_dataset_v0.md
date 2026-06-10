# KRK Abstention Training Dataset v0

This replay-free dataset reconstructs protected-control abstention labels from existing forced-provider outcomes. It is non-causal and does not run playouts.

## Summary

- `row_count`: `28`
- `state_count`: `10`
- `label_counts`: `{'safe_owner': 23, 'unsafe_owner': 5}`
- `stage_counts`: `{'stage5': 12, 'stage6': 12, 'stage4': 4}`
- `provider_family_counts`: `{'stage0_basin': 8, 'edge_trap': 15, 'fence_established': 3, 'drive_to_edge': 2}`
- `provider_maturity_counts`: `{'foundation_frozen': 8, 'validated_low_plasticity': 18, 'settling_medium_plasticity': 2}`
- `stage7_training_rows`: `0`
- `minimum_training_rows_required`: `40`
- `minimum_negative_rows_required`: `12`

## Decision

- Status: `abstention_training_dataset_under_minimum_requirements`
- Recommended next step: `probe_abstention_dataset_non_causal`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
