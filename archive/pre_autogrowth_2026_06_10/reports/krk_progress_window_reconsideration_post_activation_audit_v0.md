# KRK Progress-Window Reconsideration Post-Activation Audit v0

This is a non-causal audit of the activated-but-failed runtime-test row.

## Summary

- target: `cp.krk.state.ea634c29ece7`
- sandbox_status: `wired_but_policy_insufficient`
- promotion_status: `quarantined_or_analysis_only`
- baseline: `max_plies/40`
- enabled: `max_plies/40`
- activation_count: `14`
- selected_supported_provider_counts: `{'krk.edge_trap_close': 1, 'krk.fence_established': 7, 'krk.stage0_basin': 6}`

## Classification

- primary: `candidate_set_missing_good_alternative`
- labels: `['candidate_set_missing_good_alternative', 'visible_support_terms_overbroad']`
- supported_candidate_mate_count: `0`
- unsupported_visible_candidate_mate_count: `0`
- selected_supported_mate_count: `0`
- locally_safe_progress_count: `14`

## Activation Records

- ply `10` selected `krk.edge_trap_close` `b1b8` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `14` selected `krk.fence_established` `c7d8` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `16` selected `krk.stage0_basin` `d8c7` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `18` selected `krk.fence_established` `c7d8` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `20` selected `krk.stage0_basin` `d8c7` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `22` selected `krk.fence_established` `c7d8` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `24` selected `krk.stage0_basin` `d8c7` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `26` selected `krk.fence_established` `c7d8` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `28` selected `krk.stage0_basin` `d8c7` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `30` selected `krk.fence_established` `c7d8` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `32` selected `krk.stage0_basin` `d8c7` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`
- ply `34` selected `krk.fence_established` `c7d8` -> `max_plies`/`40`; supported_mates=`0` unsupported_mates=`0`

## Decision

- status: `post_activation_failure_classified`
- next: `return_to_candidate_generation_or_broader_strategy_sequence_track`
- implement_next_fix_now: `False`

Do not enable by default, tune support amount, run guardrails, promote Stage 7, train Stage 8, or turn this into a general pre-decision selector from this audit.
