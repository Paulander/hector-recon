# KRK Selector Stratified Label Plan v1

This is a bounded non-causal plan for improving selector objective evidence. It does not execute labels.

## Summary

- Objective review status: `selector_objective_needs_stratified_label_expansion_before_sandbox`
- Planned jobs: `11`
- Horizon: `h40`
- Stage7 training rows: `0`
- Execute labels now: `False`
- Runtime arbiter allowed: `False`

## Existing Target Counts

- By kind/stage: `{'forced_provider_conversion': {'stage5': 6, 'stage6': 6}, 'held_out_challenge': {'stage7': 9}, 'selected_playout_success': {'stage4': 6, 'stage5': 16, 'stage6': 20}}`
- By kind/label: `{'forced_provider_conversion': {'negative': 3, 'positive': 9}, 'held_out_challenge': {'none': 9}, 'selected_playout_success': {'negative': 28, 'positive': 14}}`

## Existing Proposal Label Counts

- By stage/result: `{'stage4': {'mate': 3, 'max_plies': 3}, 'stage5': {'mate': 6, 'max_plies': 10}, 'stage6': {'mate': 5, 'max_plies': 15}, 'stage7': {'mate': 2, 'max_plies': 25}}`
- Unlabeled by stage: `{'stage7': 18}`

## Planned Jobs

- `selector_label.stage4.state.1e4f48a672e8.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage4` provider=`krk.stage0_basin`
- `selector_label.stage4.state.f17117682948.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage4` provider=`krk.stage0_basin`
- `selector_label.stage4.state.02cfd843a2cf.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage4` provider=`krk.stage0_basin`
- `selector_label.stage4.state.256a3da30f0f.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage4` provider=`krk.stage0_basin`
- `selector_label.stage5.state.7bd8961882ad.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage5` provider=`krk.stage0_basin`
- `selector_label.stage5.state.87b1160e68b9.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage5` provider=`krk.edge_trap_close`
- `selector_label.stage5.state.87b1160e68b9.same_move_or_alt_provider` target=`same_move_provider_compatibility_or_forced_alternative` stage=`stage5` provider=`krk.edge_trap_enemy_between`
- `selector_label.stage5.state.2c1d6da27ea1.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage5` provider=`krk.stage0_basin`
- `selector_label.stage6.state.d1f052d2cab2.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage6` provider=`krk.stage0_basin`
- `selector_label.stage6.state.52085d244e9d.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage6` provider=`krk.stage0_basin`
- `selector_label.stage6.state.69711173114a.selected_guardrail` target=`guardrail_safe_selected_playout` stage=`stage6` provider=`krk.stage0_basin`

## Decision

Status: `bounded_selector_stratified_label_plan_ready`
Recommended next step: `review_label_plan_before_execution_or_replay_free_extraction`

The plan should be reviewed before execution. If replay-free extraction can fill the same cells, prefer that over new playouts.
