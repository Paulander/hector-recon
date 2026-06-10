# Stage 7 Learnable Capsule Phase 1 Replay

- target_state_count: `2`
- max_plies: `40`
- learned_bonus: `0.01`
- result_counts: `{'max_plies': 2}`
- selected_skill_counts: `{'krk.post_box_shrink_continuation': 2}`
- plan_owned_record_count: `2`
- candidate_status: `phase1_targeted_replay_still_failing`
- diagnosis: `provider_selected_by_visible_plan_capsule_but_multistep_policy_still_fails`

This is an opt-in diagnostic replay. DTM trajectory data provides the start states only; no DTM/tablebase lookup is used at runtime.

## Records

- `8/8/R7/8/2k5/8/8/3K4 w - - 2 2` -> result `max_plies` in `40` plies, selected `krk.post_box_shrink_continuation` move `a6a8`, plan-supported `40`
- `8/8/8/R7/4k3/8/3K4/8 w - - 2 2` -> result `max_plies` in `40` plies, selected `krk.post_box_shrink_continuation` move `a5h5`, plan-supported `40`
