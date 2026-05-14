# KRK Handoff Counterfactual Notes

This note records the current interpretation of the Stage 5 handoff diagnostics for implementation and article follow-up.

## Observations

- The ungated visible successor layer diagnostic produced `53 mate / 47 max_plies`.
- The coarse contract gate produced `42 mate / 58 max_plies`, so the gate is a useful diagnostic failure, not a default mechanism.
- The counterfactual sweep reduced the 47 failures to three unique post-reply state signatures.
- One repeated state family was helped by forcing an edge-trap successor for the first move.
- Two state families did not convert under the tested forced successors, so they remain possible missing-capacity or downstream-handoff cases.

## Interpretation

The failed gate showed that missing visible contracts must not be treated as automatic evidence against a provider skill. In particular, `mate_basin_available` was really immediate mate-in-one availability, not broad mate-basin membership. A high `krk.stage0_basin` score with no mate-in-one can still mean useful approach or coordination.

The refined rule is:

- Visible contracts license skills.
- Explicit visible vetoes suppress skills.
- Missing contracts are neutral by default.

This keeps the causal path ReCoN-shaped: visible SCRIPT/TERMINAL evidence may add support or veto a role, but packets, stats, candidates, and hidden diagnostic state remain non-causal.

## Current Implementation Direction

The next mechanism is role-contract refinement. Several visible roles may license the same learned provider, for example:

- `krk.stage0_finish` licenses `krk.stage0_basin` when mate-in-one is visible.
- `krk.stage0_king_approach_after_fence` licenses `krk.stage0_basin` when post-fence king support can improve.
- `krk.edge_trap_*_recovery` roles license edge-trap providers only when motif-specific geometry is visible.

The old coarse gate remains opt-in diagnostic mode. The new role-license mode is additive and experimental.

## First Role-License Smoke Result

A tiny bounded smoke comparison (`5` samples, `20` plies, `40` ticks) showed:

- No role-license mode: `3 mate / 2 max_plies`.
- Role-license mode with `0.25` bonus: `2 mate / 3 max_plies`.

The failure was informative: role licenses were mechanically visible, but the bonus was too strong and over-licensed `krk.fence_established` repair and `krk.edge_trap_wrong_tempo` in states where the geometry was still too broad. The next conservative patch reduced the default role bonus to `0.05`, moved the repair license away from same-skill `krk.fence_established`, and made wrong-tempo geometry require visible enemy-between geometry.

## Slice 13 Bounded Paired Comparison

A bounded `25`-sample comparison used the same Stage 5 curriculum setup with `20` plies and `40` ticks:

- No role-license mode: `17 mate / 8 max_plies`.
- Role-license mode: `17 mate / 8 max_plies`.
- One-ply local skill remained solved in both modes: `25/25 optimal`.
- Selected successors were identical in both modes: `krk.stage0_basin` `18`, `krk.edge_trap_close` `5`, `krk.fence_established` `2`.
- No selected successor, move, or outcome changed across the paired run.

The role-license layer was neutral rather than helpful in this bounded run. The important audit detail is that `role_bonus_count` was `0`, and selected providers were still sourced by actuator score. This means the conservative role contracts did not degrade routing, but they also did not yet license the selected providers in these states.

## Slice 13 Failed-State Counterfactual Sweep

The eight bounded conversion failures were replayed with forced first-successor ownership over:

- `krk.stage0_basin`
- `krk.edge_trap_close`
- `krk.fence_established`
- `krk.fence_maintenance`
- `krk.edge_trap_wrong_tempo`
- `krk.edge_trap_enemy_between`

Summary:

- `8` failed samples replayed.
- `5/8` had at least one forced successor that converted to mate.
- `3/8` had no tested forced successor convert within the bounded playout.
- `krk.fence_maintenance` was unavailable in all eight states, so it is currently a role/contract placeholder rather than an effective provider.

The five recoverable failures were all the repeated `state.394b71e02d00` family:

- Start FEN: `k7/2R5/2K5/8/8/8/8/8 w - - 0 1`
- Post-reply FEN: `1k6/7R/2K5/8/8/8/8/8 w - - 2 2`
- Actual selected successor: `krk.stage0_basin`
- Actual result: `max_plies`
- Forced `krk.edge_trap_close`: `mate`
- Forced `krk.edge_trap_wrong_tempo`: `mate`
- Forced `krk.edge_trap_enemy_between`: `mate`

