# KRK Ownership Selection Context Feature Probe v2

Non-causal probe over ownership labels enriched with FEN-derived terminal-space and selected-move geometry context.

## Summary

- `row_count`: `35`
- `state_count`: `35`
- `positive_owner_count`: `27`
- `negative_owner_count`: `8`
- `source_stage_counts`: `{'stage4': 15, 'stage5': 12, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 31, 'fence_established': 1, 'edge_trap': 3}`
- `fen_join_count`: `35`
- `exact_move_context_count`: `35`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Best Result

`{'objective': 'stage_provider_family@0.75', 'features': ['source_stage', 'provider_family'], 'row_count': 35, 'threshold': 0.75, 'true_positive': 17, 'false_positive': 3, 'true_negative': 5, 'false_negative': 10, 'accuracy': 0.6285714285714286, 'positive_precision': 0.85, 'positive_recall': 0.6296296296296297, 'negative_suppression': 0.625}`

## Best Balanced Result

`{'objective': 'raw_score_bucket@0.75', 'features': ['raw_score_bucket'], 'row_count': 35, 'threshold': 0.75, 'true_positive': 25, 'false_positive': 6, 'true_negative': 2, 'false_negative': 2, 'accuracy': 0.7714285714285715, 'positive_precision': 0.8064516129032258, 'positive_recall': 0.9259259259259259, 'negative_suppression': 0.25}`

## Decision

- `status`: `context_features_underpowered`
- `recommended_next_step`: `review_ownership_context_feature_results_before_runtime`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
