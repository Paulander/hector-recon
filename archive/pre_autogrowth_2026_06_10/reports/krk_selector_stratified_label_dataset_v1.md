# KRK Selector Stratified Label Dataset v1

This dataset fills the bounded selector label plan from existing artifacts only.

## Summary

- Rows: `11`
- Label counts: `{'negative': 1, 'positive': 10}`
- Stage counts: `{'stage4': 4, 'stage5': 4, 'stage6': 3}`
- Target kind counts: `{'guardrail_safe_selected_playout': 10, 'same_move_provider_compatibility_or_forced_alternative': 1}`
- Stage7 training rows: `0`
- Runtime arbiter allowed: `False`
- Selector sandbox ready: `False`

## Rows

- `selector_label.stage4.state.1e4f48a672e8.selected_guardrail` label=`positive` stage=`stage4` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage4.state.f17117682948.selected_guardrail` label=`positive` stage=`stage4` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage4.state.02cfd843a2cf.selected_guardrail` label=`positive` stage=`stage4` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage4.state.256a3da30f0f.selected_guardrail` label=`negative` stage=`stage4` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage5.state.7bd8961882ad.selected_guardrail` label=`positive` stage=`stage5` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage5.state.87b1160e68b9.selected_guardrail` label=`positive` stage=`stage5` provider=`krk.edge_trap_close` target=`guardrail_safe_selected_playout`
- `selector_label.stage5.state.87b1160e68b9.same_move_or_alt_provider` label=`positive` stage=`stage5` provider=`krk.edge_trap_enemy_between` target=`same_move_provider_compatibility_or_forced_alternative`
- `selector_label.stage5.state.2c1d6da27ea1.selected_guardrail` label=`positive` stage=`stage5` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage6.state.d1f052d2cab2.selected_guardrail` label=`positive` stage=`stage6` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage6.state.52085d244e9d.selected_guardrail` label=`positive` stage=`stage6` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
- `selector_label.stage6.state.69711173114a.selected_guardrail` label=`positive` stage=`stage6` provider=`krk.stage0_basin` target=`guardrail_safe_selected_playout`
