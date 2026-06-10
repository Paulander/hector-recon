# KRK Two-Stage Abstention Objective Probe v0

This offline probe evaluates whether an abstention objective can first preserve safe owners and then suppress unsafe owners. It does not implement a runtime selector.

## Summary

- `row_count`: `51`
- `state_count`: `15`
- `label_counts`: `{'safe_owner': 34, 'unsafe_owner': 17}`
- `stage_counts`: `{'stage5': 24, 'stage6': 18, 'stage4': 9}`
- `objective_count`: `192`
- `threshold_passing_objective_count`: `12`
- `runtime_review_thresholds`: `{'minimum_negative_suppression': 0.7, 'minimum_safe_preservation': 0.75}`

## Best Threshold-Passing Result

`{'objective_id': 'king_support_provider_family__preserve_monitor_provider_family__u0.45_p0.5', 'unsafe_features': ('terminal_space_context.white_king_support_bucket', 'provider_family'), 'preserve_features': ('monitor_context.monitor_signature', 'provider_family'), 'unsafe_threshold': 0.45, 'preserve_threshold': 0.5, 'row_count': 51, 'accuracy': 0.803921568627451, 'unsafe_true_positive': 12, 'unsafe_false_positive': 5, 'safe_true_negative': 29, 'unsafe_false_negative': 5, 'unsafe_precision': 0.7058823529411765, 'unsafe_recall': 0.7058823529411765, 'negative_suppression': 0.7058823529411765, 'safe_preservation': 0.8529411764705882, 'error_counts': {'true_negative_safe_owner_allowed': 29, 'false_positive_safe_owner_rejected': 5, 'true_positive_unsafe_owner_rejected': 12, 'false_negative_unsafe_owner_allowed': 5}}`

## Best By Negative Suppression

`{'objective_id': 'king_support_provider_family__preserve_support_provider_family__u0.45_p0.6', 'unsafe_features': ('terminal_space_context.white_king_support_bucket', 'provider_family'), 'preserve_features': ('terminal_space_context.white_king_support_bucket', 'provider_family'), 'unsafe_threshold': 0.45, 'preserve_threshold': 0.6, 'row_count': 51, 'accuracy': 0.7058823529411765, 'unsafe_true_positive': 14, 'unsafe_false_positive': 12, 'safe_true_negative': 22, 'unsafe_false_negative': 3, 'unsafe_precision': 0.5384615384615384, 'unsafe_recall': 0.8235294117647058, 'negative_suppression': 0.8235294117647058, 'safe_preservation': 0.6470588235294118, 'error_counts': {'true_negative_safe_owner_allowed': 22, 'false_positive_safe_owner_rejected': 12, 'true_positive_unsafe_owner_rejected': 14, 'false_negative_unsafe_owner_allowed': 3}}`

## Decision

- Status: `two_stage_abstention_signal_present_runtime_review_required`
- Recommended next step: `architecture_review_before_default_off_runtime_selector`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
