# Current Agent Brief

## Active KRK Gate

- Completed the explicitly approved bounded protected plan-window failure-contrast observation collection.
- Collection outputs: `reports/strategy_arbitration/protected_plan_window_failure_contrasts/`.
- Collection result: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_result_v0.json` with status `collection_complete_underpowered`.
- Follow-up review-only packet: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_followup_review_packet_v0.json` with status `blocked_needs_human_approval`.

## Verified Invariants

- Approved run produced 6 valid observation-only outputs, all `conversion_positive`; no new protected plan-window failure rows integrated.
- Selected move/provider deltas, score deltas, and routing deltas are zero.
- Runtime DTM/tablebase use is false.
- Gameplay-time topology mutation is false.
- Selector training rows, Stage 7 training rows, and runtime authorization rows are zero.
- Stage 7 promotion and Stage 8 training remain blocked.

## Next Needed Work

- Replay-free recovery from current artifacts is not enough: protected plan-window evidence remains sparse at 1 failure vs 19 positives in the benchmark review.
- Do not execute additional protected plan-window collection without fresh explicit approval.
- Do not set runtime-selector-ready from the current evidence.