This is evidence for a visible routing/role-license gap, not missing skill capacity, for that state family. The edge-trap providers contain useful first moves, but `krk.stage0_basin` wins the actual selection with a high score.

The three unrecovered failures were:

- `state.0d62ea23963f`, repeated twice. Actual selected successor: `krk.fence_established`; failure classes included `successor_conflict`, `maintenance_needed_but_not_detected`, and `low_support_fallback`.
- `state.3d73682bdbe3`, once. Actual selected successor: `krk.edge_trap_close`; failure class `successor_conflict`.

No tested existing successor converted these two state families in the bounded playout. These remain possible missing-capacity, missing-geometry, or downstream-handoff cases. They should be tested next with legal-first-move sweeps and/or force-until-role-breaks before training a new continuation skill.

## Slice 13 Legal-First-Move Sweep

A unique-state legal-first-move sweep was added to `scripts/sweep_krk_counterfactual_successors.py`. It pushes each legal White move from the failed post-reply state and then releases control back to normal ReCoN playout. This is still diagnostic-only and does not alter runtime routing.

Result over the three unique failed state families:

- `3/3` had at least one legal first move that converted to mate.
- Therefore the bounded failures are not yet evidence of missing basic move capacity.
- The immediate problem is successor/role selection and visible ontology: useful converting moves exist, but the current provider/role machinery does not select them.

Per-state result:

- `state.0d62ea23963f`
  - Post-reply FEN: `5k2/7R/1K6/8/8/8/8/8 w - - 2 2`
  - Actual successor: `krk.fence_established`
  - Forced-successor sweep: no tested provider converted.
  - Legal converting first moves: `b6c5`, `h7a7`, `h7h1`.
  - Best bounded result: `h7h1`, mate in `13` plies.

- `state.3d73682bdbe3`
  - Post-reply FEN: `5k2/7R/K7/8/8/8/8/8 w - - 2 2`
  - Actual successor: `krk.edge_trap_close`
  - Forced-successor sweep: no tested provider converted.
  - Legal converting first move: `h7h5`.
  - Best bounded result: mate in `17` plies.

- `state.394b71e02d00`
  - Post-reply FEN: `1k6/7R/2K5/8/8/8/8/8 w - - 2 2`
  - Actual successor: `krk.stage0_basin`
  - Forced edge-trap providers converted.
  - Legal-first sweep found `15` converting first moves.
  - Several rook moves converted in `5` plies, including `h7e7`, `h7f7`, `h7g7`, and `h7h1` through `h7h8`.

Next interpretation:

- `state.394...` is a clear role-license/routing failure: edge-trap providers can convert, but high-scoring `stage0_basin` wins.
- `state.0d62...` and `state.3d73...` are not missing-capacity examples. They are missing provider coverage or missing visible role terms for legal moves that current successor providers do not expose.
- Before training a new continuation skill, add or refine visible terms around rook transfer, checking/tempo moves, king support improvement, and corner-distance/box geometry so these legal converting moves become explainable by a ReCoN-visible role.

## Slice 14 Visible Rook-Transfer Ontology

The next ontology slice added action-relevant visible terms:

- `king_support_improvement_move_exists`
- `safe_rook_long_transfer_available`
- `safe_rook_edge_transfer_available`
- `safe_check_available`
- `rook_transfer_after_fence_available`
- `edge_rook_transfer_recovery_available`
- `corner_net_pressure_available`

Two visible role contracts were added:

- `krk.rook_transfer_after_fence`
- `krk.edge_rook_transfer_recovery`

Both roles can license the existing edge-trap providers:

- `krk.edge_trap_close`
- `krk.edge_trap_enemy_between`
- `krk.edge_trap_wrong_tempo`

This keeps the mechanism ReCoN-shaped: visible TERMINAL context terms activate visible role SCRIPTs, and those roles provide an additive provider license. The role does not directly select a move.

Validation on the three unique failed state families:

- All three expose `rook_transfer_after_fence_available`.
- All three expose `edge_rook_transfer_recovery_available`.
- All three expose `safe_rook_edge_transfer_available`.

Bounded `25`-sample paired comparison on the recompiled Slice 14 topology:

