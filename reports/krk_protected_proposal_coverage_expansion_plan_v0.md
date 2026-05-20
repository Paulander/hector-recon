# KRK Protected Proposal Coverage Expansion Plan v0

This is a non-causal design plan. It does not implement a runtime selector or alter topology.

## Problem

Protected forced-provider labels exist, but current StrategyProposalFrame rows omit those providers.

A selector benchmark cannot learn or evaluate a provider that is absent from the candidate frame. This is proposal-coverage evidence, not evidence that runtime selection should change.

## Expansion Design

- Artifact: `krk_protected_provider_coverage_frames_v0`
- Candidate record kind: `non_causal_protected_provider_candidate_frame`
- Rows to create: `16`
- Required fields: `['state_id', 'frame_id', 'source_stage', 'active_landmark_label', 'provider_id', 'provider_family', 'provider_version', 'forced_result', 'forced_plies', 'forced_first_move', 'label_semantics = forced_provider_capacity_label', 'proposal_source = offline_forced_provider_label_not_runtime_proposal', 'usable_for_training = false initially', 'causal_status = non_causal']`
- Must not include: `['runtime score override', 'provider support bonus', 'provider penalty', 'topology edge', 'runtime selector decision', 'DTM/tablebase runtime label']`

## Label Semantics

- `forced_provider_capacity_label`: Shows whether a provider can convert when forced for the first White move and then released. It is capacity/coverage evidence, not direct selector-positive evidence.
- `runtime_proposal_label`: Shows a provider was actually proposed in a runtime trace. The current missing labels are not this.
- `selected_playout_success`: Shows the normally selected path converted; separate from provider capacity.

## Acceptance For Next Slice

- `generate_rows_for_all_missing_protected_labels`: `16`
- `stage7_rows_allowed`: `0`
- `runtime_work_allowed`: `False`
- `training_allowed_initially`: `False`
- `requires_followup_review_before_training_use`: `True`

## Decision

- `status`: `protected_proposal_coverage_expansion_plan_ready`
- `recommended_next_step`: `build_non_causal_protected_provider_coverage_frames_v0`
- `runtime_work_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
