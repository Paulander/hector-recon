# KRK Candidate-Generation v3 Training Refresh Review

This review decides whether dataset v3 supports designing an offline candidate-generation training refresh. It does not implement training or runtime behavior.

## Decision

- status: `candidate_generation_v3_training_refresh_design_ready_non_causal`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `design_offline_candidate_generation_training_refresh_v3`

## Summary

- candidate_generation_training_row_count: `26`
- selector_training_row_count: `0`
- stage7_readiness_training_row_count: `0`
- runtime_trace_feature_row_count: `44`
- exact_positive_capacity_recall_from_trace: `0.3076923076923077`
- stage_family_positive_capacity_recall_from_trace: `0.7692307692307693`
- stage_family_negative_capacity_exposure_from_trace: `0.0`

## Allowed Next Design Scope

- offline_candidate_generation_training_refresh_design: `True`
- runtime_candidate_generator_change: `False`
- selector_training: `False`
- score_or_routing_change: `False`
- stage7_training_or_promotion: `False`

## Design Requirements

- `train/evaluate candidate-generation recall only, not ownership selection`
- `use protected Stage 4/5/6 rows only for readiness`
- `keep Stage 7 as held-out challenge evidence`
- `separate exact state/provider/move coverage from stage/family context`
- `report negative-capacity exposure by stage/family`
- `emit review packet before any runtime change`

## Blockers Before Runtime

- `no explicit ownership selector labels`
- `exact positive-capacity trace recall is partial`
- `capacity labels are not runtime ownership labels`
- `runtime observation context cannot select or score`
