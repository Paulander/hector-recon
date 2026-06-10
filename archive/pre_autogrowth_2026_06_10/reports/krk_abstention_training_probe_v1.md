# KRK Abstention Training Probe v0

This offline probe evaluates whether existing protected forced-provider labels can support an abstention-first selector. It does not implement a selector.

## Summary

- `row_count`: `51`
- `state_count`: `15`
- `label_counts`: `{'safe_owner': 34, 'unsafe_owner': 17}`
- `stage_counts`: `{'stage4': 9, 'stage5': 24, 'stage6': 18}`
- `provider_family_counts`: `{'drive_to_edge': 2, 'edge_trap': 27, 'fence_established': 3, 'stage0_basin': 19}`
- `under_minimum_requirements`: `False`

## Results

- `provider_family` accuracy=`0.47058823529411764` negative_suppression=`0.17647058823529413` safe_preservation=`0.6176470588235294`
- `provider_maturity` accuracy=`0.43137254901960786` negative_suppression=`0.0` safe_preservation=`0.6470588235294118`
- `source_stage` accuracy=`0.6078431372549019` negative_suppression=`0.0` safe_preservation=`0.9117647058823529`
- `stage_family` accuracy=`0.45098039215686275` negative_suppression=`0.0` safe_preservation=`0.6764705882352942`
- `family_maturity` accuracy=`0.47058823529411764` negative_suppression=`0.17647058823529413` safe_preservation=`0.6176470588235294`
- `provider_version` accuracy=`0.5098039215686274` negative_suppression=`0.17647058823529413` safe_preservation=`0.6764705882352942`

## Best Result

`{'objective': 'provider_family', 'row_count': 51, 'accuracy': 0.47058823529411764, 'unsafe_true_positive': 3, 'unsafe_false_positive': 13, 'safe_true_negative': 21, 'unsafe_false_negative': 14, 'unsafe_precision': 0.1875, 'unsafe_recall': 0.17647058823529413, 'negative_suppression': 0.17647058823529413, 'safe_preservation': 0.6176470588235294}`

## Decision

- Status: `abstention_signal_underpowered_no_runtime`
- Recommended next step: `collect_more_or_better_protected_negative_controls_before_runtime_review`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
