# Stage 7 Learnable Capsule Phase 1 Replay

- target_state_count: `2`
- max_plies: `40`
- learned_bonus: `0.01`
- result_counts: `{'max_plies': 2}`
- selected_skill_counts: `{'krk.post_box_shrink_continuation': 2}`
- plan_owned_record_count: `0`
- candidate_status: `phase1_targeted_replay_entry_or_arbitration_gap`
- diagnosis: `plan_capsule_did_not_select_owned_provider`

This is an opt-in diagnostic replay. DTM trajectory data provides the start states only; no DTM/tablebase lookup is used at runtime.

## Records

- `8/8/R7/8/2k5/8/8/3K4 w - - 2 2` -> result `max_plies` in `40` plies, selected `krk.post_box_shrink_continuation` move `a6a8`, plan-supported `0`
- `8/8/8/R7/4k3/8/3K4/8 w - - 2 2` -> result `max_plies` in `40` plies, selected `krk.post_box_shrink_continuation` move `d2e2`, plan-supported `0`
