# KRK Internal Terminal Design Review v1

This review interprets non-causal internal-terminal evidence. It does not implement runtime terminals or authorize causal use.

## Status

- Causal-ready terminals: `[]`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Answers

- Closest to runtime-visible non-causal promotion: `['terminal.krk.local_provider_competition_failed', 'terminal.krk.post_plan_stagnation']`
- Too sparse: `['terminal.krk.local_provider_competition_failed', 'terminal.krk.post_plan_stagnation', 'terminal.krk.box_shrink_owner_exit_pressure']`
- Too broad/noisy: `['terminal.krk.repair_needed_monitor']`
- Domain-general pattern: `['terminal.krk.local_provider_competition_failed', 'terminal.krk.post_plan_stagnation']`
- KRK-specific instantiation: `['terminal.krk.box_shrink_owner_exit_pressure', 'terminal.krk.repair_needed_monitor']`

## Terminal Readiness

### terminal.krk.local_provider_competition_failed

- Maturity: `internal_terminal_candidate`
- Causal ready: `False`
- Fire count: `2`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage7-only: `True`
- Shape: `sparse`
- Blocking gaps: `['current_owner', 'failed_owner', 'alternative_provider_known_mate', 'alternative_provider_known_conversion', 'route_conflict', 'selected_owner_failed_h40', 'forced_alternative_succeeded_h40', 'provider_score_scale_gap']`

### terminal.krk.post_plan_stagnation

- Maturity: `internal_terminal_candidate`
- Causal ready: `False`
- Fire count: `4`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage7-only: `True`
- Shape: `sparse`
- Blocking gaps: `['plan_id', 'plan_ttl_expired', 'plan_owned_move_count', 'plan_progress_window', 'handoff_success_after_plan', 'multi_step_progress_required', 'repeated_abstract_state', 'post_plan_max_plies', 'no_progress_after_owned_window']`

### terminal.krk.box_shrink_owner_exit_pressure

- Maturity: `monitoring_only`
- Causal ready: `False`
- Fire count: `2`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage7-only: `True`
- Shape: `sparse`
- Blocking gaps: `['box_shrink_goal_satisfied', 'box_area_relevance_low', 'black_king_near_edge', 'edge_net_affordance_high', 'king_support_affordance_high', 'validated_handoff_target_available', 'box_shrink_should_handoff', 'box_shrink_low_affordance']`

### terminal.krk.repair_needed_monitor

- Maturity: `monitoring_only`
- Causal ready: `False`
- Fire count: `15`
- Failure precision: `0.8333333333333334`
- Success precision: `0.16666666666666666`
- Stage7-only: `False`
- Shape: `moderate`
- Blocking gaps: `['repair_needed_but_no_safe_repair_available', 'safe_repair_move_exists', 'box_area_not_expanded_after_reply', 'repair_move_preserves_rook_safety', 'repair_move_leads_to_conversion', 'cut_or_fence_broken_after_reply']`

## Promotion Readiness Checklist

- `fires_on_enough_examples`
- `validated_across_multiple_seeds_or_artifacts`
- `false_positive_rate_measured`
- `false_negative_examples_reviewed`
- `companion_terms_defined`
- `source_terms_are_graph_visible`
- `consumer_is_defined`
- `sandbox_default_off_test_exists`
- `guardrails_pass`
- `no_hidden_controller`
- `no_direct_provider_routing_from_monitor`
- `no_topology_mutation_during_gameplay`

## Forbidden Future Causal Uses

- choosing providers directly
- penalizing or boosting providers
- forcing plan exit or altering TTL
- routing to a repair move
- mutating topology during gameplay
- feeding M4 edge deltas without explicit later review

## Conclusion

Internal terminals are useful monitor/evidence objects, not runtime controls. local_provider_competition_failed and post_plan_stagnation are the strongest but remain sparse and Stage7-only; repair_needed_monitor is broader but noisy; box_shrink_owner_exit_pressure needs companion handoff-target evidence.

Recommended next step: `broader_replay_free_monitor_evidence_collection_or_review`.
