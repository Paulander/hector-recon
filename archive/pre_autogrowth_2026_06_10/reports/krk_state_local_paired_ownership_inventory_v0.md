# KRK State-Local Paired Ownership Inventory v0

Replay-free non-causal inventory of same-state selected-owner vs forced-capacity alternatives.

## Summary

- `pair_count`: `15`
- `state_count`: `6`
- `comparison_label_counts`: `{'equivalent_positive_or_preserve_selected': 3, 'prefer_capacity_alternative': 7, 'abstain_or_insufficient_safe_owner': 5}`
- `pair_strength_counts`: `{'weak_same_state_context': 8, 'strong_same_state_conflict': 7}`
- `source_stage_counts`: `{'stage5': 6, 'stage4': 6, 'stage6': 3}`
- `owner_a_family_counts`: `{'fence_established': 1, 'stage0_basin': 9, 'edge_trap': 5}`
- `owner_b_family_counts`: `{'stage0_basin': 3, 'edge_trap': 9, 'fence_established': 2, 'drive_to_edge': 1}`
- `same_state_conflict_pair_count`: `7`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Minimum Readiness

- `protected_pair_count_met`: `False`
- `same_state_conflict_pair_count_met`: `False`
- `stage7_training_rows_met`: `True`

## Decision

- `status`: `paired_inventory_underpowered`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `probe_state_local_paired_ownership_objective_if_ready`
