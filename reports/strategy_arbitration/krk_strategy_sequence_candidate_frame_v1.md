# KRK Strategy/Sequence Candidate Frame v1

Non-causal schema design for candidate-generation hypotheses. This is not a runtime generator, selector, or arbiter.

## Purpose

Represent visible candidate-generation hypotheses for KRK strategy/sequence control without treating capacity evidence as selector labels.

## Frame Types

- `validated_provider_candidate` from `protected_forced_provider_capacity`: Existing provider has offline capacity evidence in this state/context. semantics=`capacity_evidence_not_ownership_label`
- `candidate_move_hypothesis` from `CandidateMoveFrame`: Legal move has visible move-shape/post-move terms worth evaluating. semantics=`move_hypothesis_not_selector_decision`
- `plan_capsule_sequence_candidate` from `PlanCapsuleSpec_or_sequence_window`: A bounded multi-step continuation may be needed. semantics=`sequence_candidate_not_runtime_commitment`
- `broader_krk_strategy_candidate` from `phase_boundary_or_internal_monitor`: Current local stage may need handoff to a broader strategy family. semantics=`strategy_candidate_not_provider_route`

## Required Fields

`['schema_version', 'frame_id', 'state_id', 'fen', 'source_stage', 'active_landmark_label', 'frame_type', 'candidate_id', 'candidate_provider_id', 'candidate_move_uci', 'candidate_plan_id', 'candidate_strategy_family', 'source_terms', 'move_shape_terms', 'post_move_terms', 'safety_terms', 'internal_monitor_terms', 'capacity_evidence', 'ownership_evidence', 'sequence_evidence', 'label_semantics', 'stage7_challenge_row', 'usable_for_selector_training', 'usable_for_candidate_generation_training', 'causal_status']`

## Forbidden Causal Uses

`['direct_provider_request', 'direct_move_selection', 'runtime_dtm_or_tablebase_lookup', 'gameplay_topology_mutation', 'stage7_promotion', 'stage8_training_from_stage7', 'default_policy_change']`

## Decision

- status: `strategy_sequence_candidate_frame_schema_defined`
- next: `populate_strategy_sequence_candidate_frames_replay_free_v1`
- runtime_sandbox_allowed: `False`
