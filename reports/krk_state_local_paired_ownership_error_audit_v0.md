# KRK State-Local Paired Ownership Error Audit v0

Non-causal audit of paired ownership probe errors.

## Summary

- `false_positive_count`: `6`
- `false_negative_count`: `1`
- `false_positive_by_evidence_channel`: `{'safe_preservation': 6}`
- `false_positive_by_family_pair`: `{'edge_trap->stage0_basin': 2, 'stage0_basin->edge_trap': 4}`
- `false_negative_by_family_pair`: `{'edge_trap->stage0_basin': 1}`
- `false_positive_by_stage`: `{'stage5': 2, 'stage6': 4}`
- `false_positive_feature_key_counts`: `{"['edge_trap', 'stage0_basin']": 2, "['stage0_basin', 'edge_trap']": 4}`
- `stage7_row_count`: `0`

## Interpretation

- Safe-preservation false positives are mostly cases where normal selected ownership already converted and the alternative is only forced-capacity evidence.
- This supports a semantic gate: do not prefer a forced-capacity alternative over a selected owner that already converted unless the selected owner failed in the same state/context.

## Candidate Features

- `owner_a_positive`
- `owner_a_evidence_channel=normal_selected_playout`
- `owner_b_evidence_channel=forced_capacity`
- `owner_b_positive`
- `comparison_semantics:selected_mate_plus_forced_mate_preserve_selected`
- `do_not_switch_from_selected_mate_to_forced_capacity_without_selected_failure`

## Decision

- `status`: `safe_preservation_false_positives_are_outcome_semantics_errors`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `probe_safe_preservation_gated_pair_models`
