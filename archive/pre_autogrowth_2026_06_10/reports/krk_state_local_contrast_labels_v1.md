# KRK State-Local Contrast Labels v1

This replay-free dataset joins ranked proposal frames with forced-provider labels by state/provider. It is non-causal and does not run playouts.

## Summary

- `row_count`: `28`
- `usable_training_row_count`: `28`
- `stage7_challenge_row_count`: `0`
- `contrast_label_counts`: `{'positive': 13, 'negative': 15}`
- `forced_result_counts`: `{'mate': 13, 'max_plies': 15}`
- `provider_family_counts`: `{'stage0_basin': 8, 'edge_trap': 20}`
- `source_stage_counts`: `{'stage5': 8, 'stage6': 20}`
- `matched_forced_label_count`: `12`
- `unmatched_forced_label_count`: `12`
- `unmatched_forced_label_job_ids`: `['job.krk.strategy_owner_contrast.14c4d6d395bb', 'job.krk.strategy_owner_contrast.1a9dfe565e76', 'job.krk.strategy_owner_contrast.40d0a6e04b05', 'job.krk.strategy_owner_contrast.4dcd4cc180e8', 'job.krk.strategy_owner_contrast.5e053ab0baa8', 'job.krk.strategy_owner_contrast.6ca3b85ce53a', 'job.krk.strategy_owner_contrast.829c9b9fe98b', 'job.krk.strategy_owner_contrast.82e91a823777', 'job.krk.strategy_owner_contrast.d1744cd54930', 'job.krk.strategy_owner_contrast.e14d23798e77', 'job.krk.strategy_owner_contrast.eae6955cdd41', 'job.krk.strategy_owner_contrast.fca927c317d8']`

## Decision

- Status: `state_local_contrast_labels_joined`
- Recommended next step: `probe_state_local_contrast_selector_v1`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
