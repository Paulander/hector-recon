# KRK State-Local Paired Selector Runtime Review Packet v0

This packet summarizes non-causal readiness evidence. It does not authorize implementation.

## Summary

- `review_status`: `semantic_gate_review_ready_runtime_feature_translation_needed`
- `best_objective`: `safe_preservation_gated_model`
- `prefer_capacity_recall`: `1.0`
- `selected_preservation_recall`: `1.0`
- `safe_preservation_recall`: `1.0`
- `strong_conflict_accuracy`: `1.0`
- `threshold_passing_model_count`: `2`
- `runtime_feature_passing_model_count`: `0`
- `runtime_feature_translation_blocker`: `True`
- `stage7_row_count`: `0`

## Runtime Sandbox Requirements

- `default_off`
- `profile_scoped_to_handoff_composition_v1_or_successor_review_profile`
- `trace_every_suppression_or_prefer_capacity_decision`
- `never_use_dtm_or_tablebase_at_runtime`
- `no_gameplay_topology_mutation`
- `no_direct_provider_request_from_metadata`
- `rollback_tag_before_implementation`

## Translation Requirements Before Implementation

- replace offline owner_a_positive with visible selected-owner safety/failure-risk proxy
- replace owner_b_positive forced-capacity labels with visible candidate-support evidence
- preserve selected-mate/safe-owner behavior unless visible failure evidence is present
- keep Stage 7 as held-out evaluation only

## Guardrails Required

- `default_off_equivalence`
- `protected_stage4_control`
- `protected_stage5_fence`
- `protected_stage6_drive`
- `Stage7_holdout_challenge_no_regression`
- `M1_M4_preservation_suite`

## Decision

- `status`: `runtime_review_packet_ready_with_translation_blocker`
- `implementation_allowed_by_this_packet`: `False`
- `recommended_next_step`: `explicit_architecture_review_for_visible_runtime_proxy_design`
