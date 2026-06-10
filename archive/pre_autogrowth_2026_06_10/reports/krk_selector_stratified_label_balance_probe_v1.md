# KRK Selector Stratified Label Balance Probe v1

This non-causal probe checks whether replay-free stratified labels are balanced enough for selector evaluation.

## Summary

- Rows: `11`
- Label counts: `{'negative': 1, 'positive': 10}`
- Underbalanced: `True`
- Decision: `stratified_labels_underbalanced_no_selector_probe`
- Runtime arbiter allowed: `False`
- Selector sandbox ready: `False`

## Breakdown

- By stage: `{'stage4': {'negative': 1, 'positive': 3}, 'stage5': {'positive': 4}, 'stage6': {'positive': 3}}`
- By target kind: `{'guardrail_safe_selected_playout': {'negative': 1, 'positive': 9}, 'same_move_provider_compatibility_or_forced_alternative': {'positive': 1}}`
- By provider: `{'krk.edge_trap_close': {'positive': 1}, 'krk.edge_trap_enemy_between': {'positive': 1}, 'krk.stage0_basin': {'negative': 1, 'positive': 8}}`

## Interpretation

- Replay-free planned labels are mostly positive protected-control examples.
- They are useful as guardrail-positive evidence but are not balanced enough to train or evaluate a selector.
- No runtime arbiter or sandbox is justified from this label set.

## Recommended Next Step

`collect_or_identify_negative_protected_controls`
