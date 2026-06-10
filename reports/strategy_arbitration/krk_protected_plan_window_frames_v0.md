# KRK Protected Plan-Window Frames v0

Status: `protected_cross_stage_plan_window_evidence_extracted`

Replay-free extraction of protected Stage 4/5/6 plan-window evidence from existing handoff packets. This is not runtime PlanCapsule behavior.

## Summary

- frame_count: `20`
- source_stage_counts: `{'stage4': 10, 'stage5': 6, 'stage6': 4}`
- outcome_bucket_counts: `{'success': 19, 'failure': 1}`
- protected_cross_stage_evidence_met: `True`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Boundary

- These frames are non-causal replay-free evidence only.
- They do not select moves, score candidates, route providers, promote Stage 7, or train Stage 8.
