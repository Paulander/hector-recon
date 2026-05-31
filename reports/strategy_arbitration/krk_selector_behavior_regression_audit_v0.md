# KRK Selector Behavior Regression Audit v0

This is a non-causal audit of the protected validation regression. It does not implement a fix or authorize runtime behavior changes.

## Summary

- validation_decision_status: `selector_behavior_sandbox_regresses_safe_controls`
- smoke_decision_status: `selector_behavior_sandbox_target_improved`
- regressed_safe_control_count: `1`
- successful_switch_count: `2`
- sample_scope: `stage5_6_protected_joined_trace_h40`
- sample_count: `8`
- enabled_switch_count: `0`
- target_improvement_count: `0`
- safe_regression_count: `1`
- h40_regression_count: `1`
- h40_improvement_count: `0`
- preserve_noop_count: `6`
- abstain_noop_count: `0`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- smoke_target_improvement_count: `2`
- smoke_safe_regression_count: `0`

## Regressed Safe-Control Row

- row_id: `joined_trace_ownership_4`
- state_id: `state.2c1d6da27ea1`
- stage: `stage5`
- selected_before: `selected_owner_converted / krk.stage0_basin / a7a8`
- replacement: `None / None`
- recommendation_class: `preserve_selected_owner`
- baseline_outcome: `{'engine_decision_count': 9, 'engine_ticks_max': 8, 'engine_ticks_total': 72, 'plies': 17, 'result': 'mate'}`
- enabled_outcome: `{'engine_decision_count': 20, 'engine_ticks_max': 8, 'engine_ticks_total': 160, 'plies': 40, 'result': 'max_plies'}`
- interpretation: The protected safe-control state did not switch on the first selector decision; it preserved the selected owner. The regression appears only in the enabled h40 continuation, so the saved data is insufficient to name a specific replacement move/provider as the direct cause.

## Cause Classification

- primary_causes: `['safe_preservation_veto_missing', 'visible_alternative_overtrusted', 'horizon/noise issue']`
- explanation: The regression is a protected h40 safe-control regression without a first-position switch. The cause is therefore classified as a missing safe-preservation/continuation veto plus overtrust in visible alternatives under limited-horizon validation, not as a demonstrated implementation bug.

## Successful Switch Comparison

- successful_switch_count: `2`
- regressed_safe_control_count: `1`
- separation_assessment: The available first-row metadata separates successful target switches from the safe-control row, but the actual regression is a later h40 continuation effect. That prevents a clean causal narrowing rule from this artifact alone.
- successful_switch: `stage4_joined_trace_ownership_1` `stage4` `selected_owner_failed` `d6c7 -> d6d5`
- successful_switch: `selector_objective_fresh_diversity.05` `stage6` `selected_owner_failed` `h7c7 -> a5b6`

## Non-Causal Fix Evaluation

- add safe-preservation veto: `promising_but_not_sufficient_from_current_data` - The regressed row is an offline safe-preservation control, but using that label directly at runtime would violate label semantics. A runtime-visible proxy needs a separate review.
- require stronger failure-risk evidence before switch: `needs_more_continuation_observability` - The first-row decision did not switch, so stronger first-row evidence would not explain the h40 continuation regression without tracing later enabled decisions.
- require target row class / switch-contrast scope: `not_runtime_eligible_as_stated` - Target row class is an audit label, not a runtime-visible ownership label. It can scope future tests but should not become behavior logic.
- abstain instead of switching on ambiguous patterns: `promising_only_after_terms_are_identified` - Ambiguity terms must be runtime-visible and must capture the later continuation switch, not just the protected row's first decision.
- restrict to exact recommendation/evidence class that improved earlier: `overfit_risk` - The two successful switches are a tiny sample and do not cover h40 continuation behavior on protected safe controls.
- quarantine behavior selector if separation is not clean: `recommended_now` - Protected validation produced one safe-control regression and no h40 improvements. Quarantine prevents promoting an unsafe causal path.

## Recommendation

- decision_recommendation: `selector_behavior_quarantined_due_to_safe_regression`
