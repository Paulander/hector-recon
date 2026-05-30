# Current Agent Brief

This report is the canonical current-agent brief. The root `current_agent_brief.md`
is only a pointer to this file.

## Active KRK Gate

- Previous approved protected plan-window failure-contrast collection completed with status `collection_complete_underpowered`.
- Collection outputs: `reports/strategy_arbitration/protected_plan_window_failure_contrasts/`.
- Collection result: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_result_v0.json`.
- Follow-up packet: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_followup_review_packet_v0.json` with status `blocked_needs_human_approval`.
- Current gate exposes `review_protected_plan_window_failure_contrast_manifest`, not a collection command.
- Additional-collection decision note: `reports/strategy_arbitration/krk_protected_failure_contrast_additional_collection_decision_v1.json`.

## Current Decision

- Decision status: `protected_failure_contrast_collection_not_worth_running`.
- The currently reviewed v0 manifest is the already-spent manifest; its six outputs already exist and all are `conversion_positive`.
- The v0 manifest includes Stage 4 rows and does not satisfy the new Stage 5/6-only diversity condition for the conditional follow-up approval.
- The conditional approval for one additional collection was not consumed.
- Do not execute additional protected failure-contrast collection without a fresh reviewed Stage 5/6-only diversity manifest and explicit approval.
- Fresh selector-objective diversity packet: `reports/strategy_arbitration/krk_selector_objective_fresh_diversity_review_packet_v0.json` with status `fresh_stage5_stage6_diversity_collection_review_ready`.
- This packet is review-only; it authorizes no collection, selector training, runtime behavior, Stage 7 promotion, or Stage 8 training.

## Verified Invariants

- Selected move/provider deltas, score deltas, and routing deltas remain zero in the previous collection result.
- Runtime behavior changed: false.
- Runtime DTM/tablebase use: false.
- Gameplay-time topology mutation: false.
- Selector training rows, Stage 7 training rows, and runtime authorization rows: zero.
- Stage 7 remains held out/challenge only.
- Stage 7 promotion and Stage 8 training remain blocked.
- M1-M4 semantics remain preserved.
- Capacity labels are not ownership labels.

## Next Needed Work

- If more protected failure-contrast evidence is desired, first author and review a fresh bounded Stage 5/6-only diversity manifest.
- The fresh Stage 5/6-only selector-objective diversity packet is ready for human review; execution would require a separate explicit approval.
- Do not set runtime-ready, selector-ready, Stage 7-ready, or Stage 8-ready from the current evidence.
