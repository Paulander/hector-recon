# KRK Ownership Selection Context Feature Probe v0

Non-causal probe over ownership labels enriched with FEN-derived terminal-space and selected-move geometry context.

## Summary

- `row_count`: `34`
- `state_count`: `34`
- `positive_owner_count`: `25`
- `negative_owner_count`: `9`
- `source_stage_counts`: `{'stage4': 15, 'stage5': 11, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 31, 'edge_trap': 3}`
- `fen_join_count`: `34`
- `exact_move_context_count`: `34`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Best Result

`{'objective': 'stage_provider_family@0.75', 'features': ['source_stage', 'provider_family'], 'row_count': 34, 'threshold': 0.75, 'true_positive': 14, 'false_positive': 4, 'true_negative': 5, 'false_negative': 11, 'accuracy': 0.5588235294117647, 'positive_precision': 0.7777777777777778, 'positive_recall': 0.56, 'negative_suppression': 0.5555555555555556}`

## Best Balanced Result

`{'objective': 'provider_edge_support@0.75', 'features': ['provider_family', 'ctx:terminal_space_context.black_king_edge_bucket', 'ctx:terminal_space_context.white_king_support_bucket'], 'row_count': 34, 'threshold': 0.75, 'true_positive': 22, 'false_positive': 5, 'true_negative': 4, 'false_negative': 3, 'accuracy': 0.7647058823529411, 'positive_precision': 0.8148148148148148, 'positive_recall': 0.88, 'negative_suppression': 0.4444444444444444}`

## Decision

- `status`: `context_features_underpowered`
- `recommended_next_step`: `review_ownership_context_feature_results_before_runtime`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
