# KRK Balanced Hard-Negative Evidence Review v0

Review after two bounded protected hard-negative label slices.

## Summary

- `new_label_count`: `24`
- `new_positive_capacity_count`: `20`
- `new_negative_capacity_count`: `4`
- `expanded_row_count`: `40`
- `expanded_positive_context_count`: `31`
- `expanded_hard_negative_count`: `9`
- `expanded_hard_negative_state_count`: `4`
- `stage7_row_count`: `0`
- `best_objective`: `provider_piece_king_delta@0.5`
- `best_negative_suppression`: `0.2222222222222222`
- `best_positive_recall`: `1.0`
- `underpowered`: `True`

## Interpretation

- `what_was_fixed`: The original evidence defect was real: hard negatives expanded from five rows to nine rows, and protected rows expanded to forty without Stage 7 training rows.
- `what_remains_blocked`: The label set is still hard-negative sparse and state-narrow. A simple offline rule now has nonzero suppression, but the evidence is not robust enough for selector training or runtime use.
- `why_not_more_blind_labels`: The second bounded slice produced only one hard negative from twelve jobs. More blind forced-provider labels are likely inefficient unless guided by sharper semantics or candidate features.

## Decision

- `status`: `balanced_hard_negative_signal_promising_but_underpowered`
- `recommended_next_step`: `review_label_semantics_or_design_stronger_selector_features_before_more_label_jobs`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `more_blind_label_farming_recommended`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
