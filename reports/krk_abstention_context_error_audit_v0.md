# KRK Abstention Context Error Audit v0

This replay-free audit explains why the context-feature abstention probe remains blocked. It does not implement a runtime selector.

## Summary

- `row_count`: `51`
- `best_objective`: `king_support_provider_family`
- `best_features`: `['terminal_space_context.white_king_support_bucket', 'provider_family']`
- `false_positive_count`: `12`
- `false_negative_count`: `3`
- `true_positive_count`: `14`
- `true_negative_count`: `22`
- `negative_suppression`: `0.8235294117647058`
- `safe_preservation`: `0.6470588235294118`

## Diagnosis

- Context features substantially improve unsafe-owner recall, but they over-reject safe owners.
- The strongest feature uses white-king support bucket plus provider family; this is useful evidence but not a safe runtime abstention rule.
- Safe-preservation misses the runtime-review threshold, so any runtime selector remains blocked.
- False positives should be analyzed before collecting more labels: the current objective suppresses too many known-safe owners.

## Error Patterns

- `false_positive_by_stage`: `{'stage5': 11, 'stage4': 1}`
- `false_positive_by_provider_family`: `{'edge_trap': 11, 'stage0_basin': 1}`
- `false_positive_by_label_source_kind`: `{'forced_provider_conversion': 8, 'selected_playout_success': 4}`
- `false_positive_by_support_bucket`: `{'far': 5, 'close': 6, 'medium': 1}`
- `false_positive_by_monitor_signature`: `{'OwnerExitMonitor+PhaseBoundaryMonitor+RepairNeededMonitor': 5, 'OwnerExitMonitor+PhaseBoundaryMonitor': 7}`
- `false_negative_by_stage`: `{'stage4': 2, 'stage5': 1}`
- `false_negative_by_provider_family`: `{'edge_trap': 2, 'stage0_basin': 1}`
- `false_negative_by_label_source_kind`: `{'forced_provider_conversion': 2, 'selected_playout_success': 1}`
- `false_negative_by_support_bucket`: `{'close': 3}`
- `false_negative_by_monitor_signature`: `{'OwnerExitMonitor+PhaseBoundaryMonitor': 3}`

## Decision

- Status: `context_signal_overrejects_safe_owners_runtime_blocked`
- Recommended next step: `non_causal_safe_preservation_label_semantics_review`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
