# KRK Protected Stage Status

This is a replay-free, non-causal status audit of the protected KRK stages. It does not change runtime behavior, defaults, topology, training, or promotion state.

## Short Answer

- Stage 1 is solved/protected as a backchain/local regression subskill.
- Stage 5 is solved/protected as the current fence/handoff provider pack.
- Stage 6 is solved/promoted as an additive overlay on frozen Stage 5 providers.
- Stage 4 is solved in the clean 500-sample `handoff_composition_v1` profile, but carries a separate 300-sample h40 overlay-control caveat that reproduces identically on the frozen Stage 5 base.

So the current architecture has validated/protected Stages 1, 4, 5, and 6, but Stage 4 should not be described as an unconditional strict h40 conversion guarantee under every guardrail configuration.

## Stage Details

### stage1_backchain

- Status: `protected_solved_local_regression`
- Solved under current architecture: `True`
- Scope: local/backchain regression; not a complete KRK policy by itself
- Caveat: Evidence is local/backchain-focused; Stage 1 is protected as a subskill.

- `manifest`: formal validation `True` (257 nodes, 796 edges)
- `documented_500_sample_regression`: `True`
- `documented_500_sample_result`: `500/500 improved, 500/500 optimal, 0 worsened, 0 no-move`

### stage4_wrong_tempo

- Status: `protected_profile_solved_with_overlay_guardrail_caveat`
- Solved under current architecture: `True`
- Scope: wrong-tempo local/conversion profile; current overlay-control h40 caveat remains separate
- Caveat: The 500-sample handoff_composition_v1 profile is clean, but the later 300-sample overlay/control guardrail has 247 mate / 53 max_plies on both overlay and frozen Stage 5 base. This is not Stage 6 overlay interference; it remains a horizon/guardrail-definition diagnostic.

- `profile_500_seed7_h40`: total `500`, mate: 500, shadow `0`
- `overlay_probe_300_seed7_h40`: total `300`, mate: 247, max_plies: 53, shadow `106`
- `base_control_300_seed7_h40`: total `300`, mate: 247, max_plies: 53, shadow `106`
- `overlay_caveat_reproduces_on_base_control`: `True`

### stage5_fence

- Status: `protected_solved_conversion_profile`
- Solved under current architecture: `True`
- Scope: protected Stage 5 fence/handoff provider pack
- Caveat: Opt-in experimental profile; default policy remains unchanged.

- `profile_1000_seed7_h40`: total `1000`, mate: 1000, shadow `0`
- `stage6_overlay_guard_300_seed7_h40`: total `300`, mate: 300, shadow `0`

### stage6_drive_overlay

- Status: `promoted_overlay_solved_against_stage5_guardrail`
- Solved under current architecture: `True`
- Scope: additive Stage 6 overlay on frozen Stage 5 provider pack
- Caveat: Stage 6 is solved as an overlay, not as a monolithic replacement topology. Use frozen-provider plus overlay composition for later stages.

- `stage6_candidate_300_seed7_h40`: total `300`, mate: 300, shadow `0`
- `stage5_guardrail_300_seed7_h40`: total `300`, mate: 300, shadow `0`
- `promotion_eval`: promotion_status `promoted`

## Current Boundary

- `handoff_composition_v1` remains an opt-in experimental KRK profile.
- Stage 6 must remain an overlay, not a monolithic replacement for validated lower providers.
- Stage 7 remains `local_valid_composition_quarantined` and must not be promoted.
- Stage 8 remains blocked until an explicit architecture decision allows it.

## Next Investigation Class

architecture-level sequence-policy or strategy-arbitration review; do not reopen Stage 7 micro-repairs without review
