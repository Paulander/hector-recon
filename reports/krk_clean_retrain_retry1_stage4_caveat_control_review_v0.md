# KRK Retry1 Stage 4 Caveat Control Review v0

Status: `stage4_caveat_reproduces_in_base_control_no_overlay_regression`

## Decision

- Stage 4 overlay regressed vs base control: `False`
- Stage 4 caveat reproduces in base control: `True`
- Clean stack replacement allowed: `False`
- Recommended next step: `run_m1_m4_and_kpk_kqk_preservation_checks_before_any_clean_stack_replacement_packet`

## Metrics

Stage 4 overlay:

- improved/worsened/optimal: `238/62/238`
- mate/max_plies: `268/32`
- shadow candidates: `0`
- one-ply/conversion status: `failed` / `failed`

Stage 4 paired base control:

- improved/worsened/optimal: `238/62/238`
- mate/max_plies: `268/32`
- shadow candidates: `0`
- one-ply/conversion status: `failed` / `failed`

Overlay-vs-control delta:

- improved delta: `0`
- worsened delta: `0`
- mate delta: `0`
- max_plies delta: `0`
- shadow candidate delta: `0`

## Interpretation

- The Stage 4 wrong-tempo caveat is identical in the Stage 6 overlay topology and the paired Stage 5 base control.
- This means the retry1 Stage 6 overlay does not worsen the known Stage 4 caveat under the corrected validation profile.
- The caveat remains real: both artifacts have 268/300 h40 mates and 32 max_plies.
- This clears the Stage 4 overlay-control regression check, but it does not authorize clean-stack replacement.

## Remaining Checks

- `m1_m4_preservation_suite`
- `kpk_kqk_bridge_preservation`
- `protected_stack_snapshot_manifest`

## Boundary

This review is non-causal. It does not replace checkpoints, change runtime behavior, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate topology.
