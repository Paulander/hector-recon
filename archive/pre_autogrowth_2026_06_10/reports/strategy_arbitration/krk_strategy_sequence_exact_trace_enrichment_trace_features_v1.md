# KRK Strategy-Sequence Exact Trace Enrichment Trace Features v1

This artifact folds emitted exact trace enrichment sandbox frames into the strategy-sequence evidence track as trace-only features. It does not alter runtime behavior and does not authorize selector behavior.

## Decision

- status: `exact_trace_enrichment_trace_features_folded_non_causal`
- selector_allowed: `False`
- recommended_next_step: `build_strategy_sequence_dataset_v5_non_causal`

## Trace Features

- trace_frame_count: `3`
- stage_counts: `{'stage5': 3}`
- strategy_family_counts: `{'edge_trap': 3}`
- capacity_label_counts: `{'positive_capacity': 3}`
- policy_cell_counts: `{'stage5|edge_trap': 3}`
- stage7_trace_frame_count: `0`
- selector_training_row_count: `0`
- candidate_generation_training_row_count: `0`

## Boundary

These frames are context evidence only. They are not capacity labels, ownership labels, selector rows, guardrail triggers, routing requests, or score changes.
