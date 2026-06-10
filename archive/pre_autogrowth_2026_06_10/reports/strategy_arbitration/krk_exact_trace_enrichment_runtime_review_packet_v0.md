# KRK Exact Trace Enrichment Runtime Review Packet v0

This packet reviews a possible future default-off exact trace enrichment sandbox. It does not authorize implementation, selection, scoring, routing, guardrails, promotion, or Stage 8 training.

## Decision

- status: `exact_trace_enrichment_runtime_review_ready`
- runtime_review_ready: `True`
- implementation_authorized_by_this_packet: `False`
- runtime_candidate_generation_allowed_by_this_packet: `False`
- selector_allowed: `False`
- recommended_next_step: `explicit_approval_required_for_default_off_exact_trace_enrichment_sandbox`

## Evidence

- options_status: `candidate_source_expansion_options_review_complete_runtime_packet_required`
- preferred_next_review: `exact_trace_enrichment_within_existing_policy_cells`
- exact_missing_positive_capacity_count: `21`
- policy_cell_covered_exact_missing_count: `15`
- policy_cell_missing_count: `6`
- gap_count_by_stage: `{'stage4': 6, 'stage5': 12, 'stage6': 3}`
- gap_count_by_family: `{'edge_trap': 12, 'stage0_basin': 9}`
- options_summary: `{'exact_missing_positive_capacity_count': 21, 'gap_count_by_family': {'edge_trap': 12, 'stage0_basin': 9}, 'gap_count_by_stage': {'stage4': 6, 'stage5': 12, 'stage6': 3}, 'policy_cell_covered_exact_missing_count': 15, 'policy_cell_missing_count': 6}`

## Approved Scope If Later Authorized

- sandbox_type: `default_off_exact_trace_enrichment`
- allowed_effect: `emit_additional_exact_candidate_generation_observation_frames_only`
- base_policy: `trace_stage_family_context`
- candidate_generation_cells: `{'stage5': ['edge_trap', 'stage0_basin'], 'stage6': ['stage0_basin']}`
- protected_stages: `['stage5', 'stage6']`
- excluded_stages: `['stage4', 'stage7', 'stage8']`
- stage4_status: `excluded_until_separate_review`
- stage7_use: `held_out_challenge_only_no_training_rows`
- direct_request: `False`
- score_delta: `0.0`
- causal_status_for_frames: `candidate_generation_only`
- capacity_label_semantics: `offline_capacity_not_runtime_ownership`

## Explicitly Forbidden

- `selector_training`
- `provider_selection`
- `move_selection`
- `score_changes`
- `provider_suppression`
- `direct_provider_routing`
- `runtime_dtm_or_tablebase`
- `state_hash_or_exact_move_runtime_exception`
- `gameplay_topology_mutation`
- `stage4_runtime_scope_without_separate_review`
- `stage7_training_rows`
- `stage7_promotion`
- `stage8_training`
- `guardrails_before_default_off_equivalence_and_enabled_smoke`

## Implementation Requirements If Explicitly Approved Later

- `new explicit opt-in flag or extension of existing refresh flag with visible mode`
- `default-off equivalence before enabled smoke`
- `bounded candidate count per decision`
- `zero selected move/provider delta`
- `zero score delta`
- `direct_request=false on every generated frame`
- `source_terms policy_cell and exact_enrichment_reason recorded on every frame`
- `capacity_evidence_kind recorded as positive_capacity negative_capacity or unknown_capacity`
- `Stage 7 rows excluded from training/readiness and marked held_out if ever traced diagnostically`
- `target smoke before guardrails`
- `separate selector review before generated frames can affect routing or scoring`

## Risk Register

- `capacity labels are still not ownership labels`
- `exact enrichment may increase trace volume without improving selection`
- `policy-cell-covered gaps may include alternative moves that are not safe owners`
- `Stage 4 gaps remain excluded and require separate review`
- `PlanCapsule or sequence candidates are still not covered by this packet`
