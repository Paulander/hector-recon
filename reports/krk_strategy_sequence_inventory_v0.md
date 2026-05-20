# KRK Strategy / Sequence Inventory v0

Status: `replay_free_inventory_complete_sequence_gap_blocks_runtime`

Replay-free inventory of existing evidence for the split strategy-ownership and sequence-policy tracks.

## Strategy Ownership

- ranked_frame_count: `87`
- ranked_frame_training_rows: `42`
- ranked_frame_stage7_challenge_rows: `45`
- state_local_contrast_rows: `20`
- state_local_training_rows: `12`
- training_label_counts: `{'negative': 3, 'positive': 9}`
- provider_family_counts: `{'drive_to_edge': 2, 'edge_trap': 9, 'fence_established': 2, 'stage0_basin': 7}`
- stage7_contrast_label_counts: `{'negative': 8}`
- state_holdout_probe_status: `state_local_contrast_signal_not_ready`
- ready_for_runtime_review: `False`

## Sequence Policy

- clean_control_count: `10`
- role_counts: `{'clean_sequence_hard_negative': 8, 'clean_sequence_success_control': 2}`
- source_classification_counts: `{'clean_current_profile_candidate': 5, 'clean_default_off_candidate': 5}`
- success_controls_met: `False`
- hard_negatives_met: `True`
- stage7_clean_review_status: `stage7_clean_control_collection_paused_architecture_review_required`
- ready_for_runtime_review: `False`

## Gaps

- strategy_ownership_has_some_signal: `True`
- strategy_ownership_state_holdout_ready: `False`
- sequence_policy_has_clean_success_gap: `True`
- runtime_work_allowed: `False`

Recommended next step: `review_diverse_sequence_policy_controls_or_curriculum_boundary`
