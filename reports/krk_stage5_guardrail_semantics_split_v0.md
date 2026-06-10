# KRK Stage 5 Guardrail Semantics Split v0

Status: `stage5_guardrail_semantics_split_defined`

## Decision

- stage5_overlay_regressed_vs_base_control: `False`
- stage5_conversion_preserved: `True`
- stage5_one_ply_debt_reproduces_in_base_control: `True`
- clean_stack_replacement_allowed: `False`
- stage6_overlay_use_allowed_as_overlay_only: `True`
- recommended_next_step: `update_clean_retrain_promotion_review_to_accept_overlay_only_with_control_debt_but_block_clean_replacement_until_stage5_local_reward_contract_debt_is_resolved_or_accepted`

## Guardrail Tracks

### `stage5.conversion_preservation_guardrail`

- Purpose: Detect whether a later overlay regresses existing Stage 5 conversion behavior.
- Comparison: `candidate_overlay_guardrail_vs_paired_stage5_base_control`
- Retry1 result: `passed_no_regression`
- Promotion effect: `allows_overlay_only_if_target_stage_passes`
- Pass condition:
  - `mate_rate_delta >= -0.02`
  - `max_plies_rate_delta <= 0.02`
  - `shadow_candidate_delta <= 0`

### `stage5.local_reward_contract_guardrail`

- Purpose: Track mismatch between Stage 5 local one-ply reward and visible fence-contract success.
- Comparison: `candidate_and_paired_base_control_against_local_reward_thresholds`
- Retry1 result: `failed_but_reproduces_in_base_control`
- Promotion effect: `blocks_clean_stack_replacement_or_full_promotion_until_reviewed`
- Pass condition:
  - `improved_rate >= 0.70`
  - `worsened_rate <= 0.20`

## Clean Retrain Promotion Policy

- stage6_target_failure: `quarantine`
- stage5_conversion_regression_vs_control: `quarantine`
- stage5_local_reward_debt_only_in_candidate: `quarantine_or_review`
- stage5_local_reward_debt_reproduces_in_base_control: `overlay_only_control_debt`
- no_debt_no_regression_target_passed: `promoted_after_remaining_guardrails`

## Boundary

This is an offline guardrail-definition artifact. It does not change runtime behavior, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate topology.
