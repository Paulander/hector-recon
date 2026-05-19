# KRK Control-Plane Evidence Contract v0

This is a non-causal schema contract. It does not add runtime terminals, runtime arbitration, score changes, topology mutation, Stage 7 promotion, or Stage 8 training.

## Purpose

Provide a shared non-causal data boundary for strategy arbitration, internal monitors, sequence-policy redesign, growth governance, and guardrail-aware promotion review.

## Primary Frame

- Name: `ControlPlaneEvidenceFrame`
- Schema: `control_plane_evidence_frame.v1`
- Causal status: `non_causal`

Required fields:

- `frame_id`
- `domain`
- `state_id`
- `fen`
- `source_stage`
- `active_landmark_label`
- `protected_provider_provenance`
- `strategy_proposal_frames`
- `internal_monitor_records`
- `plan_capsule_window_records`
- `sequence_training_examples`
- `outcome_labels`
- `guardrail_result_summaries`
- `growth_governor_status`
- `promotion_gate_status`
- `source_artifacts`
- `causal_status`

Forbidden fields:

- `runtime_selected_provider_override`
- `runtime_move_override`
- `runtime_score_bonus`
- `runtime_provider_penalty`
- `runtime_dtm_or_tablebase_label`
- `gameplay_topology_patch`

## Subschemas

### ProtectedProviderProvenance

- Schema: `protected_provider_provenance.v1`
- Purpose: Identify which validated provider pack or overlay produced evidence.
- Required fields: `skill_id`, `provider_version`, `source_stage`, `source_checkpoint`, `validated_profile`, `provider_maturity`, `frozen_provider`, `overlay_provider`, `plasticity_scope`, `guardrail_status`

### StrategyProposalFrame

- Schema: `strategy_proposal_frame.v1`
- Purpose: Represent a provider's candidate move and evidence without selecting it.
- Required fields: `provider_id`, `skill_id`, `provider_version`, `move_uci`, `raw_score`, `provider_local_rank`, `normalized_score`, `source_terms`, `role_licenses`, `move_shape_terms`, `post_move_terms`, `safety_terms`, `known_outcome_label`, `causal_status`

### InternalMonitorEvidence

- Schema: `internal_monitor_evidence.v1`
- Purpose: Attach non-causal internal-terminal/monitor evidence to a state.
- Required fields: `terminal_id`, `monitor_type`, `source_terms_met`, `missing_terms`, `confidence`, `associated_outcome`, `maturity_status`, `causal_ready`, `causal_status`

### PlanCapsuleWindowEvidence

- Schema: `plan_capsule_window_evidence.v1`
- Purpose: Describe bounded plan ownership windows and progress/exit/abort evidence.
- Required fields: `plan_id`, `plan_status`, `ttl_white_moves`, `owned_white_move_count`, `entry_terms_confirmed`, `progress_terms_confirmed`, `exit_terms_confirmed`, `abort_terms_confirmed`, `handoff_target`, `window_outcome`, `causal_status`

### SequenceTrainingExample

- Schema: `sequence_training_example.v1`
- Purpose: Store offline labels for sequence-policy benchmarks without runtime oracle use.
- Required fields: `example_id`, `family_id`, `trajectory_id`, `ply_index`, `candidate_moves`, `positive_moves`, `hard_negative_moves`, `draw_or_safety_veto_moves`, `label_source`, `offline_only`, `causal_status`

### GuardrailResultSummary

- Schema: `guardrail_result_summary.v1`
- Purpose: Summarize protected-stage and bridge validations for promotion review.
- Required fields: `guardrail_id`, `stage_or_domain`, `sample_count`, `horizon`, `mate_count`, `max_plies_count`, `shadow_candidate_count`, `passed`, `source_artifact`

### GrowthGovernorStatus

- Schema: `growth_governor_status.v1`
- Purpose: Record whether structural growth is allowed, settling, or blocked.
- Required fields: `stage_or_provider`, `status`, `active_candidate_count`, `guardrail_pass_rate`, `plasticity_improvement_slope`, `repeated_failure_family_count`, `reason`

### PromotionGateStatus

- Schema: `promotion_gate_status.v1`
- Purpose: Record candidate promotion/quarantine state and non-regression evidence.
- Required fields: `candidate_id`, `promotion_status`, `target_validation_status`, `protected_guardrail_status`, `shadow_candidate_delta`, `causal_status`, `source_artifact`

## Allowed Consumers

- `offline_strategy_arbitration_probe`
- `offline_sequence_policy_benchmark`
- `growth_monitor_candidate_generation`
- `guardrail_promotion_review`
- `architecture_review_reports`

## Forbidden Consumers

- `runtime_move_selector`
- `runtime_provider_router`
- `runtime_score_modifier`
- `runtime_topology_mutator`
- `runtime_dtm_or_tablebase_oracle`

## Validation Requirements

- `all_records_causal_status_non_causal`
- `all_runtime_behavior_flags_false`
- `no_runtime_dtm_or_tablebase_labels`
- `no_move_or_provider_override_fields`
- `offline_labels_marked_offline_only`
- `guardrail_sources_are_explicit`
- `provider_versions_are_explicit`
- `stage7_promotion_allowed_false`
- `stage8_training_allowed_false`

## First Manifest Scope

- Existing artifacts only: `True`
- Include Stage 5/6 successes: `True`
- Include Stage 4 caveat: `True`
- Include Stage 7 challenge families: `True`
- New playouts allowed: `False`

## Recommended Next Slice

`control_plane_manifest_from_existing_artifacts_v0`
