# KRK Broader Strategy / Sequence Candidate Source Design v1

This design responds to the candidate proposal quality decision. It does not implement runtime source expansion.

## Decision

- status: `broader_strategy_sequence_candidate_source_design_ready`
- implementation_allowed_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `review_plan_capsule_and_broader_strategy_observation_sources`

## Motivation

- quality_decision_status: `candidate_proposal_quality_not_selector_ready`
- gap_review_status: `observation_gap_review_blocks_selector_recommends_capacity_annotation`
- reason: provider-pack and legal-move frames are visible but not quality-sufficient; PlanCapsule and broader strategy sources are absent from observation frames

## Candidate Source Contracts

### plan_capsule_sequence_candidate

- purpose: Expose bounded sequence/continuation candidates that are already present as plan/capsule evidence.
- implementation_status: `design_only_requires_separate_review`
- required_fields: `['plan_capsule_id', 'entry_terms_confirmed', 'progress_terms_available', 'exit_terms_available', 'abort_terms_available', 'ttl_white_moves', 'handoff_targets', 'source_terms', 'capacity_evidence_kind', 'direct_request=false', 'score_delta=0.0', 'causal_status=observation_only']`
- forbidden_uses: `['force_plan_entry', 'alter_ttl', 'select_provider', 'change_scores', 'route_to_plan']`

### broader_strategy_candidate

- purpose: Expose strategy-level alternatives such as edge-net, king-support continuation, fence repair, mate-basin finish, or owner-exit candidates as visible hypotheses.
- implementation_status: `design_only_requires_separate_review`
- required_fields: `['strategy_id', 'strategy_family', 'source_monitor_records', 'licensed_provider_families', 'candidate_scope_terms', 'risk_terms', 'handoff_or_exit_terms', 'capacity_evidence_kind', 'direct_request=false', 'score_delta=0.0', 'causal_status=observation_only']`
- forbidden_uses: `['select_strategy', 'suppress_current_provider', 'boost_provider', 'direct_role_to_provider_edge', 'mutate_topology']`

## Source Quality Requirements

- candidate count must be bounded per state/source
- Stage 7 rows remain held-out challenge only
- capacity evidence remains separate from ownership labels
- source terms must be visible and explainable
- default-off equivalence must pass before any runtime source expansion
- source expansion alone must not trigger guardrails or selector review

## Forbidden Next Steps

- `runtime_selector`
- `score_changes`
- `provider_routing`
- `guardrail_campaign`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `hidden_python_controller`
- `runtime_source_expansion_without_review`
