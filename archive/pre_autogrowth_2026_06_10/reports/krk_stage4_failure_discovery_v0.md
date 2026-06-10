# KRK Stage 4 Failure Discovery v0

Replay-free review of the retry1 Stage 4 h40 caveat failure diversity.

## Decision

- status: `stage4_failure_discovery_collapsed_to_seed_state`
- selector_allowed: `False`
- selector_training_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `stage4_caveat_sequence_or_synthetic_contrast_review`

## Summary

- stage4_eval_total: `300`
- stage4_eval_conversion_failure_count: `32`
- failure_packet_count: `32`
- unique_failure_state_move_count: `1`
- unique_failure_states: `1`
- all_unique_failures_already_in_selector_seed: `True`
- independent_validation_target_counts: `{'preserve': 10}`
- independent_validation_underpowered: `True`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Unique Failure Rows

- `state.44938ccb8ab7` move=`b8h8` count=`32` in_seed=`True`

## Interpretation

- blind_label_farming_recommended: `False`
- why: `The retry1 Stage 4 h40 caveat has 32 failure packets but they collapse to one unique state/move, already present in selector seed v2. Random protected validation slices are therefore unlikely to add independent switch contrast.`
- recommended_evidence_path: `Stage4 caveat/sequence diagnosis or targeted synthetic/stratified failure manifest, not more random selected-owner validation.`
