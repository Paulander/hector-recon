# KRK Selector Label Plan Replay-Free Review v1

This review checks whether the bounded stratified label plan can be filled from existing artifacts before running any new playouts.

## Summary

- Planned jobs: `11`
- Fill status counts: `{'compatible_target_label_available': 11}`
- Missing replay-free labels: `0`
- Execute labels now: `False`
- Decision: `planned_labels_replay_free_fillable`

## Job Review

- `selector_label.stage4.state.1e4f48a672e8.selected_guardrail` status=`compatible_target_label_available` target_labels=`1` proposal_labels=`1`
- `selector_label.stage4.state.f17117682948.selected_guardrail` status=`compatible_target_label_available` target_labels=`1` proposal_labels=`1`
- `selector_label.stage4.state.02cfd843a2cf.selected_guardrail` status=`compatible_target_label_available` target_labels=`1` proposal_labels=`1`
- `selector_label.stage4.state.256a3da30f0f.selected_guardrail` status=`compatible_target_label_available` target_labels=`2` proposal_labels=`2`
- `selector_label.stage5.state.7bd8961882ad.selected_guardrail` status=`compatible_target_label_available` target_labels=`2` proposal_labels=`1`
- `selector_label.stage5.state.87b1160e68b9.selected_guardrail` status=`compatible_target_label_available` target_labels=`2` proposal_labels=`1`
- `selector_label.stage5.state.87b1160e68b9.same_move_or_alt_provider` status=`compatible_target_label_available` target_labels=`2` proposal_labels=`1`
- `selector_label.stage5.state.2c1d6da27ea1.selected_guardrail` status=`compatible_target_label_available` target_labels=`3` proposal_labels=`2`
- `selector_label.stage6.state.d1f052d2cab2.selected_guardrail` status=`compatible_target_label_available` target_labels=`3` proposal_labels=`2`
- `selector_label.stage6.state.52085d244e9d.selected_guardrail` status=`compatible_target_label_available` target_labels=`2` proposal_labels=`1`
- `selector_label.stage6.state.69711173114a.selected_guardrail` status=`compatible_target_label_available` target_labels=`3` proposal_labels=`2`

## Recommended Next Step

`build_replay_free_stratified_selector_label_dataset`
