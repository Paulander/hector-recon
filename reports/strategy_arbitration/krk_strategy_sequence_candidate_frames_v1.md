# KRK StrategySequenceCandidateFrame Population v1

This artifact materializes replay-free, non-causal candidate frames for the KRK strategy/sequence control plane.

## Summary

- frame_count: 256
- state_count: 25
- frame_type_counts: `{'broader_krk_strategy_candidate': 13, 'candidate_move_hypothesis': 140, 'validated_provider_candidate': 103}`
- source_stage_counts: `{'stage4': 12, 'stage5': 23, 'stage6': 23, 'stage7': 198}`
- stage7_challenge_row_count: 198
- readiness_training_stage7_row_count: 0
- selector_training_row_count: 42
- candidate_generation_training_row_count: 11

## Semantics

- Capacity evidence remains candidate-generation evidence, not ownership selection.
- Visible proposal frames preserve normal-routing context, not final selector authority.
- Progress-window candidate moves are held-out Stage 7 challenge evidence.
- Internal-monitor strategy candidates remain non-causal control-plane evidence.

## Decision

- status: `strategy_sequence_frames_populated_non_causal`
- recommended_next_step: `probe_strategy_sequence_candidate_frame_quality_v1`
- runtime_sandbox_allowed: `False`