- No role-license mode: `17 mate / 8 max_plies`.
- Role-license mode: `17 mate / 8 max_plies`.
- One-ply local skill remained solved in both modes: `25/25 optimal`.
- Role bonuses became active in `3/25` post-reply states.
- One selected successor changed: from `krk.fence_established` to `krk.edge_trap_close` on the `state.0d62...` family.
- The changed state still ended in `max_plies`, so the role-license direction is semantically better but not yet sufficient for conversion.

Shadow trigger changes:

- No-role mode: `repeated_conversion_failure=8`, `route_conflict=3`, `maintenance_needed_but_not_detected=2`, `low_support_fallback=2`, `high_score_conversion_failure=5`.
- Role-license mode: `repeated_conversion_failure=8`, `route_conflict=3`, `high_score_conversion_failure=5`.

Interpretation:

- The new roles reduced some diagnostic noise by replacing low/maintenance ambiguity with visible edge-trap support.
- They did not improve conversion yet because the selected edge-trap provider still chooses a non-converting first move in at least one family.
- The next likely need is finer visible terms for *which rook transfer* is appropriate, not just whether a safe rook transfer exists.

## Slice 15/16 Move-Shape Bias And Explicit Veto Audit

An experimental move-shape refinement was added behind role-license mode:

- Edge-trap providers may receive visible move-shape support when an active rook-transfer role exists and the candidate move itself is a safe rook transfer.
- Providers with explicit active visible role vetoes may be penalized when another provider has a visible role license.

The first aggressive default was intentionally tested and failed:

- Aggressive role-veto/move-shape defaults: `7 mate / 18 max_plies`.
- This is worse than the Slice 14 role-license baseline: `17 mate / 8 max_plies`.

Interpretation:

- The explicit-veto idea is ReCoN-faithful, but it is too blunt as a default causal mechanism.
- The move-shape support also needs finer evidence before it should steer normal play.
- These mechanisms were therefore made opt-in by setting their default weights to `0.0`.

Safe-default rerun:

- Slice 16 safe default role-license mode: `17 mate / 8 max_plies`.
- Selected successors matched Slice 14: `krk.edge_trap_close` `7`, `krk.stage0_basin` `18`.
- Role-license source count matched Slice 14: `visible_role_license=3`, `actuator_score=22`.

Current conclusion:

- Keep visible rook-transfer terms and role contracts.
- Keep explicit role veto and move-shape bias available for controlled experiments only.
- Do not make either a default causal path until paired diagnostics show no conversion regression.

## Slice 17 Move-Shape Audit

A non-causal move-shape audit was added to the legal-first sweep. For every legal first move from a failed post-reply state it records:

- current visible terms
- candidate move-shape terms
- post-move terms
- worst-reply survival terms

This does not change runtime behavior. It is ontology-discovery data for a future role-scoped move-shape SCRIPT layer.

The unique failed-state audit confirmed that every unique family has converting legal moves, but simple terms still do not perfectly separate conversion from failure.

Key findings:

- `state.0d62...`
  - Converting moves: `b6c5`, `h7a7`, `h7h1`.
  - No term is unique to only converting moves.
  - Converting rook moves include `rook_to_edge_file`; the best move `h7h1` includes `rook_transfer_vertical` and `rook_to_edge_rank`.

- `state.3d73...`
  - Converting move: `h7h5`.
  - The move has `rook_transfer_vertical`, `rook_to_edge_file`, `cut_preserved_after_move`, `rook_safe_after_worst_reply`, and `no_draw_after_worst_reply`.
  - These terms are not globally unique, so role-scoped context remains necessary.

- `state.394...`
  - Many converting rook transfers exist.
  - Terms unique to converting moves include `checking_line_created`, `rook_to_checking_line`, `safe_check_created`, `rook_transfer_vertical`, and `rook_to_edge_rank`.
  - Fast `5`-ply conversions often have vertical transfer or checking-line/corner-net pressure terms.

Interpretation:

- A global move-shape bonus remains too broad.
- The next causal experiment should be role-scoped and state-family-aware, e.g. `post_fence_edge_trap_recovery` licenses a move shape only when current-state terms, candidate terms, post-move terms, and worst-reply survival terms all confirm.
- The audit supports the expert's recommendation: C powered by A, with legal-first labels used non-causally.

## Slice 18 Role-Scoped Move-Shape Trace

