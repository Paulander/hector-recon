# Stage 7 Selected Path Target Dataset v0

Status: `ownership_target_minimal_sequence_target_underpowered`

Replay-free dataset assembled from existing target specs, abstention context labels, and state-local contrast labels.

## Summary

- row_count: `16`
- target_counts: `{'stage7.selected_path.strategy_ownership_gap.v0': 14, 'stage7.selected_path.sequence_continuation_gap.v0': 2}`
- row_role_counts: `{'stage7_selected_owner_failed_positive': 2, 'protected_safe_owner_control': 12, 'stage7_sequence_gap_unresolved': 2}`
- stage_counts: `{'stage7': 4, 'stage5': 7, 'stage6': 3, 'stage4': 2}`
- ownership_target_minimally_trainable: `True`
- sequence_target_minimally_trainable: `False`
- benchmark_underpowered: `True`

## Interpretation

The strategy-ownership target has a minimal positive/control split, but only two Stage 7 positive states. The sequence/continuation target has unresolved negative/gap states but no replay-free successful Stage 7 sequence controls in this dataset.

Recommended next step: `collect_or_recover_successful_post_box_sequence_controls_before_sequence_policy_runtime_work`

Blocked runtime work:

- `runtime arbiter`
- `abstention penalty tuning`
- `Stage 7 promotion`
- `Stage 8 training`
- `causal internal terminals`
