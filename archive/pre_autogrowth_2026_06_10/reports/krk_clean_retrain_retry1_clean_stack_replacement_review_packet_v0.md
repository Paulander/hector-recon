# KRK Retry1 Clean Stack Replacement Review Packet v0

Status: `retry1_clean_stack_replacement_review_ready_explicit_approval_required`

## Decision

- Replacement review ready: `True`
- Implementation allowed by this packet: `False`
- Clean stack replacement performed: `False`
- Explicit human approval required before any file change: `True`
- Recommended next step: `request_explicit_clean_stack_replacement_approval_or_keep_current_protected_stack`

## Prerequisites

- stage6_target_passed_corrected_profile: `True`
- stage5_conversion_preservation_passed: `True`
- stage5_local_reward_debt_accepted_as_known_base_control_debt: `True`
- stage4_caveat_control_review_passed: `True`
- m1_m4_preservation_passed: `True`
- kpk_kqk_bridge_preservation_passed: `True`
- snapshot_manifest_ready: `True`
- snapshot_manifest_paths_exist: `True`

## Known Caveats

- `stage4_wrong_tempo_h40_caveat`: `reproduces_in_base_control_not_overlay_regression`; impact: `does_not_block_overlay_replacement_review_but_remains_known_caveat`
- `stage5_local_reward_contract_debt`: `known_base_control_debt`; impact: `accepted_only_as_guardrail_semantics_debt_not_as_solved_contract`

## Later Approval Scope

Allowed only if explicitly approved later:

- update protected Stage 5/6 stack references only if a later explicit approval says so
- preserve rollback paths recorded in the snapshot manifest
- rerun default protected validation after any approved replacement

Forbidden:

- promote Stage 7
- train Stage 8
- change runtime defaults
- add runtime selector behavior
- use runtime DTM/tablebase
- mutate topology during gameplay
- delete or overwrite rollback sources

## Post-Approval Validation Required

- Stage 5 conversion-preservation guardrail
- Stage 6 drive_to_edge h40 validation with historical validation bonus
- Stage 4 caveat/control check remains no-regression vs base control
- M1-M4 preservation tests
- KPK-to-KQK bridge/routing preservation tests
- rollback dry-run plan

## Boundary

This packet is review-only. It does not copy, replace, delete, promote, train, route, score, mutate topology, or change runtime defaults.
