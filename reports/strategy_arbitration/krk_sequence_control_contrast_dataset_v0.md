# KRK Sequence-Control Contrast Dataset v0

Status: `krk_sequence_control_contrast_dataset_ready_non_causal`

## Summary

- row_count: `76`
- row_type_counts: `{'forced_first_move_candidate': 48, 'ownership_seed_context': 18, 'stage7_clean_sequence_control': 10}`
- source_stage_counts: `{'stage4': 54, 'stage5': 8, 'stage6': 4, 'stage7': 10}`
- target_label_counts: `{'conversion_failure': 30, 'conversion_positive': 28, 'safe_preservation_contrast_seed': 8, 'candidate_switch_contrast_seed': 5, 'failure_context_without_candidate_seed': 5}`
- stage7_heldout_row_count: `10`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Semantics

- Forced-first-move capacity is not runtime ownership.
- Stage 7 rows are held-out challenge evidence only.
- Selector seed rows are context evidence, not training rows.
- The Stage 4 runtime review packet is ready but not implementation-authorizing.
