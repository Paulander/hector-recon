# Stage 7 Post-Box Plan Capsule Audit

Schema: `stage7_post_box_plan_capsule_audit.v1`
Causal status: `non_causal`
Post-reply records: `45`

## Outcome By Successor

- `krk.drive_to_edge:mate`: 5
- `krk.edge_trap_close:mate`: 16
- `krk.post_box_shrink_continuation:max_plies`: 3
- `krk.stage0_basin:max_plies`: 3
- `krk.stage7_king_tempo:mate`: 6
- `krk.stage7_post_box_continuation:max_plies`: 6
- `none:mate`: 6

## Diagnosis

- `loss_of_cut_or_fence`: `possible_context_dependent`
- `missing_king_support`: `possible_context_dependent`
- `missing_plan_commitment`: `likely`
- `premature_stage0_fallback`: `observed_but_not_sufficient_after_ownership_tests`
- `provider_capacity_gap`: `likely_for_current_providers`
- `stagnation_or_repetition`: `possible_downstream`
- `wrong_first_post_box_move`: `not_sufficient`
- `wrong_second_or_third_move`: `likely`

## Recommendation

- Owned move count: `3_or_4_white_moves_initially`
- Own until: `ttl_white_moves_exhausted`
- Own until: `exit_role_confirmed`
- Own until: `abort_term_confirmed`

This audit is non-causal and does not change runtime behavior.
