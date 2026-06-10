# KRK Stronger Selector Feature Review v0

Offline review of richer capacity-risk features. This does not implement or train a runtime selector.

## Summary

- `row_count`: `40`
- `state_count`: `14`
- `positive_context_count`: `31`
- `hard_negative_count`: `9`
- `stage7_row_count`: `0`
- `previous_best_negative_suppression`: `0.2222222222222222`
- `previous_best_positive_recall`: `1.0`
- `best_negative_suppression`: `0.7777777777777778`
- `best_positive_recall`: `0.9032258064516129`
- `improved_over_v2_ablation`: `True`

## Best Result

`{'objective': 'piece_motion@0.5', 'features': ['piece_motion'], 'row_count': 40, 'threshold': 0.5, 'true_positive': 28, 'false_positive': 2, 'true_negative': 7, 'false_negative': 3, 'accuracy': 0.875, 'positive_precision': 0.9333333333333333, 'positive_recall': 0.9032258064516129, 'negative_suppression': 0.7777777777777778}`

## Results

- `role_fit@0.5` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `role_fit@0.6` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `role_fit@0.75` negative_suppression=`0.0` positive_recall=`0.8064516129032258` accuracy=`0.625`
- `stage_role_fit@0.5` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `stage_role_fit@0.6` negative_suppression=`0.0` positive_recall=`0.8709677419354839` accuracy=`0.675`
- `stage_role_fit@0.75` negative_suppression=`0.1111111111111111` positive_recall=`0.3870967741935484` accuracy=`0.325`
- `family_role_fit@0.5` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `family_role_fit@0.6` negative_suppression=`0.0` positive_recall=`0.8387096774193549` accuracy=`0.65`
- `family_role_fit@0.75` negative_suppression=`0.3333333333333333` positive_recall=`0.5806451612903226` accuracy=`0.525`
- `piece_motion@0.5` negative_suppression=`0.7777777777777778` positive_recall=`0.9032258064516129` accuracy=`0.875`
- `piece_motion@0.6` negative_suppression=`0.7777777777777778` positive_recall=`0.9032258064516129` accuracy=`0.875`
- `piece_motion@0.75` negative_suppression=`0.7777777777777778` positive_recall=`0.9032258064516129` accuracy=`0.875`
- `family_piece_motion@0.5` negative_suppression=`0.2222222222222222` positive_recall=`1.0` accuracy=`0.825`
- `family_piece_motion@0.6` negative_suppression=`0.2222222222222222` positive_recall=`1.0` accuracy=`0.825`
- `family_piece_motion@0.75` negative_suppression=`0.2222222222222222` positive_recall=`0.9032258064516129` accuracy=`0.75`
- `family_rook_line@0.5` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `family_rook_line@0.6` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `family_rook_line@0.75` negative_suppression=`0.0` positive_recall=`0.4838709677419355` accuracy=`0.375`
- `family_reply_pressure@0.5` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `family_reply_pressure@0.6` negative_suppression=`0.0` positive_recall=`0.7419354838709677` accuracy=`0.575`
- `family_reply_pressure@0.75` negative_suppression=`0.0` positive_recall=`0.7419354838709677` accuracy=`0.575`
- `role_fit_motion@0.5` negative_suppression=`0.4444444444444444` positive_recall=`0.9032258064516129` accuracy=`0.8`
- `role_fit_motion@0.6` negative_suppression=`0.4444444444444444` positive_recall=`0.9032258064516129` accuracy=`0.8`
- `role_fit_motion@0.75` negative_suppression=`0.7777777777777778` positive_recall=`0.9032258064516129` accuracy=`0.875`
- `stage_family_role_motion@0.5` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `stage_family_role_motion@0.6` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`
- `stage_family_role_motion@0.75` negative_suppression=`0.0` positive_recall=`1.0` accuracy=`0.775`

## Interpretation

- `primary`: This probes richer offline capacity-risk features only; it does not authorize selector training.
- `semantics_warning`: Because inputs are forced-provider capacity labels, the best feature is a capacity-risk diagnostic, not a runtime ownership selector.

## Decision

- `status`: `stronger_features_review_ready_runtime_still_blocked`
- `recommended_next_step`: `architecture_review_before_selector_training_or_runtime`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
