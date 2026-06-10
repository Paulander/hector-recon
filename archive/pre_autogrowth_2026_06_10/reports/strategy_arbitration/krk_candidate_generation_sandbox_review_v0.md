# KRK Candidate-Generation Sandbox Review v0

This packet reviews a possible default-off candidate-generation sandbox scope. It does not authorize or implement runtime behavior.

## Decision

- status: `candidate_generation_observation_sandbox_review_ready`
- recommended_first_sandbox: `default_off_observation_only_candidate_generation`
- implementation_authorized_by_this_packet: `False`
- runtime_sandbox_allowed_by_this_packet: `False`

## Allowed Candidate Channels

### validated_provider_pack_proposals

- allowed_output: visible candidate/proposal frames for protected validated providers
- label_semantics: `capacity_evidence_not_ownership_label`
- runtime_effect_allowed: `observation_only`

### CandidateMoveFrame_legal_move_hypotheses

- allowed_output: visible legal-move hypotheses with move-shape/post-move/safety terms
- label_semantics: `move_hypothesis_not_selector_decision`
- runtime_effect_allowed: `observation_only`

### PlanCapsule_sequence_candidates

- allowed_output: visible bounded sequence-candidate frames and plan context
- label_semantics: `sequence_candidate_not_runtime_commitment`
- runtime_effect_allowed: `observation_only`

### broader_KRK_strategy_proposal_candidates

- allowed_output: visible strategy-family/context candidates from monitors and phase-boundary evidence
- label_semantics: `strategy_candidate_not_provider_route`
- runtime_effect_allowed: `observation_only`

## Generation vs Selection

- candidate_generation: Expands the visible consideration set by emitting traceable candidate/proposal frames with source terms and non-causal evidence.
- selection: Chooses, scores, suppresses, or routes among candidates. Selection remains blocked and requires a separate review.
- review_boundary: The proposed sandbox may emit candidates but must preserve the existing selected move/provider and score ordering.

## Sandbox Modes

- Mode A `observation_only_candidate_generation`: `recommended_first_runtime_sandbox_if_explicitly_approved_later`
- Mode B `proposal_set_expansion_only`: `review_later`
- Mode C `candidate_generation_plus_selector_handoff`: `not_allowed`

## Supporting Evidence

- protected_positive_capacity_candidates: 11
- protected_negative_capacity_ratio: 0.3125
- stage7_training_row_count: 0
- progress_window_supported_move_h40_mate_count: 0
- candidate_proposal_coverage_status: `candidate_generation_gap_confirmed`
- frame_quality_status: `frame_quality_probe_supports_next_sequence_candidate_benchmark`
- source_benchmark_status: `candidate_generation_sources_promising_selector_blocked`

## Explicitly Forbidden

- `selecting_a_provider`
- `selecting_a_move`
- `changing_scores`
- `suppressing_providers`
- `routing_directly_to_a_provider`
- `direct_request_true`
- `promoting_Stage7`
- `training_Stage8`
- `runtime_DTM_or_tablebase`
- `gameplay_time_topology_mutation`
- `hidden_Python_routing`
- `treating_capacity_labels_as_selector_labels`
- `guardrail_validation_before_target_smoke`

## Remaining Risks

- validated provider pack includes negative-capacity candidates
- capacity labels are not ownership labels
- Stage 7 sequence candidates are held-out challenge evidence only
- selection policy remains blocked
- candidate explosion and performance risk
- accidental hidden selector risk
- observation-only data may still be too narrow for later selector design

## Acceptance Criteria Before Implementation

Observation-only sandbox:

- explicit approval after this review
- default-off equivalence
- generated candidate count bounded
- no selected-move/provider delta
- score_delta = 0.0
- no topology mutation
- trace includes source terms
- Stage 7 rows remain held-out
- focused tests pass
- tiny smoke before any guardrail validation

Beyond observation-only:

- separate review required
- selector semantics reviewed separately
- target smoke improvement required before guardrails
