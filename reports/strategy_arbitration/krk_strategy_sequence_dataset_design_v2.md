# KRK Strategy-Sequence Dataset Design v2

Make KRK strategy-sequence evidence channels explicit so future candidate generation, monitor, and selector work cannot conflate capacity labels, ownership labels, and trace-only context.

## Decision

- status: `strategy_sequence_dataset_design_v2_ready`
- implementation_allowed_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `implement_strategy_sequence_dataset_refresh_v2_non_causal`

## Evidence Channels

### validated_provider_capacity

- label_semantics: `forced_provider_capacity_label`
- allowed_use: `candidate_generation_recall_benchmark`
- forbidden_use: `selector_training_label`

### visible_provider_proposal

- label_semantics: `normal_routing_proposal_context`
- allowed_use: `proposal_context_and_score_scale_analysis`
- forbidden_use: `capacity_or_ownership_label_without_outcome`

### candidate_move_frame

- label_semantics: `legal_move_hypothesis`
- allowed_use: `candidate_coverage_and_feature_quality`
- forbidden_use: `runtime_move_suggestion_without_selector_review`

### plan_capsule_sequence_candidate

- label_semantics: `heldout_or_plan_context`
- allowed_use: `sequence_policy_evidence`
- forbidden_use: `stage7_training_row_or_promotion_evidence`

### internal_monitor_candidate

- label_semantics: `internal_control_context`
- allowed_use: `self_monitoring_and_growth_pressure_analysis`
- forbidden_use: `direct_provider_route`

### runtime_observation_trace_feature

- label_semantics: `trace_context_not_selector_label`
- allowed_use: `future_strategy_sequence_dataset_context`
- forbidden_use: `selector_training_or_guardrail_trigger`

## Partition Rules

- protected_readiness_stages: `['stage4', 'stage5', 'stage6']`
- heldout_challenge_stages: `['stage7']`
- stage7_training_rows_allowed: `False`
- stage8_training_allowed: `False`

## Minimum Next Refresh Requirements

- `keep channel-specific label_semantics`
- `carry trace_feature_channel separately from candidate-generation labels`
- `preserve stage7 held-out status`
- `report selector_training_row_count by channel`
- `report candidate_generation_training_row_count by channel`
- `report trace-only context row count by channel`
- `block selector review unless ownership labels are explicit`
