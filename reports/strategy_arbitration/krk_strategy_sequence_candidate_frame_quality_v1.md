# KRK StrategySequenceCandidateFrame Quality Probe v1

This replay-free quality probe checks whether populated frames preserve the candidate-generation / selection split.

## Summary

- total_frames: 256
- protected_frame_count: 58
- stage7_challenge_frame_count: 198
- stage7_readiness_training_row_count: 0
- protected_positive_capacity_candidate_count: 11
- protected_visible_provider_proposal_count: 42
- sequence_candidate_count: 140
- sequence_candidate_mate_count: 0

## Quality Checks

- capacity_not_selector_label: `True`
- stage7_excluded_from_training_readiness: `True`
- runtime_flags_false: `True`
- sequence_candidates_all_heldout: `True`

## Decision

- status: `frame_quality_probe_supports_next_sequence_candidate_benchmark`
- recommended_next_step: `benchmark_candidate_frame_sources_before_runtime`
- runtime_sandbox_allowed: `False`
