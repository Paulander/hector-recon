# KRK Exact Trace Enrichment Coverage Analysis v0

This replay-free analysis evaluates emitted candidate-generation-only exact trace enrichment frames. It does not authorize selection, scoring, routing, guardrails, promotion, or Stage 8 training.

## Decision

- status: `exact_trace_enrichment_coverage_ready_for_trace_dataset_refresh`
- selector_allowed: `False`
- recommended_next_step: `fold_exact_trace_enrichment_frames_into_non_causal_strategy_sequence_trace_dataset`

## Summary

- case_count: `1`
- emitted_exact_frame_count: `3`
- emitted_frame_count_by_stage: `{'stage5': 3}`
- emitted_frame_count_by_provider_family: `{'edge_trap': 3}`
- emitted_frame_count_by_policy_cell: `{'stage5|edge_trap': 3}`
- target_gap_rows_in_sample: `3`
- exact_gap_hits: `3`
- exact_gap_recall: `1.0`
- policy_cell_gap_hits: `3`
- policy_cell_gap_recall: `1.0`
- truncation_count: `0`
- truncated_frame_count: `0`
- invalid_frame_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- score_delta_count: `0`
- stage4_frame_count: `0`
- stage7_frame_count: `0`

## Interpretation

- approved_cells_only: `True`
- exact_gap_coverage_visible: `True`
- negative_or_selector_evidence_added: `False`
- selector_supported: `False`
- guardrails_supported: `False`
- capacity_gap_labels_are_not_ownership_labels: `True`

## Boundary

The emitted frames expand visible candidate-generation context only. Capacity gap labels remain capacity evidence, not selector or ownership labels.
