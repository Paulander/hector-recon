# KRK State-Local Contrast Labels v2

This replay-free dataset joins ranked proposal frames with all forced-provider labels available so far. Rows are deduplicated to one state/provider contrast label. It is non-causal and does not run playouts.

## Summary

- `row_count`: `20`
- `usable_training_row_count`: `12`
- `stage7_challenge_row_count`: `8`
- `state_count`: `10`
- `training_state_count`: `8`
- `contrast_label_counts`: `{'positive': 9, 'negative': 11}`
- `training_contrast_label_counts`: `{'positive': 9, 'negative': 3}`
- `stage7_contrast_label_counts`: `{'negative': 8}`
- `forced_result_counts`: `{'mate': 9, 'max_plies': 11}`
- `provider_family_counts`: `{'edge_trap': 9, 'drive_to_edge': 2, 'fence_established': 2, 'stage0_basin': 7}`
- `source_stage_counts`: `{'stage5': 6, 'stage7': 8, 'stage6': 6}`
- `matched_forced_label_count`: `20`
- `unmatched_forced_label_count`: `28`
- `unmatched_forced_label_job_ids`: `['job.krk.protected_missing_provider.01f7ab28aca7', 'job.krk.protected_missing_provider.104cb87db2f9', 'job.krk.protected_missing_provider.38d0a11daf0c', 'job.krk.protected_missing_provider.4dca16fc81b3', 'job.krk.protected_missing_provider.54fd6c4dd136', 'job.krk.protected_missing_provider.5f9c11521077', 'job.krk.protected_missing_provider.6262bf8a2534', 'job.krk.protected_missing_provider.75babbcc6000', 'job.krk.protected_missing_provider.8343f8b595ba', 'job.krk.protected_missing_provider.8bd0028955fa', 'job.krk.protected_missing_provider.8d58e5a5f72c', 'job.krk.protected_missing_provider.9a4cc895c68d', 'job.krk.protected_missing_provider.9df1f2680cbc', 'job.krk.protected_missing_provider.a306768e24a0', 'job.krk.protected_missing_provider.abcf6fafb467', 'job.krk.protected_missing_provider.ac1e25bed37b', 'job.krk.strategy_owner_contrast.14c4d6d395bb', 'job.krk.strategy_owner_contrast.1a9dfe565e76', 'job.krk.strategy_owner_contrast.40d0a6e04b05', 'job.krk.strategy_owner_contrast.4dcd4cc180e8', 'job.krk.strategy_owner_contrast.5e053ab0baa8', 'job.krk.strategy_owner_contrast.6ca3b85ce53a', 'job.krk.strategy_owner_contrast.829c9b9fe98b', 'job.krk.strategy_owner_contrast.82e91a823777', 'job.krk.strategy_owner_contrast.d1744cd54930', 'job.krk.strategy_owner_contrast.e14d23798e77', 'job.krk.strategy_owner_contrast.eae6955cdd41', 'job.krk.strategy_owner_contrast.fca927c317d8']`
- `deduplicated_state_provider_rows`: `True`
- `label_key_count`: `48`
- `proposal_key_count`: `68`

## Decision

- Status: `state_local_contrast_labels_v2_joined`
- Recommended next step: `probe_state_local_contrast_selector_v2`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
