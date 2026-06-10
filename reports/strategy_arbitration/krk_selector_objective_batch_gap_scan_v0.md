# KRK Selector Objective Batch Gap Scan v0

This scan ranks replay-free evidence-expansion paths. It does not execute collection, train a selector, or authorize runtime behavior.

## Decision

- status: `selector_objective_diversity_improved_replay_free`
- collection_run_allowed: `False`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `stop_at_feature_probe_review_boundary`

## Summary

- seed_row_count: `21`
- fresh_collection_seed_row_count: `4`
- fresh_collection_joined_row_count: `8`
- fresh_collection_stage_counts: `{'stage5': 4, 'stage6': 4}`
- fresh_collection_provider_counts: `{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.fence_established': 1, 'krk.stage0_basin': 5}`
- fresh_collection_selected_owner_counts: `{'selected_owner_converted': 4, 'selected_owner_failed': 4}`
- fresh_collection_generated_frame_count: `76`
- duplicate_spent_manifest_count: `0`
- stage4_7_8_fresh_row_count: `0`
- unsafe_runtime_delta_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`
- seed_probe_status: `selector_objective_seed_probe_v2_ready_for_non_causal_benchmark`
- feature_probe_status: `selector_objective_feature_probe_v2_review_ready`
- replay_free_recovery_possible: `True`

## Ranked Evidence Paths

- rank=1 path=`more_selected_owner_failed_switch_contrast_rows` expected_rows=4 duplicate_risk=`low_against_spent_manifest; overlaps prior seed for some states but refresh counts improve` label_semantics_risk=`low: selected-owner labels remain offline outcomes, capacity frames are evidence only` stage_counts={'stage5': 2, 'stage6': 2} provider_counts={'krk.edge_trap_close': 1, 'krk.stage0_basin': 3}
- rank=2 path=`more_safe_preservation_controls` expected_rows=4 duplicate_risk=`low_against_spent_manifest; includes new protected plan-window states` label_semantics_risk=`low: safe-preservation labels are selected-owner outcomes, not capacity labels` stage_counts={'stage5': 2, 'stage6': 2} provider_counts={'krk.edge_trap_enemy_between': 1, 'krk.fence_established': 1, 'krk.stage0_basin': 2}
- rank=3 path=`more_non_stage0_selected_owner_rows` expected_rows=3 duplicate_risk=`low_against_spent_manifest; limited row count remains the main risk` label_semantics_risk=`low: provider family is provenance, not ownership` stage_counts={'stage5': 2, 'stage6': 1} provider_counts={'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.fence_established': 1}
- rank=4 path=`better_stage5_6_balance` expected_rows=8 duplicate_risk=`low_against_spent_manifest` label_semantics_risk=`low` stage_counts={'stage5': 4, 'stage6': 4} provider_counts={'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.fence_established': 1, 'krk.stage0_basin': 5}
- rank=5 path=`provider_family_diversity` expected_rows=8 duplicate_risk=`medium: stage0 remains dominant despite new families` label_semantics_risk=`low: provider family is used only as a visible/provenance feature` stage_counts={'stage5': 4, 'stage6': 4} provider_counts={'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.fence_established': 1, 'krk.stage0_basin': 5}
- rank=6 path=`progress_window_failure_contrasts` expected_rows=2 duplicate_risk=`low_against_spent_manifest; only two rows available` label_semantics_risk=`low: h40 selected-successor outcome labels stay offline` stage_counts={'stage5': 1, 'stage6': 1} provider_counts={'krk.edge_trap_enemy_between': 1, 'krk.stage0_basin': 1}
