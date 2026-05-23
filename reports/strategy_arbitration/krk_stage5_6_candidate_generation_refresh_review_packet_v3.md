# KRK Stage 5/6 Candidate-Generation Refresh Review Packet v3

This packet reviews a narrow future default-off candidate-generation refresh sandbox for protected Stage 5/6 only. It does not authorize implementation by itself.

## Decision

- status: `stage5_6_candidate_generation_refresh_review_ready`
- runtime_review_ready: `True`
- implementation_authorized_by_this_packet: `False`
- selector_allowed: `False`
- runtime_candidate_generator_refresh_allowed_by_this_packet: `False`
- recommended_next_step: `explicit_approval_required_for_default_off_stage5_6_candidate_generation_refresh_sandbox`

## Evidence

- benchmark_status: `stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked`
- stage5_6_metrics: `{'balanced_recall_risk': 1.0, 'false_negative': 0, 'false_positive': 0, 'negative_count': 5, 'negative_suppression': 1.0, 'positive_count': 20, 'positive_precision': 1.0, 'positive_recall': 1.0, 'predicted_count': 20, 'row_count': 25, 'true_negative': 5, 'true_positive': 20}`
- stage4_metrics: `{'balanced_recall_risk': 0.5, 'false_negative': 6, 'false_positive': 0, 'negative_count': 5, 'negative_suppression': 1.0, 'positive_count': 6, 'positive_precision': 0.0, 'positive_recall': 0.0, 'predicted_count': 0, 'row_count': 11, 'true_negative': 5, 'true_positive': 0}`
- positive_scope_cells: `['stage5|edge_trap', 'stage5|fence_established', 'stage5|stage0_basin', 'stage6|stage0_basin']`

## Approved Scope If Later Authorized

- source_stages: `['stage5', 'stage6']`
- excluded_stages: `['stage4', 'stage7', 'stage8']`
- stage7_use: `held_out_challenge_only`
- candidate_generation_cells: `{'stage5': ['edge_trap', 'fence_established', 'stage0_basin'], 'stage6': ['stage0_basin']}`
- candidate_source: `validated_provider_capacity_scope`
- allowed_runtime_effect: `emit_extra_candidate_generation_frames_only`
- direct_request: `False`
- score_delta: `0.0`
- causal_status_for_frames: `observation_or_candidate_generation_only`

## Explicitly Forbidden

- `selecting_a_provider`
- `selecting_a_move`
- `suppressing_providers`
- `changing_scores`
- `direct_provider_routing`
- `stage4_scope_without_companion_review`
- `stage7_training_rows`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
- `hidden_python_controller`

## Implementation Requirements If Later Approved

- `explicit opt-in flag`
- `default-off equivalence on protected Stage 5/6`
- `zero selected move/provider delta when observing only`
- `zero score delta`
- `bounded generated candidate count`
- `trace every generated candidate source term`
- `mark Stage 7 rows held-out if sampled diagnostically`
- `target smoke before any guardrails`
- `separate selector review before any candidate can affect routing`

## Risk Register

- `capacity labels are not ownership labels`
- `Stage 4 remains mixed and excluded`
- `Stage 7 remains held out`
- `candidate generation may expose negative-capacity candidates if scope leaks`
- `runtime selector is still blocked`