A first role-scoped move-shape scoring path was added behind explicit opt-in flags:

- `--enable-successor-role-licenses`
- `--enable-role-scoped-move-shapes`
- `--role-scoped-move-shape-bonus`

The causal path is intentionally narrow:

- A provider must already have a visible role license.
- The candidate move must satisfy role-scoped current terms, move-shape terms, post-move terms, and worst-reply survival terms.
- The score contribution is recorded as visible evidence, not hidden arithmetic.

Trace fields now include:

- `visible_role_scoped_move_shape_bonus`
- `visible_role_scoped_move_shape_licenses`
- `visible_move_shape_audit`
- `score_after_role_scoped_move_shape_bonus`

The first 5-sample trace-fixed smoke run produced:

- `5/5` one-ply optimal.
- Conversion: `3 mate / 2 max_plies`.
- Handoff packets include the full current/candidate/post-move/worst-reply evidence for the selected role-scoped move-shape license.

Example observed license:

- Role: `krk.edge_rook_transfer_recovery`
- Provider: `krk.edge_trap_close`
- Move: `h7c7`
- Source terms: `candidate_is_rook_transfer`, `cut_preserved_after_move`, `rook_safe_after_move`, `rook_safe_after_worst_reply`, `no_draw_after_worst_reply`, `box_area_decreases_after_move`

Important performance note:

- Evaluating full worst-reply move-shape audits inside runtime scoring is expensive.
- A cache and cheap current/candidate/post-move prefilter were added.
- Runtime role-scoped move-shape bonuses now use current/candidate/post-move terms by default. Full worst-reply checks are opt-in with `--require-role-scoped-move-shape-worst-reply`.
- Diagnostic loops can stop once the top actuator suggestion is stable via `--early-stop-stable-suggestions N`.
- `--no-json-stdout` suppresses full JSON printing when `--json-output` is already writing the artifact.
- The JSON now records one-ply/playout engine decision counts, total ticks, max ticks, and early-stop counts.

Tiny verification run:

- Command shape: `--samples 1 --playout-max-plies 4 --early-stop-stable-suggestions 2 --no-json-stdout`
- One-ply engine: `1` decision, `8` ticks, `1` early stop.
- Playout engine: `2` decisions, `16` ticks, `2` early stops.
- Full worst-reply role-scoped checks were disabled: `successor_role_scoped_move_shape_require_worst_reply=false`.

Interpretation:

- The role-scoped mechanism is now inspectable and ReCoN-shaped.
- It is not ready as a default causal path.
- The next safe step is performance-oriented paired diagnostics: compare trace-only, role-license, and role-scoped move-shape modes on shared samples without increasing causal strength.

## Slice 19 Paired Early-Stop Comparison

Two 25-sample bounded diagnostics were run with identical settings except for role-scoped move-shape support:

- Role-license only: `slice19_role_license_only_stage5_25_earlystop2.json`
- Role-license + role-scoped move-shape: `slice19_role_scoped_move_shape_stage5_25_earlystop2.json`

Shared settings:

- `--samples 25`
- `--playout-max-plies 20`
- `--max-ticks 40`
- `--playout-max-ticks 40`
- `--early-stop-stable-suggestions 2`
- `--enable-successor-affordance-layer`
- `--enable-successor-role-licenses`

Result:

- Both runs: `25/25` one-ply optimal.
- Both runs: `17 mate / 8 max_plies`.
- Both runs selected successors identically: `krk.stage0_basin=18`, `krk.edge_trap_close=7`.
- Role-scoped move-shape bonuses were active in `3/25` post-reply packets, but did not change selected successors or conversion outcomes.

Performance counters:

- One-ply decisions: `25`, total ticks `200`, early-stop count `25`.
- Playout decisions: `206`, total ticks `1648`, early-stop count `206`.
- Max ticks per decision stabilized at `8`, so the main cost is the number of playout decisions, not unstable long engine loops.

Interpretation:

- Role-scoped move-shape support is currently safe and traceable, but causally neutral at bonus `0.05`.
- Increasing the global bonus is not the right next step because prior aggressive move-shape/veto mode regressed badly.
- The next implementation should use the legal-first audit to narrow role-scoped contracts for specific failure families, especially replacing broad `box_area_decreases_after_move` licensing with more specific vertical/checking-line/corner-net terms where supported by the audit.
