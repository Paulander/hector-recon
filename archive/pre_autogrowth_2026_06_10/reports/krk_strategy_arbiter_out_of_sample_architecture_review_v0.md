# KRK Strategy Arbiter Out-of-Sample Architecture Review v0

This review closes the current out-of-sample selector-readiness slice. It is non-causal and does not implement a runtime arbiter, selector sandbox, Stage 7 repair, Stage 7 promotion, or Stage 8 training.

## Evidence

- Readiness status: `readiness_criteria_defined_sandbox_still_blocked`
- Balanced review status: `selector_signal_promising_sandbox_blocked_pending_readiness_criteria`
- Out-of-sample probe status: `out_of_sample_controls_guardrail_positive_selector_sandbox_blocked`
- Out-of-sample labels: `12`
- Selected results: `{'mate': 11, 'max_plies': 1}`
- Forced selected-provider results: `{'mate': 11, 'max_plies': 1}`
- Selected providers: `{'krk.stage0_basin': 12}`
- Stage results: `{'stage4:mate': 3, 'stage4:max_plies': 1, 'stage5:mate': 4, 'stage6:mate': 4}`
- Sandbox blockers: `['class_imbalance', 'selected_provider_dominance']`

## Interpretation

- Protected stack: `mostly_converts_on_bounded_out_of_sample_controls`
- Selector signal: `not_ready_due_to_class_imbalance_and_provider_dominance`
- Stage 4 caveat: `one_stage4_wrong_tempo_control_max_plies_h40`
- Stage 7 status: `local_valid_composition_quarantined_unchanged`
- Big picture: The evidence supports protected-provider preservation and current KRK handoff conversion on most controls, but does not yet establish a general strategy arbiter because selected-provider labels are dominated by stage0_basin.

## Decision

- Status: `selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse`
- Recommended next step: `design_selector_readiness_v2_or_strategy_owner_contrast_dataset`
- Runtime arbiter remains blocked.
- Selector sandbox remains blocked.
- Stage 7 repair/promotion and Stage 8 training remain blocked.

## Options

- `strategy_owner_contrast_dataset`: Collect or derive labels where multiple providers are plausible and at least one non-stage0 owner has conversion evidence. Status: `non_causal_only`.
- `selector_readiness_v2`: Revise readiness criteria to require provider diversity, balanced labels, and explicit selected-vs-forced label semantics. Status: `design_only`.
- `pause_runtime_arbiter`: Keep strategy arbitration as an evidence pipeline until labels distinguish strategy ownership rather than mostly confirming stage0 finishing. Status: `no_runtime_change`.
