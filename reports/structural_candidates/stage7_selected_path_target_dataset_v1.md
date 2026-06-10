# Stage 7 Selected Path Target Dataset v1

Status: `split_target_dataset_ready_for_offline_probe_with_sandbox_sourced_sequence_controls`

The v1 dataset adds replay-free successful post-box sequence controls recovered from prior Stage 7 sandbox artifacts. These controls are offline-only and do not authorize runtime behavior.

## Summary

- row_count: `32`
- target_counts: `{'stage7.selected_path.strategy_ownership_gap.v0': 14, 'stage7.selected_path.sequence_continuation_gap.v0': 18}`
- row_role_counts: `{'stage7_selected_owner_failed_positive': 2, 'protected_safe_owner_control': 12, 'stage7_sequence_gap_unresolved': 2, 'stage7_sequence_success_control_recovered': 16}`
- ownership_target_minimally_trainable: `True`
- sequence_target_minimally_trainable: `True`
- benchmark_underpowered: `False`
- sequence_controls_recovered: `16`
- sequence_control_caveat: `sandbox_sourced_controls_offline_only`

Recommended next step: `run_non_causal_split_target_probe_only`

Blocked runtime work:

- `runtime arbiter`
- `abstention penalty tuning`
- `Stage 7 promotion`
- `Stage 8 training`
- `causal internal terminals`
