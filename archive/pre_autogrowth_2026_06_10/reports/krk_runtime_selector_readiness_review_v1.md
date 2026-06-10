# KRK Runtime Selector Readiness Review v1

This review closes the current runtime-selector evidence branch. It does not authorize runtime selector behavior.

## Evidence Statuses

- `runtime_test_review`: `runtime_sandbox_safe_but_additive_support_not_ready_to_scale`
- `objective_review`: `additive_support_objective_rejected_design_normalized_selector_objective`
- `normalized_objective_probe`: `normalized_objective_probe_underpowered_fields_available`
- `ranked_frame_probe`: `ranked_frames_available_label_semantics_too_coarse`
- `state_local_contrast_probe`: `state_local_contrast_signal_not_ready`

## Positive Results

- `default-off sandbox mechanics are trace-visible and default-safe`
- `small protected-control runtime tests showed no conversion/no-move/draw regression`
- `Stage7 challenge contexts are blocked by default`
- `normalized rank/score proxy improved over provenance baseline in offline labels`
- `ranked StrategyProposalFrame rows can be exported replay-free`

## Blocking Results

- `broad additive support is not effective at low support and unsafe to scale blindly`
- `ranked-frame labels are frame-level and too coarse for owner selection`
- `state-local contrast labels are sparse and do not suppress negative forced providers under leave-state-out`
- `Stage7 remains held out and unresolved`

## Readiness Assessment

- `runtime_selector`: `blocked`
- `more_additive_support_runtime_tests`: `blocked`
- `normalized_selector_objective`: `promising_but_needs_better_state_local_labels`
- `stage7_status`: `local_valid_composition_quarantined`
- `stage8_training`: `blocked`

## Minimum Next Evidence

- `more diverse state-local contrast labels across protected Stage4/5/6 states`
- `negative labels that are not dominated by one repeated provider family/state`
- `proposal-level ownership labels, not only frame-level outcome labels`
- `held-out Stage7 challenge evaluation after protected evidence improves`

## Decision

- Status: `runtime_selector_not_ready_collect_better_contrast_labels`
- Recommended next step: `design_small_diverse_state_local_contrast_label_plan`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Blocked Next Steps

- `runtime_selector`
- `increase_broad_additive_support`
- `stage7_repair`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
