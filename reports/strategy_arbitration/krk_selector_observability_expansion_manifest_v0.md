# KRK Selector Observability Expansion Manifest v0

## Decision

- status: `selector_observability_expansion_manifest_ready`
- runtime_changes_allowed: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`
- execute_without_separate_runtime_behavior_approval: `True`
- behavior_changing_selector_allowed: `False`

## Summary

- case_count: `14`
- stage_counts: `{'stage4': 6, 'stage5': 4, 'stage6': 4}`
- selected_owner_counts: `{'selected_owner_converted': 4, 'selected_owner_failed': 10}`
- objective_channel_counts: `{'candidate_switch_contrast_seed': 5, 'failure_context_without_candidate_seed': 5, 'progress_window_failure_contrast_candidate': 2, 'safe_preservation_contrast_seed': 2}`
- non_stage0_owner_count: `3`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- replay_free_recovery_used_first: `True`
- bounded_observation_run_needed: `True`

## Rows

- `stage4_joined_trace_ownership_1` stage=stage4 owner=selected_owner_failed recommendation=`` target=``
- `stage4_joined_trace_ownership_2` stage=stage4 owner=selected_owner_failed recommendation=`` target=``
- `stage4_joined_trace_ownership_3` stage=stage4 owner=selected_owner_failed recommendation=`` target=``
- `stage4_joined_trace_ownership_4` stage=stage4 owner=selected_owner_failed recommendation=`` target=``
- `stage4_joined_trace_ownership_5` stage=stage4 owner=selected_owner_failed recommendation=`` target=``
- `stage4_joined_trace_ownership_6` stage=stage4 owner=selected_owner_failed recommendation=`` target=``
- `selector_objective_fresh_diversity.01` stage=stage5 owner=selected_owner_failed recommendation=`` target=``
- `selector_objective_fresh_diversity.02` stage=stage5 owner=selected_owner_failed recommendation=`` target=``
- `selector_objective_fresh_diversity.03` stage=stage5 owner=selected_owner_converted recommendation=`` target=``
- `selector_objective_fresh_diversity.04` stage=stage6 owner=selected_owner_failed recommendation=`` target=``
- `selector_objective_fresh_diversity.05` stage=stage6 owner=selected_owner_failed recommendation=`` target=``
- `selector_objective_fresh_diversity.06` stage=stage6 owner=selected_owner_converted recommendation=`` target=``
- `selector_objective_fresh_diversity.07` stage=stage5 owner=selected_owner_converted recommendation=`` target=``
- `selector_objective_fresh_diversity.08` stage=stage6 owner=selected_owner_converted recommendation=`` target=``
