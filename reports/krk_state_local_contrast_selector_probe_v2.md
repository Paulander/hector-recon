# KRK State-Local Contrast Selector Probe v2

This offline probe evaluates deduplicated forced-provider state-local contrast labels. It trains/evaluates on protected non-Stage7 rows and reports Stage 7 challenge rows separately.

## Summary

- `row_count`: `20`
- `training_row_count`: `12`
- `stage7_eval_row_count`: `8`
- `state_count`: `10`
- `training_state_count`: `8`
- `stage7_training_leakage`: `False`
- `label_counts`: `{'positive': 9, 'negative': 11}`
- `training_label_counts`: `{'positive': 9, 'negative': 3}`
- `stage7_label_counts`: `{'negative': 8}`
- `provider_family_counts`: `{'edge_trap': 9, 'drive_to_edge': 2, 'fence_established': 2, 'stage0_basin': 7}`

## Training Leave-State-Out Results

- `provider_family` accuracy=`0.5` precision=`0.6666666666666666` recall=`0.6666666666666666` negative_suppression=`0.0`
- `provider_maturity` accuracy=`0.5` precision=`0.6666666666666666` recall=`0.6666666666666666` negative_suppression=`0.0`
- `family_maturity` accuracy=`0.5` precision=`0.6666666666666666` recall=`0.6666666666666666` negative_suppression=`0.0`
- `family_rank` accuracy=`0.5` precision=`0.6666666666666666` recall=`0.6666666666666666` negative_suppression=`0.0`
- `family_norm_score` accuracy=`0.5` precision=`0.6666666666666666` recall=`0.6666666666666666` negative_suppression=`0.0`
- `family_global_rank` accuracy=`0.5833333333333334` precision=`0.7` recall=`0.7777777777777778` negative_suppression=`0.0`
- `family_rank_norm_score` accuracy=`0.5` precision=`0.6666666666666666` recall=`0.6666666666666666` negative_suppression=`0.0`
- `stage_family_rank_score` accuracy=`0.75` precision=`0.75` recall=`1.0` negative_suppression=`0.0`

## Stage 7 Held-Out Results

- `provider_family` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`
- `provider_maturity` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`
- `family_maturity` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`
- `family_rank` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`
- `family_norm_score` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`
- `family_global_rank` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`
- `family_rank_norm_score` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`
- `stage_family_rank_score` accuracy=`0.0` precision=`0.0` recall=`None` negative_suppression=`0.0`

## Best Training Result

`{'objective': 'stage_family_rank_score', 'row_count': 12, 'accuracy': 0.75, 'true_positive': 9, 'false_positive': 3, 'true_negative': 0, 'false_negative': 0, 'positive_precision': 0.75, 'positive_recall': 1.0, 'negative_suppression': 0.0}`

## Decision

- Status: `state_local_contrast_signal_not_ready`
- Recommended next step: `review_state_local_contrast_before_runtime_tests`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
