# KRK Ownership Context Feature Review v1

Non-causal review of ownership-selection labels enriched with replay-free FEN and selected-move geometry context.

## Summary

- `context_row_count`: `35`
- `fen_join_count`: `35`
- `exact_move_context_count`: `35`
- `base_best_objective`: `stage_provider_family@0.75`
- `base_best_negative_suppression`: `0.5555555555555556`
- `base_best_positive_recall`: `0.56`
- `context_best_objective`: `stage_provider_family@0.75`
- `context_best_negative_suppression`: `0.7`
- `context_best_positive_recall`: `0.56`
- `context_best_balanced_objective`: `provider_edge_support@0.75`
- `context_best_balanced_negative_suppression`: `0.5`
- `context_best_balanced_positive_recall`: `0.88`
- `balanced_improves_recall`: `True`
- `balanced_loses_suppression`: `True`
- `runtime_threshold_passed`: `False`

## Interpretation

- FEN-derived context is useful for positive-owner preservation: the balanced context result raises positive recall to 0.88.
- The same context does not yet suppress enough unsafe selected owners: negative suppression remains 0.5 on the balanced result.
- The ownership evidence is still provider-family narrow: most rows are stage0_basin, so this should not be trained into a runtime selector.
- The next improvement should target source/provider diversity and normal-routing ownership labels, not another Stage 7 repair.
- Supplemental selected-provider-group recovery improved balanced negative suppression to 0.5, but the result is still below the 0.6 runtime-review threshold.

## Decision

- `status`: `context_features_review_ready_but_not_runtime_ready`
- `recommended_next_step`: `review_source_diversity_or_collect_non_stage7_normal_routing_ownership_labels_with_non_stage0_selected_providers`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
