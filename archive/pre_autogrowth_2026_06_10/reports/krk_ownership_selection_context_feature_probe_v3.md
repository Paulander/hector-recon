# KRK Ownership Selection Context Feature Probe v3

Non-causal probe over ownership labels enriched with FEN-derived terminal-space and selected-move geometry context.

## Summary

- `row_count`: `41`
- `state_count`: `41`
- `positive_owner_count`: `31`
- `negative_owner_count`: `10`
- `source_stage_counts`: `{'stage4': 19, 'stage5': 14, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 37, 'fence_established': 1, 'edge_trap': 3}`
- `fen_join_count`: `41`
- `exact_move_context_count`: `41`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Best Result

`{'objective': 'stage_provider_family@0.75', 'features': ['source_stage', 'provider_family'], 'row_count': 41, 'threshold': 0.75, 'true_positive': 18, 'false_positive': 4, 'true_negative': 6, 'false_negative': 13, 'accuracy': 0.5853658536585366, 'positive_precision': 0.8181818181818182, 'positive_recall': 0.5806451612903226, 'negative_suppression': 0.6}`

## Best Balanced Result

`{'objective': 'raw_score_bucket@0.75', 'features': ['raw_score_bucket'], 'row_count': 41, 'threshold': 0.75, 'true_positive': 25, 'false_positive': 8, 'true_negative': 2, 'false_negative': 6, 'accuracy': 0.6585365853658537, 'positive_precision': 0.7575757575757576, 'positive_recall': 0.8064516129032258, 'negative_suppression': 0.2}`

## Decision

- `status`: `context_features_underpowered`
- `recommended_next_step`: `review_ownership_context_feature_results_before_runtime`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
