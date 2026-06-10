# KRK Ownership Context Feature Review v2

Non-causal review of ownership-selection labels enriched with replay-free FEN and selected-move geometry context.

## Summary

- `context_row_count`: `35`
- `fen_join_count`: `35`
- `exact_move_context_count`: `35`
- `base_best_objective`: `stage_provider_family@0.75`
- `base_best_negative_suppression`: `0.7`
- `base_best_positive_recall`: `0.56`
- `context_best_objective`: `stage_provider_family@0.75`
- `context_best_negative_suppression`: `0.625`
- `context_best_positive_recall`: `0.6296296296296297`
- `context_best_balanced_objective`: `raw_score_bucket@0.75`
- `context_best_balanced_negative_suppression`: `0.25`
- `context_best_balanced_positive_recall`: `0.9259259259259259`
- `balanced_improves_recall`: `True`
- `balanced_loses_suppression`: `True`
- `runtime_threshold_passed`: `False`
- `targeted_non_stage0_status`: `non_stage0_current_profile_evidence_recovered`
- `targeted_preserved_count`: `4`

## Interpretation

- FEN-derived context is useful for positive-owner preservation: the balanced context result raises positive recall to 0.88.
- The same context does not yet suppress enough unsafe selected owners: negative suppression remains 0.25 on the balanced result.
- The ownership evidence is still provider-family narrow: most rows are stage0_basin, so this should not be trained into a runtime selector.
- The next improvement should target source/provider diversity and normal-routing ownership labels, not another Stage 7 repair.
- Targeted current-profile replay preserved four historical non-stage0 owners, so source diversity is recoverable. However, the refreshed labels reduce unsafe-owner examples, keeping selector training blocked until more true ownership negatives are recovered.

## Decision

- `status`: `context_features_review_ready_but_not_runtime_ready`
- `recommended_next_step`: `recover_more_true_ownership_negative_labels_or_review_profile_dominance_before_runtime`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
