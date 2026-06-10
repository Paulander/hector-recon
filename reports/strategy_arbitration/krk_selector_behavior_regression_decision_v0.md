# KRK Selector Behavior Regression Decision v0

This decision records the result of the regression audit. It does not implement a fix or authorize runtime behavior changes.

## Decision

- status: `selector_behavior_quarantined_due_to_safe_regression`
- promote: `False`
- make_default: `False`
- implement_fix_now: `False`
- write_narrowing_review_packet_now: `False`
- run_full_broad_guardrails: `False`
- train_anything: `False`
- selector_training_allowed: `False`
- stage7_promotion_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `quarantine_behavior_selector_and_collect_continuation_observability_before_any_narrowing_or_veto_review`

## Evidence

- regressed_safe_control_count: `1`
- successful_switch_count: `2`
- protected_safe_regression_row_ids: `['joined_trace_ownership_4']`
- enabled_switch_count_on_protected_sample: `0`
- target_improvement_count_on_protected_sample: `0`
- h40_regression_count: `1`
- h40_improvement_count: `0`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- runtime_behavior_changed: `False`
- runtime_dtm_or_tablebase_lookup: `False`
- gameplay_topology_mutation: `False`

## Rationale

Protected validation found one safe-control h40 regression and no h40 improvements. Because the regression row did not switch on the first decision, the current artifacts do not provide a clean causal separator for a narrow fix. The behavior selector should remain quarantined rather than narrowed or promoted.
