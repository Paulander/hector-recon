# KRK State-Local Contrast Selector Probe v1

This offline probe evaluates forced-provider state-local contrast labels. It does not enable a selector.

## Summary

- `row_count`: `28`
- `state_count`: `8`
- `stage7_training_leakage`: `False`
- `label_counts`: `{'positive': 13, 'negative': 15}`
- `provider_family_counts`: `{'stage0_basin': 8, 'edge_trap': 20}`

## Results

- `provider_family` accuracy=`0.2857142857142857` precision=`0.34782608695652173` recall=`0.6153846153846154` negative_suppression=`0.0`
- `provider_maturity` accuracy=`0.2857142857142857` precision=`0.34782608695652173` recall=`0.6153846153846154` negative_suppression=`0.0`
- `family_maturity` accuracy=`0.2857142857142857` precision=`0.34782608695652173` recall=`0.6153846153846154` negative_suppression=`0.0`
- `family_rank` accuracy=`0.2857142857142857` precision=`0.34782608695652173` recall=`0.6153846153846154` negative_suppression=`0.0`
- `family_norm_score` accuracy=`0.2857142857142857` precision=`0.34782608695652173` recall=`0.6153846153846154` negative_suppression=`0.0`
- `family_global_rank` accuracy=`0.2857142857142857` precision=`0.34782608695652173` recall=`0.6153846153846154` negative_suppression=`0.0`
- `family_rank_norm_score` accuracy=`0.2857142857142857` precision=`0.34782608695652173` recall=`0.6153846153846154` negative_suppression=`0.0`
- `stage_family_rank_score` accuracy=`0.4642857142857143` precision=`0.4642857142857143` recall=`1.0` negative_suppression=`0.0`

## Best Result

`{'objective': 'stage_family_rank_score', 'row_count': 28, 'accuracy': 0.4642857142857143, 'true_positive': 13, 'false_positive': 15, 'true_negative': 0, 'false_negative': 0, 'positive_precision': 0.4642857142857143, 'positive_recall': 1.0, 'negative_suppression': 0.0}`

## Interpretation

- Finding: State-local forced-provider contrast labels are a better selector target than frame-level outcomes, but coverage is still small and provider families are limited.
- Stage 7 training leakage: `False`

## Decision

- Status: `state_local_contrast_signal_not_ready`
- Recommended next step: `review_state_local_contrast_before_runtime_tests`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
