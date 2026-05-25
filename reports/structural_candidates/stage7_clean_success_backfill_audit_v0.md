# Stage 7 Clean Success Backfill Audit v0

Status: `stage7_clean_success_backfill_exhausted_pending_label_execution`

This replay-free audit checks whether existing clean/default-off Stage 7 artifacts can close the clean success-control gate without running new labels. It does not train, route, score, promote Stage 7, or train Stage 8.

## Summary

- manifest_clean_candidate_count: `34`
- manifest_h40_compatible_row_count: `147`
- manifest_h40_compatible_result_counts: `{'max_plies': 80, 'mate': 67}`
- current_clean_success_controls: `2`
- clean_success_controls_required: `5`
- manifest_unique_success_controls: `2`
- eligible_new_success_controls: `0`
- projected_success_controls_after_backfill: `2`
- can_close_success_gate_replay_free: `False`
- current_clean_hard_negative_controls: `8`
- manifest_unique_hard_negative_controls: `8`
- sandbox_sourced_post_box_success_controls: `14`
- sandbox_sourced_post_box_unique_success_controls: `10`
- sandbox_sourced_controls_usable_for_clean_gate: `False`
- skipped_counts: `{'not_h40_compatible': 93}`
- runtime_authorization_row_count: `0`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Clean Success Keys

- raw_success_rows: `67`
- unique_success_keys: `2`
- duplicate_success_rows: `65`
- `2k5/8/2K1R3/8/8/8/8/8 w - - 0 1` move=`e6e8` sources=`28`
- `8/8/8/8/8/5K2/5R2/6k1 w - - 0 1` move=`f3g3` sources=`39`

## Non-Backfillable Evidence

- reason: `sandbox_or_repair_sourced_success_controls_are_not_clean_heldout_controls`
- sandbox_sourced_success_controls: `14`
- sandbox_sourced_unique_success_controls: `10`

## Decision

- recommended_next_step: `explicitly_approve_stage7_diverse_clean_label_execution_or_defer_sequence_benchmark`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
