# KRK State-Local Paired Runtime Proxy Dataset v0

Replay-free proxy validation rows. Outcome labels are retained only as forbidden offline targets.

## Summary

- `row_count`: `40`
- `state_count`: `14`
- `failure_risk_target_count`: `7`
- `safe_preservation_target_count`: `33`
- `safe_preservation_pair_count`: `23`
- `source_stage_counts`: `{'stage4': 13, 'stage5': 14, 'stage6': 13}`
- `comparison_label_counts`: `{'equivalent_positive_or_preserve_selected': 23, 'abstain_or_insufficient_safe_owner': 8, 'prefer_capacity_alternative': 7, 'prefer_selected_owner': 2}`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`

## Feature Classes

- `runtime_visible_candidate_features`: candidate proxy inputs for future review.
- `lab_evidence_source_only_features`: evidence-source metadata; not runtime selector inputs.
- `offline_outcome_forbidden_features`: labels/targets; never runtime inputs.

## Decision

- `status`: `runtime_proxy_dataset_ready_for_non_causal_probe`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `probe_runtime_visible_proxy_candidates`
