# KRK Internal Terminal Evidence v1

This report broadens InternalTerminalSpec evidence replay-free from existing artifacts only. It is evidence-only and does not authorize runtime terminals.

## Status

- Combined records: `24`
- Terminal count: `4`
- Causal-ready terminals: `[]`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Terminal Evidence

### terminal.krk.local_provider_competition_failed

- Maturity: `internal_terminal_candidate`
- Fires: `2/24`
- Counts: success=`0`, failure=`2`, unknown=`0`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage distribution: `{'stage7': 2}`
- Label/scope distribution: `{'box_shrink': 2}`
- Shape: `sparse`
- False positives: `0`
- Inferable false negatives: `2`
- Missing companion terms: `['current_owner', 'failed_owner', 'alternative_provider_known_mate', 'alternative_provider_known_conversion', 'route_conflict', 'selected_owner_failed_h40', 'forced_alternative_succeeded_h40', 'provider_score_scale_gap']`
- Causal ready: `False`

### terminal.krk.post_plan_stagnation

- Maturity: `internal_terminal_candidate`
- Fires: `4/24`
- Counts: success=`0`, failure=`4`, unknown=`0`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage distribution: `{'stage7': 4}`
- Label/scope distribution: `{'box_shrink': 4}`
- Shape: `sparse`
- False positives: `0`
- Inferable false negatives: `0`
- Missing companion terms: `['plan_id', 'plan_ttl_expired', 'plan_owned_move_count', 'plan_progress_window', 'handoff_success_after_plan', 'multi_step_progress_required', 'repeated_abstract_state', 'post_plan_max_plies', 'no_progress_after_owned_window']`
- Causal ready: `False`

### terminal.krk.box_shrink_owner_exit_pressure

- Maturity: `monitoring_only`
- Fires: `2/24`
- Counts: success=`0`, failure=`1`, unknown=`1`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage distribution: `{'stage7': 2}`
- Label/scope distribution: `{'box_shrink': 2}`
- Shape: `sparse`
- False positives: `0`
- Inferable false negatives: `5`
- Missing companion terms: `['box_shrink_goal_satisfied', 'box_area_relevance_low', 'black_king_near_edge', 'edge_net_affordance_high', 'king_support_affordance_high', 'validated_handoff_target_available', 'box_shrink_should_handoff', 'box_shrink_low_affordance']`
- Causal ready: `False`

### terminal.krk.repair_needed_monitor

- Maturity: `monitoring_only`
- Fires: `15/24`
- Counts: success=`2`, failure=`10`, unknown=`3`
- Failure precision: `0.8333333333333334`
- Success precision: `0.16666666666666666`
- Stage distribution: `{'stage7': 9, 'stage5': 4, 'stage6': 1, 'stage4': 1}`
- Label/scope distribution: `{'box_shrink': 9, 'fence_established': 4, 'drive_to_edge': 1, 'wrong_tempo_control': 1}`
- Shape: `moderate`
- False positives: `2`
- Inferable false negatives: `0`
- Missing companion terms: `['repair_needed_but_no_safe_repair_available', 'safe_repair_move_exists', 'box_area_not_expanded_after_reply', 'repair_move_preserves_rook_safety', 'repair_move_leads_to_conversion', 'cut_or_fence_broken_after_reply']`
- Causal ready: `False`

## Monitor Class Evidence

### OwnerExitMonitor

- Records: `25`
- Outcome distribution: `{'mate': 12, 'max_plies': 12, 'unknown': 1}`
- Failure precision: `0.5`
- Success precision: `0.5`

### PhaseBoundaryMonitor

- Records: `52`
- Outcome distribution: `{'mate': 24, 'max_plies': 26, 'unknown': 2}`
- Failure precision: `0.52`
- Success precision: `0.48`

### PlanSelectionNeededMonitor

- Records: `9`
- Outcome distribution: `{'max_plies': 6, 'unknown': 3}`
- Failure precision: `1.0`
- Success precision: `0.0`

### RepairNeededMonitor

- Records: `22`
- Outcome distribution: `{'mate': 3, 'max_plies': 16, 'unknown': 3}`
- Failure precision: `0.8421052631578947`
- Success precision: `0.15789473684210525`

## Conclusion

`local_provider_competition_failed` and `post_plan_stagnation` remain the strongest internal-terminal candidates, but they are sparse and Stage7-only. `repair_needed_monitor` has broader evidence but is noisy. `box_shrink_owner_exit_pressure` remains monitoring-only and needs companion handoff-target terms. No terminal is causal-ready.
