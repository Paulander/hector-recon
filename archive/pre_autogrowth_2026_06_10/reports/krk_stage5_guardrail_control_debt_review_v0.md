# KRK Stage 5 Guardrail Control-Debt Review v0

## Decision

Status: `stage5_one_ply_guardrail_control_debt_confirmed`

- Stage 5 overlay regressed vs paired base control: `False`
- Stage 5 conversion preserved: `True`
- Stage 5 one-ply debt reproduces in base control: `True`
- Stage 6 overlay promotion eval status: `overlay_only`
- Quarantine Stage 6 overlay for Stage 5 one-ply debt: `False`
- Replace protected stack now: `False`
- Recommended next step: `split_stage5_guardrail_into_conversion_preservation_and_local_reward_contract_debt_before_clean_stack_replacement`

## Metrics

Stage 5 overlay guardrail:

- total: `300`
- improved/worsened/optimal: `144/156/144`
- mate rate / max-plies rate: `1.000` / `0.000`
- shadow candidates: `0`
- one-ply status / conversion status: `failed` / `passed`

Stage 5 base control:

- total: `300`
- improved/worsened/optimal: `144/156/144`
- mate rate / max-plies rate: `1.000` / `0.000`
- shadow candidates: `0`
- one-ply status / conversion status: `failed` / `passed`

Overlay-vs-control delta:

- improved delta: `0`
- worsened delta: `0`
- mate-rate delta: `0.000`
- max-plies-rate delta: `0.000`
- shadow-candidate delta: `0`

## Post-Own One-Ply Patterns

- unique post-own state/move rows: `6`
- status counts: `{'failed': 156, 'confirmed': 144}`

- `59`x status=`confirmed` move=`b7h7` reward=`0.07400000000000001` oracle=`0.07400000000000001` fence_stable=`False` cut=`edge` box_area=`7` fen=`4k3/1R6/1K6/8/8/8/8/8 w - - 0 1`
- `54`x status=`failed` move=`a4a8` reward=`-0.865` oracle=`0.14900000000000002` fence_stable=`False` cut=`rank` box_area=`7` fen=`4k3/8/8/8/R7/8/4K3/8 w - - 0 1`
- `54`x status=`failed` move=`e7e1` reward=`-0.016` oracle=`0.07400000000000001` fence_stable=`True` cut=`edge` box_area=`21` fen=`7k/4RK2/8/8/8/8/8/8 w - - 0 1`
- `48`x status=`failed` move=`f2g3` reward=`-0.75` oracle=`0.14900000000000002` fence_stable=`False` cut=`edge` box_area=`28` fen=`7k/8/8/8/R7/8/5K2/8 w - - 0 1`
- `44`x status=`confirmed` move=`a7h7` reward=`0.07400000000000001` oracle=`0.07400000000000001` fence_stable=`False` cut=`edge` box_area=`7` fen=`4k3/R7/K7/8/8/8/8/8 w - - 0 1`
- `41`x status=`confirmed` move=`c7h7` reward=`0.07400000000000001` oracle=`0.07400000000000001` fence_stable=`True` cut=`edge` box_area=`7` fen=`k7/2R5/2K5/8/8/8/8/8 w - - 0 1`

## Interpretation

- Stage 5 conversion preservation passes under the corrected historical validation profile: overlay and base-control both mate 300/300 with 0 shadow candidates.
- Stage 5 one-ply local reward debt is identical in the Stage 6 overlay guardrail and the fresh Stage 5 base control: 144 improved, 156 worsened.
- The one-ply failures still expose useful contract debt, but they are not evidence of Stage 6 overlay interference because the paired base control has the same debt.
- Promotion evaluation should keep this as overlay_only/control-debt, not promoted replacement, until the Stage 5 guardrail definition is split or explicitly accepted.

## Guardrail Definition Recommendation

Split Stage 5 guardrail interpretation into two tracks:

- `conversion_preservation_guardrail`: paired overlay-vs-base-control comparison. Retry1 passes this because conversion and shadow behavior do not regress.
- `local_reward_contract_guardrail`: Stage 5 fence local reward/visible-contract alignment. Retry1 fails this, but the failure is already present in the fresh Stage 5 base control.

Therefore Stage 6 overlay validation should remain `overlay_only` with control debt. Clean protected-stack replacement remains blocked until the Stage 5 contract debt is either accepted as known base debt or repaired by an explicit guardrail-semantics review.

## Invariants

- runtime defaults changed: `False`
- runtime selector implemented: `False`
- runtime DTM/tablebase lookup: `False`
- gameplay topology mutation: `False`
- Stage 7 promotion: `False`
- Stage 8 training: `False`
