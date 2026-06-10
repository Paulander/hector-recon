# KRK Strategy / Sequence Inventory v0

Status: `replay_free_inventory_state_holdout_gap_blocks_runtime`

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

- clean_control_count: `50`
- role_counts: `{'clean_sequence_hard_negative': 39, 'clean_sequence_success_control': 11}`
- source_classification_counts: `{'clean_baseline_candidate': 40, 'clean_current_profile_candidate': 5, 'clean_default_off_candidate': 5}`
- success_controls_met: `True`
- hard_negatives_met: `True`
- stage7_clean_review_status: `stage7_clean_control_collection_closed_heldout_only`
- ready_for_runtime_review: `False`

## Gaps

- strategy_ownership_has_some_signal: `True`
- strategy_ownership_state_holdout_ready: `False`
- sequence_policy_has_clean_success_gap: `False`
- sequence_policy_clean_gate_closed: `True`
- state_holdout_gap_blocks_runtime: `True`
- runtime_work_allowed: `False`

Recommended next step: `review_state_holdout_signal_before_runtime_or_continue_protected_failure_contrast_gate`
