# KRK Abstention Context Feature Dataset v0

This replay-free dataset joins abstention labels to existing control-plane evidence. It derives terminal-space context from FEN proxies and monitor/proposal metadata only; it does not run playouts or change runtime behavior.

## Summary

- `row_count`: `51`
- `state_count`: `15`
- `label_counts`: `{'safe_owner': 34, 'unsafe_owner': 17}`
- `stage_counts`: `{'stage5': 24, 'stage6': 18, 'stage4': 9}`
- `source_kind_counts`: `{'forced_provider_conversion': 28, 'selected_playout_success': 23}`
- `missing_frame_count`: `0`
- `matched_proposal_count`: `39`
- `terminal_context_proxy_count`: `51`
- `stage7_training_rows`: `0`

## Feature Groups

- `terminal_space_context`: FEN-derived KRK geometry proxies.
- `proposal_context`: matched provider proposal score/rank metadata when available.
- `monitor_context`: non-causal monitor evidence already present on the control-plane frame.

## Decision

- Status: `abstention_context_feature_dataset_ready_for_non_causal_probe`
- Recommended next step: `probe_abstention_context_features_non_causal`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
