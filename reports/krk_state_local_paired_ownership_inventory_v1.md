# KRK State-Local Paired Ownership Inventory v1

Expanded replay-free non-causal inventory across selected-owner and forced-capacity artifacts.

## Summary

- `pair_count`: `40`
- `state_count`: `14`
- `comparison_label_counts`: `{'equivalent_positive_or_preserve_selected': 23, 'abstain_or_insufficient_safe_owner': 8, 'prefer_capacity_alternative': 7, 'prefer_selected_owner': 2}`
- `evidence_channel_counts`: `{'safe_preservation': 23, 'abstain_or_insufficient_safe_owner': 8, 'strong_same_state_conflict': 9}`
- `pair_strength_counts`: `{'weak_same_state_context': 31, 'strong_same_state_conflict': 9}`
- `source_stage_counts`: `{'stage4': 13, 'stage5': 14, 'stage6': 13}`
- `owner_a_family_counts`: `{'stage0_basin': 26, 'fence_established': 3, 'edge_trap': 11}`
- `owner_b_family_counts`: `{'drive_to_edge': 10, 'fence_established': 8, 'edge_trap': 18, 'stage0_basin': 4}`
- `same_state_conflict_pair_count`: `9`
- `selected_failure_with_alternative_success_count`: `7`
- `safe_preservation_pair_count`: `23`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Minimum Readiness

- `protected_pair_count_met`: `True`
- `same_state_conflict_pair_count_met`: `True`
- `selected_failure_with_alternative_success_count_met`: `True`
- `safe_preservation_pair_count_met`: `True`
- `stage7_training_rows_met`: `True`

## Decision

- `status`: `paired_inventory_ready_for_non_causal_probe`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `probe_state_local_paired_ownership_objective`
