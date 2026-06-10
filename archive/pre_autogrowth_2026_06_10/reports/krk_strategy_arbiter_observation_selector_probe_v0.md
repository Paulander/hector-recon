# KRK Strategy Arbiter Observation Selector Probe v0

This is a replay-free probe over trace-only observation frames and existing provider labels.

## Summary

- Records: `12`
- Labeled rows: `3`
- Stage counts: `{'stage4': 2, 'stage5': 1, 'stage7': 9}`
- Selected label counts: `{'positive': 2, 'unknown': 10}`
- Positive hit rate on labeled rows: `0.6666666666666666`
- Underlabeled: `True`

## Rows

- `state.069e81a609ed` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.0926f12f8e8f` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.0afbf11aa123` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.38aed2f35911` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.4a464b782ecb` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.4e34ad0b2f29` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.ac0b7ed500ea` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.b6796dfb62ff` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.ff6652c8832c` stage=`stage7` selected=`krk.stage0_basin` label=`unknown` positives=`[]` negatives=`[]`
- `state.02cfd843a2cf` stage=`stage4` selected=`krk.stage0_basin` label=`positive` positives=`['krk.stage0_basin']` negatives=`[]`
- `state.02feb8593cc6` stage=`stage5` selected=`krk.fence_established` label=`unknown` positives=`['krk.edge_trap_close']` negatives=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- `state.1e4f48a672e8` stage=`stage4` selected=`krk.stage0_basin` label=`positive` positives=`['krk.stage0_basin']` negatives=`[]`

## Decision

Status: `observation_selector_probe_underlabeled`
Sandbox ready: `False`
Runtime arbiter allowed: `False`
Recommended next step: `add_small_labeled_observation_controls_before_sandbox_review`

Do not implement a runtime selector from this probe.
