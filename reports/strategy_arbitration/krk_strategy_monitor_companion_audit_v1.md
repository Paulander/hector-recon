# KRK Strategy Monitor Companion Audit V1

This replay-free audit checks whether proposed companion terms are already available in the existing strategy-arbitration dataset, only proxied, or missing.

## Status

- Dataset records: `33`
- Companion sets: `5`
- Term status counts: `{'proxy_available': 13, 'missing_requires_visible_extraction': 11, 'available_expression': 1, 'available_extracted': 6, 'available_exact': 3}`
- All terms available without new extraction: `False`
- Visible terms applied: `True`
- Visible term count: `6`
- Terms moved to extracted: `['box_area_no_longer_decision_relevant', 'safe_repair_move_exists', 'cut_or_fence_restored_after_move', 'post_plan_stagnation', 'local_provider_competition_failed', 'king_support_improves_after_move']`
- Still missing terms: `['box_shrink_goal_satisfied', 'box_shrink_owner_repeats_without_progress', 'edge_net_pressure_increases_after_move', 'handoff_success_after_plan', 'king_support_aligned_with_cut_or_edge_net', 'king_support_aligned_with_edge_net', 'king_support_improves_after_reply', 'multi_step_progress_required', 'repair_needed_but_no_safe_repair_available', 'repair_preserves_mate_basin_progress', 'safe_edge_net_tighten_move_exists']`
- Broad extracted terms: `['box_area_no_longer_decision_relevant', 'king_support_improves_after_move', 'safe_repair_move_exists']`
- Sparse extracted terms: `['local_provider_competition_failed', 'post_plan_stagnation']`
- Monitors better grounded: `['owner_exit_companions', 'repair_needed_companions', 'plan_selection_companions', 'king_support_redesign']`
- Potential future internal-terminal candidates: `['local_provider_competition_failed', 'post_plan_stagnation']`
- Recommended next step: `architecture_review_before_runtime_or_new_extraction`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Companion Sets

### phase_boundary_companions

- Target monitors: `['PhaseBoundaryMonitor']`
- Source concepts: `['edge_net_affordance', 'phase_boundary_near_edge']`
- Availability status: `proxy_only`
- Term status counts: `{'proxy_available': 4, 'missing_requires_visible_extraction': 3}`

| Term | Status | Exact/expression count | Extracted true/records | Proxies |
| --- | --- | ---: | ---: | --- |
| `current_owner` | `proxy_available` | 0 | 0/0 | `{'active_landmark_label': 33}` |
| `successful_next_provider` | `proxy_available` | 0 | 0/0 | `{'strategy_proposals.known_outcome_label': 31}` |
| `safe_edge_net_tighten_move_exists` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `safe_check_or_cut_tighten_move_exists` | `proxy_available` | 0 | 0/0 | `{'safe_check_available': 33, 'repair_or_reestablish_cut_available': 33}` |
| `edge_net_pressure_increases_after_move` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `draw_risk_absent_after_edge_net_move` | `proxy_available` | 0 | 0/0 | `{'stalemate_or_draw_risk': 33}` |
| `king_support_aligned_with_edge_net` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |

### owner_exit_companions

- Target monitors: `['OwnerExitMonitor']`
- Source concepts: `['box_shrink_exit_condition']`
- Availability status: `improved_by_visible_extraction`
- Term status counts: `{'available_expression': 1, 'missing_requires_visible_extraction': 2, 'available_extracted': 1, 'proxy_available': 2, 'available_exact': 1}`

| Term | Status | Exact/expression count | Extracted true/records | Proxies |
| --- | --- | ---: | ---: | --- |
| `active_landmark_label == box_shrink` | `available_expression` | 9 | 0/0 | `{'active_landmark_label': 33}` |
| `box_shrink_goal_satisfied` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `box_area_no_longer_decision_relevant` | `available_extracted` | 0 | 26/33 | `{'box_area_relevance': 33}` |
| `edge_net_affordance_scoped` | `proxy_available` | 0 | 0/0 | `{'edge_net_pressure_proxy': 33, 'black_king_edge_bucket': 33}` |
| `mate_basin_readiness` | `available_exact` | 33 | 0/0 | `{}` |
| `validated_handoff_target_available` | `proxy_available` | 0 | 0/0 | `{'strategy_proposals.known_outcome_label': 31}` |
| `box_shrink_owner_repeats_without_progress` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |

