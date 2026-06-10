# KRK Candidate Proposal Quality Decision v1

This decision gate closes the current observation-candidate quality slice.

## Decision

- status: `candidate_proposal_quality_not_selector_ready`
- selector_allowed: `False`
- recommended_next_step: `design_broader_strategy_sequence_candidate_sources`

## Evidence

- dataset_row_count: 569
- quality_probe_row_count: 38
- stage7_challenge_row_count: 111
- best_probe: `candidate_move_frame_source`
- best_positive_precision: `0.864`
- best_positive_recall: `0.633`
- best_negative_suppression: `0.625`
- best_balanced_score: `0.629`

## Rationale

- observation-only candidate generation is safe and visible
- candidate proposal quality axes have some signal but do not jointly pass recall and negative-suppression thresholds
- more blind candidate-move capacity labels are inefficient because candidate coverage is broad and sparse
- PlanCapsule sequence and broader strategy candidates are still absent from runtime observation frames
- candidate generation remains separate from selection

## Blocked Next Steps

- `runtime_selector`
- `score_changes`
- `provider_routing`
- `guardrail_campaign`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
