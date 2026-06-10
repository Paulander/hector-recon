# KRK Geometry-Augmented Selector Feature Probe v0

This non-causal probe evaluates whether simple geometry terms improve protected capacity-label selection.

## Summary

- `row_count`: `16`
- `state_count`: `6`
- `positive_count`: `11`
- `negative_count`: `5`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Results

- `provider_family` accuracy=`0.6875` precision=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_family` accuracy=`0.5` precision=`0.6153846153846154` recall=`0.7272727272727273` negative_suppression=`0.0`
- `provider_piece` accuracy=`0.5` precision=`0.6153846153846154` recall=`0.7272727272727273` negative_suppression=`0.0`
- `provider_piece_king_delta` accuracy=`0.6875` precision=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `provider_piece_rook_delta` accuracy=`0.5` precision=`0.6153846153846154` recall=`0.7272727272727273` negative_suppression=`0.0`
- `stage_provider_piece_delta` accuracy=`0.6875` precision=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `edge_stage_provider_piece_delta` accuracy=`0.6875` precision=`0.6875` recall=`1.0` negative_suppression=`0.0`

## Best Result

`{'objective': 'provider_family', 'row_count': 16, 'true_positive': 11, 'false_positive': 5, 'true_negative': 0, 'false_negative': 0, 'accuracy': 0.6875, 'positive_precision': 0.6875, 'positive_recall': 1.0, 'negative_suppression': 0.0}`

## Interpretation

- `primary`: `Geometry features can be benchmarked, but the current protected capacity set is still too small for runtime conclusions.`
- `directed_fix_class`: `expand protected hard-negative capacity evidence and geometry-aware selector scoring non-causally`

## Decision

- `status`: `geometry_augmented_features_underpowered`
- `recommended_next_step`: `collect_more_protected_capacity_rows_or_design_hard_negative_labels`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
