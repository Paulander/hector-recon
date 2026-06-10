# KRK Selector Objective Label Semantics v0

This non-causal label contract separates selector target types before any arbiter sandbox.

## Why

The current evidence mixes several different label meanings:

- selected-provider playout success,
- forced-provider conversion,
- same-move provider compatibility,
- guardrail safety,
- handoff/plan success,
- held-out Stage 7 challenge status.

Those cannot be collapsed into a single “provider should own” label without creating a hidden or overfit controller.

## Target Kinds

`selected_playout_success`

The currently selected provider/move converted under the normal graph within the validation horizon. This measures current policy quality, not provider capacity.

`forced_provider_conversion`

A provider converted when forced for the first White move and then released to normal topology. This measures provider expressivity or ownership opportunity, not safe runtime selection.

`same_move_provider_compatibility`

A provider produced or endorsed the same move as another provider. This diagnoses score-scale and identity ambiguity, not conversion success.

`guardrail_safety`

A selection preserves protected lower-stage behavior and bridge tests. This is a promotion/sandbox gate, not a target-stage improvement label.

`handoff_or_plan_success`

A bounded handoff or plan window exited or handed off successfully. This is future Plan Capsule / strategy-monitor evidence.

`held_out_challenge`

A state is reserved for architecture validation and must not be used as a direct optimization target.

## Dataset Rules

- Every selector example must cite exactly one primary `target_kind`.
- Forced-provider conversion labels must not be treated as direct runtime-selection labels.
- Selected playout failures must not be treated as provider incapacity without forced-provider evidence.
- Stage 7 held-out challenge rows must stay excluded from training targets until review reclassifies them.
- Guardrail safety must remain a separate gate, not a score target alone.

## Recommended Next Step

`build_krk_selector_target_dataset_v0`

Create a replay-free dataset that maps existing labels into explicit target-kind buckets and excludes held-out Stage 7 challenge rows from training targets.

## Blocked

- Runtime arbiter.
- Default-off selector sandbox.
- Provider support adapter.
- Score bonus or provider penalty.
- Stage 7 repair or promotion.
- Stage 8 training.
