# KRK Ownership Selection Context Dataset v3

Replay-free enrichment of normal-routing ownership labels with FEN-derived terminal-space and selected-move geometry context. This is offline evidence only.

## Summary

- `row_count`: `41`
- `state_count`: `41`
- `label_counts`: `{'selected_owner_converted': 31, 'selected_owner_failed': 10}`
- `source_stage_counts`: `{'stage4': 19, 'stage5': 14, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 37, 'fence_established': 1, 'edge_trap': 3}`
- `fen_join_count`: `41`
- `missing_fen_count`: `0`
- `exact_move_context_count`: `41`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Decision

- `status`: `ownership_selection_context_dataset_ready_for_non_causal_probe`
- `recommended_next_step`: `probe_targeted_negative_context_features`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
