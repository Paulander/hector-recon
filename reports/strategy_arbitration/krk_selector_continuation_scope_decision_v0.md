# KRK Selector Continuation Scope Decision v0

## Decision

- status: `selector_scope_initial_owner_only_supported`
- promote_selector: `False`
- make_default: `False`
- implement_fix_now: `False`
- write_future_narrowed_sandbox_review_only: `True`
- train_stage8: `False`
- promote_stage7: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `write a separate future default-off narrowed selector sandbox review that allows behavior only for initial-owner choice and blocks active continuation windows`

## Evidence

- regression_row_id: `joined_trace_ownership_4`
- regression_ply: `4`
- successful_initial_switch_count: `2`
- safe_regression_count: `1`
- target_improvement_count: `2`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- selector_remains_quarantined: `True`

## Rationale

Initial-owner-only scoping matches the current positive evidence and blocks the known ply-4 continuation regression. It is not an implemented fix; it is only supported enough for a future default-off review packet.
