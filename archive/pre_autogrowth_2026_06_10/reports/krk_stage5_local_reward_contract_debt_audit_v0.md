# KRK Stage 5 Local Reward Contract-Debt Audit v0

Status: `stage5_local_reward_contract_debt_is_guardrail_semantics_debt`

## Decision

- overlay matches base-control patterns: `True`
- conversion preserved: `True`
- local reward debt is Stage 6 regression: `False`
- clean stack replacement allowed: `False`
- recommended next step: `accept_stage5_local_reward_debt_as_known_base_control_debt_for_overlay_only_review_and_run_remaining_preservation_checks_before_any_clean_stack_replacement`

## Pattern Summary

- unique overlay patterns: `6`
- unique base-control patterns: `6`
- post-own statuses: `{'confirmed': 144, 'failed': 156}`
- post-reply statuses: `{'confirmed': 144, 'failed': 156}`
- semantic alignment: `{'reward_visible_contract_conversion_aligned': 144, 'visible_contract_and_conversion_without_local_reward': 156}`
- root-cause labels: `{'no_debt_pattern': 144, 'local_reward_too_strict_for_conversion': 156, 'one_ply_worst_reply_reward_prefers_alternative': 156, 'fence_break_after_reply_still_converts': 54, 'box_area_expands_after_reply_but_converts': 54, 'stable_fence_still_negative_dense_reward': 54}`

## Pattern Rows

- `59`x `reward_visible_contract_conversion_aligned` move=`b7h7` status=`confirmed` reply=`confirmed` chosen=`0.07400000000000001` oracle=`0.07400000000000001` labels=`['no_debt_pattern']` fen=`4k3/1R6/1K6/8/8/8/8/8 w - - 0 1`
- `54`x `visible_contract_and_conversion_without_local_reward` move=`a4a8` status=`failed` reply=`failed` chosen=`-0.865` oracle=`0.14900000000000002` labels=`['local_reward_too_strict_for_conversion', 'one_ply_worst_reply_reward_prefers_alternative', 'fence_break_after_reply_still_converts', 'box_area_expands_after_reply_but_converts']` fen=`4k3/8/8/8/R7/8/4K3/8 w - - 0 1`
- `54`x `visible_contract_and_conversion_without_local_reward` move=`e7e1` status=`failed` reply=`failed` chosen=`-0.016` oracle=`0.07400000000000001` labels=`['local_reward_too_strict_for_conversion', 'one_ply_worst_reply_reward_prefers_alternative', 'stable_fence_still_negative_dense_reward']` fen=`7k/4RK2/8/8/8/8/8/8 w - - 0 1`
- `48`x `visible_contract_and_conversion_without_local_reward` move=`f2g3` status=`failed` reply=`failed` chosen=`-0.75` oracle=`0.14900000000000002` labels=`['local_reward_too_strict_for_conversion', 'one_ply_worst_reply_reward_prefers_alternative']` fen=`7k/8/8/8/R7/8/5K2/8 w - - 0 1`
- `44`x `reward_visible_contract_conversion_aligned` move=`a7h7` status=`confirmed` reply=`confirmed` chosen=`0.07400000000000001` oracle=`0.07400000000000001` labels=`['no_debt_pattern']` fen=`4k3/R7/K7/8/8/8/8/8 w - - 0 1`
- `41`x `reward_visible_contract_conversion_aligned` move=`c7h7` status=`confirmed` reply=`confirmed` chosen=`0.07400000000000001` oracle=`0.07400000000000001` labels=`['no_debt_pattern']` fen=`k7/2R5/2K5/8/8/8/8/8 w - - 0 1`

## Interpretation

- All Stage 5 overlay and base-control samples convert at h40 with zero shadow candidates under the corrected profile.
- The one-ply debt reproduces with the same state/move pattern signature in the paired base control.
- The dominant debt class is visible fence contract plus h40 conversion without local dense reward confirmation.
- This is guardrail semantics/control debt, not evidence that Stage 6 damaged Stage 5.

## Boundary

This audit is replay-free and non-causal. It does not change runtime behavior, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate topology.
