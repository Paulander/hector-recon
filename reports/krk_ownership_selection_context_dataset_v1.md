# KRK Ownership Selection Context Dataset v1

Replay-free enrichment of normal-routing ownership labels with FEN-derived terminal-space and selected-move geometry context. This is offline evidence only.

## Summary

- `row_count`: `35`
- `state_count`: `35`
- `label_counts`: `{'selected_owner_converted': 25, 'selected_owner_failed': 10}`
- `source_stage_counts`: `{'stage4': 15, 'stage5': 12, 'stage6': 8}`
- `provider_family_counts`: `{'stage0_basin': 31, 'fence_established': 1, 'edge_trap': 3}`
- `fen_join_count`: `35`
- `missing_fen_count`: `0`
- `exact_move_context_count`: `35`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Decision

- `status`: `ownership_selection_context_dataset_ready_for_non_causal_probe`
- `recommended_next_step`: `probe_supplemented_context_enriched_ownership_selection_features`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
