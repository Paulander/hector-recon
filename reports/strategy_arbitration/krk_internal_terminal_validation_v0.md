# KRK Internal Terminal Validation v0

This replay-free validation evaluates InternalTerminalSpec candidates against existing visible monitor terms.

## Status

- Terminal count: `4`
- Validation records: `30`
- Causal-ready terminals: `[]`
- Strongest candidates: `['terminal.krk.local_provider_competition_failed', 'terminal.krk.post_plan_stagnation']`
- Recommended next step: `broader_evidence_collection_or_internal_monitor_design_review`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Terminal Validation

### terminal.krk.local_provider_competition_failed

- Record count: `2/33`
- Stage 7 count: `2`
- Stage 5/6/4 count: `0`
- Result distribution: `{'max_plies': 2}`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage7-only: `True`
- Generalizes across stages: `False`
- Shape: `too_sparse`
- Recommended maturity: `internal_terminal_candidate`
- Missing terms: `['current_owner', 'alternative_provider_known_mate', 'route_conflict']`
- Causal use blocked: `True`

### terminal.krk.post_plan_stagnation

- Record count: `4/33`
- Stage 7 count: `4`
- Stage 5/6/4 count: `0`
- Result distribution: `{'max_plies': 4}`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage7-only: `True`
- Generalizes across stages: `False`
- Shape: `too_sparse`
- Recommended maturity: `internal_terminal_candidate`
- Missing terms: `['handoff_success_after_plan', 'multi_step_progress_required', 'repeated_abstract_state']`
- Causal use blocked: `True`

### terminal.krk.box_shrink_owner_exit_pressure

- Record count: `2/33`
- Stage 7 count: `2`
- Stage 5/6/4 count: `0`
- Result distribution: `{'unknown': 1, 'max_plies': 1}`
- Failure precision: `1.0`
- Success precision: `0.0`
- Stage7-only: `True`
- Generalizes across stages: `False`
- Shape: `too_sparse`
- Recommended maturity: `monitoring_only`
- Missing terms: `['box_shrink_goal_satisfied', 'validated_handoff_target_available']`
- Causal use blocked: `True`

### terminal.krk.repair_needed_monitor

- Record count: `22/33`
- Stage 7 count: `9`
- Stage 5/6/4 count: `13`
- Result distribution: `{'unknown': 3, 'max_plies': 16, 'mate': 3}`
- Failure precision: `0.8421052631578947`
- Success precision: `0.15789473684210525`
- Stage7-only: `False`
- Generalizes across stages: `True`
- Shape: `moderate`
- Recommended maturity: `monitoring_only`
- Missing terms: `['repair_needed_but_no_safe_repair_available', 'box_area_not_expanded_after_reply']`
- Causal use blocked: `True`

## Conclusion

`terminal.krk.local_provider_competition_failed` and `terminal.krk.post_plan_stagnation` remain the strongest internal-terminal candidates, but they are sparse and need broader validation. `box_shrink_owner_exit_pressure` and `repair_needed_monitor` remain monitoring-only / companion-dependent. No runtime use is authorized.
