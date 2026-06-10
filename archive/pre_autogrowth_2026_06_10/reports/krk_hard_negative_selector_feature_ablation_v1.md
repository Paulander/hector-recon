# KRK Hard-Negative Selector Feature Ablation v1

Expanded offline ablation after balanced protected hard-negative label collection.

## Summary

- `row_count`: `28`
- `state_count`: `12`
- `positive_context_count`: `20`
- `hard_negative_count`: `8`
- `hard_negative_state_count`: `4`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Results

- `provider_family@0.5` accuracy=`0.7142857142857143` recall=`1.0` negative_suppression=`0.0`
- `provider_family@0.6` accuracy=`0.39285714285714285` recall=`0.55` negative_suppression=`0.0`
- `provider_family@0.75` accuracy=`0.25` recall=`0.35` negative_suppression=`0.0`
- `stage_provider_family@0.5` accuracy=`0.5714285714285714` recall=`0.8` negative_suppression=`0.0`
- `stage_provider_family@0.6` accuracy=`0.2857142857142857` recall=`0.4` negative_suppression=`0.0`
- `stage_provider_family@0.75` accuracy=`0.17857142857142858` recall=`0.25` negative_suppression=`0.0`
- `provider_piece@0.5` accuracy=`0.6071428571428571` recall=`0.85` negative_suppression=`0.0`
- `provider_piece@0.6` accuracy=`0.4642857142857143` recall=`0.65` negative_suppression=`0.0`
- `provider_piece@0.75` accuracy=`0.25` recall=`0.35` negative_suppression=`0.0`
- `provider_piece_king_delta@0.5` accuracy=`0.7142857142857143` recall=`1.0` negative_suppression=`0.0`
- `provider_piece_king_delta@0.6` accuracy=`0.6428571428571429` recall=`0.9` negative_suppression=`0.0`
- `provider_piece_king_delta@0.75` accuracy=`0.21428571428571427` recall=`0.3` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.5` accuracy=`0.6071428571428571` recall=`0.85` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.6` accuracy=`0.39285714285714285` recall=`0.55` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.75` accuracy=`0.17857142857142858` recall=`0.25` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.5` accuracy=`0.7142857142857143` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.6` accuracy=`0.7142857142857143` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.75` accuracy=`0.35714285714285715` recall=`0.45` negative_suppression=`0.125`
- `stage_provider_edge_reply@0.5` accuracy=`0.6071428571428571` recall=`0.85` negative_suppression=`0.0`
- `stage_provider_edge_reply@0.6` accuracy=`0.4642857142857143` recall=`0.65` negative_suppression=`0.0`
- `stage_provider_edge_reply@0.75` accuracy=`0.32142857142857145` recall=`0.45` negative_suppression=`0.0`
- `provider_alignment_flags@0.5` accuracy=`0.7142857142857143` recall=`1.0` negative_suppression=`0.0`
- `provider_alignment_flags@0.6` accuracy=`0.6428571428571429` recall=`0.9` negative_suppression=`0.0`
- `provider_alignment_flags@0.75` accuracy=`0.25` recall=`0.35` negative_suppression=`0.0`

## Best Result

`{'objective': 'stage_provider_piece_delta@0.75', 'features': ['source_stage', 'provider_family', 'forced_piece_type', 'white_king_distance_delta_bucket', 'rook_distance_delta_bucket'], 'row_count': 28, 'threshold': 0.75, 'true_positive': 9, 'false_positive': 7, 'true_negative': 1, 'false_negative': 11, 'accuracy': 0.35714285714285715, 'positive_precision': 0.5625, 'positive_recall': 0.45, 'negative_suppression': 0.125}`

## Interpretation

- `primary`: `This remains an offline feature ablation; no selector training or runtime use is authorized.`
- `evidence_delta`: `The balanced label run adds protected negative diversity, but runtime work still requires a reviewed, robust suppression/preservation signal.`

## Decision

- `status`: `hard_negative_feature_ablation_still_not_runtime_ready`
- `recommended_next_step`: `collect_more_balanced_protected_hard_negatives_or_review_label_semantics`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
