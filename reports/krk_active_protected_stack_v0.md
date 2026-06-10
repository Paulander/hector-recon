# KRK Active Protected Stack v0

Status: `retry1_protected_stage5_6_stack_adopted_manifest_only`

## Decision

- Clean stack adopted: `True`
- Adoption mechanism: `tracked_active_stack_manifest`
- Filesystem snapshots replaced: `False`
- Post-adoption validation required: `True`

## Scope

- Stage 5: `retry1_fence_handoff`
- Stage 6: `retry1_drive_overlay_composed`
- Stage 4: `unchanged_known_caveat_guardrail`
- Stage 7: `unchanged_quarantined_held_out`
- Stage 8: `unchanged_blocked`

## Boundary

This is a tracked active-stack reference update. It does not copy, delete, or overwrite snapshot files; rollback paths are preserved.
