# KRK Candidate-Generation Training Refresh Runtime Review Packet v3

This packet reviews a future default-off candidate-generation refresh sandbox. It does not authorize implementation, selection, scoring, routing, guardrails, promotion, or Stage 8 training.

## Decision

- status: `candidate_generation_training_refresh_runtime_review_ready`
- runtime_review_ready: `True`
- implementation_authorized_by_this_packet: `False`
- runtime_candidate_generation_allowed_by_this_packet: `False`
- selector_allowed: `False`
- recommended_next_step: `explicit_approval_required_for_default_off_candidate_generation_refresh_sandbox`

## Evidence

- benchmark_status: `candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed`
- best_policy: `trace_stage_family_context`
- best_policy_metrics: `{'balanced_recall_risk': 0.8846153846153846, 'false_negative': 6, 'false_positive': 0, 'negative_capacity_suppression': 1.0, 'negative_count': 10, 'positive_capacity_recall': 0.7692307692307693, 'positive_count': 26, 'positive_precision': 1.0, 'predicted_count': 20, 'row_count': 36, 'true_negative': 10, 'true_positive': 20}`
- best_policy_leave_stage_out_metrics: `{'balanced_recall_risk': 0.8846153846153846, 'false_negative': 6, 'false_positive': 0, 'negative_capacity_suppression': 1.0, 'negative_count': 10, 'positive_capacity_recall': 0.7692307692307693, 'positive_count': 26, 'positive_precision': 1.0, 'predicted_count': 20, 'row_count': 36, 'true_negative': 10, 'true_positive': 20}`
- thresholds_met: `True`

## Approved Scope If Later Authorized

- sandbox_type: `default_off_candidate_generation_refresh`
- allowed_effect: `emit_extra_candidate_generation_frames_only`
- candidate_generation_policy: `trace_stage_family_context`
- candidate_generation_cells: `{'stage5': ['edge_trap', 'fence_established', 'stage0_basin'], 'stage6': ['stage0_basin']}`
- protected_stages: `['stage5', 'stage6']`
- excluded_from_training_or_readiness: `['stage7', 'stage8']`
- stage4_status: `positive_capacity_exists_but_not_covered_by_current_trace_stage_family_policy`
- stage7_use: `held_out_challenge_visibility_only`
- direct_request: `False`
- score_delta: `0.0`
- causal_status_for_frames: `candidate_generation_only`

## Explicitly Forbidden

- `selector_training`
- `provider_selection`
- `move_selection`
- `score_changes`
- `provider_suppression`
- `direct_provider_routing`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
- `stage7_training_rows`
- `stage7_promotion`
- `stage8_training`
- `stage4_runtime_scope_without_separate_review`
- `guardrails_before_target_smoke`

## Implementation Requirements If Explicitly Approved Later

- `explicit opt-in flag`
- `default-off equivalence before enabled smoke`
- `bounded candidate count per decision`
- `zero selected move/provider delta in observation-only mode`
- `zero score delta`
- `direct_request=false on every generated frame`
- `source terms and policy cell recorded on every frame`
- `Stage 7 frames marked held_out_challenge if diagnostic sampling is enabled`
- `target smoke before guardrails`
- `separate selector review before generated frames can affect routing or scoring`

## Risk Register

- `capacity labels are not ownership labels`
- `current best policy misses protected Stage 4 positive-capacity rows`
- `current best policy is a candidate-generation scope, not a sequence policy`
- `candidate generation can increase trace volume if unbounded`
- `selector remains blocked`
