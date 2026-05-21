# KRK Ownership Context Feature Review v3

Non-causal review of ownership-selection labels enriched with replay-free FEN and selected-move geometry context.

## Summary

- `context_row_count`: `41`
- `fen_join_count`: `41`
- `exact_move_context_count`: `41`
- `base_best_objective`: `stage_provider_family@0.75`
- `base_best_negative_suppression`: `0.625`
- `base_best_positive_recall`: `0.6296296296296297`
- `context_best_objective`: `stage_provider_family@0.75`
- `context_best_negative_suppression`: `0.6`
- `context_best_positive_recall`: `0.5806451612903226`
- `context_best_balanced_objective`: `raw_score_bucket@0.75`
- `context_best_balanced_negative_suppression`: `0.2`
- `context_best_balanced_positive_recall`: `0.8064516129032258`
- `balanced_improves_recall`: `True`
- `balanced_loses_suppression`: `True`
- `runtime_threshold_passed`: `False`
- `targeted_negative_label_count`: `6`
- `targeted_negative_failure_count`: `2`

## Interpretation

- FEN-derived context is useful for positive-owner preservation: the balanced context result raises positive recall to 0.88.
- The same context does not yet suppress enough unsafe selected owners: negative suppression remains 0.2 on the balanced result.
- The ownership evidence is still provider-family narrow: most rows are stage0_basin, so this should not be trained into a runtime selector.
- The next improvement should target source/provider diversity and normal-routing ownership labels, not another Stage 7 repair.
- Targeted false-positive risk-cell labels added true negatives but did not clear the balanced runtime-review threshold.

## Decision

- `status`: `context_features_review_ready_but_not_runtime_ready`
- `recommended_next_step`: `architecture_review_before_any_selector_runtime_or_collect_more_targeted_negatives`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
