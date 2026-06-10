# Stage 7 Clean Success Backfill Audit v0

Status: `stage7_clean_success_backfill_available`

This replay-free audit checks whether existing clean/default-off Stage 7 artifacts can close the clean success-control gate without running new labels. It does not train, route, score, promote Stage 7, or train Stage 8.

## Summary

- manifest_clean_candidate_count: `46`
- manifest_h40_compatible_row_count: `243`
- manifest_h40_compatible_result_counts: `{'max_plies': 145, 'mate': 98}`
- current_clean_success_controls: `11`
- clean_success_controls_required: `5`
- manifest_unique_success_controls: `11`
- eligible_new_success_controls: `0`
- projected_success_controls_after_backfill: `11`
- can_close_success_gate_replay_free: `True`
- current_clean_hard_negative_controls: `39`
- manifest_unique_hard_negative_controls: `39`
- sandbox_sourced_post_box_success_controls: `16`
- sandbox_sourced_post_box_unique_success_controls: `15`
- sandbox_sourced_controls_usable_for_clean_gate: `False`
- skipped_counts: `{'not_h40_compatible': 93}`
- runtime_authorization_row_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Clean Success Keys

- raw_success_rows: `98`
- unique_success_keys: `11`
- duplicate_success_rows: `87`
- `2k5/8/2K1R3/8/8/8/8/8 w - - 0 1` move=`e6e8` sources=`39`
- `3K2k1/8/8/8/8/8/1R6/8 w - - 0 1` move=`b2b7` sources=`1`
- `7k/8/8/8/R7/8/K7/8 w - - 0 1` move=`a4h4` sources=`1`
- `8/3R4/8/7k/8/8/1K6/8 w - - 0 1` move=`b2c1` sources=`1`
- `8/8/2R5/8/8/8/6k1/3K4 w - - 0 1` move=`c6c8` sources=`1`
- `8/8/3R4/6K1/8/6k1/8/8 w - - 0 1` move=`d6a6` sources=`1`
- `8/8/6R1/4K3/8/7k/8/8 w - - 0 1` move=`g6g1` sources=`1`
- `8/8/8/8/8/5K2/5R2/6k1 w - - 0 1` move=`f3g3` sources=`50`
- `8/8/8/8/8/8/k1K5/3R4 w - - 0 1` move=`d1d3` sources=`1`
- `8/8/8/R7/8/8/1K2k3/8 w - - 0 1` move=`a5h5` sources=`1`
- `8/8/R3K3/8/5k2/8/8/8 w - - 0 1` move=`e6f6` sources=`1`

## Non-Backfillable Evidence

- reason: `sandbox_or_repair_sourced_success_controls_are_not_clean_heldout_controls`
- sandbox_sourced_success_controls: `16`
- sandbox_sourced_unique_success_controls: `15`

## Decision

- recommended_next_step: `refresh_sequence_policy_inputs_with_replay_free_backfill`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
