# KRK Strategy Arbiter Out-of-Sample Control Probe v0

This replay-free probe evaluates the new protected-control labels. It does not implement a selector, change runtime behavior, promote Stage 7, or train Stage 8.

## Metrics

- Label count: `12`
- Selected result counts: `{'mate': 11, 'max_plies': 1}`
- Forced selected-provider result counts: `{'mate': 11, 'max_plies': 1}`
- Selected provider counts: `{'krk.stage0_basin': 12}`
- Stage result counts: `{'stage4:mate': 3, 'stage4:max_plies': 1, 'stage5:mate': 4, 'stage6:mate': 4}`
- Forced selected agreement rate: `1.000`
- Selected provider dominance: `1.000`

## Interpretation

- Out-of-sample controls mostly confirm the protected stack converts under current routing.
- All selected providers are dominated by stage0_basin, so this is weak evidence for a general selector.
- The single Stage4 max_plies remains a protected-control caveat, not Stage7 evidence.

## Decision

- Status: `out_of_sample_controls_guardrail_positive_selector_sandbox_blocked`
- Sandbox blockers: `['class_imbalance', 'selected_provider_dominance']`
- Recommended next step: `architecture_review_of_selector_signal_before_runtime_sandbox`
