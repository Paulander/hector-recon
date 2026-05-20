# KRK Hard-Negative Selector Feature Ablation v1

Expanded offline ablation after balanced protected hard-negative label collection.

## Summary

- `row_count`: `40`
- `state_count`: `14`
- `positive_context_count`: `31`
- `hard_negative_count`: `9`
- `hard_negative_state_count`: `4`
- `stage7_row_count`: `0`
- `underpowered`: `True`

## Results

- `provider_family@0.5` accuracy=`0.775` recall=`1.0` negative_suppression=`0.0`
- `provider_family@0.6` accuracy=`0.775` recall=`1.0` negative_suppression=`0.0`
- `provider_family@0.75` accuracy=`0.4` recall=`0.5161290322580645` negative_suppression=`0.0`
- `stage_provider_family@0.5` accuracy=`0.7` recall=`0.9032258064516129` negative_suppression=`0.0`
- `stage_provider_family@0.6` accuracy=`0.45` recall=`0.5806451612903226` negative_suppression=`0.0`
- `stage_provider_family@0.75` accuracy=`0.375` recall=`0.4838709677419355` negative_suppression=`0.0`
- `provider_piece@0.5` accuracy=`0.625` recall=`0.8064516129032258` negative_suppression=`0.0`
- `provider_piece@0.6` accuracy=`0.625` recall=`0.8064516129032258` negative_suppression=`0.0`
- `provider_piece@0.75` accuracy=`0.675` recall=`0.8064516129032258` negative_suppression=`0.2222222222222222`
- `provider_piece_king_delta@0.5` accuracy=`0.825` recall=`1.0` negative_suppression=`0.2222222222222222`
- `provider_piece_king_delta@0.6` accuracy=`0.825` recall=`1.0` negative_suppression=`0.2222222222222222`
- `provider_piece_king_delta@0.75` accuracy=`0.75` recall=`0.9032258064516129` negative_suppression=`0.2222222222222222`
- `provider_piece_rook_delta@0.5` accuracy=`0.625` recall=`0.8064516129032258` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.6` accuracy=`0.625` recall=`0.8064516129032258` negative_suppression=`0.0`
- `provider_piece_rook_delta@0.75` accuracy=`0.675` recall=`0.8064516129032258` negative_suppression=`0.2222222222222222`
- `stage_provider_piece_delta@0.5` accuracy=`0.775` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.6` accuracy=`0.775` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_piece_delta@0.75` accuracy=`0.775` recall=`1.0` negative_suppression=`0.0`
- `stage_provider_edge_reply@0.5` accuracy=`0.7` recall=`0.9032258064516129` negative_suppression=`0.0`
- `stage_provider_edge_reply@0.6` accuracy=`0.6` recall=`0.7741935483870968` negative_suppression=`0.0`
- `stage_provider_edge_reply@0.75` accuracy=`0.525` recall=`0.6774193548387096` negative_suppression=`0.0`
- `provider_alignment_flags@0.5` accuracy=`0.825` recall=`1.0` negative_suppression=`0.2222222222222222`
- `provider_alignment_flags@0.6` accuracy=`0.825` recall=`1.0` negative_suppression=`0.2222222222222222`
- `provider_alignment_flags@0.75` accuracy=`0.75` recall=`0.9032258064516129` negative_suppression=`0.2222222222222222`

## Best Result

`{'objective': 'provider_piece_king_delta@0.5', 'features': ['provider_family', 'forced_piece_type', 'white_king_distance_delta_bucket'], 'row_count': 40, 'threshold': 0.5, 'true_positive': 31, 'false_positive': 7, 'true_negative': 2, 'false_negative': 0, 'accuracy': 0.825, 'positive_precision': 0.8157894736842105, 'positive_recall': 1.0, 'negative_suppression': 0.2222222222222222}`

## Interpretation

- `primary`: `This remains an offline feature ablation; no selector training or runtime use is authorized.`
- `evidence_delta`: `The balanced label run adds protected negative diversity, but runtime work still requires a reviewed, robust suppression/preservation signal.`

## Decision

- `status`: `hard_negative_feature_ablation_promising_underpowered`
- `recommended_next_step`: `review_promising_offline_signal_before_any_selector_training`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
