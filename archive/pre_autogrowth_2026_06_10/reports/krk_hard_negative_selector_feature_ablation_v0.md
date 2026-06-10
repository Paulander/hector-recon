# KRK Hard-Negative Selector Feature Ablation v0

This offline ablation tests simple feature sets against protected hard-negative selector targets.

## Summary

- `row_count`: `16`
- `state_count`: `6`
- `positive_context_count`: `11`
- `hard_negative_count`: `5`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Results

- `provider_family@0.5` accuracy=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `provider_family@0.6` accuracy=`0.1875` recall=`0.2727272727272727` negative_suppression=`0.0`
- `provider_family@0.75` accuracy=`0.1875` recall=`0.2727272727272727` negative_suppression=`0.0`
- `stage_provider_family@0.5` accuracy=`0.5` recall=`0.7272727272727273` negative_suppression=`0.0`
- `stage_provider_family@0.6` accuracy=`0.5` recall=`0.7272727272727273` negative_suppression=`0.0`
- `stage_provider_family@0.75` accuracy=`0.3125` recall=`0.45454545454545453` negative_suppression=`0.0`
- `provider_piece@0.5` accuracy=`0.5` recall=`0.7272727272727273` negative_suppression=`0.0`
- `provider_piece@0.6` accuracy=`0.375` recall=`0.5454545454545454` negative_suppression=`0.0`
- `provider_piece@0.75` accuracy=`0.1875` recall=`0.2727272727272727` negative_suppression=`0.0`
- `provider_piece_king_delta@0.5` accuracy=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `provider_piece_king_delta@0.6` accuracy=`0.5625` recall=`0.8181818181818182` negative_suppression=`0.0`
- `provider_piece_king_delta@0.75` accuracy=`0.1875` recall=`0.2727272727272727` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.5` accuracy=`0.5` recall=`0.7272727272727273` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.6` accuracy=`0.375` recall=`0.5454545454545454` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.75` accuracy=`0.1875` recall=`0.2727272727272727` negative_suppression=`0.0`
- `provider_piece_move_flags@0.5` accuracy=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `provider_piece_move_flags@0.6` accuracy=`0.5625` recall=`0.8181818181818182` negative_suppression=`0.0`
- `provider_piece_move_flags@0.75` accuracy=`0.1875` recall=`0.2727272727272727` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.5` accuracy=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.6` accuracy=`0.6875` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.75` accuracy=`0.3125` recall=`0.45454545454545453` negative_suppression=`0.0`

## Best Result

`{'objective': 'provider_family@0.5', 'features': ['provider_family'], 'row_count': 16, 'threshold': 0.5, 'true_positive': 11, 'false_positive': 5, 'true_negative': 0, 'false_negative': 0, 'accuracy': 0.6875, 'positive_precision': 0.6875, 'positive_recall': 1.0, 'negative_suppression': 0.0}`

## Interpretation

- `primary`: `This remains an offline feature ablation; no selector training or runtime use is authorized.`
- `directed_evidence`: `If no objective improves negative suppression without destroying recall, more balanced protected hard negatives are required.`

## Decision

- `status`: `hard_negative_feature_ablation_no_runtime_ready_signal`
- `recommended_next_step`: `collect_more_balanced_protected_hard_negatives`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
