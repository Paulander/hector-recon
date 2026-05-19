# KRK Strategy Monitor Maturity Gate v0

This gate classifies extracted monitor terms and missing backlog terms before any runtime or sandbox work. It is non-causal.

## Status

- Term count: `6`
- Maturity status counts: `{'context_feature': 2, 'monitor_candidate': 1, 'too_broad': 1, 'internal_terminal_candidate': 2}`
- Backlog priority counts: `{'high': 5, 'backlog': 3, 'lower_defer': 3}`
- Causal-ready terms: `[]`
- Strongest internal-terminal candidates: `['post_plan_stagnation', 'local_provider_competition_failed']`
- Broad context terms: `['king_support_improves_after_move', 'safe_repair_move_exists', 'box_area_no_longer_decision_relevant']`
- Recommended next step: `broader_evidence_collection_or_internal_monitor_design_review`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Extracted Term Maturity

### king_support_improves_after_move

- Maturity status: `context_feature`
- Support: `30/33`
- Result distribution: `{'unknown': 3, 'max_plies': 17, 'mate': 10}`
- Source-stage distribution: `{'stage7': 8, 'stage5': 8, 'stage6': 10, 'stage4': 4}`
- Stage7 support: `8`
- Success precision: `0.37037037037037035`
- Failure precision: `0.6296296296296297`
- Shape: `broad`
- Use as: `['context feature']`
- Required companion terms: `['king_support_needed_for_current_phase', 'king_support_aligned_with_cut_or_edge_net']`
- Causal use blocked: `True`
- Rationale: Action-relevant improvement is better than static support, but still broad.

### cut_or_fence_restored_after_move

- Maturity status: `monitor_candidate`
- Support: `22/33`
- Result distribution: `{'unknown': 3, 'max_plies': 16, 'mate': 3}`
- Source-stage distribution: `{'stage7': 9, 'stage5': 6, 'stage6': 5, 'stage4': 2}`
- Stage7 support: `9`
- Success precision: `0.15789473684210525`
- Failure precision: `0.8421052631578947`
- Shape: `moderate`
- Use as: `['failure/risk monitor']`
- Required companion terms: `['fence_or_cut_repair_affordance', 'safe_repair_move_exists']`
- Causal use blocked: `True`
- Rationale: Useful repair-progress evidence when paired with repair-needed context.

### safe_repair_move_exists

- Maturity status: `too_broad`
- Support: `33/33`
- Result distribution: `{'unknown': 3, 'max_plies': 18, 'mate': 12}`
- Source-stage distribution: `{'stage7': 9, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Stage7 support: `9`
- Success precision: `0.4`
- Failure precision: `0.6`
- Shape: `broad`
- Use as: `['context feature']`
- Required companion terms: `['repair_needed', 'cut_or_fence_restored_after_move', 'box_area_not_expanded_after_reply']`
- Causal use blocked: `True`
- Rationale: True across the full current dataset, so it is not separable alone.

### box_area_no_longer_decision_relevant

- Maturity status: `context_feature`
- Support: `26/33`
- Result distribution: `{'unknown': 1, 'max_plies': 13, 'mate': 12}`
- Source-stage distribution: `{'stage7': 2, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Stage7 support: `2`
- Success precision: `0.48`
- Failure precision: `0.52`
- Shape: `broad`
- Use as: `['context feature', 'owner-exit monitor']`
- Required companion terms: `['active_landmark_label == box_shrink', 'validated_handoff_target_available']`
- Causal use blocked: `True`
- Rationale: Broad owner-exit companion; useful context but too common to trigger behavior alone.

### post_plan_stagnation

- Maturity status: `internal_terminal_candidate`
- Support: `4/33`
- Result distribution: `{'max_plies': 4}`
- Source-stage distribution: `{'stage7': 4}`
- Stage7 support: `4`
- Success precision: `0.0`
- Failure precision: `1.0`
- Shape: `sparse`
- Use as: `['plan-selection monitor', 'growth-pressure monitor']`
- Required companion terms: `['plan_capsule_context', 'handoff_success_after_plan']`
- Causal use blocked: `True`
- Rationale: Sparse and semantically strong trace-window signal for plan/capsule failure.

### local_provider_competition_failed

- Maturity status: `internal_terminal_candidate`
- Support: `2/33`
- Result distribution: `{'max_plies': 2}`
- Source-stage distribution: `{'stage7': 2}`
- Stage7 support: `2`
- Success precision: `0.0`
- Failure precision: `1.0`
- Shape: `sparse`
- Use as: `['growth-pressure monitor', 'plan-selection monitor']`
- Required companion terms: `['current_owner', 'alternative_provider_known_mate']`
- Causal use blocked: `True`
- Rationale: Sparse but directly expresses provider-arbitration failure.

## Monitor Class Maturity

- `OwnerExitMonitor`: maturity=`needs_companion_terms`, outcomes=`{'mate': 12, 'max_plies': 12, 'unknown': 1}`, failure_precision=`0.5`
- `PhaseBoundaryMonitor`: maturity=`needs_companion_terms`, outcomes=`{'mate': 24, 'max_plies': 26, 'unknown': 2}`, failure_precision=`0.52`
- `PlanSelectionNeededMonitor`: maturity=`monitor_candidate`, outcomes=`{'max_plies': 6, 'unknown': 3}`, failure_precision=`1.0`
- `RepairNeededMonitor`: maturity=`monitor_candidate`, outcomes=`{'mate': 3, 'max_plies': 16, 'unknown': 3}`, failure_precision=`0.8421052631578947`

## Backlog Missing Extraction

- `edge_net_pressure_increases_after_move`: priority=`high`, maturity=`backlog_missing_extraction`
- `handoff_success_after_plan`: priority=`high`, maturity=`backlog_missing_extraction`
- `king_support_aligned_with_edge_net`: priority=`high`, maturity=`backlog_missing_extraction`
- `multi_step_progress_required`: priority=`high`, maturity=`backlog_missing_extraction`
- `safe_edge_net_tighten_move_exists`: priority=`high`, maturity=`backlog_missing_extraction`
- `box_shrink_goal_satisfied`: priority=`backlog`, maturity=`backlog_missing_extraction`
- `box_shrink_owner_repeats_without_progress`: priority=`backlog`, maturity=`backlog_missing_extraction`
- `king_support_aligned_with_cut_or_edge_net`: priority=`backlog`, maturity=`backlog_missing_extraction`
- `king_support_improves_after_reply`: priority=`lower_defer`, maturity=`backlog_missing_extraction`
- `repair_needed_but_no_safe_repair_available`: priority=`lower_defer`, maturity=`backlog_missing_extraction`
- `repair_preserves_mate_basin_progress`: priority=`lower_defer`, maturity=`backlog_missing_extraction`

## Conclusion

`post_plan_stagnation` and `local_provider_competition_failed` are the strongest internal-monitor candidates, but they remain non-causal and sparse. Broad terms remain context features only. Missing phase-boundary terms remain backlog, not immediate runtime work.

No runtime terminal, causal affordance, runtime arbiter, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, topology mutation, or monitor-to-provider routing is authorized.
