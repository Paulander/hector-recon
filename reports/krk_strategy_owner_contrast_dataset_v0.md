# KRK Strategy Owner Contrast Dataset v0

This replay-free dataset separates protected-control strategy-owner contrast evidence from Stage 7 held-out challenge evidence. It is non-causal and does not authorize a selector sandbox.

## Summary

- Rows: `8`
- Rows by stage: `{'stage5': 3, 'stage6': 1, 'stage7': 4}`
- Training-eligible rows: `4`
- Held-out challenge rows: `4`
- Training non-stage0-positive rows: `1`
- Held-out non-stage0-positive rows: `2`
- Training positive provider labels: `3`
- Training negative provider labels: `9`
- Training positive provider families: `['edge_trap']`
- Selected training provider families: `['edge_trap']`
- Same-move compatibility training rows: `4`
- Stage 7 training rows: `0`
- Readiness blockers: `['insufficient_training_label_balance', 'insufficient_protected_non_stage0_positive_rows', 'insufficient_conversion_positive_provider_family_diversity', 'insufficient_selected_provider_family_diversity', 'missing_stage4_contrast_rows']`

## Decision

- Status: `strategy_owner_contrast_dataset_underpowered_no_selector_sandbox`
- Recommended next step: `collect_or_derive_more_protected_non_stage0_contrast_rows`
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
