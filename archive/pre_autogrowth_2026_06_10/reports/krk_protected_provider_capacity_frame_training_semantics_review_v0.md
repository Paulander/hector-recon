# KRK Protected Provider Capacity Frame Training Semantics Review v0

This review decides whether protected capacity frames are safe to use as selector-training rows. They are not.

## Summary

- `row_count`: `16`
- `positive_capacity_count`: `11`
- `negative_capacity_count`: `5`
- `stage7_row_count`: `0`
- `training_row_count`: `0`
- `runtime_proposal_row_count`: `0`
- `provider_family_counts`: `{'stage0_basin': 3, 'fence_established': 3, 'edge_trap': 9, 'drive_to_edge': 1}`
- `source_stage_counts`: `{'stage5': 7, 'stage6': 3, 'stage4': 6}`

## Findings

- `forced_provider_capacity_is_not_direct_selector_supervision`: Positive capacity labels should not become selector positives without a separate proposal-generation or ownership review.
- `candidate_generation_gap_precedes_selector_gap`: The architecture needs non-causal proposal/candidate coverage evidence before selector training can be evaluated fairly.
- `negative_capacity_labels_are_useful_hard_negatives_but_not_runtime_vetoes`: They can test capacity limits, but must not suppress providers at runtime.

## Allowed Uses

- `proposal_coverage_audit`
- `candidate_generator_evaluation`
- `capacity_map_diagnostic`
- `state_provider_contrast_review`

## Blocked Uses

- `direct_selector_training_positive`
- `runtime_provider_boost`
- `runtime_provider_penalty`
- `runtime_candidate_generation`
- `topology_edge_creation`
- `stage7_repair_or_promotion`
- `stage8_training`

## Requirements Before Training Use

- `define a separate candidate-generator target or runtime-proposal target`
- `separate forced-provider capacity labels from selected-playout and runtime-proposal labels`
- `validate false positives with protected guardrails`
- `include negative-capacity labels and same-state alternatives`
- `keep Stage 7 held out unless explicitly reclassified`
- `run a non-causal review before any sandbox`

## Decision

- `status`: `capacity_frames_diagnostic_not_selector_training_ready`
- `recommended_next_step`: `design_non_causal_candidate_generator_coverage_audit`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
