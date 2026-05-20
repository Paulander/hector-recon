# KRK Abstention Context Feature Probe v0

This offline probe tests whether replay-free state context improves abstention labels over provider-family provenance. It does not implement a runtime selector.

## Summary

- `row_count`: `51`
- `state_count`: `15`
- `label_counts`: `{'safe_owner': 34, 'unsafe_owner': 17}`
- `stage_counts`: `{'stage5': 24, 'stage6': 18, 'stage4': 9}`
- `baseline_negative_suppression`: `0.17647058823529413`
- `best_negative_suppression`: `0.8235294117647058`
- `best_safe_preservation`: `0.6470588235294118`
- `context_improved_negative_suppression`: `True`

## Results

- `provider_family` negative_suppression=`0.17647058823529413` safe_preservation=`0.6176470588235294` accuracy=`0.47058823529411764`
- `stage_provider_family` negative_suppression=`0.0` safe_preservation=`0.6764705882352942` accuracy=`0.45098039215686275`
- `edge_bucket_provider_family` negative_suppression=`0.17647058823529413` safe_preservation=`0.6176470588235294` accuracy=`0.47058823529411764`
- `box_relevance_provider_family` negative_suppression=`0.17647058823529413` safe_preservation=`0.6176470588235294` accuracy=`0.47058823529411764`
- `king_support_provider_family` negative_suppression=`0.8235294117647058` safe_preservation=`0.6470588235294118` accuracy=`0.7058823529411765`
- `monitor_signature_provider_family` negative_suppression=`0.7058823529411765` safe_preservation=`0.6764705882352942` accuracy=`0.6862745098039216`
- `repair_monitor_provider_family` negative_suppression=`0.7058823529411765` safe_preservation=`0.6764705882352942` accuracy=`0.6862745098039216`
- `proposal_match_provider_family` negative_suppression=`0.35294117647058826` safe_preservation=`0.6764705882352942` accuracy=`0.5686274509803921`
- `label_source_provider_family` negative_suppression=`0.5294117647058824` safe_preservation=`0.9117647058823529` accuracy=`0.7843137254901961`
- `context_combo_provider_family` negative_suppression=`0.17647058823529413` safe_preservation=`0.8235294117647058` accuracy=`0.6078431372549019`

## Best Result

`{'objective': 'king_support_provider_family', 'features': ('terminal_space_context.white_king_support_bucket', 'provider_family'), 'row_count': 51, 'accuracy': 0.7058823529411765, 'unsafe_true_positive': 14, 'unsafe_false_positive': 12, 'safe_true_negative': 22, 'unsafe_false_negative': 3, 'unsafe_precision': 0.5384615384615384, 'unsafe_recall': 0.8235294117647058, 'negative_suppression': 0.8235294117647058, 'safe_preservation': 0.6470588235294118}`

## Decision

- Status: `context_features_help_but_runtime_blocked`
- Recommended next step: `refine_context_labels_or_features_non_causal_only`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
