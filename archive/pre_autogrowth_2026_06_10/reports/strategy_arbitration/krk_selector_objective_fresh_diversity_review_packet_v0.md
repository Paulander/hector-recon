# KRK Selector Objective Fresh Diversity Review Packet v0

Status: `fresh_stage5_stage6_diversity_collection_review_ready`

This artifact is review-only. It does not execute collection, train a selector, change runtime behavior, promote Stage 7, or train Stage 8.

## Summary

- candidate_row_count: `8`
- stage_counts: `{'stage5': 4, 'stage6': 4}`
- provider_counts: `{'krk.edge_trap_close': 1, 'krk.edge_trap_enemy_between': 1, 'krk.fence_established': 1, 'krk.stage0_basin': 5}`
- provider_family_counts: `{'edge_trap_close': 1, 'edge_trap_enemy_between': 1, 'fence_established': 1, 'stage0_basin': 5}`
- selected_owner_failed_count: `4`
- selected_owner_converted_count: `4`
- switch_contrast_count: `4`
- safe_preservation_count: `4`
- progress_window_failure_contrast_count: `2`
- non_stage0_selected_owner_count: `3`
- spent_manifest_duplicate_count: `0`
- duplicate_candidate_fen_count: `0`
- existing_seed_manifest_v2_state_overlap_count: `5`
- prior_diverse_review_packet_state_overlap_count: `3`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Candidate Rows

- `selector_objective_fresh_diversity.01` stage=`stage5` provider=`krk.stage0_basin` label=`selected_owner_failed` channel=`candidate_switch_contrast_seed` why=adds a Stage 5/6 selected-owner failure switch-contrast row without using capacity labels as ownership labels
- `selector_objective_fresh_diversity.02` stage=`stage5` provider=`krk.stage0_basin` label=`selected_owner_failed` channel=`candidate_switch_contrast_seed` why=adds a Stage 5/6 selected-owner failure switch-contrast row without using capacity labels as ownership labels
- `selector_objective_fresh_diversity.03` stage=`stage5` provider=`krk.fence_established` label=`selected_owner_converted` channel=`safe_preservation_contrast_seed` why=adds Stage 5/6 safe-preservation balance for the switch-vs-preserve objective
- `selector_objective_fresh_diversity.04` stage=`stage6` provider=`krk.stage0_basin` label=`selected_owner_failed` channel=`candidate_switch_contrast_seed` why=adds a Stage 5/6 selected-owner failure switch-contrast row without using capacity labels as ownership labels
- `selector_objective_fresh_diversity.05` stage=`stage6` provider=`krk.edge_trap_close` label=`selected_owner_failed` channel=`candidate_switch_contrast_seed` why=adds a Stage 5/6 selected-owner failure switch-contrast row without using capacity labels as ownership labels
- `selector_objective_fresh_diversity.06` stage=`stage6` provider=`krk.stage0_basin` label=`selected_owner_converted` channel=`safe_preservation_contrast_seed` why=adds Stage 5/6 safe-preservation balance for the switch-vs-preserve objective
- `selector_objective_fresh_diversity.07` stage=`stage5` provider=`krk.edge_trap_enemy_between` label=`selected_owner_converted` channel=`progress_window_failure_contrast_candidate` why=adds an unused protected plan-window state for future failure-contrast observation while avoiding the spent v0 manifest
- `selector_objective_fresh_diversity.08` stage=`stage6` provider=`krk.stage0_basin` label=`selected_owner_converted` channel=`progress_window_failure_contrast_candidate` why=adds an unused protected plan-window state for future failure-contrast observation while avoiding the spent v0 manifest

## Decision

- recommended_next_step: `stop_until_future_explicit_approval_to_execute_reviewed_collection`
- collection_run_allowed: `false`
- selector_training_allowed: `false`
- runtime_changes_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