### repair_needed_companions

- Target monitors: `['RepairNeededMonitor']`
- Source concepts: `['fence_or_cut_repair_affordance']`
- Availability status: `improved_by_visible_extraction`
- Term status counts: `{'available_exact': 1, 'available_extracted': 2, 'proxy_available': 2, 'missing_requires_visible_extraction': 2}`

| Term | Status | Exact/expression count | Extracted true/records | Proxies |
| --- | --- | ---: | ---: | --- |
| `repair_or_reestablish_cut_available` | `available_exact` | 33 | 0/0 | `{'repair_or_reestablish_cut_available': 33}` |
| `safe_repair_move_exists` | `available_extracted` | 0 | 33/33 | `{'repair_or_reestablish_cut_available': 33}` |
| `rook_safe_after_repair` | `proxy_available` | 0 | 0/0 | `{'rook_safe': 33}` |
| `box_area_not_expanded_after_reply` | `proxy_available` | 0 | 0/0 | `{'box_area_relevance': 33}` |
| `cut_or_fence_restored_after_move` | `available_extracted` | 0 | 22/33 | `{}` |
| `repair_preserves_mate_basin_progress` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `repair_needed_but_no_safe_repair_available` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |

### plan_selection_companions

- Target monitors: `['PlanSelectionNeededMonitor']`
- Source concepts: `['plan_selection_needed']`
- Availability status: `improved_by_visible_extraction`
- Term status counts: `{'proxy_available': 4, 'missing_requires_visible_extraction': 2, 'available_extracted': 2}`

| Term | Status | Exact/expression count | Extracted true/records | Proxies |
| --- | --- | ---: | ---: | --- |
| `plan_capsule_context` | `proxy_available` | 0 | 0/0 | `{'role_capsule_context': 33}` |
| `handoff_success_after_plan` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `post_plan_stagnation` | `available_extracted` | 0 | 4/33 | `{}` |
| `local_provider_competition_failed` | `available_extracted` | 0 | 2/33 | `{'result_label.current_graph_h40': 4, 'strategy_proposals': 31}` |
| `selected_provider_closed_loop_failed` | `proxy_available` | 0 | 0/0 | `{'result_label.closed_loop_capsule': 2}` |
| `multi_step_progress_required` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `single_move_affordance_insufficient` | `proxy_available` | 0 | 0/0 | `{'hypothesis_labels': 9}` |
| `growth_pressure_repeated_family` | `proxy_available` | 0 | 0/0 | `{'hypothesis_labels': 9}` |

### king_support_redesign

- Target monitors: `['RejectedFeatureDefinition']`
- Source concepts: `['king_support_conversion_affordance']`
- Availability status: `improved_by_visible_extraction`
- Term status counts: `{'available_exact': 1, 'available_extracted': 1, 'missing_requires_visible_extraction': 2, 'proxy_available': 1}`

| Term | Status | Exact/expression count | Extracted true/records | Proxies |
| --- | --- | ---: | ---: | --- |
| `king_support_improvement_move_exists` | `available_exact` | 30 | 0/0 | `{'king_support_improvement_move_exists': 30}` |
| `king_support_improves_after_move` | `available_extracted` | 0 | 30/33 | `{}` |
| `king_support_improves_after_reply` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `king_support_aligned_with_cut_or_edge_net` | `missing_requires_visible_extraction` | 0 | 0/0 | `{}` |
| `king_support_needed_for_current_phase` | `proxy_available` | 0 | 0/0 | `{'white_king_support_available': 33, 'black_king_edge_bucket': 33}` |

## Conclusion

The extracted Tier 1 diagnostic terms improve monitor grounding but do not justify runtime terminals or sandbox behavior. Several terms are still missing, and some extracted terms are broad enough to remain monitor evidence rather than affordances. The next step is architecture review before runtime use or additional visible extraction.

No runtime arbiter, causal terminal, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, topology mutation, or monitor-to-provider routing is authorized.
