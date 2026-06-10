# KRK Ownership Source Diversity Review v0

Non-causal review of ownership-label source/provider diversity after context enrichment.

## Summary

- `ownership_row_count`: `35`
- `ownership_label_counts`: `{'selected_owner_converted': 25, 'selected_owner_failed': 10}`
- `ownership_provider_counts`: `{'krk.stage0_basin': 31, 'krk.fence_established': 1, 'krk.edge_trap_close': 3}`
- `non_stage0_ownership_row_count`: `4`
- `source_provider_counts`: `{'normal_selected_playout': {'krk.stage0_basin': 11, 'krk.edge_trap_close': 3}, 'selected_provider_group_recovery': {'krk.fence_established': 1}, 'selected_provider_diversity_normal_routing_h40': {'krk.stage0_basin': 20}}`
- `artifact_count_reviewed`: `5`
- `artifact_count_with_non_stage0_selected`: `3`
- `best_balanced_objective`: `provider_edge_support@0.75`
- `best_balanced_negative_suppression`: `0.5`
- `best_balanced_positive_recall`: `0.88`

## Interpretation

- Ownership evidence is still dominated by stage0_basin selected owners.
- Existing replay-free artifacts prove non-stage0 selected owners exist, but only a small subset has been converted into direct ownership labels.
- More random selected-provider diversity sampling is likely inefficient because two bounded slices overlapped heavily.
- The next useful evidence should target non-stage0 selected-owner contexts or explain why current handoff_composition_v1 routes protected jobs to stage0_basin so often.

## Decision

- `status`: `source_diversity_gap_blocks_runtime`
- `recommended_next_step`: `design_targeted_non_stage0_ownership_label_manifest_or_review_routing_profile_dominance`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
