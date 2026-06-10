# KRK Abstention Training Probe v0

This offline probe evaluates whether existing protected forced-provider labels can support an abstention-first selector. It does not implement a selector.

## Summary

- `row_count`: `28`
- `state_count`: `10`
- `label_counts`: `{'safe_owner': 23, 'unsafe_owner': 5}`
- `stage_counts`: `{'stage4': 4, 'stage5': 12, 'stage6': 12}`
- `provider_family_counts`: `{'drive_to_edge': 2, 'edge_trap': 15, 'fence_established': 3, 'stage0_basin': 8}`
- `under_minimum_requirements`: `True`

## Results

- `provider_family` accuracy=`0.8214285714285714` negative_suppression=`0.0` safe_preservation=`1.0`
- `provider_maturity` accuracy=`0.8214285714285714` negative_suppression=`0.0` safe_preservation=`1.0`
- `source_stage` accuracy=`0.7857142857142857` negative_suppression=`0.0` safe_preservation=`0.9565217391304348`
- `stage_family` accuracy=`0.75` negative_suppression=`0.0` safe_preservation=`0.9130434782608695`
- `family_maturity` accuracy=`0.8214285714285714` negative_suppression=`0.0` safe_preservation=`1.0`
- `provider_version` accuracy=`0.8214285714285714` negative_suppression=`0.0` safe_preservation=`1.0`

## Best Result

`{'objective': 'provider_family', 'row_count': 28, 'accuracy': 0.8214285714285714, 'unsafe_true_positive': 0, 'unsafe_false_positive': 0, 'safe_true_negative': 23, 'unsafe_false_negative': 5, 'unsafe_precision': None, 'unsafe_recall': 0.0, 'negative_suppression': 0.0, 'safe_preservation': 1.0}`

## Decision

- Status: `abstention_signal_underpowered_no_runtime`
- Recommended next step: `collect_more_protected_negative_controls_before_runtime_review`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
