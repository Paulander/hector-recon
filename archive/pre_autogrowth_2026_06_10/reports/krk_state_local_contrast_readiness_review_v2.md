# KRK State-Local Contrast Readiness Review v2

This review closes the bounded diverse contrast-label slice. It is non-causal and does not authorize a runtime selector.

## Evidence Summary

- `row_count`: `20`
- `usable_training_row_count`: `12`
- `training_state_count`: `8`
- `stage7_challenge_row_count`: `8`
- `training_contrast_label_counts`: `{'negative': 3, 'positive': 9}`
- `stage7_contrast_label_counts`: `{'negative': 8}`
- `best_training_objective`: `stage_family_rank_score`
- `best_training_accuracy`: `0.75`
- `best_training_negative_suppression`: `0.0`
- `best_stage7_negative_suppression`: `0.0`
- `benchmark_underpowered`: `True`

## Readiness Failures

- `training_rows_under_40`
- `training_negative_labels_sparse`
- `leave_state_out_negative_suppression_zero`
- `stage7_heldout_negative_suppression_zero`
- `stage4_wrong_tempo_labels_deferred_due_to_runtime_cost`

## Interpretation

- The diverse labels confirm Stage 7 residual providers remain max_plies under forced ownership, but those rows are correctly held out and cannot train a selector.
- Protected training labels remain too positive-heavy after dedupe, so simple selectors still predict positives and fail to suppress negative controls.
- A runtime selector would currently inherit the same failure mode as broad additive support: insufficient negative ownership evidence.

## Decision

- Status: `runtime_selector_blocked_negative_suppression_zero`
- Recommended next step: `architecture_review_before_more_runtime_tests`
- Runtime test allowed next: `False`
- Blocked next steps: `['runtime_selector', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation', 'm3_m4_arbitration_update']`
