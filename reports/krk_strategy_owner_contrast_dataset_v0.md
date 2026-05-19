# KRK Strategy Owner Contrast Dataset v0

This replay-free dataset separates protected-control strategy-owner contrast evidence from Stage 7 held-out challenge evidence. It is non-causal and does not authorize a selector sandbox.

## Summary

- Rows: `13`
- Rows by stage: `{'stage4': 2, 'stage5': 4, 'stage6': 3, 'stage7': 4}`
- Training-eligible rows: `9`
- Held-out challenge rows: `4`
- Training non-stage0-positive rows: `6`
- Held-out non-stage0-positive rows: `2`
- Training positive provider labels: `13`
- Training negative provider labels: `11`
- Training positive provider families: `['drive_to_edge', 'edge_trap', 'fence_established']`
- Selected training provider families: `['edge_trap']`
- Same-move compatibility training rows: `4`
- Stage 7 training rows: `0`
- Readiness blockers: `['insufficient_selected_provider_family_diversity']`

## Decision

- Status: `strategy_owner_contrast_dataset_ready_for_non_causal_probe_selector_sandbox_blocked`
- Recommended next step: `run_non_causal_strategy_owner_contrast_probe`
- Runtime arbiter and selector sandbox remain blocked.

## Rows

- `state.0afbf11aa123` stage=`stage7` providers=`6` non_stage0_positive=`False` training=`False` heldout=`True`
- `state.38aed2f35911` stage=`stage7` providers=`6` non_stage0_positive=`False` training=`False` heldout=`True`
- `state.ac0b7ed500ea` stage=`stage7` providers=`6` non_stage0_positive=`True` training=`False` heldout=`True`
- `state.ff6652c8832c` stage=`stage7` providers=`6` non_stage0_positive=`True` training=`False` heldout=`True`
- `state.87b1160e68b9` stage=`stage5` providers=`3` non_stage0_positive=`True` training=`True` heldout=`False`
- `state.02feb8593cc6` stage=`stage5` providers=`3` non_stage0_positive=`False` training=`True` heldout=`False`
- `state.326222aefdf1` stage=`stage5` providers=`3` non_stage0_positive=`False` training=`True` heldout=`False`
- `state.699f0003a511` stage=`stage6` providers=`3` non_stage0_positive=`False` training=`True` heldout=`False`
- `state.1e4f48a672e8` stage=`stage4` providers=`3` non_stage0_positive=`True` training=`True` heldout=`False`
- `state.f17117682948` stage=`stage4` providers=`1` non_stage0_positive=`True` training=`True` heldout=`False`
- `state.7bd8961882ad` stage=`stage5` providers=`4` non_stage0_positive=`True` training=`True` heldout=`False`
- `state.d1f052d2cab2` stage=`stage6` providers=`3` non_stage0_positive=`True` training=`True` heldout=`False`
- `state.52085d244e9d` stage=`stage6` providers=`1` non_stage0_positive=`True` training=`True` heldout=`False`
