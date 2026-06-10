# KRK Protected Strategy Monitor Observation Source Review Packet v1

This packet is a review artifact only. It does not implement runtime source expansion.

## Decision

- status: `protected_repair_monitor_observation_source_review_ready`
- implementation_allowed_by_this_packet: `False`
- selector_allowed: `False`
- recommended_next_step: `request_explicit_approval_for_default_off_repair_monitor_observation_source`

## Future Scope If Explicitly Approved Later

- candidate_source: `broader_strategy_candidate`
- strategy_family: `terminal.krk.repair_needed_monitor`
- mode: `observation_only`
- default_off_required: `True`
- direct_request: `False`
- score_delta: `0.0`
- causal_status: `observation_only`
- protected_stages: `['stage4', 'stage5', 'stage6']`
- stage7_usage: `held_out_evaluation_only`

## Evidence

- expanded_frame_count: `85`
- expanded_frame_count_by_stage: `{'stage4': 20, 'stage5': 30, 'stage6': 35}`
- repair_needed_frame_count: `13`
- repair_needed_failure_precision: `0.7692307692307693`
- repair_needed_success_precision: `0.23076923076923078`
- stage7_challenge_row_count: `0`

## Required Future Acceptance

- separate explicit approval before implementation
- default-off flag
- default-off equivalence on protected Stage 4/5/6 and Stage 7 held-out smoke
- emit observation frames only
- no selected move/provider delta
- no score changes
- no direct routing or provider request
- bounded candidate count
- trace visible source terms and monitor id
- Stage 7 remains held-out and not training/readiness

## Explicitly Forbidden

- `selector`
- `provider_boost`
- `provider_suppression`
- `score_change`
- `direct_provider_route`
- `guardrail_campaign_from_observation_only_source`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
