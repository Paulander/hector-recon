# KRK Stage 4 Sequence Candidate Review v0

## Decision

- status: `stage4_first_move_ranking_gap`
- recommended_next_step: `non_causal_stage4_first_move_feature_review`
- causal_status: `non_causal_forced_first_move_sequence_review`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`

## Target

- state_id: `state.44938ccb8ab7`
- fen: `1R6/1K6/8/k7/8/8/8/8 w - - 0 1`
- selected_move_from_failure: `b8h8`
- source_primary_diagnosis: `stage4_sequence_followup_gap_single_state`

## Summary

- legal_first_move_count: `12`
- candidate_result_counts: `{'mate': 7, 'max_plies': 5}`
- converting_first_move_count: `7`
- converting_first_moves: `['b8e8', 'b8d8', 'b8c8', 'b7c8', 'b7a8', 'b7c7', 'b7c6']`
- selected_first_move_result: `max_plies`

## Interpretation

- selected first move b8h8 remains max_plies
- 7 legal first moves convert under the same bounded continuation
- the target is a repeated single-state caveat, so this is not enough for a broad selector

## Candidate Results

| first_move | result | total_plies | first_reply | first_successor_skill |
| --- | --- | ---: | --- | --- |
| b8h8 | max_plies | 40 | a5a4 | krk.stage0_basin |
| b8g8 | max_plies | 40 | a5a4 | krk.stage0_basin |
| b8f8 | max_plies | 40 | a5a4 | krk.stage0_basin |
| b8e8 | mate | 25 | a5a4 | krk.stage0_basin |
| b8d8 | mate | 25 | a5a4 | krk.stage0_basin |
| b8c8 | mate | 25 | a5a4 | krk.stage0_basin |
| b8a8 | max_plies | 40 | a5b5 | krk.stage0_basin |
| b7c8 | mate | 17 | a5a6 | krk.stage0_basin |
| b7a8 | mate | 21 | a5a6 | krk.stage0_basin |
| b7c7 | mate | 25 | a5a6 | krk.stage0_basin |
| b7a7 | max_plies | 40 | a5a4 | krk.stage0_basin |
| b7c6 | mate | 31 | a5a4 | krk.stage0_basin |

## Boundaries

- These forced-first-move labels are offline diagnostics, not ownership labels.
- No runtime selector, score change, direct routing, topology mutation, Stage 7 promotion, or Stage 8 training is authorized.
