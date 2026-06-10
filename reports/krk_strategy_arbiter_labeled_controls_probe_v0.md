# KRK Strategy Arbiter Labeled Controls Probe v0

This is a replay-free probe over labeled trace-only observation controls.

## Summary

- Records: `21`
- Labeled controls: `14`
- Selected label counts: `{'negative': 5, 'positive': 9, 'unknown': 7}`
- Stage label counts: `{'stage4': {'negative': 2, 'positive': 3}, 'stage5': {'negative': 2, 'positive': 3, 'unknown': 1}, 'stage6': {'negative': 1, 'positive': 3}, 'stage7': {'unknown': 6}}`
- Positive rate on labeled controls: `0.6428571428571429`
- Negative rate on labeled controls: `0.35714285714285715`
- Stage7 unknown count: `6`

## Interpretation

- Trace-only observations now have context and provider summaries.
- Protected labeled controls are mixed under current raw selection.
- Stage7 rows remain unlabeled held-out challenge cases.
- This does not justify a runtime arbiter or Stage7 repair.

## Decision

Status: `labeled_controls_mixed_no_sandbox`
Sandbox ready: `False`
Runtime arbiter allowed: `False`
Recommended next step: `architecture_review_for_control_plane_selector_objective_or_more_labels`
