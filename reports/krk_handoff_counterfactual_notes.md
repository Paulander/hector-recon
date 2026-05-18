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

## Slice 20 Narrow Edge-Rook Recovery Contract

The `krk.edge_rook_transfer_recovery` move-shape license was narrowed:

- Removed `box_area_decreases_after_move` as a sufficient shape by itself.
- Added `rook_to_edge_rank` alongside the already-supported vertical transfer, edge-file transfer, checking-line, and safe-check terms.
- Added a regression test that confirms `h7c7` no longer receives an edge-rook recovery shape bonus merely because it shrinks the box, while `h7h1` remains licensed through edge-rank/vertical transfer geometry.

Bounded diagnostic:

- Artifact: `slice20_narrow_edge_rook_recovery_stage5_25_earlystop2.json`
- Settings matched Slice 19 role-scoped mode.
- One-ply: `25/25` optimal.
- Conversion improved from Slice 19 `17 mate / 8 max_plies` to `19 mate / 6 max_plies`.
- Selected successor counts did not change: `krk.stage0_basin=18`, `krk.edge_trap_close=7`.
- The gain came entirely from `krk.edge_trap_close` conversions:
  - Slice 19: `4 mate / 3 max_plies`
  - Slice 20: `6 mate / 1 max_plies`
- Stage0 remained unchanged:
  - `13 mate / 5 max_plies`

Interpretation:

- This validates the expert's recommendation: narrow visible role-scoped move-shape contracts beat broader/global bonuses.
- The role-scoped mechanism can improve conversion without changing successor ownership, by licensing better first-move shapes within an already selected provider.
- Remaining failures are now mostly stage0 high-score conversion failures and one residual edge-trap-close failure. The next refinement should target `stage0_basin` role splitting / first-move shape, not further broad edge-trap bonus increases.

## Slice 21 Broad Role-Veto Negative Result

A broad visible role-veto penalty was tested as an opt-in diagnostic mode:

- Flag: `--successor-role-veto-penalty 6.0`
- Artifact: `slice21_stage0_veto_penalty6_stage5_25_earlystop2.json`
- Same bounded 25-sample settings as Slice 20.

Result:

- One-ply remained solved: `25/25` optimal.
- Conversion regressed badly: `7 mate / 18 max_plies`.
- Selected successors shifted only mildly: `krk.stage0_basin=17`, `krk.edge_trap_close=8`.
- The regression confirms the expert warning: missing or vetoed role contracts are too coarse to use as blanket provider suppression.

Interpretation:

- Keep broad role-veto disabled by default.
- Do not use it as the next causal mechanism.
- The safe path remains narrow, role-scoped move-shape evidence and explicit geometry terms, not global penalties.

## Slice 22 Narrow Stage0 Drift Penalty

A narrower opt-in penalty was added for one repeated failure family:

- Flag: `--successor-stage0-drift-penalty 6.0`
- Artifact: `slice22_stage0_drift_penalty6_stage5_25_earlystop2.json`
- Same bounded 25-sample settings as Slice 20, with `--suggestion-limit 20` to preserve richer trace evidence.

The rule is intentionally narrow:

- It applies only to `krk.stage0_basin`.
- It requires visible edge-trap context: `edge_trap_close_geometry`, `edge_trap_shape_available`, `fence_stable`, `rook_safe`.
- It requires an already licensed visible edge-trap recovery role for `krk.edge_trap_close`.
- It applies only to king moves that lack visible progress terms such as moving toward the enemy king or toward rook support.

Result:

- One-ply remained solved: `25/25` optimal.
- Conversion matched Slice 20: `19 mate / 6 max_plies`.
- Shadow candidates dropped from `16` in Slice 20 to `12`.
- The repeated `state.394` family was shifted from `krk.stage0_basin` to `krk.edge_trap_close`, but still max-plied.
- Selected successor counts changed from `stage0=18, edge_trap_close=7` to `stage0=13, edge_trap_close=12`.
- Stage0 failures were converted into edge-trap-close failures rather than solved:
  - Slice 20: `stage0_basin 13 mate / 5 max_plies`, `edge_trap_close 6 mate / 1 max_plies`
  - Slice 22: `stage0_basin 13 mate / 0 max_plies`, `edge_trap_close 6 mate / 6 max_plies`

Interpretation:

- The narrow drift penalty is semantically useful as a diagnostic: it identifies unproductive stage0 king drift in an edge-trap-ready state.
- It is not sufficient as a conversion fix, because ownership transfer to `edge_trap_close` still does not select a converting continuation in the repeated family.
- Do not enable this by default yet.
- The next problem is first-move selection inside a licensed edge-trap role, not just successor ownership.

Targeted replay note:

- A matching-mode counterfactual/legal-first replay was started for the two unique Slice 22 failure states, but the exhaustive legal-first portion was too slow interactively and was stopped after partial output.
- Partial output for `state.3d73682bdbe3` showed all tested rook transfers through `h7h5` still max-plied at the 20-ply bound.
- Forced-successor replays for that state also max-plied for all available existing successors at the 20-ply bound.
- This suggests either the 20-ply bound is too short for that family, or the current continuation policy still lacks a visible move-shape/continuation mechanism after the first edge-trap move.

## Slice 23 Filtered Legal-First Replay

The counterfactual sweep tool was extended with cheaper legal-first filtering:

- `--skip-forced-successor-sweep`
- `--legal-first-require-any-terms`
- `--legal-first-require-all-terms`
- `--legal-first-max-moves`
- `--legal-first-audit-no-worst-reply`

This keeps the offline audit behavior-preserving while avoiding exhaustive legal-first playouts when only selected visible move-shape families are relevant.

Filtered replay artifact:

- `slice23_filtered_legal_first.json`
- Source diagnostic: `slice22_stage0_drift_penalty6_stage5_25_earlystop2.json`
- Failed unique states: `2`
- Forced-successor sweep skipped.
- Legal-first filter terms:
  - `rook_to_checking_line`
  - `safe_check_created`
  - `rook_to_edge_rank`
  - `king_moves_toward_enemy`
  - `king_moves_toward_rook_support`
  - `white_king_distance_to_enemy_decreases`
  - `white_king_distance_to_rook_decreases`

Result:

- `state.3d73682bdbe3` (`5k2/7R/K7/8/8/8/8/8 w - - 2 2`)
  - Tested `12` filtered legal first moves.
  - Outcomes: `9 max_plies`, `3 draw`, `0 mate`.
  - Candidate king-support moves and rook-transfer/checking-line moves did not convert within the 20-ply bound.
- `state.394b71e02d00` (`1k6/7R/2K5/8/8/8/8/8 w - - 2 2`)
  - Tested `12` filtered legal first moves.
  - Outcomes: `10 mate`, `1 max_plies`, `1 draw`.
  - Best mating first moves at the 20-ply bound included `h7e7`, `h7f7`, `h7g7`, `h7h1`, and `h7h8`, all mating in `5` plies.
  - Several king-support moves also mated but more slowly, e.g. `c6d7` in `7` plies and `c6d5/c6d6` in `19` plies.

Interpretation:

- `state.394` is not missing first-move capacity. The graph has many converting legal first moves, and the visible move-shape vocabulary can describe them.
- `state.394` should be targeted by role-scoped move-shape ranking/calibration, especially distinguishing stronger rook transfers/checking-line/edge-rank moves from weaker lateral transfers such as `h7c7`.
- `state.3d73` is different: filtered promising moves did not convert within the bounded test. This may require a longer playout bound, a deeper continuation skill, or additional geometry terms before training.
- The next causal refinement should stay narrow: improve role-scoped ranking inside `state.394`-like edge-trap recovery states. Do not use broad provider gates or train on `state.3d73` until its required continuation is clearer.

## Slice 24/25 Rook Destination Distance Ranking

The visible move-shape vocabulary was extended with rook-destination distance terms:

- `rook_destination_not_adjacent_enemy`
- `rook_destination_far_from_enemy`

The `krk.edge_rook_transfer_recovery` / `krk.rook_transfer_after_fence` role-scoped move-shape license was refined:

- Lateral box-shrink transfers can now be licensed only when the rook destination is not adjacent to the enemy king.
- Far rook destinations and edge-rank transfers receive stronger visible shape support than merely non-adjacent lateral transfers.
- Adjacent lateral transfers such as `h7c7` in `state.394` remain unlicensed by the edge-rook recovery shape.

Bounded diagnostics:

- Slice 24 artifact: `slice24_lateral_distance_shape_stage5_25_earlystop2.json`
- Slice 25 artifact: `slice25_stronger_far_edge_rank_shape_stage5_25_earlystop2.json`
- Both kept one-ply solved: `25/25` optimal.
- Both remained conversion-neutral versus Slice 22: `19 mate / 6 max_plies`.

Trace interpretation:

- The refinement changed visible support terms and shifted the repeated `state.394` selected edge-trap move from `h7b7` to `h7d7`.
- Conversion did not improve because the better legal-first moves (`h7e7`, `h7f7`, `h7g7`, `h7h1`, `h7h8`) were not surfaced as selected provider suggestions in the runtime trace.
- This suggests the bottleneck is no longer the visible role license alone. The current provider/action layer may not expose the best legal first moves as actuator suggestions for the licensed provider.

Implication:

- Further increasing visible score pressure is unlikely to solve the remaining failures cleanly.
- The next useful diagnostic should compare filtered legal-first mating moves against provider actuator suggestions and emit a `provider_missing_converting_shape` / `converting_move_not_proposed` signal.
- If confirmed, the next architectural step is likely a small visible move-shape action provider or training target for post-fence continuation, rather than more role bonus tuning.

## Slice 26 Provider Suggestions vs Legal-First Conversions

The counterfactual sweep tool now has a provider-suggestion audit:

- Flag: `--provider-suggestion-audit`
- It runs one normal ReCoN decision from each failed post-reply state.
- It compares the runtime suggestion set against filtered legal-first moves that converted in replay.
- It classifies each state as:
  - `no_converting_legal_first_in_filter`
  - `selected_converting_move`
  - `converting_move_proposed_not_selected`
  - `converting_move_not_proposed`

Artifact:

- `slice26_provider_vs_legal_first.json`
- Source diagnostic: `slice25_stronger_far_edge_rank_shape_stage5_25_earlystop2.json`
- Failed unique states: `2`

Summary:

- `state.3d73682bdbe3`
  - Runtime selected `h7c7`.
  - Filtered legal-first replay found no mating first move within the 20-ply bound.
  - Classification: `no_converting_legal_first_in_filter`.
- `state.394b71e02d00`
  - Runtime selected `h7d7`.
  - Filtered legal-first replay says `h7d7` itself can convert.
  - Other converting first moves exist but were not proposed: `c6d5`, `c6d6`, `c6d7`, `h7e7`, `h7f7`, `h7g7`, `h7h1`, `h7h8`.
  - Classification: `selected_converting_move`.

Important correction:

- The remaining `state.394` failure is not primarily a missing first-move proposal after Slice 25. The runtime already selected a first move that can convert under the filtered replay.
- The failure is downstream continuation instability after a good first move, or replay sensitivity under bounded playout.
- More first-move score pressure is therefore the wrong next step.

Implication:

- For `state.394`, inspect the post-`h7d7` continuation trace and identify where conversion diverges.
- For `state.3d73`, keep it separate: either the 20-ply bound is too short, the filtered move set is incomplete, or a deeper continuation skill is missing.
- The next safe implementation should add continuation-phase diagnostics after a selected converting first move, rather than further provider/move-shape bonuses.

## Slice 27 Selected-Converting Continuation Trace

The counterfactual sweep tool now has continuation-phase tracing:

- Flag: `--continuation-trace-audit`
- Optional focus: `--continuation-trace-only-selected-converting`
- Trace cap: `--continuation-trace-max-plies`

The audit applies the runtime-selected first move from the provider audit, then runs a traced ReCoN continuation. It records compact per-ply summaries:

- White/Black move
- selected skill
- confidence
- top suggestions
- resulting FEN

Artifact:

- `slice27_selected_converting_continuation_trace.json`
- Source diagnostic: `slice25_stronger_far_edge_rank_shape_stage5_25_earlystop2.json`

Result:

- Only `state.394b71e02d00` was traced because it was the only state where the selected first move was also a converting legal-first move.
- First move: `h7d7`
- Continuation trace result: `mate`
- Plies including first move: `19`
- Final FEN: `8/5K1k/8/8/8/8/8/7R b - - 21 11`

Observed continuation pattern:

- `h7d7`
- Black `b8c8`
- `d7h7` by `krk.stage0_basin`
- Black `c8d8`
- `h7d7` by `krk.edge_trap_close`
- Black `d8e8`
- `d7h7` by `krk.stage0_basin`
- Black `e8f8`
- `h7c7` by `krk.edge_trap_close`
- Then `stage0_basin` king approach converts to mate.

Interpretation:

- The `state.394` remaining failures are not explained by a bad selected first move or by missing immediate continuation capacity in the traced replay.
- The traced replay can mate after `h7d7`, using the current graph.
- The discrepancy with bounded diagnostic max-plies likely reflects continuation sensitivity: duplicate-state replay context, trace/replay seed path, or subtle state/timing differences.
- Do not add more first-move or provider score pressure for `state.394` until the exact divergence between the failing playout and the successful traced replay is captured.

Next diagnostic target:

- Capture full trace for failing `state.394` duplicates directly inside the 25-sample landmark diagnostic when conversion fails.
- Compare failing trace against the successful Slice 27 trace to locate the first divergent White move or Black reply.

## Slice 29 Horizon Mate-In-One Classification

The Stage 5 landmark diagnostic now records end-of-horizon state facts for max-plies playouts:

- `final_turn`
- `final_mate_in_one_available`
- failure class `horizon_mate_in_one`

Artifacts:

- `slice29_horizon_mate_in_one_stage5_25.json`
- `slice29_state394_horizon_traces.jsonl`

Result:

- One-ply objective remains solved: `25/25 improved`, `25/25 optimal`.
- Bounded conversion remains `19 mate / 6 max_plies` at `--playout-max-plies 20`.
- Shadow triggers now distinguish:
  - `repeated_conversion_failure`: 6
  - `route_conflict`: 6
  - `horizon_mate_in_one`: 5

Failure class split:

- `5` cases: `horizon_mate_in_one + successor_conflict`
- `1` case: `successor_conflict`

Targeted `state.394b71e02d00` traces:

- All five `state.394` max-plies cases end at:
  - `8/5K1k/8/8/8/8/8/2R5 w - - 20 11`
  - White to move
  - mate-in-one available

Interpretation:

- The apparent `state.394` failures are horizon misses under a 20-ply cap, not true conversion failures.
- This matches Slice 27, where the same family converted in 19 plies after the post-reply state, but the full diagnostic includes the initial Stage 5 move and Black reply inside the same 20-ply budget.
- For diagnostics, `max_plies` should now be read with the horizon marker. A max-plies playout ending with White-to-move mate-in-one is a near-pass/measurement-boundary case, not evidence for missing first-move selection or missing KRK capacity.

Remaining real bounded failure:

- `state.3d73682bdbe3`
- Start FEN: `4k3/R7/K7/8/8/8/8/8 w - - 0 1`
- Stage 5 move/reply: `a7h7`, Black `e8f8`
- Post-reply FEN: `5k2/7R/K7/8/8/8/8/8 w - - 2 2`
- Selected successor: `krk.edge_trap_close`
- Failure class: `successor_conflict`
- Route margin: approximately `0.00118`

Next implication:

- Do not add broader first-move pressure for `state.394`; it is already near conversion and only crosses the cap boundary.
- Focus the next diagnostic/implementation slice on `state.3d73`: legal-first coverage, horizon extension sensitivity, and whether any visible move-shape or continuation trace can distinguish a converting route from the low-margin conflict.

## Slice 31 Final-Ply Mate Accounting

While checking the +1 horizon run, the diagnostic exposed an accounting issue:

- If White delivered checkmate on the final permitted ply, `play_to_mate` exited the loop and returned `max_plies` before checking the terminal board.
- The diagnostic now checks terminal mate/draw state once more after the loop before reporting `max_plies`.
- This changes diagnostic conversion accounting only; it does not change routing, topology, or move selection.

Artifacts:

- `slice31_horizon_plus_one_fixed_stage5_25.json`
- `slice31_horizon_plus_one_fixed_stage5_25_analysis.md`

Result at `--playout-max-plies 21`:

- One-ply objective: `25/25 improved`, `25/25 optimal`
- Conversion: `24 mate / 1 max_plies`
- Shadow triggers:
  - `repeated_conversion_failure`: 1
  - `route_conflict`: 1

Remaining bounded failure:

- `state.3d73682bdbe3`
- Start FEN: `4k3/R7/K7/8/8/8/8/8 w - - 0 1`
- Stage 5 move/reply: `a7h7`, Black `e8f8`
- Post-reply FEN: `5k2/7R/K7/8/8/8/8/8 w - - 2 2`
- Selected successor: `krk.edge_trap_close`
- Failure class: `successor_conflict`
- Best/second score: approximately `0.17334 / 0.17216`
- Route margin: approximately `0.00118`

Interpretation:

- The previous `19/25` conversion result at 20 plies was mostly a horizon/reporting boundary, not a real KRK capability gap.
- With one extra ply and corrected final-ply mate accounting, only one of the 25 sampled Stage 5 cases remains unresolved.
- The remaining problem is compact and inspectable: a single low-margin `state.3d73` route conflict.

Next target:

- Run a targeted legal-first and continuation trace for `state.3d73`.
- Determine whether the non-converting result is another horizon artifact, a legal-first selection gap, or a genuinely missing continuation role/move-shape.

## Slice 32 State 3d73 Legal-First And Continuation Audit

Artifact:

- `slice32_state3d73_legal_provider_trace.json`
- `slice32_state3d73_legal_steps.jsonl`

Target state:

- `state.3d73682bdbe3`
- Post-reply FEN: `5k2/7R/K7/8/8/8/8/8 w - - 2 2`
- Runtime first successor move: `h7c7`

Legal-first result at `--playout-max-plies 21`:

- Tested legal moves: 19
- `mate`: 0
- `max_plies`: 16
- `draw`: 3

Draw moves:

- `h7e7`
- `h7f7`
- `h7g7`

Continuation trace after runtime first move `h7c7`:

- Result: `max_plies`
- Final FEN: `5k2/8/K7/8/4R3/8/8/8 b - - 23 12`
- The trace enters a repeated rook oscillation pattern:
  - `h4e4`
  - `e4h4`
  - repeated while Black oscillates `f8g8` / `g8f8`

Interpretation:

- `state.3d73` is not a simple first-move selection gap under the current 21-ply continuation policy: no legal first move converted in the audit.
- The visible graph reaches a stagnating rook-transfer loop after the initial edge-trap move.
- This is a better target for a stagnation/loop detector and later post-fence continuation ontology than for more provider-level score pressure.

Implementation follow-up:

- Add non-causal playout stagnation summaries:
  - repeated abstract state count
  - max state repetition
  - reversible rook-move oscillation pairs
- Add failure class `rook_oscillation_loop` and shadow trigger `stagnation_loop`.
- Keep this diagnostic-only; do not let loop detection suppress moves or route causally yet.

## Slice 33-35 ReCoN-Visible Stagnation Breaker

Implemented:

- Non-causal stagnation/loop audit fields:
  - exact and abstract repeated-state counts
  - abstract state history
  - rook/king square histories
  - box-area and enemy-edge-distance histories
  - mate-in-one and safe-check histories
  - rook reversal count and oscillation pairs
  - legal loop-breaking move audits
- Visible dynamic terms:
  - `repeated_abstract_state`
  - `rook_oscillation_loop`
  - `no_box_progress_recently`
  - `no_edge_progress_recently`
  - `no_mate_progress_recently`
  - `safe_loop_breaking_move_available`
  - `loop_breaking_rook_transfer_available`
  - `loop_breaking_check_or_cut_available`
- Compiler metadata for `krk.stagnation_breaker_affordance`.
- Opt-in causal flags:
  - `--enable-stagnation-breaker`
  - `--stagnation-breaker-bonus`

Hard constraints preserved:

- Defaults are unchanged.
- No state-hash exception was added.
- Handoff packets, stats, and shadow candidates remain non-causal.
- The opt-in causal path only adds support when visible stagnation terms confirm and the candidate move is in the audited loop-breaking legal set.

Targeted `state.3d73` replay with `--enable-stagnation-breaker --stagnation-breaker-bonus 0.5`:

- Artifact: `slice35_state3d73_stagnation_breaker_trace.json`
- Result remains `max_plies` at 21 plies.
- The visible loop-breaker license fires at later loop points:
  - `h4d4`
  - `h4f4`
- Example source terms include:
  - `rook_oscillation_loop`
  - `no_box_progress_recently`
  - `safe_loop_breaking_move_available`
  - `escapes_rook_oscillation_pair`
  - `rook_safe_after_move`
  - `no_draw_after_move`
  - `box_area_decreases_after_move`
  - `checking_line_created`

25-sample opt-in comparison:

- Artifact: `slice35_stagnation_breaker_stage5_25.json`
- One-ply objective remains solved: `25/25 improved`, `25/25 optimal`.
- Conversion remains `24 mate / 1 max_plies`.
- Remaining failure is still `state.3d73682bdbe3`.
- Failure classes: `rook_oscillation_loop + successor_conflict`.
- Shadow triggers: `repeated_conversion_failure`, `stagnation_loop`, `route_conflict`.

Interpretation:

- The loop is now visible and causally addressable in ReCoN terms, but the first loop-breaker license is not enough to convert the remaining state within 21 plies.
- This is no longer a generic max-plies failure. It is a visible stagnation-control problem: the system can notice the loop, find safe loop-breaking rook transfers, and choose different licensed moves, but it still lacks a reliable post-break continuation.

Next likely target:

- Compare licensed loop-breaking moves by downstream outcome over a longer horizon.
- Add a non-causal `loop_breaking_moves_that_convert` audit for the detected loop state, not only for the original post-reply state.
- Only after that, consider a stricter visible post-break continuation role or train a small `post_stagnation_break_continuation` skill from the loop-break examples.

## Slice 36: Post-Break Continuation Audit

Implemented a non-causal targeted audit for the first state where `krk.stagnation_breaker_affordance` fires.

Target state:

```text
5k2/8/K7/8/7R/8/8/8 w - - 18 10
```

Bounded post-break sweep:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice36_state3d73_post_break_sweep_bounded.json
trace:    snapshots/krk_triplet_pipeline/handoff_observability_check/slice36_state3d73_post_break_trace_bounded.jsonl
horizons: 21, 30, 40
audited visible loop-breaking candidates: 6
```

Results:

```text
21 plies: 0 mate / 6 max_plies
30 plies: 0 mate / 6 max_plies
40 plies: 2 mate / 4 max_plies
converting moves at 40 plies: a6a7, a6b7
runtime-selected break h4d4: max_plies through 40, re-enters/no-progress oscillation
```

Unchanged Stage 5 regressions:

```text
slice36_stage5_25_unchanged_regression.json:
  local:      25/25 improved, 25/25 optimal
  conversion: 19 mate / 6 max_plies at 20 plies

slice36_stage5_100_unchanged_regression.json:
  local:      100/100 improved, 100/100 optimal
  conversion: 65 mate / 35 max_plies at 20 plies
```

Interpretation:

```text
The remaining state is not fixed by increasing the loop-breaker bonus.
The loop-breaker can identify and license safe loop-breaking moves, but the selected break is not reliably followed by conversion.
Some loop-breaking moves convert only at longer horizon, so this is partly a post-break continuation/horizon problem rather than missing local Stage 5 capacity.
```

Recommended next causal shape:

```text
detect loop
-> break loop
-> confirm loop was broken and confinement/safety were preserved
-> request a visible post-stagnation-break continuation role
```

Do not train yet from this single family. If a full post-break sweep shows that no existing provider can reliably convert after a good break, then a narrow `krk.post_stagnation_break_continuation` skill becomes justified.

## Slice 37: Visible Post-Break Continuation Role

Implemented default-off scaffolding for a visible post-break continuation role:

```text
krk.post_stagnation_break_continuation
```

New dynamic terms:

```text
rook_oscillation_loop_recently_broken
confinement_preserved_after_break
enemy_king_edge_control_preserved
post_stagnation_break_continuation_needed
safe_followup_available
```

The role is opt-in only:

```text
--enable-post-break-continuation
--post-break-continuation-bonus <small value>
```

Hard constraints preserved:

- Defaults are unchanged.
- No broad provider penalty was added.
- No training was added.
- The role only adds support when the recent loop-break context is visible and the candidate move has visible safety/progress terms.

Targeted `state.3d73` h4d4 audit:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice37_state3d73_post_break_continuation_h4d4.json
first break: h4d4
horizon: 40
result: max_plies
classification: changes_loop_family
```

Interpretation:

```text
The post-break continuation role fires and is traceable, but it is still too broad.
It licenses safe/progress-looking rook moves after the break, yet the playout remains in an oscillation family.
This supports the earlier conclusion: do not increase bonuses. Refine the post-break role toward moves that preserve the break and avoid immediate return to the rook oscillation family.
```

## Slice 38: Narrow Post-Break Continuation To King Follow-Up

Refined the opt-in post-break continuation role so it no longer licenses ordinary lateral rook transfers after a loop break. The loop breaker remains responsible for escaping the repeated rook-control state; the post-break continuation role now licenses visible king follow-up moves that preserve confinement and KRK safety.

Narrowed rule:

```text
rook_oscillation_loop_recently_broken
AND confinement_preserved_after_break
AND post_stagnation_break_continuation_needed
AND safe_followup_available
AND candidate_is_king_move
AND rook_safe_after_move
AND box_area_not_increased_after_move
AND visible progress/preservation term
```

Targeted `state.3d73`, first break `h4d4`:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice38_state3d73_post_break_king_followup_h4d4.json
horizon: 40
result: mate
first post-break king follow-up license: a6a7
later licensed king moves: a7b8, b8c8, c8c7, c7d6
```

Matched 25-sample comparison at 40 plies:

```text
no post-break continuation:
  artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice38_stage5_25_no_post_break_h40.json
  conversion: 19 mate / 6 max_plies

narrow king-followup post-break continuation:
  artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice38_stage5_25_post_break_king_followup_h40.json
  conversion: 20 mate / 5 max_plies
```

Interpretation:

```text
The narrowed role fixes the targeted h4d4 continuation at the longer horizon and gives a small positive 25-sample effect.
It should remain opt-in/experimental until tested on larger samples and against regressions.
The next useful diagnostic is to inspect the remaining 5 max_plies cases under the narrowed role and decide whether they are horizon-limited, loop-family changes, or genuine post-break capacity gaps.
```

## Slice 39: State394 Stage0 Drift Audit

Remaining failures after Slice 38 were a single clean bucket:

```text
state: state.394b71e02d00
post-reply FEN: 1k6/7R/2K5/8/8/8/8/8 w - - 2 2
selected successor: krk.stage0_basin
failure class: selected_successor_miscalibrated
```

Targeted audit:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice39_state394_audit.json
```

Findings:

```text
forced krk.stage0_basin: max_plies
forced krk.edge_trap_close: mate
forced krk.fence_established: mate
forced krk.edge_trap_wrong_tempo: mate
forced krk.edge_trap_enemy_between: mate
```

Legal-first audit:

```text
many converting legal first moves exist
runtime selected c6b6, which did not convert
provider audit: converting_move_not_proposed
```

The existing opt-in `successor_stage0_drift_penalty` targets exactly this condition: a high-scoring `stage0_basin` king drift while edge-trap recovery is visibly licensed and the king move does not improve visible support/progress.

Targeted run with `--successor-stage0-drift-penalty 6.0`:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice39_state394_stage0_drift_penalty_audit.json
selected first move: h7d7
result: mate
provider audit: selected_converting_move
```

Matched 25-sample Stage 5 at 40 plies:

```text
narrow post-break only:
  artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice38_stage5_25_post_break_king_followup_h40.json
  conversion: 20 mate / 5 max_plies

narrow post-break + existing stage0 drift penalty:
  artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice39_stage5_25_post_break_plus_stage0_drift_h40.json
  conversion: 25 mate / 0 max_plies
  shadow candidates: 0
```

Interpretation:

```text
This is not missing KRK capacity. The graph had converting providers and moves.
The remaining error was miscalibrated stage0 ownership in an edge-trap recovery geometry.
The existing narrow drift penalty is sufficient for the 25-sample bounded set when combined with the narrowed post-break continuation role.
```

Keep this experimental until larger validation passes.

100-sample validation:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice39_stage5_100_post_break_plus_stage0_drift_h40.json
local:      100/100 improved, 100/100 optimal
conversion: 100 mate / 0 max_plies at 40 plies
shadow candidates: 0
semantic alignment: 100 reward_visible_fence_aligned_survived
```

This is the first clean 100-sample Stage 5 conversion pass for the visible successor/stagnation/post-break configuration. It remains opt-in and should be validated against larger randomized Stage 5 and cross-stage regressions before becoming a default runtime path.

## Slice 40: Bounded Cross-Seed Validation

Attempted a naive 500-sample Stage 5 validation with the Slice 39 opt-in configuration:

```text
artifact target: snapshots/krk_triplet_pipeline/handoff_observability_check/slice40_stage5_500_post_break_plus_stage0_drift_h40.json
status: stopped manually at 10/500
reason: too slow for interactive validation; projected runtime was hours
```

The runtime bottleneck is CPU-side adversarial ReCoN playout, not neural training/GPU work. Each sample may require many White decisions, and each decision evaluates visible roles, move-shapes, stagnation/post-break terms, and actuator suggestions.

Instead, ran a bounded different-seed validation:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice40_stage5_30_seed11_post_break_plus_stage0_drift_h40.json
analysis: snapshots/krk_triplet_pipeline/handoff_observability_check/slice40_stage5_30_seed11_post_break_plus_stage0_drift_h40_analysis.md
seed: 11
samples: 30
horizon: 40 plies
local: 30/30 improved, 30/30 optimal
conversion: 30 mate / 0 max_plies
shadow candidates: 0
semantic alignment: 30 reward_visible_fence_aligned_survived
```

Regression suite:

```text
tests: architecture preservation, plasticity, consolidation, routing contracts, shadow queue, KRK successor affordance, diagnostic early stop, counterfactual sweep
result: 94 passed
```

Interpretation:

```text
The Slice 39 configuration is not just memorizing the seed-7 100-sample run; it also passes a different bounded curriculum sample.
The mechanisms remain opt-in. The next engineering bottleneck is diagnostic throughput, so larger randomized validation should be preceded by more performance work or run as an overnight job.
```

## Slice 41: Performance Profiling Baseline

Added diagnostic-only profiling via:

```text
--profile-performance
```

The profiler records timing/count buckets without changing scoring, routing, packets, shadow candidates, or topology. It is attached to the diagnostic blackboard only when enabled.

30-sample seed-11 profile:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice41_profile_stage5_30_seed11_h40.json
samples: 30
conversion: 30 mate / 0 max_plies
total wall time: 645.44s
choose_move_details: 638.58s (98.94%)
engine.step: 638.51s (98.93%)
actuator scoring: 635.44s (98.45%)
goal_distance: 472.61s (73.22%)
teacher.features: 137.39s (21.29%)
worst_reply_reward: 91.83s (14.23%)
move_shape_audit: 0.76s (0.12%)
stagnation_summary: 1.22s (0.19%)
```

30-sample counts:

```text
playout decisions: 291
engine ticks: 2568
actuator evaluations: 8934
legal moves scored: 175054
board.copy calls instrumented: 690245
teacher.features calls: 752541
worst_reply_reward calls: 80654
oracle_best_reward calls: 667
context cache: 41746 hits / 5183 misses
move-shape audit cache: 174702 hits / 4862 misses
```

100-sample seed-7 profile:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice41_profile_stage5_100_seed7_h40.json
samples: 100
conversion: 100 mate / 0 max_plies
total wall time: 2142.45s
choose_move_details: 2121.62s (99.03%)
engine.step: 2121.40s (99.02%)
actuator scoring: 2111.60s (98.56%)
goal_distance: 1576.65s (73.59%)
teacher.features: 464.34s (21.67%)
worst_reply_reward: 314.62s (14.69%)
move_shape_audit: 2.30s (0.11%)
stagnation_summary: 3.51s (0.16%)
```

100-sample counts:

```text
playout decisions: 933
engine ticks: 8264
actuator evaluations: 28522
legal moves scored: 569892
board.copy calls instrumented: 2287601
teacher.features calls: 2491687
worst_reply_reward calls: 264447
oracle_best_reward calls: 2197
context cache: 135354 hits / 15715 misses
move-shape audit cache: 461786 hits / 14682 misses
```

Interpretation:

```text
The throughput problem is not JSON serialization, stagnation diagnostics, move-shape audit, or Black reply selection.
The bottleneck is actuator scoring, dominated by repeated goal-distance computation and repeated teacher feature extraction inside legal-move/reply loops.
The next safe optimization slice should target immutable feature/goal-distance/reward caches and goal-bank precomputation before parallel validation.
```

## Slice 42: Opt-In Diagnostic Caches

Added behavior-preserving memoization behind:

```text
--enable-diagnostic-caches
```

The caches are scaffolding, not ReCoN evidence:

```text
feature cache: teacher.features(board)
goal-distance cache: board/goal/sensor-contract distance
worst-reply reward cache: board/move/label/lookahead
oracle-best reward cache: board/label/lookahead
black-reply cache: deterministic adversarial reply
```

They are keyed by board state and deterministic config. They do not create activations, packets, role licenses, shadow candidates, learning updates, or topology changes.

Small smoke comparison:

```text
uncached smoke artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice41_profile_smoke.json
cached smoke artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice42_cache_smoke.json
behavior: identical 1 mate / 1 max_plies
wall time: 5.63s -> 2.07s
teacher.features calls: 4545 -> 242
goal-distance time: 2.58s -> 0.25s
```

30-sample seed-11 comparison:

```text
uncached artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice41_profile_stage5_30_seed11_h40.json
cached artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice42_cache_profile_stage5_30_seed11_h40.json
behavior: 30 mate / 0 max_plies in both
wall time: 645.44s -> 124.79s
speedup: ~5.2x
goal-distance time: 472.61s -> 38.16s
teacher.features time: 137.39s -> 4.38s
teacher.features calls: 752541 -> 24325
worst_reply_reward time: 91.83s -> 28.40s
worst_reply_reward calls: 80654 -> 23875
```

100-sample seed-7 comparison:

```text
uncached artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice41_profile_stage5_100_seed7_h40.json
cached artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice42_cache_profile_stage5_100_seed7_h40.json
behavior: 100 mate / 0 max_plies in both
wall time: 2142.45s -> 404.04s
speedup: ~5.3x
goal-distance time: 1576.65s -> 130.13s
teacher.features time: 464.34s -> 15.41s
teacher.features calls: 2491687 -> 82936
worst_reply_reward time: 314.62s -> 95.58s
worst_reply_reward calls: 264447 -> 72183
```

Cached 100-sample cache counts:

```text
teacher_features: 657384 hits / 82936 misses
goal_distance: 1751367 hits / 169395 misses
worst_reply_reward: 150765 hits / 72183 misses
black_reply: 784 hits / 49 misses
oracle_best_reward: 7 hits / 125 misses
context_terms: 135354 hits / 15715 misses
move_shape_audit: 461786 hits / 14682 misses
```

Interpretation:

```text
The cache slice preserves the 100-sample Stage 5 result and removes the largest known throughput bottleneck.
The remaining dominant cost is still actuator scoring, now mostly non-cached goal-distance misses and reward evaluation.
Next optimization should be parallel validation and/or deeper goal-bank vector precomputation, not more role/stagnation logic.
```

## Slice 43: Parallel Validation

Added multiprocessing validation via:

```text
--parallel-workers N
--chunk-size M
```

Parallel mode is for validation throughput, not behavior change. It splits sample indices into chunks, each worker loads/builds its own graph and engine, and each sample uses a deterministic seed:

```text
sample_seed = base_seed * 1_000_000 + sample_index
```

This avoids shared mutable engine state and avoids thread/GIL contention. Worker summaries are merged into the same result schema. Shared JSONL streaming outputs are disabled inside workers; use normal single-process mode for detailed targeted trace streaming.

Smoke:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice43_parallel_smoke.json
samples: 4
workers: 2
chunk_size: 2
result: 4/4 local optimal, 4 max_plies at 8-ply smoke horizon
```

30-sample Stage 5:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice43_parallel_stage5_30_seed11_h40.json
samples: 30
workers used: 3
chunk_size: 10
wall time: 70.86s
local: 30/30 improved, 30/30 optimal
conversion: 30 mate / 0 max_plies
shadow candidates: 0
```

100-sample Stage 5:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice43_parallel_stage5_100_seed7_h40.json
samples: 100
workers used: 4
chunk_size: 25
wall time: 135.03s
local: 100/100 improved, 100/100 optimal
conversion: 100 mate / 0 max_plies
shadow candidates: 0
```

Interpretation:

```text
Parallel validation plus diagnostic caches makes larger Stage 5 sweeps practical.
The 100-sample parallel validation finishes in ~2.25 minutes instead of ~35.7 minutes uncached/profiled or ~6.7 minutes cached/profiled single-process.
The next practical validation is 500 or 1000 samples with --enable-diagnostic-caches and --parallel-workers sized to available CPU cores.
```

## Slice 44: 500-Sample Parallel Stage 5 Validation

Ran the first large cached parallel Stage 5 validation:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice44_parallel_stage5_500_seed7_h40.json
samples: 500
seed: 7
workers: 8
chunk_size: 25
horizon: 40 plies
black policy: adversarial
wall time: 397.14s
```

Result:

```text
local: 500/500 improved, 500/500 optimal
conversion: 500 mate / 0 max_plies
shadow candidates: 0
semantic alignment: 500 reward_visible_fence_aligned_survived
```

Interpretation:

```text
The visible successor/role-scoped move-shape/stagnation/post-break/stage0-drift configuration survives a materially larger Stage 5 curriculum validation.
This is still opt-in and should not be treated as a default runtime path until cross-stage and non-Stage-5 regressions are run.
The next useful validation is either 1000 samples or cross-stage checks against Stage 1, Stage 2C, KPK->KQK bridge behavior, and old M1-M4 learning tests.
```

## Slice 45: Cross-Stage Non-Regression Validation

After the 500-sample Stage 5 validation, ran cross-stage and bridge regressions before considering the opt-in path stable.

Bridge/subgraph/KRK tests:

```text
tests:
  test_subgraph_delegation.py
  test_goal_hierarchy.py
  test_endgame_components.py
  test_tactics_subgraph.py
  test_handoff_analysis.py
  test_krk_landmarks.py
  test_krk_baseline_runtime.py
result: 58 passed
note: pytest still reports pre-existing warnings for test_subgraph_delegation functions returning bool
```

Stage 1 backchain:

```text
topology: snapshots/krk_triplet_pipeline/handoff_observability_check/slice14_role_ontology_topology.json
learner: snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/final_learner.pkl
samples: 100
result: 100/100 improved, 100/100 optimal, 0 worsened, 0 no-move
avg reward: 0.4606
```

Stage 4 wrong-tempo:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice45_stage4_wrong_tempo_100_seed7_h40.json
label: edge_trap_wrong_tempo
samples: 100
seed: 7
horizon: 40 plies
local: 100/100 improved, 100/100 optimal
conversion: 100 mate / 0 max_plies
shadow candidates: 0
wall time: 80.37s
```

Stage 5 different seed:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice45_stage5_fence_100_seed11_h40.json
label: fence_established
samples: 100
seed: 11
horizon: 40 plies
local: 100/100 improved, 100/100 optimal
conversion: 100 mate / 0 max_plies
shadow candidates: 0
wall time: 145.27s
```

M1-M4 preservation suite remains green:

```text
tests: architecture preservation, consolidation, plasticity, plasticity integration, routing contracts, shadow queue, KRK successor affordance, diagnostic early stop, counterfactual sweep
result: 96 passed
```

Interpretation:

```text
The opt-in successor/role/move-shape/stagnation/post-break/stage0-drift path now passes Stage 5 at 500 samples, Stage 4 wrong-tempo at 100 samples, Stage 1 backchain at 100 samples, KPK->KQK bridge/subgraph tests, and M1-M4 learning preservation tests.
It is reasonable to treat this as the current stable experimental handoff-composition configuration, while still keeping it opt-in until default-policy implications are reviewed.
```

## Slice 46: Named Experimental Profile Freeze

The Stage 5 handoff-composition path is now packaged as a named profile rather than a repeated flag pile:

```text
profile_id: handoff_composition_v1
domain: KRK
experimental_profile: true
default_policy: false
```

Behavioral settings captured by the profile:

```text
successor_affordance_layer_enabled: true
successor_role_license_enabled: true
successor_role_scoped_move_shape_enabled: true
successor_role_scoped_move_shape_bonus: 0.05
stagnation_breaker_enabled: true
stagnation_breaker_bonus: 0.5
post_break_continuation_enabled: true
post_break_continuation_bonus: 0.25
successor_stage0_drift_penalty: 6.0
```

Recommended validation scaffolding captured as profile metadata:

```text
enable_diagnostic_caches: true
parallel_workers: 8
chunk_size: 25
```

Interpretation:

```text
handoff_composition_v1 is the stable experimental KRK handoff-composition profile.
It remains opt-in, domain-scoped, and non-default.
Handoff packets, shadow candidates, and skill-contract stats remain trace/evidence records and do not become M4 causal inputs by virtue of selecting the profile.
```

Added a non-causal EpisodeSummary export helper for future consolidation analysis:

```text
event_type: handoff_composition_event
schema_version: handoff_composition_event.v1
credit: 0.0
payload: from_skill, to_skill, role, move_shape, status, handoff packet / route / shadow metadata
```

Validation:

```text
focused M1-M4 + handoff diagnostics suite: 101 passed
profile smoke artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice46_profile_smoke.json
```

## Slice 47: Profile Robustness Validation And Curriculum Passthrough

Large validation with `handoff_composition_v1`:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice47_profile_stage5_1000_seed7_h40.json
label: fence_established
samples: 1000
seed: 7
horizon: 40 plies
local: 1000/1000 improved, 1000/1000 optimal
conversion: 1000 mate / 0 max_plies
shadow candidates: 0
parallel: 8 workers, chunk size 25
wall time: 781.77s
```

Cross-stage validation:

```text
artifact: snapshots/krk_triplet_pipeline/handoff_observability_check/slice47_profile_stage4_wrong_tempo_500_seed7_h40.json
label: edge_trap_wrong_tempo
samples: 500
seed: 7
horizon: 40 plies
local: 500/500 improved, 500/500 optimal
conversion: 500 mate / 0 max_plies
shadow candidates: 0
parallel: 8 workers, chunk size 25
wall time: 235.24s
```

Stage 1 regression:

```text
samples: 500
seed: 7
position mode: mate_in_2
result: 500/500 improved, 500/500 optimal, 0 worsened, 0 no-move
avg reward: 0.5035
```

The triplet pipeline and adaptive baseline trainer now accept profile-aware adaptive validation:

```text
--adaptive-composition-profile handoff_composition_v1
--adaptive-use-profile-validation-defaults
```

Pipeline dry-run verified that those flags are passed through to `train_baseline_krk_chain.py` and recorded in the run manifest.

KPK/KQK bridge-adjacent regression:

```text
tests: test_subgraph_delegation.py, test_endgame_components.py, test_routing_contracts.py
result: 10 passed
note: existing pytest return-value warnings remain in test_subgraph_delegation.py
```

Interpretation:

```text
The profile is now validated beyond the original Stage 5 tuning set and can be used as the conversion/handoff evaluation harness for subsequent KRK curriculum stages.
This remains an opt-in experimental profile; default training/eval behavior is unchanged unless the profile is selected.
```

## Slice 48: Strict Stage 6 Curriculum Gate

The next curriculum trial used `handoff_composition_v1` as the conversion harness for Stage 6:

```text
label: drive_to_edge
source stages: Opposition_Approach, Tempo_Wait, King_Close_1
load learner: adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl
output: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict
adaptive eval samples: 200
adaptive playout horizon: 40
```

A curriculum bug was found and fixed before accepting this stage:

```text
StageEvalResult.passed now requires one_ply_passed AND conversion_passed.
Late KRK stages now have conversion criteria, not local-only criteria:
  fence_established
  drive_to_edge
  box_shrink
  opposition_tempo
  full_krk
```

This prevented false advancement. With strict criteria, Stage 6 did not pass:

```text
cycle 9:  149 mate / 51 max_plies, max_plies_rate=0.255 > 0.250
cycle 14: 149 mate / 51 max_plies, plateau patience 1
cycle 19: 149 mate / 51 max_plies, plateau patience 2
cycle 24: 149 mate / 51 max_plies, plateau patience 3
result: plateau stop, no strict Stage 6 pass
```

The compiled final learner still preserved core regressions:

```text
KRK entry: 100/100 mate
Stage 1 backchain: 100/100 improved, 100/100 optimal
```

Interpretation:

```text
The profile harness is doing its job: it blocks a locally-good but conversion-incomplete stage.
Do not advance to Stage 7 from this checkpoint as if Stage 6 were solved.
```

## Slice 49: Stage 6 Failure Classification

A 200-sample Stage 6 diagnostic on the strict topology produced:

```text
artifact: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict/stage6_drive_strict_debug_200_seed7_h40.json
analysis: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict/stage6_drive_strict_debug_200_seed7_h40_analysis.md
local: 200/200 improved
optimal: 149/200
conversion: 149 mate / 51 max_plies
shadow candidates: 153
```

The failure set was compact:

```text
rook_oscillation_loop: 51
successor_conflict: 51
selected successor by outcome:
  krk.stage0_basin: 149 mate
  krk.edge_trap_close: 51 max_plies
```

Representative repeated start:

```text
4k3/R7/8/K7/8/8/8/8 w - - 0 1
```

Observed early sequence:

```text
a7h7
... e8f8
h7c7
```

There were no handoff gaps and semantic alignment was still fine. A forced-successor sweep over the unique failure family did not find a tested successor that mated by horizon 40:

```text
artifact: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict/stage6_counterfactual_summary.json
unique states: 1
forced successors tested:
  krk.stage0_basin
  krk.edge_trap_close
  krk.fence_established
  krk.fence_maintenance
  krk.edge_trap_wrong_tempo
  krk.edge_trap_enemy_between
  krk.drive_to_edge
result: no forced successor mated by horizon 40
```

Interpretation:

```text
This is not a simple wrong-successor handoff.
It is a post-drive edge-rim continuation / rook-oscillation / horizon family.
The existing stagnation breaker can fire, but the selected break is not the fastest conversion path.
```

## Slice 50: Stage 6 Post-Break Continuation Audit

The post-break audit script now reads full diagnostic `debug_playouts`, detects stagnation-breaker licenses embedded in selected suggestion metadata, and summarizes horizon-specific converters.

Targeted audit:

```text
artifact: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict/stage6_post_break_audit.json
steps: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict/stage6_post_break_audit_steps.jsonl
first stagnation-breaker state:
  5k2/8/8/K7/7R/8/8/8 w - - 18 10
licensed loop-breaking candidates: 18
```

Outcome by horizon:

```text
horizon 21: 3 mate / 15 max_plies
horizon 40: 7 mate / 11 max_plies
horizon 60: 17 mate / 1 max_plies
```

Key finding:

```text
The runtime-selected break move h4f4 is not hopeless; it mates by horizon 60.
Several alternatives convert faster:
  a5b4
  a5b5
  a5b6
```

Interpretation:

```text
The remaining Stage 6 issue is mostly post-break continuation quality and horizon sensitivity, not missing local Stage 6 capacity.
Good loop-breaking moves exist, but the current visible loop-breaker does not yet rank quick king-support continuation shapes over slower rook-transfer continuations.
The next safe work should be non-causal post-break move-shape classification and then a narrow visible post-drive/post-break continuation role if the terms separate fast converters cleanly.
Do not add broad score bonuses or train a generic convert-from-fence skill yet.
```

## Slice 51: Replay-Free Post-Break Term Augmentation

The post-break audit can now enrich an existing full audit artifact without replaying playouts:

```text
flag: --augment-existing-audit
input: stage6_post_break_audit.json
output: stage6_post_break_audit_augmented.json
```

This adds:

```text
candidate_terms
loop_breaking_moves_that_convert_by_horizon
fastest_mating_horizon_by_move
fastest_converting_moves
selected_break_move_outcomes
common_converter_terms_by_horizon
distinctive_converter_terms_by_horizon
term_outcomes_by_horizon
```

Augmented Stage 6 post-break result:

```text
artifact: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict/stage6_post_break_audit_augmented.json
first stagnation-breaker state:
  5k2/8/8/K7/7R/8/8/8 w - - 18 10
candidate count: 18
```

Converters by horizon:

```text
21 plies:
  a5b4
  a5b5
  a5b6

40 plies:
  a5a6
  a5b4
  a5b5
  a5b6
  h4h3
  h4h5
  h4h7

60 plies:
  17/18 candidates convert
```

The runtime-selected loop break remains horizon-sensitive:

```text
selected break: h4f4
21 plies: max_plies
40 plies: max_plies
60 plies: mate
```

Fast-converter visible terms:

```text
21-ply converters all include:
  candidate_is_king_move
  post_break_king_move
  post_break_king_moves_toward_enemy
  post_break_king_moves_toward_rook_support
  box_area_not_increased_after_move
  enemy_edge_distance_not_increased_after_move
  rook_safe_after_move
  no_draw_after_move
```

Distinctive terms for fast converters:

```text
post_break_king_moves_toward_enemy
post_break_king_moves_toward_rook_support
```

Interpretation:

```text
Stage 6 now has a clean non-causal target for the next possible visible role:
  post-drive/post-break king-support continuation.

The candidate role should not be a broad loop-break bonus.
It should be narrow:
  loop was detected / recently broken
  candidate is a king move
  king moves toward enemy king
  king moves toward rook support
  box/confinement is not released
  rook remains safe

This is the first plausible causal follow-up, but it should still be implemented as an opt-in visible role/move-shape license and validated against the 200-sample Stage 6 diagnostic before retraining.
```

## Slice 52: Opt-In King-Support Loop Breaker And Stage 6 Pass

A narrow opt-in causal experiment was added:

```text
flag: --stagnation-breaker-king-support-bonus
adaptive passthrough: --adaptive-stagnation-breaker-king-support-bonus
default: 0.0
```

This does not change `handoff_composition_v1` by default. It only adds extra visible support when:

```text
rook_oscillation_loop
no_box_progress_recently
safe_loop_breaking_move_available
candidate_is_king_move
king_moves_toward_enemy
king_moves_toward_rook_support
rook_safe_after_move
box_area_not_increased_after_move
enemy_edge_distance_not_increased_after_move
no_draw_after_move
```

Stage 6 diagnostic with the opt-in bonus:

```text
artifact: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_strict/stage6_drive_king_support_breaker_200_seed7_h40.json
label: drive_to_edge
samples: 200
horizon: 40
bonus: 2.0
local improved: 200/200
local optimal: 149/200
conversion: 200 mate / 0 max_plies
shadow candidates: 0
```

Strict adaptive Stage 6 run:

```text
output: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support
cycle: 9
adaptive result: passed
one_ply_status: passed under adaptive criteria
conversion_status: passed
playouts: 200 mate / 0 max_plies
KRK entry regression: 100/100 mate
Stage 1 backchain regression: 100/100 improved, 100/100 optimal
```

Stage 6 robustness validation:

```text
artifact: snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/stage6_drive_king_support_500_seed7_h40.json
samples: 500
horizon: 40
local improved: 500/500
local optimal: 374/500
conversion: 500 mate / 0 max_plies
shadow candidates: 0
```

Interpretation:

```text
The narrow king-support loop-break license fixes the compact Stage 6 conversion family without making the profile default more aggressive.
For Stage 6 itself, this is a successful opt-in architecture slice.
```

## Slice 53: Earlier-Stage Guardrail Regression On Stage 6 Topology

Cross-stage guardrails on the Stage 6 topology exposed a separate architecture issue.

With the opt-in king-support bonus enabled:

```text
Stage 4 wrong-tempo guard, 300 samples:
  artifact: stage4_wrong_tempo_king_support_guard_300_seed7_h40.json
  local: 300/300 optimal
  conversion: 242 mate / 58 max_plies
  shadow candidates: 116

Stage 5 fence guard, 300 samples:
  artifact: stage5_fence_king_support_guard_300_seed7_h40.json
  local: 300/300 optimal
  conversion: 259 mate / 41 max_plies
  shadow candidates: 82
```

The same guardrails without the new king-support bonus produced essentially the same failures:

```text
Stage 4 wrong-tempo guard without bonus:
  artifact: stage4_wrong_tempo_no_king_support_guard_300_seed7_h40.json
  conversion: 242 mate / 58 max_plies

Stage 5 fence guard without bonus:
  artifact: stage5_fence_no_king_support_guard_300_seed7_h40.json
  conversion: 256 mate / 44 max_plies
```

Therefore:

```text
The regression is not caused by the new king-support loop-breaker.
It is caused by adding/training Stage 6 into the learner/topology, which changes downstream conversion behavior for earlier-stage guardrails.
```

Analysis summaries:

```text
Stage 4:
  analysis: stage4_wrong_tempo_no_king_support_guard_300_seed7_h40_analysis.md
  failure motif: selected_successor_miscalibrated
  selected successor by outcome:
    krk.stage0_basin: 114 mate / 45 max_plies
    krk.edge_trap_close: 41 mate

Stage 5:
  analysis: stage5_fence_no_king_support_guard_300_seed7_h40_analysis.md
  failure motifs:
    horizon_mate_in_one
    successor_conflict
  selected successor by outcome:
    krk.edge_trap_close: 105 mate / 28 max_plies
    krk.stage0_basin: 67 mate
```

Interpretation:

```text
Do not promote the Stage 6 topology as a globally safe successor to Stage 5 yet.
The next architecture decision is not another Stage 6 move-shape tweak.
It is how Hector should preserve previously validated subskills while adding later curriculum stages.

Likely options:
  freeze/layer older actuator providers during later-stage training
  add versioned skill contracts/checkpoints per stage
  add a visible stage/domain ownership lock during lower-stage guardrail conversion
  train Stage 6 as an overlay rather than mutating earlier skill providers

This should be reviewed before implementing a broad preservation mechanism.
```

## Slice 54-56: Frozen Providers, Stage 6 Overlay, And Promotion Gate

The preservation mechanism was implemented as a versioned frozen-provider plus overlay-stage compiler path.

New provider metadata is attached to compiled skill nodes, actuator legs, and actuator terminals:

```text
skill_id
curriculum_label
provider_version
source_stage
source_checkpoint
validated_profile
frozen_provider
overlay_provider
guardrail_status
```

The Stage 5 validated topology is now treated as a frozen base, and the Stage 6 learner is compiled as an additive overlay:

```text
base:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json

overlay learner:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl

overlay label:
  drive_to_edge

output:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json
```

The overlay compiler:

```text
keeps frozen Stage 5 provider nodes unchanged
extracts only drive_to_edge actuators from the Stage 6 learner
adds them under skill.krk.drive_to_edge with provider_version = stage6_overlay_v1
records provider_preservation.v1 metadata
marks promotion_status = overlay_candidate until guardrails pass
```

Compiled overlay topology summary:

```text
nodes: 286
edges: 866
frozen_base_provider_count: 102
overlay_provider_count: 10
overlay_actuators_added:
  actuator_34
  actuator_35
  actuator_36
```

Validation results:

```text
Stage 6 drive_to_edge on composed overlay:
  artifact: stage6_drive_overlay_300_seed7_h40.json
  conversion: 300 mate / 0 max_plies
  shadow candidates: 0

Stage 5 fence on composed overlay:
  artifact: stage5_fence_overlay_300_seed7_h40.json
  conversion: 300 mate / 0 max_plies
  shadow candidates: 0

Stage 5 fence on frozen Stage 5 base control:
  artifact: stage5_fence_stage5_base_control_300_seed7_h40.json
  conversion: 300 mate / 0 max_plies
```

This confirms the main preservation hypothesis:

```text
The monolithic Stage 6 topology damaged Stage 5 conversion.
The frozen-provider overlay composition preserves Stage 5 while adding Stage 6 capacity.
```

Stage 4 wrong-tempo was also checked:

```text
Stage 4 wrong-tempo on composed overlay:
  artifact: stage4_wrong_tempo_overlay_300_seed7_h40.json
  conversion: 247 mate / 53 max_plies

Stage 4 wrong-tempo on frozen Stage 5 base control:
  artifact: stage4_wrong_tempo_stage5_base_control_300_seed7_h40.json
  conversion: 247 mate / 53 max_plies
```

Therefore the Stage 4 40-ply conversion failure is not overlay interference. It is already present in the frozen Stage 5 base under this guardrail configuration and should be tracked as a separate horizon/guardrail-definition issue.

A guardrail-aware promotion evaluator was added:

```text
script:
  scripts/evaluate_provider_promotion.py

promotion artifact:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json

result:
  promotion_status = promoted
```

The promotion evaluation used Stage 6 as the candidate artifact and Stage 5 fence as the protected prior-stage guardrail. Stage 4 was intentionally excluded from this promotion decision because the base-control topology fails the same Stage 4 40-ply conversion check, so it is not evidence of overlay regression.

Interpretation:

```text
Stage 6 drive_to_edge is safe as an overlay against the current protected Stage 5 guardrail.
It should not be treated as a monolithic replacement topology.
The next curriculum stages should use frozen validated provider packs plus additive overlays.
Stage 4 wrong-tempo conversion at 40 plies remains a separate diagnostic target.
```

## Slice 57: Preservation Evidence Export And Cross-Domain Bridge Check

Provider promotion is now exportable as non-causal episode metadata:

```text
event_type: provider_promotion_event
schema_version: provider_promotion_event.v1
credit: 0.0
payload:
  skill_id
  provider_version
  promotion_status
  source_checkpoint
  base_provider_version
  overlay_provider_version
  validated_profile
  stage artifact
  guardrail artifacts
  provider_promotion_eval.v1 payload
```

This mirrors the handoff-composition event path. It lets future M5 tooling preserve promotion evidence in `EpisodeSummary.learning_events` without making the event causal and without changing M4 consolidation inputs.

A persistent manifest was added:

```text
reports/stage6_overlay_validation_manifest.md
```

It records the frozen base, Stage 6 overlay learner/checkpoint, composed topology, validation artifacts, promotion artifact, and reproduction commands for the current `stage6_overlay_v1` checkpoint.

The existing KPK to KQK bridge suite was re-run under the current routing-contract instrumentation:

```text
command:
  uv run python tests/test_subgraph_delegation.py

result:
  all tests passed

checks covered:
  KPK direct promotion
  KQK direct move selection
  pre-promotion KQK execution veto
  KPK promotion handoff packet
  post-promotion KQK route eligibility
  KQK continuation move
  SubgraphLock
```

Interpretation:

```text
The frozen-provider overlay work did not break the older bridge machinery.
KQK approach affordance may be visible before promotion, but KQK execution remains vetoed until material eligibility confirms.
The promotion handoff packet remains trace-only and does not cause the KQK route.
```

## Slice 58: Stage 7 Box-Shrink Overlay Smoke

The next curriculum stage was attempted as an overlay candidate source rather than a replacement topology.

Training setup:

```text
label: box_shrink
source stages: Box_Small, Box_Medium, Edge_Fence_Deep
load learner: adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl
profile: handoff_composition_v1
adaptive eval: 50 samples
adaptive playout horizon: 20 plies
output: snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_profile_overlay_smoke
```

Two evaluator robustness fixes were needed before the smoke could run:

```text
sample index bug:
  semantic mismatch snapshots used sample=i even though the loop variable is sample_index

successor summary schema bug:
  empty post-reply summaries did not include visible_eligible_successors
```

Adaptive checkpoint evaluation was also changed to use the existing parallel landmark evaluator when `--adaptive-use-profile-validation-defaults` is selected:

```text
parallel_workers: 8
chunk_size: 25
diagnostic caches: enabled
```

This is behavior-preserving for default training and only affects profile-selected adaptive validation.

Smoke result:

```text
local one-ply objective:
  50/50 improved
  50/50 optimal during adaptive validation

conversion:
  19 mate / 31 max_plies

status:
  plateaued at cycle 24
  saved learner: adaptive_krk_stage7_box_profile_overlay_smoke/baseline/final_learner.pkl
```

The learned Stage 7 provider was then compiled as an additive overlay on top of the Stage 6 overlay topology:

```text
base:
  adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json

overlay learner:
  adaptive_krk_stage7_box_profile_overlay_smoke/baseline/final_learner.pkl

overlay label:
  box_shrink

output:
  adaptive_krk_stage7_box_overlay_composed_smoke/topology/krk_entry_topology.json

overlay actuators:
  11
```

Overlay validation:

```text
artifact:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_overlay_composed_smoke/stage7_box_overlay_smoke_50_seed7_h20.json

local:
  improved: 50/50
  optimal: 32/50
  one_ply_status: failed

conversion:
  19 mate / 31 max_plies
  conversion_status: failed

shadow candidates:
  86
```

Promotion gate:

```text
artifact:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_overlay_composed_smoke/promotion_eval_stage7_box_overlay_smoke.json

promotion_status:
  quarantine

failure reasons:
  mate_rate=0.380 < 0.650
  max_plies_rate=0.620 > 0.250
  shadow_candidates=86 > 0
```

Handoff analysis:

```text
artifact:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_overlay_composed_smoke/stage7_box_overlay_smoke_50_seed7_h20_analysis.md

failure motifs:
  selected_successor_miscalibrated: 31

selected successor by outcome:
  krk.stage0_basin:max_plies: 31
  krk.edge_trap_close:mate: 8

semantic alignment:
  reward_contract_mismatch: 24
  reward_visible_fence_aligned_survived: 15
  reward_visible_fence_aligned_reply_not_checked: 11

shadow triggers:
  repeated_conversion_failure: 31
  high_score_conversion_failure: 31
  reward_contract_mismatch: 24
```

Interpretation:

```text
Stage 7 box_shrink is locally learnable but not composition-ready.
The overlay mechanism correctly quarantines it instead of promoting it.
The failure is not diffuse: box_shrink rewards often confirm when the visible fence/contract does not, and continuation falls back to high-scoring stage0_basin paths that fail conversion.
Do not train Stage 8 or promote Stage 7 yet.
The next work should be a Stage 7 semantic/contract audit around box-shrink reward confirmation versus visible box/fence contraction terms.
```

## Slice 59: Growth Monitor v0 Structural Candidates

The Stage 7 failure is now framed as the first Growth Monitor v0 test case rather than a manual patch request.

New schema:

```text
StructuralCandidate
schema_version: structural_candidate.v1
causal_status: non_causal
credit: 0.0
promotion_status: shadow/proposed/sandboxed/validated/promoted/quarantined/rejected
```

New non-causal event export:

```text
event_type: structural_candidate_event
schema_version: structural_candidate_event.v1
credit: 0.0
```

Initial monitor families:

```text
growth.monitor.reward_contract_mismatch
growth.monitor.successor_miscalibration
growth.monitor.stage_overlay_quarantine
```

Stage 7 candidate artifact:

```text
reports/structural_candidates/stage7_box_shrink_candidates.json
```

Generated candidates:

```text
cand.krk.box_shrink.reward_contract_refinement.v1
  type: contract_refinement
  monitor: growth.monitor.reward_contract_mismatch
  status: proposed
  source terms:
    reward_confirmed
    visible_contract_not_confirmed
    conversion_failed
    shadow_support_high

cand.krk.box_shrink.handoff_role_refinement.v1
  type: successor_contract_refinement
  monitor: growth.monitor.successor_miscalibration
  status: proposed
  source terms:
    selected_successor_miscalibrated
    repeated_conversion_failure
    high_score_conversion_failure

cand.krk.box_shrink.overlay_quarantine_confirmed.v1
  type: quarantine_overlay
  monitor: growth.monitor.stage_overlay_quarantine
  status: quarantined
  source terms:
    target_stage_local_success
    target_stage_conversion_failure
    shadow_candidates_above_threshold
```

The generated candidates point to the next audit domains, but do not apply any repair:

```text
visible box-shrink contract audit:
  box_area_decreased_after_own_move
  box_area_not_increased_after_reply
  fence_or_cut_preserved
  rook_safe_after_reply
  enemy_king_mobility_reduced

handoff role audit:
  krk.box_shrink_to_edge_trap_handoff
  krk.box_shrink_to_drive_repair
  krk.box_shrink_post_reply_continuation
```

Architecture note:

```text
reports/structural_growth_lab_note.md
```

Core boundary:

```text
The Structural Growth Lab is not the cognitive mechanism itself.
It is the compiler/evaluator/safety harness.

The cognitive mechanism begins when ReCoN-visible monitor SCRIPTs emit candidate hypotheses with source terms.

External tooling may sandbox, validate, promote, quarantine, and serialize candidates.
External tooling must not become a hidden runtime controller.
```

Interpretation:

```text
Stage 7 failure now produces ReCoN-shaped structural hypotheses.
The next Stage 7 semantic audit should be candidate-driven, starting from the generated candidates, not from a human-invented patch.
Handoff packets, stats, shadow candidates, provider-promotion events, and structural candidates all remain non-causal.
```

## Slice 60: Stage 7 Candidate-Driven Semantic Audit

Added an offline audit tool:

```text
scripts/audit_stage7_structural_candidates.py
```

Input artifacts:

```text
reports/structural_candidates/stage7_box_shrink_candidates.json
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_overlay_composed_smoke/stage7_box_overlay_smoke_50_seed7_h20.json
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_overlay_composed_smoke/promotion_eval_stage7_box_overlay_smoke.json
```

Output artifacts:

```text
reports/structural_candidates/stage7_box_shrink_semantic_audit.json
reports/structural_candidates/stage7_box_shrink_semantic_audit.md
```

Audit result:

```text
schema_version: structural_candidate_audit.v1
causal_status: non_causal

needs_more_terms: 1
handoff_role_audit_required: 1
quarantine_confirmed: 1
```

Candidate outcomes:

```text
cand.krk.box_shrink.reward_contract_refinement.v1
  proposed -> needs_more_terms
  reward_contract_mismatch samples: 24

cand.krk.box_shrink.handoff_role_refinement.v1
  proposed -> sandbox_ready
  stage0_basin max_plies ratio after box_shrink: 31/31

cand.krk.box_shrink.overlay_quarantine_confirmed.v1
  quarantined -> quarantined
```

Suggested term counts over the 50-sample smoke:

```text
box_area_decreased_after_own_move:
  true: 17
  false: 33

box_area_not_increased_after_reply:
  true: 39
  false: 0
  unknown: 11

fence_or_cut_preserved:
  true: 26
  false: 24

rook_safe_after_reply:
  true: 39
  false: 0
  unknown: 11

enemy_king_mobility_reduced:
  true: 34
  false: 16
```

For `max_plies` cases specifically:

```text
box_area_decreased_after_own_move:
  true: 6
  false: 25

box_area_not_increased_after_reply:
  true: 31
  false: 0

fence_or_cut_preserved:
  true: 7
  false: 24

rook_safe_after_reply:
  true: 31
  false: 0

enemy_king_mobility_reduced:
  true: 23
  false: 8
```

Interpretation:

```text
The current Stage 7 reward can confirm without visible box contraction.
Non-expansion after reply is too weak to stand in for box_shrink.
Many failed reward-confirmed samples preserve rook safety but do not preserve a visible fence/cut.
The dominant failed continuation remains stage0_basin, selected 31/31 times in max_plies cases.
```

Next candidate-driven step:

```text
Use the sandbox_ready handoff-role candidate to audit Stage 7 successor ownership and visible box-shrink handoff roles.
Do not promote Stage 7.
Do not make the audit causal.
Do not patch box_shrink directly until the candidate-specific audit identifies the proposed role/contract repair.
```

## Slice 61: Stage 7 Successor Ownership Audit

Added:

```text
scripts/audit_stage7_successor_ownership.py
```

This script consumes the Stage 7 semantic audit and the original handoff trace. It expands:

```text
cand.krk.box_shrink.handoff_role_refinement.v1
```

into candidate handoff-role evidence. It is still non-causal.

Output artifacts:

```text
reports/structural_candidates/stage7_box_shrink_successor_ownership_audit.json
reports/structural_candidates/stage7_box_shrink_successor_ownership_audit.md
```

Observed successor ownership:

```text
krk.stage0_basin:max_plies: 31
krk.edge_trap_close:mate: 8
none:mate: 11
```

Role audit results:

```text
krk.box_shrink_to_edge_trap_handoff
  audit_status: sandbox_candidate
  positive_support: 8
  negative_support: 0

krk.box_shrink_to_drive_repair
  audit_status: needs_counterfactual_evidence
  unsupported_failure_support: 31

krk.box_shrink_post_reply_continuation
  audit_status: needs_role_split_or_successor_sweep
  positive_support: 11
  negative_support: 31
```

Candidate-visible terms proposed by the audit:

```text
krk.box_shrink_to_edge_trap_handoff:
  box_area_not_increased_after_reply
  rook_safe_after_reply
  fence_or_cut_preserved
  successor_edge_trap_close_available

krk.box_shrink_to_drive_repair:
  box_shrink_reward_confirmed
  fence_or_cut_not_preserved
  drive_to_edge_affordance_after_box_shrink
  repair_or_reestablish_cut_available

krk.box_shrink_post_reply_continuation:
  post_box_shrink_conversion_needed
  stage0_basin_fallback_detected
  stage0_basin_unlicensed_after_box_shrink
  edge_or_drive_repair_not_selected
```

Recommended next action from the audit:

```text
sandbox_edge_trap_handoff_role_and_counterfactual_stage0_failures
```

Interpretation:

```text
There is direct positive evidence for an edge-trap handoff after box_shrink.
There is direct negative evidence for unlicensed stage0_basin fallback after box_shrink.
Drive repair remains a plausible hypothesis, but it needs counterfactual evidence before sandboxing.
```

## Slice 62: Stage 7 Quick Counterfactual Candidate Update

Ran a bounded forced-successor counterfactual sweep over the unique Stage 7 `stage0_basin:max_plies` post-reply families.

Command profile:

```text
source diagnostic:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_overlay_composed_smoke/stage7_box_overlay_smoke_50_seed7_h20.json

topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_overlay_composed_smoke/topology/krk_entry_topology.json

successors:
  krk.edge_trap_close
  krk.drive_to_edge
  krk.stage0_basin

quick profile:
  playout_max_plies: 8
  max_ticks: 12
  early_stop_stable_suggestions: 1
```

Artifacts:

```text
reports/structural_candidates/stage7_box_shrink_forced_successor_quick_sweep.json
reports/structural_candidates/stage7_box_shrink_forced_successor_quick_steps.jsonl
reports/structural_candidates/stage7_box_shrink_forced_successor_quick_sweeps.jsonl
```

The full legal-first sweep was intentionally stopped because it was too slow for an interactive pass. The quick sweep is only triage evidence, not validation.

Quick sweep result:

```text
unique failed state families: 4
families with any forced mate: 1
families without any forced mate: 3

krk.edge_trap_close:max_plies: 4
krk.drive_to_edge:mate: 1
krk.drive_to_edge:max_plies: 3
krk.stage0_basin:max_plies: 4
```

Added summarizer:

```text
scripts/summarize_stage7_counterfactual_evidence.py
```

Candidate update artifacts:

```text
reports/structural_candidates/stage7_box_shrink_counterfactual_candidate_update.json
reports/structural_candidates/stage7_box_shrink_counterfactual_candidate_update.md
```

Candidate update result:

```text
schema_version: stage7_counterfactual_candidate_update.v1
causal_status: non_causal
recommended_next_action: sandbox_visible_drive_repair_role
```

Candidate statuses:

```text
krk.box_shrink_to_drive_repair
  status: counterfactual_supported
  support: 1
  proposed next action: sandbox_visible_drive_repair_role

krk.box_shrink_post_reply_continuation
  status: insufficient_existing_successor_capacity_in_quick_sweep
  support: 3
  proposed next action: run_targeted_legal_first_or_longer_horizon_sweep

krk.stage0_basin_after_box_shrink
  status: negative_counterfactual_evidence
  support: 4
  proposed next action: avoid_sandboxing_stage0_as_default_box_shrink_continuation
```

Interpretation:

```text
The earlier edge-trap handoff evidence is real, but it does not explain the unique stage0 failure families under forced replay.
The quick forced replay gives the first concrete support for a box_shrink_to_drive_repair role.
Stage0 should not be sandboxed as the default post-box-shrink continuation.
Three unique families still need either longer-horizon replay, targeted legal-first sweeps, or a future post-box-shrink continuation candidate.
```

## Slice 63: Visible Box-Shrink Drive-Repair Sandbox Role

Added a visible successor role:

```text
krk.box_shrink_to_drive_repair
  provider: krk.drive_to_edge
```

Visible context terms:

```text
fence_or_cut_not_preserved
drive_to_edge_affordance_after_box_shrink
repair_or_reestablish_cut_available
box_shrink_drive_repair_available
```

Role contract:

```text
required:
  box_shrink_drive_repair_available
  enemy_king_not_at_edge
  rook_safe

veto:
  mate_in_one_available
```

Role-scoped move-shape support:

```text
king move or rook transfer/check
rook_safe_after_move
box/edge/corner/confinement non-regression or cut/check creation
optional worst-reply safety if the diagnostic flag requires it
```

Compiler fix:

```text
overlay compilation now refreshes generated successor-affordance nodes from current compiler definitions.
This prevents overlays from inheriting stale role ontology from the frozen base topology.
```

Sandbox topology:

```text
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_drive_repair_sandbox/topology/krk_entry_topology.json
```

Smoke command:

```text
scripts/test_krk_landmark_progress.py
  --label box_shrink
  --samples 10
  --composition-profile handoff_composition_v1
  --use-profile-validation-defaults
```

Smoke result:

```text
improved: 10/10
optimal: 7/10
playouts: 3 mate / 7 max_plies
shadow candidates: 19
```

Trace observation:

```text
box_shrink_to_drive_repair role was visible and contract-met in several failed continuations.
It did not overcome stage0_basin selection in the smoke.
```

Interpretation:

```text
The drive-repair role is now ReCoN-visible and traceable, but not yet a sufficient causal repair.
Do not promote Stage 7.
Do not increase broad bonuses or add hidden penalties.
The next repair should be candidate-driven: either a narrow stage0-after-box-shrink suppression term with visible evidence, or a longer/legal-first sweep to identify first-move shapes for the unresolved families.
```

## Slice 64: Plasticity Balance Protocol And Growth Governor V0

Added plan note:

```text
reports/plasticity_balance_protocol.md
```

Policy:

```text
First try existing structure.
Then try bounded weight/plasticity calibration.
Only then propose or sandbox new topology.
```

Growth Governor v0 is metadata/reporting only. It records:

```text
recent_conversion_rate_history
recent_shadow_candidate_rate
repeated_failure_family_count
route_conflict_rate
handoff_gap_rate
reward_contract_mismatch_rate
guardrail_pass_rate
weight_delta_magnitude
weight_saturation_rate
plasticity_improvement_slope
active_candidate_count
provider_maturity
promotion_status
performance metadata
```

`StructuralCandidate` now carries:

```text
governor_status
governor_metadata
topology_weight_diagnosis
candidate_diagnostic_labels
```

Topology-vs-weight diagnosis fields:

```text
frozen_weight_probe_result
forced_oracle_probe_result
bounded_m3_warmup_result
bounded_m4_consolidation_result
guardrail_delta
weight_saturation
candidate_locality
candidate_complexity
diagnostic_labels
evaluation_phases
```

Provider metadata now includes:

```text
provider_maturity
plasticity_scope
can_m3_update
can_m4_consolidate
```

Current Stage 7 Growth Governor states:

```text
cand.krk.box_shrink.reward_contract_refinement.v1
  governor_status: growth_allowed
  diagnostic_labels: topology_underbroad

cand.krk.box_shrink.handoff_role_refinement.v1
  governor_status: growth_allowed
  diagnostic_labels: parameter_miscalibrated

cand.krk.box_shrink.overlay_quarantine_confirmed.v1
  governor_status: growth_blocked_by_guardrail
  diagnostic_labels: quarantined_after_calibration_budget
```

Current Stage 7 governor metrics:

```text
mate_count: 19
max_plies_count: 31
recent_conversion_rate_history: [0.38]
recent_shadow_candidate_rate: 1.72
repeated_failure_family_count: 4
reward_contract_mismatch_rate: 0.48
active_candidate_count: 3
provider_maturity: quarantined_no_plasticity
promotion_status: quarantine
```

Counterfactual candidate diagnosis:

```text
krk.box_shrink_to_drive_repair
  status: counterfactual_supported
  labels: topology_present_untrained, trainable_candidate

krk.box_shrink_post_reply_continuation
  status: insufficient_existing_successor_capacity_in_quick_sweep
  labels: provider_capacity_missing

krk.stage0_basin_after_box_shrink
  status: negative_counterfactual_evidence
  labels: parameter_miscalibrated, topology_overbroad
```

Boundary:

```text
The governor and diagnosis fields are non-causal.
They do not alter routing, M3, M4, M5, or topology during gameplay.
They only decide whether an offline candidate should settle, receive more weight/plasticity diagnosis, enter sandbox, or remain quarantined.
```

## Slice 65: Growth Governor Evaluation Plan

Added non-causal evaluation planner:

```text
scripts/plan_structural_candidate_evaluation.py
```

Generated artifacts:

```text
reports/structural_candidates/stage7_box_shrink_growth_governor_plan.json
reports/structural_candidates/stage7_box_shrink_growth_governor_plan.md
```

Planner input:

```text
reports/structural_candidates/stage7_box_shrink_candidates.json
reports/structural_candidates/stage7_box_shrink_counterfactual_candidate_update.json
reports/structural_candidates/stage7_box_shrink_drive_repair_sandbox_smoke_10.json
```

Growth Governor result:

```text
recommended_next_action:
  bounded_m3_warmup_for_box_shrink_to_drive_repair

hard_blocks:
  do_not_train_stage8
  do_not_promote_stage7
  do_not_enable_stage7_repair_by_default
  do_not_make_packets_stats_or_candidates_causal
```

Role plan:

```text
krk.box_shrink_to_drive_repair
  decision: needs_more_weight_training
  phase: phase_3_bounded_plasticity_warmup
  next_action: run_candidate_local_m3_warmup_probe
  labels: parameter_miscalibrated, topology_present_untrained, trainable_candidate
  sandbox smoke: role contract met 5 times, selected 0 times, stage0 selected under role 5 times

krk.box_shrink_post_reply_continuation
  decision: growth_blocked_by_cooldown
  phase: phase_2_forced_oracle_probe
  next_action: run_targeted_legal_first_or_longer_horizon_sweep
  blocked: existing_provider_capacity_inconclusive

krk.stage0_basin_after_box_shrink
  decision: growth_blocked_by_guardrail
  phase: phase_1_frozen_weight_probe
  next_action: do_not_sandbox_as_default_continuation
  blocked: negative_counterfactual_evidence
```

Interpretation:

```text
The next Stage 7 step is not a new topology patch.
The current box_shrink_to_drive_repair role is visible and counterfactually plausible,
but the sandbox smoke shows it is not selected over stage0_basin.
That makes the next bounded probe a candidate-local M3 warmup with protected frozen providers,
not Stage 8 training and not Stage 7 promotion.
```

## Slice 66: Candidate-Local M3 Warmup Scope

Added offline warmup-scope planner:

```text
scripts/plan_candidate_local_m3_warmup.py
```

The planner consumes the Growth Governor plan and topology, then emits an edge whitelist for a later bounded M3 probe. It does not run plasticity, mutate topology, alter routing, consolidate M4, or promote candidates.

Initial stale-topology artifact:

```text
reports/structural_candidates/stage7_box_shrink_candidate_local_m3_warmup_plan.json
reports/structural_candidates/stage7_box_shrink_candidate_local_m3_warmup_plan.md
```

This correctly flagged missing provider maturity/plasticity fields in the older sandbox topology. The overlay compiler was then fixed so `only_missing` backfills missing maturity/plasticity masks without relabeling existing provider versions.

Refreshed sandbox topology:

```text
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_drive_repair_sandbox/topology/krk_entry_topology_refreshed.json
```

Refreshed warmup plan:

```text
reports/structural_candidates/stage7_box_shrink_candidate_local_m3_warmup_plan_refreshed.json
reports/structural_candidates/stage7_box_shrink_candidate_local_m3_warmup_plan_refreshed.md
```

Warmup scope:

```text
target_role: krk.box_shrink_to_drive_repair
target_provider: krk.drive_to_edge
eligible M3 edges: 21
  candidate_provider_leg_selection: 3
  candidate_provider_internal: 12
  candidate_provider_triplet_temporal: 6

protected provider versions:
  stage5_validated_v1

M4 consolidation:
  disabled

topology mutation:
  disabled

protected provider mutation:
  disabled
```

Interpretation:

```text
The next executable probe can warm up only the candidate-local drive_to_edge overlay edges.
Visible role-support edges remain observe-only because the current topology represents role-provider support through visible role SCRIPT payloads rather than explicit provider-support edges.
Frozen base providers are excluded from the M3 whitelist.
```

## Slice 67: Candidate-Local M3 Probe And Role-Provider Support Proposal

Added non-causal M3 feasibility probe:

```text
scripts/probe_candidate_local_m3_warmup.py
```

Generated artifacts:

```text
reports/structural_candidates/stage7_box_shrink_candidate_local_m3_probe.json
reports/structural_candidates/stage7_box_shrink_candidate_local_m3_probe.md
```

Probe result:

```text
target_role: krk.box_shrink_to_drive_repair
target_provider: krk.drive_to_edge
probe_result: blocked_no_candidate_provider_eligibility
recommended_next_action: compile_visible_role_provider_support_or_owner_eligibility_before_m3

role_contract_met: 5
role_met_provider_not_selected: 5
role_met_selected:krk.stage0_basin: 5
candidate_edge_eligibility_events: 0
```

Interpretation:

```text
The role is visible and confirms, but the provider never owns the continuation.
Candidate-local drive_to_edge edges therefore do not fire, so M3 has no eligible candidate-local edge activity to warm up.
Running a weight update now would be fake progress.
```

Added non-causal role-provider support proposal generator:

```text
scripts/propose_role_provider_support_edges.py
```

Generated artifacts:

```text
reports/structural_candidates/stage7_box_shrink_role_provider_support_proposal.json
reports/structural_candidates/stage7_box_shrink_role_provider_support_proposal.md
```

Proposed sandbox edge:

```text
script.krk.successor.box_shrink_to_drive_repair_affordance
  -- SUB / initial_weight=0.0 / trainable=true -->
skill.krk.drive_to_edge
```

Proposal constraints:

```text
causal_status: non_causal
proposal_status: sandbox_ready
do_not_insert_into_default_topology
do_not_train_stage8
do_not_promote_stage7_without_guardrails
do_not_make_probe_or_candidate_causal
```

This is the first concrete handoff from:

```text
visible monitor evidence
  -> structural candidate
  -> bounded topology-vs-weight diagnosis
  -> explicit sandbox support-edge proposal
```

It keeps the external lab as sandbox/evaluator only; the proposed edge is sourced by visible SCRIPT evidence and remains non-causal until explicitly sandbox-compiled and guardrail validated.

## Slice 68: Gated Support Adapter Sandbox

Important executor finding:

```text
A direct SUB edge from a role SCRIPT to a provider SCRIPT is unsafe in the current executor,
because SCRIPT children can be requested while the parent SCRIPT is WAITING,
before the role predicate has confirmed.
```

The role-provider support proposal was therefore corrected:

```text
unsafe_direct_graph_edges_emitted: false
sandbox_compile_strategy: compile_gated_support_adapter_not_direct_sub_edge
```

Added runtime factory:

```text
recon_lite_chess.krk_baseline_nodes:create_krk_role_provider_support_adapter
```

Adapter behavior:

```text
reads visible role-provider contract evidence from blackboard
records krk_explicit_role_provider_supports only when the role contract is already met
does not request the provider skill
is ignored unless explicit_role_provider_support_enabled is true
```

Added sandbox compiler:

```text
scripts/compile_role_provider_support_sandbox.py
```

Compiled sandbox topology:

```text
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_drive_repair_sandbox/topology/krk_entry_topology_support_adapter_sandbox.json
```

Compiled adapter:

```text
script.krk.support.krk_box_shrink_to_drive_repair_to_krk_drive_to_edge
  -- SUB / weight=0.0 / trainable=true / edge_kind=visible_role_provider_support_weight -->
terminal.krk.support.krk_box_shrink_to_drive_repair_to_krk_drive_to_edge_marker
```

The topology loads and validates formal pairs:

```text
nodes: 458
edges: 1316
adapter present: true
```

Minimal default-off local check:

```text
artifact:
  reports/structural_candidates/stage7_box_shrink_support_adapter_default_off_local_1.json

result:
  no_move: 0
  improved: 1/1
  conversion_status: not_checked
```

The attempted 10-sample playout smoke was stopped after exceeding the intended quick-check window. That run should be repeated later with performance profiling or a smaller playout budget if needed; it was not used as acceptance evidence for this slice.

Current acceptance basis:

```text
adapter is default-off
adapter does not insert direct role->provider request edge
adapter support is explicit and opt-in
topology loads with formal pairs
unit/regression suite passes
```

## Slice 69: Stage 7 Support-Adapter Behavioral Validation

Validation focus:

```text
prove adapter default-off equivalence
make adapter support traceable in diagnostics
run small Stage 7 smoke before any guardrails or promotion
```

Important implementation correction:

```text
Stage 7 overlay topology does not currently expose `skill.krk.edge_trap_close`
as a provider node; edge-trap ownership is represented through actuator/leg
metadata. The support-adapter compiler was relaxed to allow provider-ID
support without requiring a provider SCRIPT node. It still emits no direct
provider request edge.
```

Default-off equivalence:

```text
base:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_drive_repair_sandbox/topology/krk_entry_topology_refreshed.json

sandbox:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_drive_repair_sandbox/topology/krk_entry_topology_edge_trap_support_adapter_off.json

artifact:
  reports/structural_candidates/stage7_default_off_equiv_edge_adapter_3_h5.json

result:
  equivalent: true
  packet_count: 9
  shadow_candidate_count: 6
  adapter_fire_count: 0
```

Adapter traceability:

```text
adapter:
  script.krk.support.krk_edge_rook_transfer_recovery_to_krk_edge_trap_close

source role:
  krk.edge_rook_transfer_recovery

provider:
  krk.edge_trap_close

trace fields:
  adapter_id
  source_role
  provider_id
  role_confirmed
  source_terms
  support_amount
  direct_request=false
```

The diagnostic path now reports both selected-suggestion adapter support and
lower-ranked adapter-supported suggestions:

```text
adapter_fire_count
adapter_supported_provider_by_outcome
adapter_supported_move_by_outcome
```

Small smoke matrix:

```text
baseline:
  reports/structural_candidates/stage7_overlay_no_adapter_10_h20.json

adapter 0.05:
  reports/structural_candidates/stage7_edge_adapter_on_w005_10_h20.json

adapter 0.10:
  reports/structural_candidates/stage7_edge_adapter_on_w010_10_h20.json

comparison:
  reports/structural_candidates/stage7_edge_adapter_smoke_comparison_10_h20.json
```

Observed result:

```text
baseline:
  playouts: {max_plies: 10}
  shadow_candidate_count: 20

initial 0.05/0.10 adapter:
  adapter fired on krk.edge_trap_close suggestions
  supported move family: a7d7
  conversion remained max_plies
```

Diagnosis:

```text
adapter_traceable_but_target_neutral
candidate_status: sandboxed_neutral_parameter_or_role_insufficient
promotion_status: sandboxed
causal_status: opt_in_only
```

No guardrails were run because the adapter did not improve Stage 7 target
conversion. The next useful diagnostic is not stronger support by default; it
is to inspect why the supported edge-trap move family (`a7d7`) remains
max-plies under current continuation.

Follow-up targeted probe:

```text
artifact:
  reports/structural_candidates/stage7_supported_a7d7_probe.json

state:
  6k1/R7/8/8/8/8/5K2/8 w - - 2 2

result:
  a7d7 -> max_plies at horizons 10/20/40
  nearby sampled alternatives -> max_plies at horizons 10/20/40
```

Visible term interpretation:

```text
edge_rook_transfer_recovery_available: true
safe_rook_edge_transfer_available: true
white_king_can_improve_support: true
white_king_support_available: false
```

The original adapter hypothesis was therefore overbroad. It supported an
edge-trap transfer in a state where the white king can improve support but does
not yet actually support the trap. The adapter contract was tightened:

```text
support_required_terms:
  white_king_support_available
```

Post-fix smoke:

```text
0.05 adapter:
  playouts: {max_plies: 10}
  shadow_candidate_count: 20
  adapter_fire_count: 0

0.10 adapter:
  playouts: {max_plies: 10}
  shadow_candidate_count: 20
  adapter_fire_count: 0
```

Updated diagnosis:

```text
adapter_candidate_overbroad_then_blocked_by_support_precondition
candidate_status: sandboxed_needs_more_terms_or_downstream_capacity
promotion_status: sandboxed
```

The edge-trap support adapter should not be guardrailed or promoted. Stage 7's
remaining issue is not solved by first-move edge-trap support; it is either a
missing/weak downstream continuation after box-shrink or a need for a
king-support-before-edge-trap handoff candidate.

## Stage 7 King-Tempo Sandbox Outcome

Artifacts:

```text
reports/structural_candidates/stage7_king_support_handoff_probe.json
reports/structural_candidates/stage7_king_support_handoff_probe.md
reports/structural_candidates/stage7_king_tempo_default_off_equiv_3_h5.json
reports/structural_candidates/stage7_king_tempo_on_10_h20.json
reports/structural_candidates/stage7_king_tempo_on_10_h20_analysis.md
```

The targeted probe found that the repeated support-gap FEN had converting
quiet king moves:

```text
FEN: 6k1/R7/8/8/8/8/5K2/8 w - - 2 2

f2e2 -> mate in 18 plies at horizons 20/40/60
f2e1 -> mate by horizon 40/60
f2f1 -> mate by horizon 40/60
```

This justified a narrow opt-in visible sandbox provider:

```text
terminal.krk.stage7_king_tempo
role: krk.box_shrink_king_tempo_handoff
causal_status: sandbox_opt_in
default: off
```

Default-off equivalence passed:

```text
equivalent: true
packet_count: 9
shadow_candidate_count: 6
adapter_fire_count: 0
```

Enabled smoke result:

```text
samples: 10
horizon: 20
playouts: {max_plies: 10}
shadow_candidate_count: 20
selected successor: krk.stage7_king_tempo in 10/10 post-reply states
```

The sandbox was therefore traceable and behaviorally isolated, but did not
solve Stage 7. In the sampled states it licensed quiet king moves such as
`e2d2` and `d2c2`, not the original `f2e2` state-family move. This means the
current visible king-tempo contract is still too broad: it recognizes a
general "quiet not-toward-enemy king tempo" shape, but not the more specific
geometry that makes the original `f2e2` move convert.

Diagnosis:

```text
candidate_status: sandbox_failed_parameter_or_ontology_miscalibrated
diagnostic_label: selected_successor_miscalibrated
promotion_status: sandboxed
guardrails_run: false
```

Do not promote or guardrail this sandbox. The useful evidence is that
converting king-tempo moves exist in at least one Stage 7 failure family, but
the visible contract needs a more precise move-shape/audit boundary before any
causal Stage 7 repair should be retried.

Follow-up move-shape audit:

```text
artifact:
  reports/structural_candidates/stage7_king_tempo_move_shape_audit.json
  reports/structural_candidates/stage7_king_tempo_move_shape_audit.md

diagnosis:
  king_tempo_contract_too_broad

probe_converting: 3
probe_nonconverting: 5
failed_sandbox_unique_moves: 2
```

The audit compared the targeted converting family against the failed sandbox
selections. It found that the converters share:

```text
compact_box_area_before_move
fence_survives_worst_reply
```

The failed sandbox selections share:

```text
box_area_large_before_move
king_moves_toward_rook_support
white_king_distance_to_rook_decreases
```

Candidate update:

```text
candidate_status: needs_contract_refinement
proposed required terms:
  compact_box_area_before_move
  fence_survives_worst_reply
proposed veto terms:
  box_area_large_before_move
  king_moves_toward_rook_support
causal_status: non_causal
promotion_status: sandboxed
```

This should be treated as a candidate-driven audit result, not a runtime patch.
The next causal attempt, if any, should first compile these terms as visible
move-shape contract terms and repeat default-off equivalence before enabling
the sandbox.

## Stage 7 King-Tempo Refined Single-Use Sandbox

The audit terms were compiled into the opt-in sandbox terminal:

```text
required:
  compact_box_area_before_move
  fence_survives_worst_reply

veto:
  box_area_large_before_move
  king_moves_toward_rook_support

temporal scope:
  single use per playout
```

The single-use scope matters. Without it, the sandbox correctly selected the
first compact king-tempo move but kept re-firing later instead of handing
control back to the normal continuation graph.

Default-off equivalence:

```text
artifact:
  reports/structural_candidates/stage7_king_tempo_single_use_default_off_equiv_3_h5.json

equivalent: true
packet_count: 9
shadow_candidate_count: 6
```

Paired horizon-40 smoke:

```text
baseline:
  artifact: reports/structural_candidates/stage7_king_tempo_baseline_10_h40.json
  playouts: {max_plies: 10}
  shadow_candidate_count: 20
  selected: krk.stage0_basin:max_plies = 10

single-use sandbox:
  artifact: reports/structural_candidates/stage7_king_tempo_single_use_on_10_h40.json
  playouts: {mate: 3, max_plies: 7}
  shadow_candidate_count: 14
  selected: krk.stage7_king_tempo:mate = 3
            krk.stage7_king_tempo:max_plies = 7
```

Updated diagnosis:

```text
candidate_status: sandbox_promising_not_validated
diagnosis: visible_contract_refinement_improves_target_but_incomplete
promotion_status: sandboxed
guardrails_run: false
```

Do not promote yet. The next step is a larger Stage 7 target smoke, still
opt-in, before protected Stage 6/5/1 guardrails.

Larger paired target smoke:

```text
baseline:
  artifact: reports/structural_candidates/stage7_king_tempo_baseline_25_h40.json
  playouts: {max_plies: 25}
  shadow_candidate_count: 50
  selected: krk.stage0_basin:max_plies = 25

sandbox:
  artifact: reports/structural_candidates/stage7_king_tempo_single_use_on_25_h40.json
  playouts: {mate: 13, max_plies: 12}
  shadow_candidate_count: 24
  selected: krk.stage7_king_tempo:mate = 13
            krk.stage7_king_tempo:max_plies = 12
```

This is a real target improvement, so modest protected guardrails were run.

Guardrails:

```text
Stage 6 drive_to_edge, 50 samples:
  artifact: reports/structural_candidates/stage7_king_tempo_guard_stage6_drive_50_h40.json
  playouts: {mate: 50}
  shadow_candidate_count: 0
  status: passed

Stage 5 fence, 50 samples:
  artifact: reports/structural_candidates/stage7_king_tempo_guard_stage5_fence_50_h40.json
  playouts: {mate: 50}
  shadow_candidate_count: 0
  status: passed

Stage 4 wrong-tempo, 50 samples, king-tempo enabled:
  artifact: reports/structural_candidates/stage7_king_tempo_guard_stage4_wrong_tempo_50_h40.json
  playouts: {mate: 43, max_plies: 7}
  shadow_candidate_count: 14
  status: failed

Stage 4 wrong-tempo, 50 samples, king-tempo disabled:
  artifact: reports/structural_candidates/stage7_king_tempo_guard_stage4_wrong_tempo_50_h40_disabled.json
  playouts: {mate: 43, max_plies: 7}
  shadow_candidate_count: 14
  status: failed_same_as_disabled
```

Initial interpretation:

```text
candidate_status: target_improved_but_guardrail_blocked
promotion_status: quarantined_by_existing_stage4_guardrail
diagnosis: target_improves_but_stage7_overlay_has_preexisting_stage4_guardrail_failure
```

The candidate itself is not causing the Stage 4 regression; the enabled and
disabled runs are identical. But promotion is still blocked because the Stage 7
overlay/topology is not globally guardrail-safe. The next architecture step is
not to tune this king-tempo candidate further; it is to fix the Stage 7 overlay
composition/provider-preservation issue exposed by the Stage 4 guardrail.

Baseline-aware promotion evaluation:

```text
script:
  scripts/evaluate_provider_promotion.py

artifact:
  reports/structural_candidates/stage7_king_tempo_baseline_aware_promotion_eval.json

target baseline:
  reports/structural_candidates/stage7_king_tempo_baseline_25_h40.json

target candidate:
  reports/structural_candidates/stage7_king_tempo_single_use_on_25_h40.json

guardrail controls:
  stage6 disabled: reports/structural_candidates/stage7_king_tempo_guard_stage6_drive_50_h40_disabled.json
  stage5 disabled: reports/structural_candidates/stage7_king_tempo_guard_stage5_fence_50_h40_disabled.json
  stage4 disabled: reports/structural_candidates/stage7_king_tempo_guard_stage4_wrong_tempo_50_h40_disabled.json
```

Baseline-aware result:

```text
target_improved_vs_baseline: true
target delta:
  mate_rate_delta: +0.52
  max_plies_rate_delta: -0.52
  shadow_candidates_delta: -26

guardrail regressions versus controls:
  stage6: false
  stage5: false
  stage4: false

promotion_status: quarantine
```

Updated interpretation:

```text
candidate_status: target_improved_but_stage_incomplete
diagnosis: target_improves_without_guardrail_regression_but_stage_threshold_not_met
promotion_status: quarantine
```

The Stage 4 result is not a new regression and should not be attributed to the
king-tempo candidate. The candidate still cannot be promoted because the Stage
7 target itself remains below promotion thresholds: 13/25 mate, 12/25 max_plies,
and 24 shadow candidates.

## Stage 7 Post-King-Tempo Continuation Audit

The remaining Stage 7 failures were audited without changing runtime behavior.
The audit groups the post-reply state where the opt-in king-tempo provider fires,
applies the king-tempo move, and replays the resulting continuation at bounded
horizons.

Artifacts:

```text
script:
  scripts/audit_stage7_post_king_tempo_continuation.py

json:
  reports/structural_candidates/stage7_post_king_tempo_continuation_audit.json

markdown:
  reports/structural_candidates/stage7_post_king_tempo_continuation_audit.md
```

Result:

```text
records: 25
families: 2
outcomes: {mate: 13, max_plies: 12}
diagnosis: post_king_tempo_followup_needed
causal_status: non_causal
```

Failure family:

```text
family: stage7.post_king_tempo.family_01
support: 12
post-reply FEN: 3k4/R7/8/8/8/8/4K3/8 w - - 2 2
king-tempo move: e2f2
post-tempo FEN: 3k4/R7/8/8/8/8/5K2/8 b - - 3 2
class: post_king_tempo_lacks_corner_net_pressure

replay:
  h=20: max_plies, first white f2g3 via krk.stage0_basin
  h=40: max_plies, first white f2g3 via krk.stage0_basin
  h=60: max_plies, first white f2g3 via krk.stage0_basin
```

Successful family:

```text
family: stage7.post_king_tempo.family_02
support: 13
post-reply FEN: 6k1/R7/8/8/8/8/5K2/8 w - - 2 2
king-tempo move: f2e2
post-tempo FEN: 6k1/R7/8/8/8/8/4K3/8 b - - 3 2
class: post_king_tempo_converts

replay:
  h=20/40/60: mate in 18 plies, first white a7a8 via krk.stage0_basin
```

Candidate update:

```text
candidate_id: cand.krk.box_shrink.post_king_tempo_continuation.v1
candidate_status: proposed
source_monitor_script: growth.monitor.successor_miscalibration
promotion_status: proposed
causal_status: non_causal
```

Interpretation:

```text
The first king-tempo move is useful but not sufficient. The remaining repeated
failure is not a broader first-move king-tempo licensing problem; it is a
post-tempo continuation ownership problem. The next repair, if attempted, should
target a visible post_king_tempo_continuation role or a candidate-driven
legal-first/post-tempo follow-up sweep, not a broader king-tempo bonus.
```

Filtered legal-first follow-up sweep:

```text
filter:
  box_area_decreases_after_move OR rook_to_checking_line

failed family:
  first White FEN: 4k3/R7/8/8/8/8/5K2/8 w - - 4 3
  tested moves: 7
  converting move: a7c7

successful family:
  first White FEN: 5k2/R7/8/8/8/8/4K3/8 w - - 4 3
  tested moves: 7
  converting move: a7a8

diagnosis:
  post_king_tempo_followup_selection_problem
```

This proves the remaining Stage 7 failure is not missing KRK motor capacity:
the existing continuation graph converts if the first post-tempo follow-up move
has the right visible shape.

## Stage 7 Post-King-Tempo Scoped Sandbox

A narrow opt-in follow-up provider was added:

```text
terminal.krk.stage7_post_king_tempo
role: krk.post_king_tempo_continuation
causal_status: sandbox_opt_in
default: off
scope: active_landmark_label == box_shrink
temporal scope: after stage7_king_tempo has fired, single-use per playout
```

The first attempt solved Stage 7 but regressed Stage 4 because the provider was
not label-scoped:

```text
artifact:
  reports/structural_candidates/stage7_post_king_tempo_single_use_on_25_h40.json

target:
  Stage 7 box_shrink, 25 samples, h40
  playouts: {mate: 25}
  shadow_candidate_count: 0

guardrail regression:
  Stage 4 enabled:  33/50 mate, 17/50 max_plies, 34 shadows
  Stage 4 disabled: 36/50 mate, 14/50 max_plies, 28 shadows
  delta: -0.06 mate rate, +6 shadows

promotion_status:
  quarantine
```

The repair was not another score tweak. The Stage 7 sandbox providers are now
explicitly label/profile scoped:

```text
active_landmark_label must equal stage7_provider_scope_label
default scope label: box_shrink
```

Scoped result:

```text
target:
  artifact: reports/structural_candidates/stage7_post_king_tempo_scoped_on_25_h40.json
  playouts: {mate: 25}
  shadow_candidate_count: 0

Stage 4 scoped guard:
  artifact: reports/structural_candidates/stage7_post_king_tempo_scoped_guard_stage4_wrong_tempo_50_h40.json
  playouts: {mate: 36, max_plies: 14}
  shadow_candidate_count: 28

Stage 4 disabled control:
  artifact: reports/structural_candidates/stage7_post_king_tempo_guard_stage4_wrong_tempo_50_h40_disabled.json
  playouts: {mate: 36, max_plies: 14}
  shadow_candidate_count: 28

delta:
  mate_rate_delta: 0.0
  max_plies_rate_delta: 0.0
  shadow_candidates_delta: 0
```

Baseline-aware evaluation:

```text
artifact:
  reports/structural_candidates/stage7_post_king_tempo_scoped_promotion_eval.json

target delta versus Stage 7 baseline:
  mate_rate_delta: +1.0
  max_plies_rate_delta: -1.0
  shadow_candidates_delta: -50

guardrail deltas versus controls:
  Stage 6: no regression
  Stage 5: no regression
  Stage 4: no regression

promotion_status: promoted
```

Interpretation:

```text
This is a validated scoped sandbox candidate, not a global/default policy.
The key architectural lesson is that late-stage repair providers must be
profile/domain scoped unless and until cross-stage validation proves they are
safe globally.
```

Scaled target validation:

```text
artifact:
  reports/structural_candidates/stage7_post_king_tempo_scoped_on_100_h40.json

analysis:
  reports/structural_candidates/stage7_post_king_tempo_scoped_on_100_h40_analysis.md

result:
  Stage 7 box_shrink, 100 samples, h40
  playouts: {mate: 100}
  shadow_candidate_count: 0
  improved: 100/100
  local optimal: 49/100

promotion eval:
  reports/structural_candidates/stage7_post_king_tempo_scoped_100_promotion_eval.json
  promotion_status: promoted
```

The local one-ply objective is still not fully optimal, but conversion is
solved on this scaled validation. This reinforces the architectural separation:
Stage 7 local reward calibration can improve later through weight/plasticity
work, while the scoped handoff repair is currently composition-valid.
## Stage 8 opposition-tempo overlay candidate

Status: `overlay_only`, not global default.

Stage 8 initially had no explicit provider in the validated Stage 7 topology:

```text
label: opposition_tempo
stage_filter: 8
baseline result: no_move=25/25
```

The first Stage 8 training attempt produced many positive transitions, but all
candidate actuator patterns merged into older labelled providers. That is a
provider-preservation problem: a later stage cannot become a versioned overlay
if its patterns silently rewrite or reinforce lower-stage labels. I added an
opt-in training flag:

```text
--prevent-cross-label-actuator-merge
```

With that flag enabled, Stage 8 produced 7 explicit `opposition_tempo`
actuators. The overlay compiler then composed only those actuators onto the
validated scoped Stage 7 topology as `stage8_opposition_overlay_v1`. The
compiler now remaps overlay actuator IDs deterministically if they collide with
frozen base topology IDs, preserving the original `source_actuator_id` in node
metadata.

Target validation:

```text
artifact: reports/structural_candidates/stage8_opposition_overlay_target_100_h40.json
result: 100/100 mate
local: 100/100 improved, 100/100 optimal
shadow candidates: 0
```

Paired guardrails:

```text
Stage 6 drive_to_edge: 50/50 mate, 0 shadows
Stage 5 fence_established: 50/50 mate, 0 shadows
Stage 4 wrong_tempo: 47/50 mate, 6 shadows
Stage 7 box_shrink: 19/50 mate, 87 shadows
```

The Stage 7 box-shrink guardrail did not regress relative to the same command
on the validated Stage 7 base topology; the control also produced 19/50 mate and
87 shadows. That means this is existing guardrail debt or command/provenance
drift, not a Stage 8 overlay delta. The promotion evaluator was tightened so
paired guardrail controls that fail absolute thresholds now block full
promotion. The resulting status is:

```text
promotion_status: overlay_only
reason: target passes and no paired guardrail deltas regress, but control guardrail debt exists
artifact: reports/structural_candidates/stage8_opposition_overlay_promotion_eval.json
manifest: reports/structural_candidates/stage8_opposition_overlay_manifest.json
```

Architectural note: Stage 8 is useful as an overlay candidate, but should not
be treated as a globally promoted KRK base until the Stage 7/Stage 4 guardrail
debt is resolved or explicitly scoped.

## Stage 7 current guardrail debt retry

Status: `not solved` on the current harder guardrail profile.

After Stage 8 exposed Stage 7 guardrail debt, I rechecked Stage 7 against the
current profile:

```text
label: box_shrink
source stages: Box_Small, Box_Medium, Edge_Fence_Deep
horizon: 40 / adversarial Black
baseline artifact: reports/structural_candidates/stage7_current_base_25_h40_compare.json
baseline result: 12/25 mate, 13/25 max_plies, 28 shadows
```

I added a scoped, default-off visible repair provider:

```text
terminal.krk.stage7_drive_repair
role: krk.box_shrink_drive_repair_move
enabled by: --enable-stage7-drive-repair
scope: post-reply only, active_landmark_label == box_shrink
causal status: sandbox_opt_in
```

The terminal only fires when visible context says the box-shrink attempt broke
or failed to preserve the drive/fence context:

```text
box_shrink_drive_repair_available
enemy_king_not_at_edge
rook_safe
rook_safe_after_move
rook_safe_after_worst_reply
no_draw_after_worst_reply
safe check/cut repair or box-progress move shape
```

This repair is not a hidden router: it emits an ordinary visible terminal
suggestion with `direct_request = false` and source terms in
`visible_stage7_drive_repair_license`. It is also gated to post-reply
continuation so it cannot hijack the first local Stage 7 move.

Result:

```text
artifact: reports/structural_candidates/stage7_drive_repair_on_25_h40.json
result: 15/25 mate, 10/25 max_plies, 23 shadows
delta vs baseline: +3 mates, -5 shadows
```

I then tried the Plasticity Balance Protocol step: retrain a guarded Stage 7
overlay from the validated Stage 6 provider with
`--prevent-cross-label-actuator-merge`:

```text
learner: snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/baseline/final_learner.pkl
overlay topology: snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_sandbox.json
```

The guarded retrain produced explicit `box_shrink` overlay actuators, but did
not improve conversion on the harder profile:

```text
artifact: reports/structural_candidates/stage7_guarded_retry_target_25_h40.json
result: 15/25 mate, 10/25 max_plies, 23 shadows
```

An 80-ply check did not change the result:

```text
artifact: reports/structural_candidates/stage7_guarded_retry_target_25_h80.json
result: 15/25 mate, 10/25 max_plies, 23 shadows
```

Interpretation:

```text
Stage 7 old scoped profile remains historically solved, but the current
Box_Small/Box_Medium/Edge_Fence_Deep guardrail profile is not solved.
The first visible repair reduced failures but plateaued.
The guarded weight retrain did not move the plateau.
The remaining failures are not a simple horizon-40 artifact.
```

Next candidate source should be the remaining Stage 7 max-plies families from
`stage7_guarded_retry_target_25_h80.json`, not another broad score bonus.
Likely diagnosis to verify before more code:

```text
post-drive-repair continuation gap / loop recurrence
or box_shrink reward distribution mismatch on Box_Small/Box_Medium/Edge_Fence_Deep
```

## Stage 7 Local Repair And Remaining Conversion Gap

Follow-up implementation made the Stage 7 sandbox providers visible early
enough for the one-ply evaluator:

```text
_materialize_stage7_sandbox_providers(...)
```

This is an activation adapter for compiled, opt-in visible terminals only. It
does not directly choose a move or request a provider; it makes the terminal
suggestions compete with the learned actuator suggestions before diagnostic
early-stop can stabilize.

The Stage 7 drive-repair terminal was also broadened from post-reply-only to a
scoped initial/local box-shrink repair:

```text
terminal.krk.stage7_drive_repair
scope: active_landmark_label == box_shrink
causal_status: sandbox_opt_in
direct_request: false
```

The visible contract remains:

```text
box_shrink_drive_repair_available or compact broken-cut support context
enemy_king_not_at_edge
rook_safe
rook_safe_after_move
rook_safe_after_worst_reply
no_draw_after_worst_reply
box_area_decreases_after_move or safe cut/check repair or king_support_repair
```

This fixed the local Stage 7 decision on the harder guardrail profile:

```text
artifact: reports/structural_candidates/stage7_eval_flag_wiring_25_h80.json
local: 25/25 improved, 21/25 optimal
previous: 21/25 improved, 16/25 optimal
```

Conversion did not solve:

```text
artifact: reports/structural_candidates/stage7_king_support_repair_25_h80.json
conversion: 12/25 mate, 13/25 max_plies
shadow candidates: 33
```

I tested several narrow visible refinements:

```text
edge-corner king support step: regressed the target, reverted
initial/local visible box-shrink repair: fixed local one-ply quality
post-reply drive-repair second use: exposed remaining continuation gap
box-shrink-first priority and lateral-transfer tie-breaks: no conversion lift
king-support repair mode: no conversion lift
compiled support adapters: no useful firing on this topology/profile
```

Current interpretation:

```text
Stage 7 local box-shrink can now be made semantically aligned.
Stage 7 conversion is still not solved.
The remaining failures are downstream post-box-shrink continuation failures,
not merely bad one-ply box-shrink move selection.
```

Do not promote Stage 7 yet. The next repair should be candidate-driven and
should classify whether the remaining post-reply families need:

```text
1. a post-box-shrink continuation overlay,
2. a Stage 7 handoff into existing drive/edge providers with real adapter firing,
3. or a broader full-KRK continuation stage rather than more box-shrink patches.
```

## Stage 7 Topology-Vs-Weight Diagnosis Artifact

Per the Plasticity Balance Protocol, I stopped local box-shrink tuning and added
a replay-free diagnosis artifact:

```text
script: scripts/diagnose_stage7_post_box_continuation.py
json: reports/structural_candidates/stage7_post_box_continuation_diagnosis.json
md: reports/structural_candidates/stage7_post_box_continuation_diagnosis.md
```

It extracts one record per Stage 7 sample:

```text
start_fen
stage7 move
post_own_move_fen
black_reply
post_reply_fen
reward_confirmed
visible_box_area_decreased_after_own_move
visible_box_area_not_increased_after_reply
fence_or_cut_preserved
rook_safe_after_reply
enemy_king_mobility_delta
selected_successor / selected_move
conversion_result
failure_classes
```

Current diagnosis from `stage7_eval_flag_wiring_25_h80.json`:

```text
Stage 7 status: local_valid_composition_quarantined
Records: 25
Conversion failures: 13
Unique failed post-reply states: 4

Buckets:
  box_shrink_visible_confirmed_mate: 2
  box_shrink_visible_confirmed_max_plies: 13
  reward_confirmed_no_visible_shrink_mate: 10

Failure class:
  selected_successor_miscalibrated: 13
```

Candidate updates:

```text
cand.krk.box_shrink.handoff_role_refinement.v1
  status: needs_bounded_forced_provider_probe
  role: krk.post_box_shrink_continuation
  diagnosis:
    post_box_shrink_continuation_gap
    topology_present_untrained_or_miscalibrated

cand.krk.box_shrink.overlay_quarantine_confirmed.v1
  status: local_valid_composition_quarantined
```

Runtime note: broad forced-provider / legal-first probes over the four failed
post-reply states were too slow under current playout settings, so this artifact
marks the bounded forced-provider/M3 probe as the next targeted step rather than
pretending it completed. This keeps the causal boundary clean: no new topology,
no Stage 8 training, no Stage 7 promotion.

## Stage 7 Bounded Forced-Provider Probe

Added a bounded, non-causal topology-vs-weight probe:

```text
script: scripts/probe_stage7_post_box_continuation.py
first-move probe:
  reports/structural_candidates/stage7_post_box_forced_provider_firstmove_probe.json
h40 forced playout:
  reports/structural_candidates/stage7_post_box_forced_provider_h40_probe.json
unresolved h80 forced playout:
  reports/structural_candidates/stage7_post_box_forced_provider_unresolved_h80_probe.json
```

The first-move-only probe was cheap and showed all six existing providers can
propose legal first moves from all four unique failed post-reply families:

```text
krk.stage0_basin: available 4/4
krk.edge_trap_close: available 4/4
krk.edge_trap_wrong_tempo: available 4/4
krk.edge_trap_enemy_between: available 4/4
krk.drive_to_edge: available 4/4
krk.fence_established: available 4/4
```

The h40 forced-playout probe found two state families where existing providers
can convert when granted first ownership:

```text
state.ff6652c8832c
  post-reply FEN: 8/8/8/8/4R3/2k5/4K3/8 w - - 2 2
  forced krk.drive_to_edge -> mate in 7, first move e4h4

state.ac0b7ed500ea
  post-reply FEN: 8/8/8/4k3/R7/8/3K4/8 w - - 2 2
  forced krk.fence_established -> mate in 13, first move d2e3
```

The remaining two families did not convert under any tested existing provider
even at h80:

```text
state.0afbf11aa123
  post-reply FEN: 8/8/8/8/4K3/4R3/3k4/8 w - - 2 2
  h80 forced providers: all max_plies

state.38aed2f35911
  post-reply FEN: 8/8/8/R7/4k3/8/8/3K4 w - - 2 2
  h80 forced providers: all max_plies
```

Diagnosis:

```text
Stage 7 is mixed.

Two failed families are topology-present but miscalibrated:
  existing providers can solve if ownership is forced.

Two failed families are unresolved by current providers under h80:
  possible provider_capacity_missing, horizon_limited, or missing
  post-box-shrink continuation concept.
```

Implication:

```text
Do not keep tuning the local box-shrink first move.
Do not train Stage 8.
Do not promote Stage 7.

Next safe repair is candidate-driven:
  1. create/validate a visible post_box_shrink_continuation role or support
     adapter for the two solvable families;
  2. separately classify the two h80-unresolved families before adding a new
     overlay provider.
```

## Stage 7 Support Adapter Wiring Fix

While validating the existing `box_shrink_to_drive_repair -> drive_to_edge`
support sandbox, I found a runtime wiring bug:

```text
_record_explicit_role_provider_support() expected env["__graph__"]
choose_move_details() did not provide it
adapter_fire_count stayed at 0 even when visible role terms matched
```

Fix:

```text
scripts/test_krk_landmark_progress.py now includes "__graph__": graph in the
diagnostic runtime env.
```

After the fix, the existing support adapter fired, but it did not improve the
Stage 7 smoke:

```text
artifact: reports/structural_candidates/stage7_support_adapter_graphfix_10_h80.json
result: 5 mate / 5 max_plies
adapter_fire_count: 12
adapter_supported_provider_by_outcome:
  krk.drive_to_edge:max_plies: 12
```

I then compiled a narrower support proposal requiring
`white_king_support_available`, because that term distinguishes the h40 forced
`drive_to_edge` converting family from several non-converting families:

```text
proposal:
  reports/structural_candidates/stage7_box_shrink_drive_support_available_proposal.json
topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_support_drive_support_available_w005.json
smoke:
  reports/structural_candidates/stage7_support_available_adapter_10_h80.json
```

Narrowed result:

```text
result: 5 mate / 5 max_plies
adapter_fire_count: 9
adapter_supported_provider_by_outcome:
  krk.drive_to_edge:max_plies: 9
```

Interpretation:

```text
The support adapter path is now wired and inspectable.
The current drive support candidate is not the Stage 7 solution.
It should remain sandbox/quarantined, not promoted.
```

## Stage 7 Family-Split Continuation Diagnosis

Added a non-causal family diagnosis artifact:

```text
script:
  scripts/diagnose_stage7_post_box_families.py
json:
  reports/structural_candidates/stage7_post_box_family_diagnosis.json
md:
  reports/structural_candidates/stage7_post_box_family_diagnosis.md
```

It splits the four unique post-box-shrink failed families into:

```text
existing_provider_can_convert_if_family_role_selects_it: 2
unresolved_by_existing_forced_providers_at_h80: 2
```

Family-specific candidates:

```text
state.ff6652c8832c
  best forced provider: krk.drive_to_edge
  candidate: cand.krk.box_shrink.family_ff6652c8832c.drive_to_edge_adapter.v1
  status: sandbox_ready_if_terms_separate

state.ac0b7ed500ea
  best forced provider: krk.fence_established
  candidate: cand.krk.box_shrink.family_ac0b7ed500ea.fence_established_adapter.v1
  status: sandbox_ready_if_terms_separate

state.0afbf11aa123
  h80 forced providers: all max_plies
  h40 filtered legal-first: 7 moves tested, 5 max_plies, 2 draw, 0 mate
  candidate: cand.krk.box_shrink.family_0afbf11aa123.unresolved_continuation.v1
  status: needs_legal_first_or_longer_horizon_sweep

state.38aed2f35911
  h80 forced providers: all max_plies
  h40 filtered legal-first: 17 moves tested, 14 max_plies, 3 draw, 0 mate
  candidate: cand.krk.box_shrink.family_38aed2f35911.unresolved_continuation.v1
  status: needs_legal_first_or_longer_horizon_sweep
```

The h80 legal-first continuation probe for the two unresolved families was
stopped because it exceeded the bounded diagnostic budget. This should not be
treated as evidence of conversion. It means the next unresolved-family probe
needs either stronger filtering, continuation trace profiling, or a cheaper
oracle/tablebase-style classifier before expensive h80/h120 sweeps.

Decision:

```text
Do not add a broad post-box-shrink overlay.
Do not run M3 on the current broad drive adapter.
Do not promote Stage 7.
Do not train Stage 8.

Proceed with role factorization:
  family-specific adapters only if visible terms separate;
  unresolved families require targeted legal-first / longer-horizon audit
  before declaring provider capacity missing.
```

## Stage 7 Family-Specific Adapter Attempt

Added a non-causal proposal generator:

```text
script:
  scripts/propose_stage7_family_support_adapters.py
proposal set:
  reports/structural_candidates/stage7_family_support_adapter_proposals.json
split proposals:
  reports/structural_candidates/stage7_family_support_adapter_proposals/
```

It only emits sandbox-ready adapters when current visible terms separate a
forced-success family from non-converting families. Result:

```text
cand.krk.box_shrink.family_ff6652c8832c.drive_to_edge_visible_support.v1
  provider: krk.drive_to_edge
  status: sandbox_ready
  required terms:
    box_area_large
    box_shrink_drive_repair_available
    drive_to_edge_affordance_after_box_shrink
    enemy_king_edge_distance_bin
    king_support_improvement_move_exists
    white_king_support_available

cand.krk.box_shrink.family_ac0b7ed500ea.fence_established_visible_support.v1
  provider: krk.fence_established
  status: needs_more_terms
  reason:
    visible terms also match state.38aed2f35911
```

The sandbox compiler now supports an explicit, opt-in
`--augment-role-provider-ids` mode so a visible role can license a new provider
inside a sandbox without adding unsafe direct role->provider SUB edges. This was
added for future fence-family experiments, but was not used for promotion.

Compiled and tested the one sandbox-ready drive-family adapter:

```text
topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_family_ff_drive_support_w005.json
default-off equivalence:
  reports/structural_candidates/stage7_family_drive_default_off_equiv_5_h40.json
adapter-on smoke:
  reports/structural_candidates/stage7_family_drive_adapter_10_h80.json
outcome:
  reports/structural_candidates/stage7_family_drive_adapter_outcome.json
```

Default-off equivalence passed:

```text
equivalent: true
adapter_fire_count: 0
```

Adapter-on smoke did not improve conversion:

```text
result: 5 mate / 5 max_plies
adapter_fire_count: 9
adapter_supported_provider_by_outcome:
  krk.drive_to_edge:max_plies: 9
```

Candidate update:

```text
cand.krk.box_shrink.family_ff6652c8832c.drive_to_edge_visible_support.v1
  status: overbroad_or_misdirected_candidate
  promotion_status: quarantined
  diagnosis:
    adapter_fires_without_conversion
    do_not_run_m3_on_this_adapter
    needs_family_specific_or_move_shape_terms
```

Conclusion:

```text
Provider-level support adapters are still too coarse for Stage 7.
The next repair should not be a stronger provider bonus.
The next useful evidence is move-shape-level separation or a cheaper
continuation oracle for the two unresolved families.
```

## Stage 7 move-shape-gated adapter follow-up

Added move-shape/post-move constraints to the explicit role-provider support
adapter path. Constrained adapters are no longer reported at provider-license
time; they become visible only when the candidate move itself confirms the
required move-shape/post-move terms. This preserves the rule:

```text
visible role may support a provider,
but a move-shape-constrained adapter only supports a concrete candidate move
when that move confirms visible terms.
```

Compiled a constrained drive-family sandbox:

```text
topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_family_ff_drive_move_shape_support_w005.json
default-off equivalence:
  reports/structural_candidates/stage7_family_drive_moveshape_default_off_equiv_5_h40.json
adapter-on smoke:
  reports/structural_candidates/stage7_family_drive_moveshape_adapter_10_h80.json
targeted forced-family probe:
  reports/structural_candidates/stage7_family_ff_drive_moveshape_targeted_probe.json
outcome:
  reports/structural_candidates/stage7_family_drive_moveshape_adapter_outcome.json
```

Default-off equivalence passed:

```text
equivalent: true
adapter_fire_count: 0
```

Adapter-on smoke was neutral and did not fire:

```text
result: 5 mate / 5 max_plies
adapter_fire_count: 0
```

Targeted forced replay of the known drive-convertible family did fire:

```text
state.ff6652c8832c
forced provider: krk.drive_to_edge
first move: e4h4
forced playout: mate
targeted_adapter_fire_count: 3
matched_move_shape_terms:
  candidate_is_rook_transfer
  rook_lateral_transfer
  rook_to_edge_file
matched_post_move_terms:
  rook_safe_after_move
direct_request: false
```

Candidate update:

```text
cand.krk.box_shrink.family_ff6652c8832c.drive_to_edge_visible_support.v1
  status: wired_but_arbitration_dominated
  promotion_status: proposed
  diagnosis:
    adapter_did_not_fire_under_normal_routing
    adapter_fires_under_forced_provider
    forced_provider_converts
    provider_score_arbitration_dominates_visible_support
```

Interpretation:

```text
The adapter is ReCoN-visible and correctly move-shape-gated.
It is not composition-sufficient because normal routing is dominated by
high-scoring stage0_basin candidates before the drive provider can matter.
Do not increase broad support. The next diagnosis is stage0 fallback
arbitration or candidate-local weight calibration under the Plasticity Balance
Protocol.
```

## Stage 7 arbitration / weight-vs-topology diagnosis

Added a non-causal arbitration diagnostic:

```text
script:
  scripts/diagnose_stage7_arbitration.py
targeted artifact:
  reports/structural_candidates/stage7_family_ff_arbitration_diagnosis.json
all-family artifact:
  reports/structural_candidates/stage7_arbitration_diagnosis_all_families.json
```

The diagnostic compares normal routing against forced-provider candidates and
records score gaps, adapter visibility, known forced outcomes, and the support
needed to overtake the normally selected provider.

Key result for the drive-convertible family:

```text
state.ff6652c8832c
normal selected:
  provider: krk.stage0_basin
  move: e4e8
  score: 33.6848

forced provider:
  provider: krk.drive_to_edge
  move: e4h4
  score: 0.2136
  known outcome: mate in 7
  adapter fired: true
  adapter support: 0.05
  required support to overtake selected provider: 33.4712
  support / required ratio: 0.00149
```

All-family summary:

```text
forced_provider_can_convert: 2
provider_score_scale_mismatch: 1
adapter_wired_and_visible_under_forced_provider: 1
no_candidate_support_available: 7
adapter_not_visible_for_forced_provider: 11
```

Second forced-success family:

```text
state.ac0b7ed500ea
normal selected:
  provider: krk.stage0_basin
  move: a4a8

forced provider:
  provider: krk.fence_established
  move: d2e3
  known outcome: mate
  score gap to selected: 15.099
  adapter fired: false
```

Candidate update:

```text
cand.krk.box_shrink.stage0_fallback_arbitration.v1
  status: needs_weight_or_score_normalization_probe
  diagnosis:
    forced_provider_can_convert
    adapter_wired
    visible_support_too_small_relative_to_provider_score_gap
  next_action:
    run_bounded_candidate_local_calibration_or_score_scale_audit_before_new_topology
```

Interpretation:

```text
Stage 7 should remain local_valid_composition_quarantined.
The next repair is not new topology and not a broad stage0 penalty.
First run a bounded score-scale / candidate-local calibration probe:
  if score normalization or local calibration allows the existing converting
  providers to win without guardrail regression, classify as parameter or
  arbitration calibration;
  if not, only then consider a narrow continuation overlay.
```

## Stage 7 score-calibration plan

Added a non-causal calibration planner:

```text
script:
  scripts/plan_stage7_score_calibration.py
artifact:
  reports/structural_candidates/stage7_score_calibration_plan.json
```

Result:

```text
next_phase: bounded_score_normalization_probe
candidate_count: 2
status_counts:
  score_scale_normalization_probe_ready: 1
  needs_visible_support_before_calibration: 1
growth_status:
  growth_blocked_by_weight_vs_topology_diagnosis
```

Candidate split:

```text
state.ff6652c8832c / krk.drive_to_edge
  status: score_scale_normalization_probe_ready
  reason:
    adapter fires
    forced provider converts
    additive support required is too large
    provider scores are not comparable across skills

state.ac0b7ed500ea / krk.fence_established
  status: needs_visible_support_before_calibration
  reason:
    forced provider converts
    no visible adapter/support exists yet
```

Growth governor blocks:

```text
promote_stage7
train_stage8
add_broad_stage0_penalty
new_post_box_topology_before_calibration_probe
```

Next safe implementation target:

```text
bounded_score_normalization_probe
```

It should remain sandbox-only and compare alternative score semantics, such as
provider-local normalization or role-owned arbitration, without changing default
runtime behavior. If normalization lets existing converting providers win and
guardrails hold, Stage 7 is primarily a calibration/arbitration problem. If not,
then a narrow post-box continuation overlay becomes better justified.

## Stage 7 score-normalization probe

Added a replay-only score-normalization probe:

```text
script:
  scripts/probe_stage7_score_normalization.py
artifact:
  reports/structural_candidates/stage7_score_normalization_probe.json
```

It compares:

```text
raw:
  current runtime winner
adapter_role_priority:
  non-causal replay where adapter-visible role ownership beats raw cross-skill score
forced_success_oracle:
  diagnostic upper bound from known forced-provider mates; never causal
```

Result:

```text
record_count: 4
raw:
  krk.stage0_basin selected in all 4 families
adapter_role_priority:
  selects krk.drive_to_edge -> mate for state.ff6652c8832c
forced_success_oracle:
  selects krk.drive_to_edge -> mate for state.ff6652c8832c
  selects krk.fence_established -> mate for state.ac0b7ed500ea
```

Candidate update:

```text
cand.krk.box_shrink.score_normalized_role_arbitration.v1
  status: role_owned_score_normalization_sandbox_candidate
  next_action: sandbox_role_owned_arbitration_with_guardrails
  hard blocks:
    do_not_promote_stage7
    do_not_train_stage8
    do_not_make_oracle_choice_causal
    do_not_use_score_normalization_without_guardrails
```

Interpretation:

```text
For the drive family, visible role-owned arbitration is enough in replay.
For the fence family, the oracle can identify a converting provider, but no
visible support/adapter exists yet, so a fence-family visible-support candidate
must be derived before any calibration.

The next causal experiment, if attempted, should be narrow:
  role-owned score normalization for adapter-visible candidates only,
  sandbox-only,
  default-off,
  guarded by Stage 7 target + Stage 6/5/1 and bridge/M1-M4 guardrails.
```

## Stage 7 role-owned score-normalization sandbox

Implemented a default-off sandbox runtime flag:

```text
--enable-role-owned-score-normalization
```

Semantics:

```text
Only suggestions with visible_role_provider_support_adapter may enter the
role-owned arbitration set.
The adapter must be enabled, direct_request must be false, and move_shape_gated
must be true.
Provider-level adapters without move-shape confirmation are ignored.
The raw selected provider/move/score are preserved in trace metadata.
No oracle information is used.
```

Default-off check:

```text
artifact:
  reports/structural_candidates/stage7_role_owned_default_off_equiv_5_h40.json
result:
  equivalent: true
  adapter_fire_count: 0
```

Random 10-sample smoke:

```text
artifact:
  reports/structural_candidates/stage7_role_owned_adapter_10_h80.json
result:
  5 mate / 5 max_plies
  role_owned_score_normalization_selected_count: 0
```

Interpretation:

```text
The random smoke did not encounter a state where the move-shape-gated adapter
was visible, so it is a non-regression check rather than a target success.
```

Targeted normal playout from the known drive-convertible family:

```text
artifact:
  reports/structural_candidates/stage7_ff_role_owned_targeted_playout.json
state:
  state.ff6652c8832c
  8/8/8/8/4R3/2k5/4K3/8 w - - 2 2
result:
  mate in 7
first trace move:
  e4h4
raw selected before role-owned arbitration:
  krk.stage0_basin / e4e8 / score 33.6848
role-owned selected:
  krk.drive_to_edge / e4h4 / score 0.2136
```

Note:

```text
The existing play_to_mate first_successor field captures the second White move
when no forced successor is active. For the targeted first-move evidence, use
the trace event at ply 0.
```

Current status:

```text
role-owned score normalization is a plausible sandbox candidate for the drive
family only.
It is not enough for the fence family because no visible support exists there.
Stage 7 remains local_valid_composition_quarantined.
```

## Stage 7 family-split continuation diagnosis

Fence-family support term separation:

```text
artifact:
  reports/structural_candidates/stage7_fence_support_term_separation.json
target:
  state.ac0b7ed500ea
  forced provider krk.fence_established -> mate, first move d2e3
result:
  separable after adding post-move geometry vocabulary
key separating term:
  white_king_and_rook_same_rank_side_after_move
example separating combo:
  move_shape_terms:king_moves_toward_enemy
  post_move_terms:white_king_and_rook_same_rank_side_after_move
candidate status:
  separable_with_existing_visible_terms
hard block:
  do_not_promote_stage7
```

Interpretation:

```text
The fence-convertible family now has a visible non-hash separator: a king move
toward the enemy that leaves the white king and rook on the same rank-side of
the black king. The previous false positive state.38aed2f35911 has split
rank-side geometry instead.

This is still non-causal. The next safe step is a sandbox-only, move-shape
gated support adapter for this fence-family candidate, followed by default-off
equivalence and Stage 7 target/guardrail validation.
```

Unresolved-family legal-first action sweep:

```text
artifact:
  reports/structural_candidates/stage7_post_box_unresolved_legal_first_h40_h80_action_probe.json
states:
  state.0afbf11aa123
  state.38aed2f35911
tested:
  action-filtered legal first moves at horizons 40 and 80
filters:
  checking_line_created
  rook_to_checking_line
  box_area_decreases_after_move
  king_moves_toward_enemy
  king_moves_toward_rook_support
result:
  states_with_any_legal_first_mate: 0
  h40: 4 max_plies, 2 draw
  h80: 4 max_plies, 2 draw
diagnosis:
  no_tested_legal_first_conversion_at_horizon
candidate status:
  needs_more_terms_or_capacity_probe
```

Interpretation:

```text
The two unresolved families should not be called solved by existing providers.
The action-filtered legal-first subset did not convert by h80, and some moves
draw immediately. This supports keeping Stage 7 quarantined and blocking broad
post-box-shrink adapters.

Next safe options:
  add missing geometric/durability terms and rerun separation,
  or sandbox a narrow post-box continuation capacity probe.

Do not:
  promote Stage 7,
  train Stage 8,
  run M3 on the broad drive adapter,
  compile a fence adapter from the current non-separating terms.
```

## Stage 7 fence-family sandbox adapter

Compiled a move-shape-gated fence-family support adapter after adding the
same-rank-side post-move term.

Important executor-safety finding:

```text
--augment-role-provider-ids is not default-off safe for targeted forced
continuation. It changes role/provider license arbitration even when explicit
support is disabled.
```

Fix:

```text
create_krk_role_provider_support_adapter can now read the confirmed role
payload from krk_successor_role_affordances when the target provider is not in
the role's provider_skill_ids.

This lets sandbox adapters support a provider without mutating the visible
role's provider list.
```

Corrected sandbox:

```text
topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_family_ff_drive_ac_fence_move_shape_support_noaugment_w005.json
proposal:
  reports/structural_candidates/stage7_family_ac_fence_support_proposal.json
default-off:
  reports/structural_candidates/stage7_family_ac_fence_noaugment_default_off_equiv_5_h40.json
targeted forced replay:
  reports/structural_candidates/stage7_family_ac_fence_noaugment_targeted_probe.json
adapter-on smoke:
  reports/structural_candidates/stage7_family_ac_fence_noaugment_adapter_10_h80.json
outcome:
  reports/structural_candidates/stage7_family_ac_fence_noaugment_adapter_outcome.json
```

Default-off equivalence:

```text
equivalent: true
adapter_fire_count: 0
```

Targeted forced replay:

```text
state: state.ac0b7ed500ea
provider: krk.fence_established
first move: d2e3
forced playout: mate in 13
adapter:
  enabled: true
  direct_request: false
  move_shape_gated: true
  matched_move_shape_terms:
    king_moves_toward_enemy
  matched_post_move_terms:
    box_area_not_increased_after_move
    rook_safe_after_move
    white_king_and_rook_same_rank_side_after_move
```

Adapter-on random smoke:

```text
10 samples, h80:
  5 mate / 5 max_plies
  adapter_fire_count: 0
  role_owned_score_normalization_selected_count: 0
```

Interpretation:

```text
The corrected adapter is wired and traceable for the target family, but the
small random smoke did not encounter the shape. It is a sandbox candidate, not
a promoted repair. Next validation should be targeted or paired against known
post-box family states before any M3 warmup or broader Stage 7 promotion.

Candidate status:
  wired_but_arbitration_dominated
  adapter_did_not_fire_under_normal_routing
  adapter_fires_under_forced_provider
  forced_provider_converts

This mirrors the drive-family result: visible support can identify the right
provider/move under forced ownership, but normal routing is still dominated by
the existing fallback/provider score scale.
```

## Stage 7 bounded role-owned arbitration probe

Combined drive/fence arbitration evidence:

```text
arbitration:
  reports/structural_candidates/stage7_drive_fence_arbitration_diagnosis.json
score-normalization replay:
  reports/structural_candidates/stage7_drive_fence_score_normalization_probe.json
calibration plan:
  reports/structural_candidates/stage7_drive_fence_score_calibration_plan.json
runtime probe:
  reports/structural_candidates/stage7_drive_fence_role_owned_runtime_probe.json
```

Non-causal arbitration diagnosis:

```text
records: 2
forced_provider_can_convert: 2
adapter_wired_and_visible_under_forced_provider: 2
provider_score_scale_mismatch: 2
```

Score gap:

```text
state.ff6652c8832c:
  raw selected: krk.stage0_basin / e4e8 / score ~33.68
  adapter provider: krk.drive_to_edge / e4h4 / score ~0.21
  required additive support: ~33.47

state.ac0b7ed500ea:
  raw selected: krk.stage0_basin / a4a8 / score ~15.11
  adapter provider: krk.fence_established / d2e3 / score ~0.06
  required additive support: ~15.05
```

Interpretation:

```text
This is not a missing visible support problem for the two solvable families.
It is score-scale arbitration: provider scores are not comparable across skill
families, and bounded additive support is not a sensible repair.
```

Runtime sandbox result:

```text
role-owned score normalization enabled, no forced provider:
  state.ff6652c8832c -> krk.drive_to_edge -> mate
  state.ac0b7ed500ea -> krk.fence_established -> mate
```

Candidate update:

```text
cand.krk.box_shrink.score_normalized_role_arbitration.v1
  status: role_owned_score_normalization_sandbox_candidate
  next_action:
    paired Stage 7 target validation with role-owned arbitration enabled
    then Stage 6/5/1 and bridge/M1-M4 guardrails if target improves
```

Hard blocks remain:

```text
do_not_promote_stage7
do_not_train_stage8
do_not_make_oracle_choice_causal
do_not_use_score_normalization_without_guardrails
```

Paired 25-sample Stage 7 target validation:

```text
role-owned off:
  reports/structural_candidates/stage7_drive_fence_paired_off_25_h80.json
role-owned on:
  reports/structural_candidates/stage7_drive_fence_role_owned_on_25_h80.json
comparison:
  reports/structural_candidates/stage7_drive_fence_role_owned_on_vs_off_25_h80.json
```

Result:

```text
both modes:
  25/25 improved
  21/25 optimal
  12 mate / 13 max_plies
  shadow candidates: 35
  adapter_fire_count: 0
  role_owned_score_normalization_selected_count: 0
comparison:
  equivalent: true
```

Interpretation:

```text
Role-owned arbitration is default-safe on this 25-sample target slice, but the
sample did not hit either adapter-visible family. This is a neutral validation,
not a target improvement.

The next meaningful validation should be targeted/family-balanced sampling of
post-box states that include ff6652/ac0b7-like geometry plus the unresolved
0af/38 families. Do not promote Stage 7 from this neutral 25-sample result.
```

Family-balanced four-state validation:

```text
role-owned off:
  reports/structural_candidates/stage7_drive_fence_family_balanced_off_4_h80.json
role-owned on:
  reports/structural_candidates/stage7_drive_fence_family_balanced_on_4_h80.json
summary:
  reports/structural_candidates/stage7_drive_fence_family_balanced_summary.json
```

Result:

```text
role-owned off:
  state.ff6652c8832c -> krk.stage0_basin / e4e8 -> max_plies
  state.ac0b7ed500ea -> krk.stage0_basin / a4a8 -> max_plies
  state.0afbf11aa123 -> krk.stage0_basin / e3a3 -> max_plies
  state.38aed2f35911 -> krk.stage0_basin / d1e2 -> max_plies

role-owned on:
  state.ff6652c8832c -> krk.drive_to_edge / e4h4 -> mate in 7
  state.ac0b7ed500ea -> krk.fence_established / d2e3 -> mate in 13
  state.0afbf11aa123 -> krk.stage0_basin / e3a3 -> max_plies
  state.38aed2f35911 -> krk.stage0_basin / d1e2 -> max_plies
```

Interpretation:

```text
The role-owned candidate fixes exactly the two forced-provider-solvable
families and leaves the two unresolved families unchanged. This is the first
clean evidence that role-owned arbitration is not merely a broad Stage 7
score hack: it acts only where a visible move-shape support adapter fires.

Candidate status:
  family_balanced_sandbox_validated_for_solvable_families

Remaining Stage 7 work:
  the unresolved 0af/38 families remain unresolved_by_existing_forced_providers_at_h80
  and need a separate capacity/horizon/continuation diagnosis.
```

Smoke50 unique max-plies overfire check:

```text
families:
  reports/structural_candidates/stage7_smoke50_unique_maxplies_families.json
role-owned off:
  reports/structural_candidates/stage7_smoke50_unique_maxplies_role_owned_off_4_h80.json
role-owned on:
  reports/structural_candidates/stage7_smoke50_unique_maxplies_role_owned_on_4_h80.json
summary:
  reports/structural_candidates/stage7_smoke50_unique_maxplies_role_owned_summary.json
```

Result:

```text
four unique unrelated max-plies families:
  role-owned off: 0 mate / 4 max_plies
  role-owned on:  0 mate / 4 max_plies
  changed families: 0
  adapter overfire count: 0
```

Interpretation:

```text
No broader overfire was observed on the compact smoke50 max-plies set. The
candidate remains narrow: it fixes the known drive/fence-solvable families and
does not touch unrelated unresolved Stage 7 max-plies families.

Horizon policy:
  h80 was conservative and inherited from the earlier unresolved-family probe.
  Future smoke/overfire checks should default to h40 or h50, escalating only
  ambiguous unresolved/capacity classifications to h80.
```

H40 family-balanced confirmation:

```text
role-owned off:
  reports/structural_candidates/stage7_drive_fence_family_balanced_off_4_h40.json
role-owned on:
  reports/structural_candidates/stage7_drive_fence_family_balanced_on_4_h40.json
summary:
  reports/structural_candidates/stage7_drive_fence_family_balanced_h40_summary.json
```

Result:

```text
h40 preserves the h80 conclusion:
  role-owned off: 0 mate / 4 max_plies
  role-owned on:  2 mate / 2 max_plies

Fixed at h40:
  state.ff6652c8832c -> krk.drive_to_edge / e4h4 -> mate in 7
  state.ac0b7ed500ea -> krk.fence_established / d2e3 -> mate in 13

Unchanged at h40:
  state.0afbf11aa123 -> krk.stage0_basin / e3a3 -> max_plies
  state.38aed2f35911 -> krk.stage0_basin / d1e2 -> max_plies
```

## Stage 7 unresolved-family legal-first diagnosis

Artifacts:

```text
exhaustive h40:
  reports/structural_candidates/stage7_unresolved_legal_first_exhaustive_h40.json
state38 h50 escalation:
  reports/structural_candidates/stage7_state38_legal_first_exhaustive_h50.json
growth-monitor summary:
  reports/structural_candidates/stage7_unresolved_legal_first_summary.json
summarizer:
  scripts/summarize_stage7_unresolved_legal_first.py
```

Result:

```text
state.0afbf11aa123:
  legal-first exhaustive h40 found e4d4 -> mate in 5
  diagnosis: legal_first_action_selection_gap
  candidate status: sandbox_ready_if_terms_separate
  visible terms:
    candidate_is_king_move
    rook_safe_after_move
    box_area_not_increased_after_move
    black_king_escape_count_not_increased_after_move
    white_king_and_rook_same_rank_side_after_move
    white_king_file_opposition_distance_two_after_move

state.38aed2f35911:
  legal-first exhaustive h40: no mate
  legal-first exhaustive h50: no mate
  diagnosis: no_legal_first_conversion_under_current_graph
  candidate status: needs_longer_horizon_or_new_provider_probe
```

Interpretation:

```text
The previous unresolved bucket has split again:
  state.0afbf11aa123 is not missing capacity; a converting first move exists
  and the missing piece is visible action selection for a king opposition/support
  move after box shrink.

  state.38aed2f35911 remains unresolved under the current graph through h50.
  Do not call it permanently missing capacity yet, but it is now the strongest
  candidate for a deeper post-box continuation provider or higher-horizon probe.
```

## Stage 7 0af trace-role support candidate

Artifacts:

```text
proposal:
  reports/structural_candidates/stage7_family_0af_king_opposition_support_proposal.json
compiled topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_family_ff_drive_ac_fence_0af_king_support_trace_role_w005.json
family-balanced off/on:
  reports/structural_candidates/stage7_family_0af_trace_role_support_off_4_h40.json
  reports/structural_candidates/stage7_family_0af_trace_role_support_on_4_h40.json
summary:
  reports/structural_candidates/stage7_family_0af_trace_role_support_summary.json
```

Important correction:

```text
The first 0af role proposal directly licensed krk.edge_trap_close. That was too
causal: it changed downstream ac0b7 continuation even though the intended
adapter was not the first-move owner.

Corrected form:
  krk.post_box_king_opposition_repair is a trace/internal role.
  It does not directly license krk.edge_trap_close.
  edge_trap_close receives support only through the move-shape-gated adapter.
```

Family-balanced h40 result:

```text
off:
  0 mate / 4 max_plies

on:
  state.ff6652c8832c -> krk.drive_to_edge / e4h4 -> mate in 7
  state.ac0b7ed500ea -> krk.fence_established / d2e3 -> mate in 13
  state.0afbf11aa123 -> krk.edge_trap_close / e4d4 -> mate in 5
  state.38aed2f35911 -> krk.stage0_basin / d1e2 -> max_plies
```

Smoke50 overfire check:

```text
reports/structural_candidates/stage7_smoke50_unique_maxplies_0af_trace_role_off_4_h40.json
reports/structural_candidates/stage7_smoke50_unique_maxplies_0af_trace_role_on_4_h40.json

result:
  off: 0 mate / 4 max_plies
  on:  0 mate / 4 max_plies
  changed families: 0
  adapter overfire count: 0
```

Candidate status:

```text
cand.krk.box_shrink.family_0afbf11aa123.king_opposition_edge_trap_support.v1
  status: family_balanced_sandbox_validated_for_0af
  remaining blocker: state.38aed2f35911
```

Stage 7 target smoke:

```text
pre-0af trace role:
  reports/structural_candidates/stage7_pre_0af_trace_role_target_smoke_25_h40.json
with 0af trace role:
  reports/structural_candidates/stage7_0af_trace_role_target_smoke_25_h40.json
comparison:
  reports/structural_candidates/stage7_0af_trace_role_target_smoke_comparison.json
```

Result:

```text
both modes:
  improved: 18/25
  optimal: 14/25
  worsened: 7/25
  mate: 4/25
  max_plies: 21/25
  shadow candidates: 28
```

Interpretation:

```text
The 0af candidate does not regress this broader target smoke, but it also does
not improve it. This target set exposes a wider Stage 7 local/composition
problem: visible_contract_without_reward appears in 7/25 samples and conversion
is still weak. Do not promote Stage 7 from this result.
```

Growth-monitor readout:

```text
reports/structural_candidates/stage7_target_smoke_growth_monitor_summary.json

dominant target-smoke buckets:
  visible_contract_without_reward: 7/25
  reward_visible_fence_aligned_survived: 18/25
    mate: 4
    max_plies: 14

shadow triggers:
  repeated_conversion_failure: 14
  high_score_conversion_failure: 13
  route_conflict: 1

dominant state signatures:
  state.7b116c49a009: 20 shadow candidates
  state.7cab65617cd8: 6 shadow candidates
  state.dcea518838ac: 2 shadow candidates
```

Next candidate-driven work:

```text
1. Family-split state.7b116c49a009 and state.7cab65617cd8.
2. Audit visible_contract_without_reward samples before adding causal support.
3. Keep state.38aed2f35911 as the deeper continuation/capacity probe.
```

## Stage 7 target-smoke dominant family split

Artifacts:

```text
source-family extraction:
  reports/structural_candidates/stage7_target_smoke_source_family_diagnosis.json
h40 forced/legal-first probe:
  reports/structural_candidates/stage7_target_smoke_source_families_probe_h40.json
h50 unresolved escalation:
  reports/structural_candidates/stage7_target_smoke_unresolved_h50.json
h40/h50 summary:
  reports/structural_candidates/stage7_target_smoke_source_families_legal_first_h40_h50_summary.json
candidate summary:
  reports/structural_candidates/stage7_target_smoke_source_family_summary.json
```

Result:

```text
state.7cab65617cd8 -> post-reply state.1b912dd78357:
  source FEN:     7k/8/8/8/R7/8/5K2/8 w - - 0 1
  post-reply FEN: 6k1/R7/8/8/8/8/5K2/8 w - - 2 2
  legal-first f2e2 -> mate in 19
  f2e2 is not present in current provider suggestions
  diagnosis: legal_first_action_provider_gap

state.dcea518838ac -> post-reply state.2942b4d1224f:
  source FEN:     4k3/R7/K7/8/8/8/8/8 w - - 0 1
  post-reply FEN: 3k4/7R/K7/8/8/8/8/8 w - - 2 2
  no legal-first conversion at h40/h50
  diagnosis: no_legal_first_conversion_under_current_graph_h40_h50

state.7b116c49a009 -> post-reply state.73530ec4170e:
  source FEN:     4k3/8/8/8/R7/8/4K3/8 w - - 0 1
  post-reply FEN: 3k4/R7/8/8/8/8/4K3/8 w - - 2 2
  no legal-first conversion at h40/h50
  diagnosis: no_legal_first_conversion_under_current_graph_h40_h50
```

Interpretation:

```text
The dominant target-smoke failures are no longer one bucket:
  one family needs a narrow king-support action provider or training target
  because the converting move is absent from existing suggestions;

  two families need deeper h80/h120 or tablebase-style capacity probes before
  we call them missing topology.

Do not add another broad adapter from this evidence.
```

## Stage 7 trace-role + king-tempo sandbox probe

Artifacts:

```text
compiled king-tempo topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_0af_trace_role_plus_king_tempo_w25.json

compiled full Stage 7 sandbox topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_trace_role_full_sandbox_w25_28_30.json

target source-family probe:
  reports/structural_candidates/stage7_source_families_king_tempo_probe_h40.json

full sandbox target profile:
  reports/structural_candidates/stage7_trace_role_full_sandbox_25_h40.json
  reports/structural_candidates/stage7_trace_role_full_sandbox_25_h40_analysis.md

family-split diagnosis:
  reports/structural_candidates/stage7_full_sandbox_post_box_diagnosis.json
  reports/structural_candidates/stage7_full_sandbox_failed_families_forced_h40_h50.json
  reports/structural_candidates/stage7_full_sandbox_state6ed_legal_first_h50.json
  reports/structural_candidates/stage7_full_sandbox_family_split_candidate_update.json
```

Result:

```text
Target source families, h40:
  state.7cab65617cd8 -> krk.stage7_king_tempo f2e2 -> mate
  state.dcea518838ac -> krk.stage7_king_tempo a6a5 -> max_plies
  state.7b116c49a009 -> krk.stage7_king_tempo e2f2 -> max_plies

Current 25-sample Stage 7 target, h40, full sandbox:
  local improved: 25/25
  local optimal:  21/25
  conversion:     16/25 mate, 9/25 max_plies
  shadows:        25

Remaining failures:
  krk.stage7_drive_repair selected 9 times
  krk.stage7_drive_repair produced 9 max_plies
```

Family split:

```text
state.ff6652c8832c:
  runtime selected stage7_drive_repair e2e3 -> max_plies
  forced drive_to_edge e4h4 -> mate at h40/h50
  diagnosis: existing provider can solve if family-specific role selects it

state.38aed2f35911:
  runtime selected stage7_drive_repair a5b5 -> max_plies
  forced stage0_basin / edge_trap_close / edge_trap_enemy_between /
  fence_established d1e2 -> mate at h40/h50
  diagnosis: existing providers can solve under controlled ownership

state.6ed746a91c76:
  runtime selected stage7_drive_repair d2c1 -> max_plies
  no existing forced provider converted at h50
  no legal-first move converted at h50 under the current graph
  diagnosis: capacity-or-horizon gap candidate
```

Interpretation:

```text
The current broad stage7_drive_repair provider is overbroad. It fires in all
remaining full-sandbox failures and does not convert them.

Do not promote Stage 7 from this profile.
Do not run M3 warmup on the broad stage7_drive_repair path.
Do not add another broad Stage 7 score bonus.

Next repair should split the remaining problem:
  1. family-specific visible roles/adapters for the two controlled-provider
     success families;
  2. deeper capacity/horizon or narrow overlay diagnosis for state.6ed746a91c76.
```

## Stage 7 no-drive family refinement

I tested a narrower profile that removes the broad `stage7_drive_repair`
provider while keeping the existing trace-role/family adapters and
king-tempo/post-king-tempo providers:

```text
topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_trace_role_king_post_no_drive_w25_30.json

target artifact:
  reports/structural_candidates/stage7_trace_role_king_post_no_drive_25_h40.json

result:
  16/25 mate
  9/25 max_plies
  27 shadow candidates
```

The failures all moved back to `stage0_basin` fallback. A bounded
forced-provider probe split those failures:

```text
state.069e81a609ed:
  FEN: 8/8/8/8/7R/2k5/4K3/8 w - - 2 2
  forced drive_to_edge e2e3 -> mate at h40/h50

state.2cc0b3e1033a:
  FEN: 8/8/R7/8/2k5/8/8/3K4 w - - 2 2
  no existing forced provider converted at h50
  no legal-first move converted at h50 under the current graph

state.bace6f82b671:
  FEN: 8/8/8/R7/4k3/8/3K4/8 w - - 2 2
  no existing forced provider converted at h50
  no legal-first move converted at h50 under the current graph
```

I added a narrow, sandbox-only support adapter for the 069 family:

```text
proposal:
  reports/structural_candidates/stage7_family_069_drive_king_support_proposal.json

topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_trace_role_king_post_no_drive_069_support_w005.json

targeted probe:
  reports/structural_candidates/stage7_069_drive_king_support_targeted_probe_h40.json

target validation:
  reports/structural_candidates/stage7_069_drive_support_target_25_h40.json

candidate update:
  reports/structural_candidates/stage7_069_drive_support_candidate_update.json
```

Targeted result:

```text
state.069e81a609ed:
  selected krk.drive_to_edge / e2e3
  role-owned score normalization: true
  adapter direct_request: false
  mate in 9
```

25-sample target result:

```text
before:
  16/25 mate
  27 shadow candidates

after 069 adapter:
  19/25 mate
  21 shadow candidates
```

Interpretation:

```text
The 069 adapter is a validated sandbox candidate for its family and improves
the target slice. It is still opt-in and not promoted.

The two remaining no-drive families are stronger capacity-or-horizon
candidates: neither existing forced providers nor legal-first continuation
converted at h50 under the current graph.

Do not reintroduce the broad stage7_drive_repair provider.
Do not promote Stage 7 yet.
Next: either a deeper non-causal oracle/horizon audit for state.2cc/state.bace
or a narrow post-box continuation overlay candidate for exactly those families.
```

## Stage 7 bounded score-normalization probe

Following the expert guidance, I stopped adding Stage 7 topology and ran a
bounded arbitration/score-scale probe on the current no-drive + 069-support
sandbox.

Artifacts:

```text
arbitration:
  reports/structural_candidates/stage7_069_score_arbitration_diagnosis.json

score normalization:
  reports/structural_candidates/stage7_069_score_normalization_probe.json
  reports/structural_candidates/stage7_069_score_normalization_probe.md

target:
  reports/structural_candidates/stage7_069_drive_support_target_25_h40.json

guardrails:
  reports/structural_candidates/stage7_069_guard_stage6_drive_50_h40.json
  reports/structural_candidates/stage7_069_guard_stage5_fence_50_h40.json
  reports/structural_candidates/stage7_069_guard_stage4_wrong_tempo_50_h40.json
  reports/structural_candidates/stage7_069_guard_stage4_wrong_tempo_50_h40_disabled_control.json
```

Normalization modes:

```text
raw:
  current global score winner

bounded_tanh_support:
  tanh(raw_score / 10) + visible adapter support

provider_local_rank_support:
  provider-local rank baseline + visible adapter support

adapter_role_priority / role_owned_normalized:
  only visible move-shape-gated adapter candidates can override raw global
  score ownership

forced_success_oracle:
  non-causal upper bound from known forced-provider mates
```

Result:

```text
state.069e81a609ed:
  raw -> stage0_basin / e2d1
  bounded_tanh_support -> stage0_basin / e2d1
  provider_local_rank_support -> drive_to_edge / e2e3 -> mate
  adapter_role_priority -> drive_to_edge / e2e3 -> mate
  role_owned_normalized -> drive_to_edge / e2e3 -> mate

state.2cc0b3e1033a:
  provider_local_rank_support would select drive_to_edge / a6a8,
  but forced/controlled evidence says that path still max-plies.

state.bace6f82b671:
  provider_local_rank_support would select drive_to_edge / d2c3,
  but forced/controlled evidence says that path still max-plies.
```

Interpretation:

```text
Bounded score transforms do not solve the score-scale problem.
Naive provider-local rank normalization is too broad; it over-selects drive
providers in unresolved families.

The safe arbitration mechanism remains role-owned / adapter-priority ownership:
only visible move-shape-gated adapter candidates can override raw cross-provider
scores. This fixes the 069 family and does not touch unresolved families.
```

Target validation:

```text
Stage 7, 25 samples, h40:
  19/25 mate
  21 shadow candidates
```

Guardrails:

```text
Stage 6 drive_to_edge, 50 samples, h40:
  50/50 mate
  0 shadows

Stage 5 fence_established, 50 samples, h40:
  50/50 mate
  0 shadows

Stage 4 wrong_tempo, 50 samples, h40:
  enabled:  38/50 mate, 24 shadows
  disabled: 38/50 mate, 24 shadows
```

Conclusion:

```text
The 069 role-owned arbitration candidate improves Stage 7 and does not regress
Stage 6/5. The Stage 4 result is not a candidate regression because enabled and
disabled controls are identical on the same topology/profile.

Stage 7 remains local_valid_composition_quarantined. The remaining two
families, state.2cc0b3e1033a and state.bace6f82b671, should be treated as
capacity-or-horizon candidates for a narrow post-box continuation overlay or
deeper oracle/horizon analysis. Do not add broader score normalization.
```

## Stage 7 DTM oracle follow-up for remaining post-box families

I ran a non-causal KRK DTM oracle on the two remaining unresolved Stage 7
post-box families after the bounded score-normalization slice.

Artifacts:

```text
reports/structural_candidates/stage7_remaining_krk_dtm_oracle.json
reports/structural_candidates/stage7_remaining_dtm_candidate_summary.json
reports/structural_candidates/stage7_remaining_dtm_candidate_summary.md
reports/structural_candidates/stage7_post_box_training_seed_h40.json
reports/structural_candidates/stage7_post_box_training_seed_h40.jsonl
```

Result:

```text
state.2cc0b3e1033a / FEN 8/8/R7/8/2k5/8/8/3K4 w - - 2 2:
  DTM = 27 plies
  best winning moves include a6a5, a6d6, d1d2

state.bace6f82b671 / FEN 8/8/8/R7/4k3/8/3K4/8 w - - 2 2:
  DTM = 21 plies
  best winning moves include d2c3, a5b5, a5c5, a5g5, a5h5
```

Interpretation:

```text
Both remaining families are won well inside the h40 practical validation
horizon. Since the current graph failed under forced existing-provider and
legal-first-current-continuation probes, these are not unwinnable or merely
80-ply horizon cases.

The correct classification is:
  DTM-won within h40
  current continuation providers fail to exploit the won state
  narrow post-box continuation overlay/training candidate is justified

The DTM oracle remains non-causal diagnostic evidence only. It must not become
a runtime policy, hidden selector, or tablebase-backed controller.
```

Candidate summary:

```text
cand.krk.box_shrink.family_b6796dfb62ff.post_box_continuation_overlay_probe.v1
cand.krk.box_shrink.family_4e34ad0b2f29.post_box_continuation_overlay_probe.v1
```

Next safe implementation step:

```text
Sandbox a narrow post-box-shrink continuation overlay/training target for these
DTM-won unresolved families, with visible source terms and guardrails. Do not
change defaults, do not promote Stage 7 yet, and do not use DTM/tablebase data
at runtime.
```

Training seed generated:

```text
schema: stage7_post_box_training_seed.v1
causal_status: non_causal_training_evidence
examples: 2
positive seed moves:
  8/8/R7/8/2k5/8/8/3K4 w - - 2 2 -> a6a5, a6d6, d1d2
  8/8/8/R7/4k3/8/3K4/8 w - - 2 2 -> d2c3
runtime constraints:
  do_not_use_dtm_or_tablebase_at_runtime
  do_not_promote_without_guardrails
```

## Stage 7 post-box continuation sandbox result

I added an opt-in visible provider:

```text
terminal.krk.stage7_post_box_continuation
provider_skill_id: krk.stage7_post_box_continuation
role_id: krk.post_box_shrink_continuation
causal_status: sandbox_opt_in
runtime forbidden terms:
  tablebase_lookup
  dtm_oracle_move_selection
  state_hash_exception
```

The provider is compiled default-off into:

```text
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_post_box_continuation_sandbox.json
```

Default-off equivalence:

```text
base topology, 10 samples, h40:
  7 mate / 3 max_plies
  10 shadow candidates

post-box sandbox topology with provider disabled, 10 samples, h40:
  7 mate / 3 max_plies
  10 shadow candidates

equivalence result:
  equivalent = true
```

Provider-on smoke:

```text
broad first attempt, 25 samples, h40:
  17 mate / 8 max_plies
  25 shadow candidates
  result: regressed, overbroad

narrowed provider, 25 samples, h40:
  19 mate / 6 max_plies
  21 shadow candidates
  result: no regression versus the current 069 support baseline, but no gain
```

Selected-successor comparison against the current 069 support baseline:

```text
current 069 support baseline:
  edge_trap_close -> mate: 10
  stage0_basin -> max_plies: 6
  stage7_king_tempo -> mate: 4
  drive_to_edge -> mate: 3
  None -> mate: 2

narrow post-box provider enabled:
  edge_trap_close -> mate: 10
  stage7_post_box_continuation -> max_plies: 6
  stage7_king_tempo -> mate: 4
  drive_to_edge -> mate: 3
  None -> mate: 2
```

Interpretation:

```text
The narrowed provider is default-off safe and no longer causes broad damage,
but it only replaces stage0_basin ownership in the remaining failures. It does
not convert those failures.

This means the visible owner/first-move scaffolding is wired, but the provider
is expressive_but_untrained / capacity-limited under current hand-written
terms. Stage 7 remains local_valid_composition_quarantined.
```

Next safe step:

```text
Stop hand-tuning post-box move rules. Use the generated DTM seed as offline,
non-causal training evidence for a bounded M3/sandbox warmup of
krk.post_box_shrink_continuation. Keep validated providers frozen, keep the
candidate opt-in, and require Stage 7 target validation plus Stage 6/5/4/1
guardrails before any promotion.
```

## Stage 7 post-box M3 trainability assessment

I ran a non-causal M3 trainability assessment on the narrowed sandbox result.

Artifacts:

```text
reports/structural_candidates/stage7_post_box_narrow_continuation_diagnosis.json
reports/structural_candidates/stage7_post_box_narrow_continuation_diagnosis.md
reports/structural_candidates/stage7_post_box_m3_trainability_assessment.json
reports/structural_candidates/stage7_post_box_m3_trainability_assessment.md
```

Result:

```text
target_role: krk.post_box_shrink_continuation
target_provider: krk.stage7_post_box_continuation
visible_license_met: 6
candidate_provider_selected: 6
candidate_provider_selected_max_plies: 6
trainable_internal_edge_count: 0
activation_edge_count: 1 observe-only hub->terminal edge
probe_result: scripted_provider_selected_but_not_trainable_for_move_policy
```

Interpretation:

```text
This is not a useful candidate-local M3 warmup target as currently compiled.
The visible terminal can own the remaining families, but it has no internal
trainable move-selection edge. Updating its activation edge would not teach it
which continuation moves to play after the first DTM-seeded move.

The correct next step is to compile or train a learnable
krk.post_box_shrink_continuation provider from the offline seed, then run a
bounded candidate-local warmup/validation. Do not M3-warm the current scripted
terminal and do not promote Stage 7 from this result.
```

## Stage 7 post-box DTM trajectory seed

Because the narrowed provider selected good first moves but still failed the
continuation, I generated multi-ply offline DTM trajectories for the two
remaining unresolved families.

Artifacts:

```text
reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json
reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.jsonl
```

Result:

```text
trajectory_count: 2
white_training_step_count: 25

8/8/R7/8/2k5/8/8/3K4 w - - 2 2:
  DTM 27
  trajectory plies 27
  ended in checkmate true
  white training steps 14

8/8/8/R7/4k3/8/3K4/8 w - - 2 2:
  DTM 21
  trajectory plies 21
  ended in checkmate true
  white training steps 11
```

Interpretation:

```text
The remaining Stage 7 issue is now a candidate-provider learning problem, not
another visible first-move patch. A useful training target must cover the
post-box continuation sequence after the first correct move.

These trajectories are offline supervision only. They must not be read by
runtime policy as a tablebase, DTM oracle, or state-hash exception.
```

## Stage 7 post-box visible-term model probe

I trained a small sandbox visible-term scorer from the DTM trajectory seed.

Artifact:

```text
reports/structural_candidates/stage7_post_box_trajectory_provider_model.json
```

Model:

```text
schema: stage7_post_box_trajectory_provider_model.v1
causal_status: sandbox_model_non_promoted
model_kind: visible_term_log_odds_linear_scorer
positive legal-move labels: 53
negative legal-move labels: 426
features: 90
train positions: 25
train top-1 accuracy: 0.44
```

Interpretation:

```text
The simple visible-term linear model is not good enough to compile as a runtime
provider. It fails to identify the DTM-optimal move on more than half of the
offline training positions.

This is a useful bounded training result: the issue is not merely activation
or first-move ownership. The post-box continuation provider needs either a
richer learned representation or a proper actuator/overlay training run, not a
hand-written terminal and not a weak linear visible-term scorer.
```

Candidate status:

```text
cand.krk.box_shrink.post_box_continuation_overlay_probe.v1:
  status: trainable_candidate_but_linear_visible_term_probe_failed
  diagnosis:
    visible ownership works
    scripted provider has no trainable move-policy edges
    simple visible-term model underfits trajectory labels
  next action:
    train a narrow post_box_shrink_continuation overlay provider using the
    trajectory seed and normal actuator/provider machinery, then sandbox it
    with Stage 7 target validation and Stage 6/5/4/1 guardrails
```

## Stage 7 post-box learned overlay probe

I trained a normal baseline overlay learner from the DTM trajectory seed and
compiled it as:

```text
reports/structural_candidates/stage7_post_box_overlay_learner.pkl
reports/structural_candidates/stage7_post_box_overlay_learner_training.json
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_post_box_learned_overlay.json
```

Training summary:

```text
transition_count: 479
positive_transition_count: 53
negative_transition_count: 426
sensor_count: 15
overlay_actuator_count: 24
label: post_box_shrink_continuation
```

Runtime safety change:

```text
skill.krk.post_box_shrink_continuation is gated by:
  stage7_learned_post_box_continuation_enabled
  stage7_post_box_post_reply_context
  active_landmark_label == box_shrink

The learned provider is default-off and cannot participate in the initial
local box-shrink move.
```

Smoke results:

```text
learned overlay default-off, 10 samples, h40:
  local: 10/10 improved, 8/10 optimal
  conversion: 7 mate / 3 max_plies
  shadows: 10

learned overlay enabled, no owner bonus, 10 samples, h40:
  local: 10/10 improved, 8/10 optimal
  conversion: 7 mate / 3 max_plies
  shadows: 13

learned overlay enabled, owner bonus 0.01, 10 samples, h40:
  local: 10/10 improved, 8/10 optimal
  conversion: 7 mate / 3 max_plies
  shadows: 10
```

Interpretation:

```text
With the tiny owner bonus, the learned provider does win ownership in the three
remaining max-plies post-box families:
  state.2cc0b3e1033a -> krk.post_box_shrink_continuation
  state.bace6f82b671 -> krk.post_box_shrink_continuation

But those cases still max out. Therefore the bottleneck is no longer just
provider selection or score-scale arbitration. The learned overlay generated
from the current DTM trajectory seed is not composition-ready.
```

Candidate status:

```text
cand.krk.box_shrink.post_box_continuation_overlay_probe.v1:
  status: quarantined_after_bounded_overlay_training_probe
  diagnosis:
    default_off_safe
    ownership_possible
    trained_actuator_overlay_selected_but_conversion_failed
  next action:
    do not tune Stage 7 local box_shrink further
    do not increase owner bonus
    either ask for expert review or move to broader full-KRK/post-box
    continuation design rather than another micro-patch
```

## Stage 7 Plan Capsule candidate

The next Stage 7 step is no longer a local move-shape, score-arbitration, or
single-provider patch. Stage 7 remains:

```text
local_valid_composition_quarantined
```

The new non-causal candidate is:

```text
cand.krk.box_shrink.post_box_continuation_capsule.v1
capsule_id: krk.post_box_shrink_continuation
schema: plan_capsule_spec.v1
causal_status: non_causal
promotion_status: proposed
ttl_white_moves: 3
```

Artifacts:

```text
reports/structural_candidates/stage7_post_box_continuation_capsule_candidate.json
reports/structural_candidates/stage7_post_box_continuation_capsule_candidate.md
reports/structural_candidates/stage7_post_box_plan_capsule_audit.json
reports/structural_candidates/stage7_post_box_plan_capsule_audit.md
```

This is not a new fixed `Stage 7.5` curriculum step. It is the first proposed
Plan Capsule / Commitment Bias test case: a bounded multi-ply continuation with
visible entry, progress, exit, and abort terms. The broader lesson is that local
skill success sometimes needs short visible commitment rather than another
single-move provider or broad score adjustment.

Audit result:

```text
post_reply_records: 45
wrong_first_post_box_move: not_sufficient
wrong_second_or_third_move: likely
missing_plan_commitment: likely
premature_stage0_fallback: observed_but_not_sufficient_after_ownership_tests
provider_capacity_gap: likely_for_current_providers
```

Candidate status updates:

```text
learned post-box overlay:
  status: quarantined
  diagnosis: selected_provider_still_cannot_convert / continuation_topology_underexpressive

broad drive support adapter:
  status: quarantined_or_overbroad
  diagnosis: adapter fires but supported provider outcome remains max_plies

local box-shrink repairs:
  status: local_semantic_alignment_improved_but_conversion_insufficient

plan capsule:
  status: proposed
  next_action: trajectory_gap_audit
```

No runtime behavior changed in this slice. The capsule, StructuralCandidate,
HandoffPacket, SkillContractStats, ShadowStemCandidate, GrowthGovernor, and
provider-promotion records remain evidence only. A future causal capsule would
require explicit sandboxing, visible SCRIPT/TERMINAL terms, bounded TTL,
handoff exports, and Stage 7 + Stage 6/5/4/1 + bridge/M1-M4 guardrails before
any promotion.

## Stage 7 Plan Capsule sandbox protocol

I added a non-causal sandbox protocol check for the proposed capsule. It does
not compile a runtime plan owner and does not affect move selection. It checks
whether the existing DTM/reference trajectories support the proposed bounded
entry/progress/exit/abort semantics.

Artifact:

```text
reports/structural_candidates/stage7_post_box_plan_capsule_sandbox_protocol.json
reports/structural_candidates/stage7_post_box_plan_capsule_sandbox_protocol.md
```

Result:

```text
schema: stage7_post_box_plan_capsule_sandbox_protocol.v1
causal_status: non_causal
runtime_behavior_changed: false
ttl_white_moves: 3
reference_supported_count: 2/2

8/8/R7/8/2k5/8/8/3K4 w - - 2 2:
  DTM 27 -> 22 after 3 owned white moves
  abort_terms: none

8/8/8/R7/4k3/8/3K4/8 w - - 2 2:
  DTM 21 -> 16 after 3 owned white moves
  abort_terms: none
```

Interpretation:

```text
The reference trajectories support a bounded three-white-move commitment
protocol. The next candidate action is a default-off visible capsule sandbox,
not Stage 8 training, not Stage 7 promotion, and not a broad provider penalty.
```

## Stage 7 default-off Plan Capsule sandbox topology

I compiled a default-off visible capsule sandbox marker into the Stage 7
post-box learned-overlay topology.

Artifact:

```text
snapshots/krk_triplet_pipeline/adaptive_krk_stage7_box_guarded_retry/topology/krk_entry_topology_stage7_plan_capsule_sandbox.json
```

Sandbox metadata:

```text
schema: plan_capsule_sandbox.v1
capsule_id: krk.post_box_shrink_continuation
enabled_by_default: false
causal_status: sandbox_opt_in_non_requesting
direct_request: false
runtime_behavior_change_when_disabled: false
```

The added marker node records capsule entry/progress/exit/abort evidence only
if `plan_capsule_sandbox_enabled` is explicitly true. It does not request a
provider and does not change move scores.

Default-off equivalence check:

```text
base topology:
  reports/structural_candidates/stage7_plan_capsule_default_off_base_10_h20.json

capsule sandbox topology:
  reports/structural_candidates/stage7_plan_capsule_default_off_sandbox_10_h20.json

comparison:
  reports/structural_candidates/stage7_plan_capsule_default_off_equivalence_10_h20.json
```

Result:

```text
equivalent: true
differences: []
packet_count: 30
shadow_candidate_count: 14
adapter_fire_count: 0
```

The default-off capsule topology therefore preserves observed behavior on the
small Stage 7 smoke. Any future causal experiment still needs an explicit
opt-in flag, visible source terms, target validation, and protected guardrails.

## Stage 7 opt-in Plan Capsule marker smoke

I added an opt-in diagnostic flag:

```text
--enable-plan-capsule-sandbox
```

This enables only the non-requesting Plan Capsule marker. It records visible
entry/progress/exit/abort evidence into handoff packets and does not alter
provider requests or move scores.

Artifact:

```text
reports/structural_candidates/stage7_plan_capsule_marker_enabled_10_h20.json
```

Result:

```text
10 samples, h20:
  local: 10/10 improved, 8/10 optimal
  conversion: 5 mate / 5 max_plies
  shadows: 14

plan_capsule_marker_count: 8
plan_capsule_marker_by_outcome:
  krk.post_box_shrink_continuation:max_plies: 5
  krk.post_box_shrink_continuation:mate: 3
```

The top-level behavior matches the default-off smoke. The marker trace shows
entry evidence is close but not always complete; the first max-plies sample had:

```text
entry_terms_met:
  active_landmark_label.box_shrink
  box_shrink_attempt_confirmed_or_candidate_confirmed
  post_reply_state_reached
  conversion_not_immediate
  rook_safe
  no_stronger_mate_or_tactic_interrupt_available

missing entry term:
  enemy_king_constrained_or_recoverable

abort_terms_met:
  none
```

Interpretation:

```text
The marker is wired and inspectable. Before any causal capsule sandbox, the
entry/progress vocabulary needs one more refinement pass so terms like
enemy_king_constrained_or_recoverable and progress-after-owned-move are
graph-visible in the live trace, not only in offline DTM reference artifacts.
```

## Stage 7 Plan Capsule live-term refinement

I refined the non-causal marker vocabulary so capsule-level terms are derived
from existing graph-visible KRK context terms rather than from offline labels.

Examples:

```text
enemy_king_constrained_or_recoverable
  derives from enemy_king_restricted, edge-trap availability,
  box_shrink_drive_repair_available, or repair_or_reestablish_cut_available

cut_or_fence_preserved_or_restored
  derives from fence_exists, fence_stable, cut_stable, or repair availability

white_king_support_improves
  derives from white_king_can_improve_support,
  king_support_improvement_move_exists, or current support availability
```

Artifact:

```text
reports/structural_candidates/stage7_plan_capsule_marker_terms_refined_10_h20.json
```

Result:

```text
10 samples, h20:
  local: 10/10 improved, 8/10 optimal
  conversion: 5 mate / 5 max_plies
  shadows: 14
  plan_capsule_marker_count: 8
```

The behavior is unchanged from the prior marker smoke, but trace quality
improved. In the inspected max-plies post-box state:

```text
before:
  entry_confirmed: false
  progress_terms_met: []

after:
  entry_confirmed: true
  progress_terms_met:
    box_area_decreases_or_does_not_expand
    cut_or_fence_preserved_or_restored
    white_king_support_improves
    safe_check_or_cut_created
  abort_terms_met: []
```

This keeps the capsule non-causal while making its proposed entry/progress
conditions live-visible and auditable.

## Stage 7 Plan Capsule marker analysis

I added an offline marker-analysis script:

```text
scripts/analyze_plan_capsule_markers.py
```

Artifact:

```text
reports/structural_candidates/stage7_plan_capsule_marker_analysis_10_h20.json
reports/structural_candidates/stage7_plan_capsule_marker_analysis_10_h20.md
```

Result:

```text
marker_records: 8
outcomes:
  mate: 3
  max_plies: 5

entry_confirmed_max_plies_count: 5
entry_confirmed_mate_count: 0
mate_exit_count: 3
max_plies_without_abort_count: 5
```

Interpretation:

```text
The capsule entry terms now separate candidate ownership states from already
successful exit states: max-plies cases enter the capsule, while mate cases
already expose exit terms.

The remaining gap is not entry gating. It is that max-plies cases enter the
capsule without any abort firing. Before causal sandboxing, the system needs a
non-causal owned-move progress / TTL-failure monitor so it can say whether the
capsule would have made progress over its 3-white-move window.
```

Next action:

```text
design_non_causal_owned_move_progress_monitor
```

## Stage 7 Plan Capsule owned-window analysis

I generated a trace-retaining 10-sample marker diagnostic and added an offline
owned-window analyzer for the proposed capsule.

Artifacts:

```text
reports/structural_candidates/stage7_plan_capsule_marker_terms_refined_trace10_h20.json
reports/structural_candidates/stage7_plan_capsule_owned_window_10_h20.json
reports/structural_candidates/stage7_plan_capsule_owned_window_10_h20.md
```

Result:

```text
capsule: krk.post_box_shrink_continuation
ttl_white_moves: 3
windows: 5
ttl_failures: 3
```

Per-window summary:

```text
sample 1 max_plies:
  moves: e2d1, d1c1, c1c2
  progress: box preserved, edge distance not worse
  ttl_failure: true

sample 2 max_plies:
  moves: e4f3, f3g4, g4f3
  progress: king support improved
  ttl_failure: false

sample 3 max_plies:
  moves: a6a8, a8d8, d1e2
  progress: box decreased, king support improved
  ttl_failure: false

sample 6 / 9 max_plies:
  moves: a5h5, h5h8, h8d8
  progress: box preserved, edge/corner not worse
  ttl_failure: true
```

Interpretation:

```text
The remaining failures split into:
  A. capsule entry + owned-window progress, but later conversion still fails;
  B. capsule entry + no strong owned-window progress before TTL.

This is still non-causal. It gives a better sandbox criterion: a future runtime
capsule should not merely enter; it must show owned-window progress or emit a
visible TTL/progress failure.
```

## Stage 7 Plan Capsule v0 default-off sandbox

I implemented the first default-off Plan Capsule runtime sandbox for:

```text
cand.krk.box_shrink.post_box_continuation_capsule.v1
capsule_id: krk.post_box_shrink_continuation
```

This is still not Stage 7.5 and not promoted topology. It is an opt-in
bounded commitment-bias experiment with explicit state:

```text
candidate -> active -> progress_confirmed -> exited / aborted / expired
```

The sandbox remains disabled by default and only runs with:

```text
--enable-plan-capsule-sandbox
--enable-stage7-plan-capsule
--stage7-plan-capsule-ttl {3,4}
--stage7-plan-capsule-support-bonus 0.05
```

Default-off equivalence passed:

```text
reports/structural_candidates/stage7_plan_capsule_default_off_equivalence_10_h20_rerun.json
equivalent: true
differences: []
```

Larger non-causal marker audit:

```text
reports/structural_candidates/stage7_plan_capsule_marker_trace25_h40.json
reports/structural_candidates/stage7_plan_capsule_marker_analysis_25_h40.json
reports/structural_candidates/stage7_plan_capsule_owned_window_25_h40.json
```

Result:

```text
marker_records: 23
entry_confirmed_max_plies_count: 13
entry_confirmed_mate_count: 0
mate_exit_count: 10
owned_windows: 13
ttl_failures: 8
```

Tiny causal smoke:

```text
marker-only h40: 5 mate / 5 max_plies
ttl=3 h40:      5 mate / 5 max_plies
ttl=4 h40:      5 mate / 5 max_plies
shadow candidates: 14 in all three
```

Interpretation:

```text
The capsule entry terms remain meaningful and separate failure windows from
already-successful exits. The default-off topology is behavior-preserving.
The opt-in runtime state now enters the max-plies windows and exits mate
windows, but the small support amount does not yet create selected owned-window
progress or improve conversion.
```

Current candidate status:

```text
promotion_status: sandbox_ready
runtime_status: sandbox_opt_in
diagnosis: plan_entry_valid_but_policy_insufficient
next_action: inspect owned-provider licenses / commitment ownership strength
```

## Stage 7 Plan Capsule support/opportunity accounting

I added explicit non-causal support/opportunity counters so capsule smokes can
distinguish these cases:

```text
plan active, but no owned-provider suggestions exist
plan active, owned-provider suggestions exist and are licensed
plan active, a licensed owned-provider move is selected
plan active, licensed owned-provider moves lose arbitration
```

New summary fields include:

```text
plan_capsule_active_decision_count
plan_capsule_supported_suggestion_count
plan_capsule_selected_supported_count
plan_capsule_active_without_support_count
plan_capsule_supported_provider_by_outcome
plan_capsule_supported_move_by_outcome
plan_capsule_selected_supported_by_outcome
```

Smoke artifact:

```text
reports/structural_candidates/stage7_plan_capsule_support_accounting_5_h20.json
```

Result:

```text
playouts: 2 mate / 3 max_plies
plan_capsule_active_decision_count: 3
plan_capsule_supported_suggestion_count: 48
plan_capsule_selected_supported_count: 0
plan_capsule_active_without_support_count: 0
```

Provider support in max-plies windows:

```text
krk.edge_trap_close: 12
krk.edge_trap_wrong_tempo: 6
krk.edge_trap_enemy_between: 18
krk.drive_to_edge: 9
krk.fence_established: 3
```

Interpretation:

```text
The capsule is not under-entering and not lacking owned-provider candidates.
It licenses many visible owned-provider moves, but none are selected. The next
question is not entry/progress detection; it is whether commitment should own
arbitration within the bounded capsule window, still with visible traceability
and default-off semantics.
```

## Stage 7 Plan Capsule owned-arbitration sandbox

I added a second default-off sandbox flag:

```text
--enable-stage7-plan-capsule-owned-arbitration
```

This does not add a hidden provider request and does not use packet/stat/candidate
metadata causally. It only lets an active Plan Capsule select among already
visible, licensed plan-capsule suggestions inside the bounded TTL window.
Every selected override records:

```text
visible_stage7_plan_capsule_owned_arbitration.enabled
mode = bounded_plan_capsule_owned_window
raw_selected_skill / raw_selected_move / raw_selected_score
selected_skill / selected_move / selected_score
candidate_count
causal_status = sandbox_opt_in
direct_request = false
```

Default-off check:

```text
reports/structural_candidates/stage7_plan_capsule_owned_arb_default_off_equivalence_5_h10.json
equivalent: true
differences: []
```

Opt-in 10-sample h40 smoke:

```text
reports/structural_candidates/stage7_plan_capsule_owned_arb_ttl3_10_h40.json
reports/structural_candidates/stage7_plan_capsule_owned_arb_ttl4_10_h40.json
```

Result:

```text
marker-only baseline: 5 mate / 5 max_plies, shadow candidates 14
ttl=3 owned arbitration: 7 mate / 3 max_plies, shadow candidates 9
ttl=4 owned arbitration: 7 mate / 3 max_plies, shadow candidates 9
```

TTL=3 support details:

```text
plan_capsule_active_decision_count: 5
plan_capsule_supported_suggestion_count: 80
plan_capsule_selected_supported_count: 5
plan_capsule_owned_arbitration_selected_count: 4
plan_capsule_active_without_support_count: 0
```

Provider outcomes:

```text
krk.edge_trap_close:mate = 2
krk.edge_trap_close:max_plies = 1-2 depending on selected/support count
krk.fence_established:max_plies = 1
```

Interpretation:

```text
Bounded visible commitment ownership is now a plausible Stage 7 repair
hypothesis. It improves the small target smoke without changing defaults, but
it is not validated or promoted. The remaining max-plies cases show that
owned arbitration helps some windows and still needs larger target validation
and, only if target improves, protected guardrails.
```

## Stage 7 Plan Capsule owned-arbitration 25-sample target

I ran a paired 25-sample h40 target validation with identical seed/positions and
`suggestion_limit=20`.

Artifacts:

```text
reports/structural_candidates/stage7_plan_capsule_marker_only_s20_25_h40.json
reports/structural_candidates/stage7_plan_capsule_owned_arb_ttl3_s20_25_h40.json
```

Result:

```text
marker-only baseline:
  12 mate / 13 max_plies
  shadow candidates: 35

owned-arbitration ttl=3:
  17 mate / 8 max_plies
  shadow candidates: 21
```

Owned-arbitration trace counters:

```text
plan_capsule_active_decision_count: 13
plan_capsule_supported_suggestion_count: 208
plan_capsule_selected_supported_count: 13
plan_capsule_owned_arbitration_selected_count: 9
```

Guardrail spot checks with the same opt-in flags enabled:

```text
Stage 6 drive_to_edge:
  25 mate / 0 max_plies
  shadow candidates: 0
  plan_capsule_active_decision_count: 0

Stage 5 fence_established:
  20 mate / 5 max_plies
  shadow candidates: 10
  plan_capsule_active_decision_count: 0

Stage 4 edge_trap_wrong_tempo:
  22 mate / 3 max_plies
  shadow candidates: 6
  plan_capsule_active_decision_count: 0
```

Interpretation:

```text
The owned-arbitration sandbox improves Stage 7 target conversion and reduces
shadow candidates on the 25-sample paired target. The capsule does not fire on
Stage 6/5/4 guardrail labels, so the new mechanism is label-scoped as intended.
The Stage 5/4 guardrails are not perfect under this Stage 7 topology, but the
plan capsule itself is not the active cause in those runs.
```

Candidate status:

```text
candidate_status: sandbox_improves_target_small_sample
promotion_status: sandboxed
next_action: larger Stage 7 target validation, then broader guardrail comparison
```

## Stage 7 Plan Capsule owned-arbitration 50-sample target

I scaled the owned-arbitration sandbox target to 50 samples at h40 with
parallel validation.

Artifact:

```text
reports/structural_candidates/stage7_plan_capsule_owned_arb_ttl3_s20_50_h40.json
```

Result:

```text
25 mate / 25 max_plies
shadow candidates: 67
parallel workers: 4
wall time: 260.14 sec
```

Plan Capsule counters:

```text
plan_capsule_active_decision_count: 31
plan_capsule_supported_suggestion_count: 496
plan_capsule_selected_supported_count: 31
plan_capsule_owned_arbitration_selected_count: 24
plan_capsule_active_without_support_count: 0
```

Provider outcomes:

```text
krk.edge_trap_close:mate = 6
krk.edge_trap_close:max_plies = 10-17 depending on arbitration/support count
krk.fence_established:max_plies = 8
```

Interpretation:

```text
The mechanism remains useful but insufficient. It improves over the earlier
Stage 7 50-sample smoke baseline (19 mate / 31 max_plies), but the larger run
shows that bounded ownership alone does not solve Stage 7. The remaining
failures are now sharper: the capsule enters, licensed providers exist, owned
arbitration selects them, but many selected edge_trap_close/fence_established
continuations still max-plies.
```

Candidate status update:

```text
candidate_status: sandbox_partially_validated_target_improvement
promotion_status: sandboxed_not_promoted
diagnosis: visible_commitment_ownership_helps_but_continuation_policy_insufficient
next_action: classify residual capsule-owned max-plies by selected provider and
             post-owned-window failure mode before any promotion or new training
```

Hard boundary:

```text
No promotion.
No Stage 8.
No hidden controller.
No gameplay-time topology mutation.
HandoffPacket, stats, shadow candidates, StructuralCandidate,
GrowthGovernor, and PlanCapsuleSpec remain non-causal.
```

## Stage 7 Plan Capsule residual owned-failure analysis

After the 50-sample owned-arbitration validation, I added a replay-free
non-causal analyzer for the remaining max-plies cases.

Artifacts:

```text
scripts/analyze_stage7_plan_capsule_owned_failures.py
reports/structural_candidates/stage7_plan_capsule_owned_failure_analysis_50_h40.json
reports/structural_candidates/stage7_plan_capsule_owned_failure_analysis_50_h40.md
```

Residual max-plies buckets:

```text
krk.edge_trap_close: 17
krk.fence_established: 8
```

The 25 max-plies rows collapse to 3 unique failure families:

```text
state.069e81a609ed:
  support=10
  provider=krk.edge_trap_close
  selected_move=h4g4
  semantic=reward_contract_mismatch
  failure=successor_conflict

state.2cc0b3e1033a:
  support=8
  provider=krk.fence_established
  selected_move=a6h6
  semantic=reward_contract_mismatch
  failure=successor_conflict

state.0926f12f8e8f:
  support=7
  provider=krk.edge_trap_close
  selected_move=e4d4
  semantic=reward_visible_fence_aligned_survived
  failure=conversion_failure_unclassified
```

By semantic alignment:

```text
krk.edge_trap_close + reward_contract_mismatch: 10
krk.edge_trap_close + reward_visible_fence_aligned_survived: 7
krk.fence_established + reward_contract_mismatch: 8
```

Failure classes:

```text
successor_conflict: 18
conversion_failure_unclassified: 7
```

Interpretation:

```text
The Plan Capsule is doing useful work: it enters only in the intended Stage 7
post-box context, finds licensed owned providers, and can override raw
stage0_basin dominance. But residual failures are now family-specific. This is
no longer a generic ownership problem. The remaining question is why two
edge_trap_close families and one fence_established family fail after being
visibly licensed inside the capsule window.
```

Candidate status:

```text
candidate_status: sandbox_improves_target_but_provider_residuals_remain
promotion_status: sandboxed_not_promoted
next_action: provider-specific post-owned-window audits for edge_trap_close
             and fence_established residuals
```

Hard boundary:

```text
Do not promote the capsule.
Do not increase broad support bonuses.
Do not add broad provider penalties.
Do not train Stage 8.
Do not make the analyzer causal.
```

## Stage 7 Plan Capsule residual forced-provider / legal-first probe

I ran a targeted, non-causal h40 forced-provider replay on the three residual
Plan Capsule families.

Artifacts:

```text
reports/structural_candidates/stage7_plan_capsule_residual_forced_provider_h40.json
reports/structural_candidates/stage7_plan_capsule_residual_forced_provider_h40_steps.jsonl
reports/structural_candidates/stage7_state0926_legal_first_h40.json
reports/structural_candidates/stage7_state0926_legal_first_h40_steps.jsonl
reports/structural_candidates/stage7_plan_capsule_residual_candidate_updates.json
```

Forced-provider summary:

```text
states tested: 3
providers tested: edge_trap_close, fence_established, drive_to_edge, stage0_basin
horizon: 40

state.069e81a609ed:
  edge_trap_close -> h4g4 -> max_plies
  fence_established -> h4h8 -> max_plies
  drive_to_edge -> e2e3 -> mate in 7
  stage0_basin -> e2d1 -> max_plies

state.0926f12f8e8f:
  edge_trap_close -> e4d4 -> max_plies
  fence_established -> e4f4 -> max_plies
  drive_to_edge -> e4f3 -> max_plies
  stage0_basin -> e4f3 -> max_plies

state.2cc0b3e1033a:
  edge_trap_close -> a6a7 -> max_plies
  fence_established -> a6h6 -> max_plies
  drive_to_edge -> a6a8 -> max_plies
  stage0_basin -> a6a8 -> max_plies
```

The missing legal-first classification for `state.0926f12f8e8f` is now filled:

```text
state.0926f12f8e8f:
  exhaustive legal-first h40:
    1 mate
    18 max_plies
    3 draw
  converting move:
    e4d3 -> mate in 9
  converting move terms:
    candidate_is_king_move
    king_moves_toward_enemy
    king_moves_toward_rook_support
    fence_exists_after_move
    fence_stable_after_move
    cut_preserved_after_move
    white_king_distance_to_enemy_decreases
    white_king_distance_to_rook_decreases
```

Existing evidence for `state.2cc0b3e1033a` still applies:

```text
legal-first h50:
  no converting legal first move under current graph continuation
DTM oracle:
  won in 27 plies
```

Updated family diagnoses:

```text
state.069e81a609ed:
  diagnosis: wrong owned provider / role boundary
  evidence: drive_to_edge converts at h40 when forced, but capsule selected edge_trap_close
  next action: refine visible role terms so this family licenses drive_to_edge,
               not edge_trap_close

state.0926f12f8e8f:
  diagnosis: legal-first action-selection gap
  evidence: no tested provider converts, but legal move e4d3 converts in 9
  next action: add non-causal candidate for a king-support/fence-stabilizing
               post-box move-shape, then sandbox only if visible terms separate

state.2cc0b3e1033a:
  diagnosis: current-continuation capacity gap or underexpressive topology
  evidence: DTM-won in h40, but no existing provider or legal-first current
            continuation converts at h50
  next action: keep as narrow post-box continuation overlay/training candidate,
               not a broad full-KRK patch
```

Interpretation:

```text
The residual Stage 7 failures are now split cleanly:
  1 family is wrong-provider ownership,
  1 family is legal-first action selection,
  1 family is likely continuation capacity/expressivity.

This argues against another broad Plan Capsule bonus. The next repair, if any,
should be family/term specific and still sandbox-only.
```

I also emitted three non-causal StructuralCandidate updates:

```text
cand.krk.box_shrink.family_069.drive_role_refinement.v1
  type: family_specific_role_refinement
  diagnosis: drive_to_edge solves when forced; current capsule selected edge_trap_close

cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1
  type: move_shape_role_refinement
  diagnosis: legal-first e4d3 converts; no tested provider selected it

cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1
  type: narrow_overlay_training_candidate
  diagnosis: DTM-won but current graph cannot convert under existing providers or legal-first current continuation
```

These candidate records round-trip through `StructuralCandidate` and keep
`causal_status = non_causal` and `credit = 0.0`.

## Stage 7 residual repair protocol planning

I added a non-causal protocol planner that converts the residual candidate
updates into explicit sandbox protocols.

Artifacts:

```text
scripts/plan_stage7_residual_repair_protocols.py
reports/structural_candidates/stage7_residual_repair_protocols.json
reports/structural_candidates/stage7_residual_repair_protocols.md
```

Protocol statuses:

```text
stage7.residual.069.drive_role_refinement.rejected_general_priority:
  source candidate: cand.krk.box_shrink.family_069.drive_role_refinement.v1
  status: rejected_as_general_priority_rule
  reason:
    targeted_family_improved
    25_sample_target_regressed
    visible_terms_do_not_yet_separate_safe_general_use

stage7.residual.0926.king_support_fence_stabilizer.sandbox_design:
  source candidate: cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1
  status: sandbox_design_ready
  repair kind: visible_move_shape_role

stage7.residual.2cc.narrow_post_box_overlay.training_protocol:
  source candidate: cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1
  status: training_protocol_ready_not_run
  repair kind: narrow_overlay_training_candidate
```

Recommended order:

```text
1. Try the 0926 visible move-shape role as a default-off sandbox.
2. Only if that does not generalize, proceed to the 2cc narrow overlay training
   protocol.
```

Boundary:

```text
The planner is non-causal. It does not compile topology, train weights,
promote Stage 7, or alter runtime routing.
```

## Stage 7 0926 move-shape role spec

I added a general non-causal schema for visible move-shape roles:

```text
MoveShapeRoleSpec
```

This is deliberately not a move selector. It records the visible entry,
candidate-move, post-move, veto, validation, and guardrail terms that would be
required before a later sandbox can compile a role into explicit topology or
adapter metadata.

Stage 7 0926 export artifacts:

```text
scripts/export_stage7_0926_move_shape_role.py
reports/structural_candidates/stage7_0926_king_support_fence_stabilizer_role_spec.json
reports/structural_candidates/stage7_0926_king_support_fence_stabilizer_role_spec.md
```

Role:

```text
krk.post_box.king_support_fence_stabilizer
```

Required move-shape terms:

```text
candidate_is_king_move
king_moves_toward_enemy
king_moves_toward_rook_support
```

Required post-move terms:

```text
rook_safe_after_move
box_area_not_increased_after_move
fence_exists_after_move
fence_stable_after_move
cut_preserved_after_move
white_king_distance_to_enemy_decreases
white_king_distance_to_rook_decreases
```

Boundary:

```text
The role spec is non-causal.
It does not generate moves.
It does not request providers.
It does not use a state hash exception.
It must not be compiled until default-off sandbox and traceability tests exist.
```

## Stage 7 0926 move-shape role candidate audit

I added a replay-free role candidate auditor:

```text
scripts/audit_move_shape_role_candidates.py
```

It evaluates legal moves against a non-causal `MoveShapeRoleSpec` using visible
move-shape and post-move terms. It does not change play.

Artifact:

```text
reports/structural_candidates/stage7_0926_move_shape_role_candidate_audit.json
reports/structural_candidates/stage7_0926_move_shape_role_candidate_audit.md
```

Audit inputs:

```text
state.069e81a609ed
state.0926f12f8e8f
state.2cc0b3e1033a
```

Result:

```text
states with matches: 1 / 3
total matching moves: 1

state.069e81a609ed:
  matches: 0

state.0926f12f8e8f:
  matches: 1
  move: e4d3

state.2cc0b3e1033a:
  matches: 0
```

Interpretation:

```text
The 0926 role terms are not obviously overbroad on the current residual family
set. They recover exactly the legal-first converting move e4d3 and do not fire
on the 069 or 2cc families.
```

## Stage 7 Plan Capsule drive-priority sandbox negative result

I tested the smallest causal follow-up suggested by the residual split:
a default-off Plan Capsule owned-arbitration priority that lets a visible
drive-repair king move outrank a slightly higher edge-trap candidate in
069-like contexts.

Artifacts:

```text
reports/structural_candidates/stage7_plan_capsule_drive_priority_ttl3_10_h40.json
reports/structural_candidates/stage7_plan_capsule_drive_priority_ttl3_10_h40_rerun.json
reports/structural_candidates/stage7_plan_capsule_drive_priority_ttl3_25_h40.json
```

Result:

```text
10-sample smoke before context merge:
  7 mate / 3 max_plies
  shadow candidates: 9
  no behavior change versus prior owned-arbitration smoke

10-sample smoke after context merge:
  8 mate / 2 max_plies
  shadow candidates: 7
  state.069e81a609ed selected krk.drive_to_edge and converted

25-sample target:
  16 mate / 9 max_plies
  shadow candidates: 26
```

Comparison baseline:

```text
prior owned-arbitration 25-sample:
  17 mate / 8 max_plies
  shadow candidates: 21
```

Interpretation:

```text
The drive-priority idea fixes the targeted 069-like family but regresses the
25-sample target aggregate. That means the visible role boundary is still too
coarse for a general sandbox rule. I reverted the runtime/test change and kept
the artifacts as negative evidence.
```

Candidate status update:

```text
cand.krk.box_shrink.family_069.drive_role_refinement.v1:
  status: rejected_as_general_priority_rule
  diagnosis:
    targeted_family_improves
    25_sample_target_regresses
    role_boundary_underseparated
  next_action:
    do not reintroduce priority without additional separating terms
```

## CandidateMoveFrame layer and 0926 sandbox result

Implemented a minimal visible candidate-move layer for the 0926 family.
This is not a durable legal-move topology expansion. Candidate moves are
ephemeral runtime/trace records emitted by:

```text
terminal.krk.candidate_move_enumerator
```

The default-off sandbox role:

```text
krk.post_box.king_support_fence_stabilizer
```

matches legal moves using visible current, move-shape, and post-move terms.
The role-scoped actuator emits an ordinary suggestion only when the role
matches, with `direct_request = false` and explicit source terms.

Artifacts:

```text
reports/structural_candidates/stage7_0926_king_support_fence_stabilizer_role_spec.json
reports/structural_candidates/stage7_0926_move_shape_role_candidate_audit.json
reports/structural_candidates/stage7_0926_candidate_move_layer_smoke.json
reports/structural_candidates/stage7_0926_candidate_move_layer_smoke_support30.json
reports/structural_candidates/stage7_candidate_move_layer_default_off_10_h40.json
reports/structural_candidates/stage7_candidate_move_layer_10_h40_support30.json
reports/structural_candidates/stage7_candidate_move_layer_default_off_25_h40.json
reports/structural_candidates/stage7_candidate_move_layer_25_h40_support30.json
```

Non-causal audit:

```text
state.069e81a609ed: 0 matches
state.0926f12f8e8f: 1 match, e4d3
state.2cc0b3e1033a: 0 matches
```

Targeted runtime smoke:

```text
support 3.0:
  role match emitted but loses arbitration to stage0 score scale

support 30.0:
  selected e4d3
  selected_supported = true
  source terms include:
    candidate_is_king_move
    king_moves_toward_enemy
    king_moves_toward_rook_support
    fence_exists_after_move
    fence_stable_after_move
    cut_preserved_after_move
    white_king_distance_to_enemy_decreases
    white_king_distance_to_rook_decreases
```

Paired Stage 7 results, same seed/settings:

```text
10-sample default-off:
  5 mate / 5 max_plies
  shadow candidates: 8
  candidate role suggestions: 0

10-sample enabled:
  6 mate / 4 max_plies
  shadow candidates: 6
  candidate role suggestions: 1
  selected e4d3 -> mate

25-sample default-off:
  12 mate / 13 max_plies
  shadow candidates: 23
  local improved/optimal: 21/16

25-sample enabled:
  16 mate / 9 max_plies
  shadow candidates: 15
  local improved/optimal: 21/16
  candidate role suggestions: 4
  e4d3:mate = 4
```

Interpretation:

```text
The CandidateMoveFrame layer gives the first clean visible legal-action
hypothesis path. It does not solve Stage 7 globally, but it validates the 0926
family repair without local one-ply regression on the paired 25-sample run.
Stage 7 remains quarantined. The sandbox needs guardrails before any larger
candidate status update.
```

Small guardrails with candidate flags enabled:

```text
Stage 6 drive_to_edge, 25 samples h40:
  25 mate / 0 max_plies
  candidate role suggestions: 0

Stage 5 fence_established, 25 samples h40:
  20 mate / 5 max_plies
  local optimal: 25/25
  candidate role suggestions: 0

Stage 4 edge_trap_wrong_tempo, 25 samples h40:
  22 mate / 3 max_plies
  local optimal: 25/25
  candidate role suggestions: 0
```

Interpretation:

```text
The role does not fire outside the Stage 7 post-box scope in these guardrails.
Stage 6 is clean. Stage 4/5 conversion limits are inherited from the current
Stage 7 sandbox topology/profile rather than candidate-move overfire, because
candidate role suggestions remain zero.
```

## 2cc CandidateMoveFrame audit

After adding the candidate-move layer, I generated a non-causal frame audit for
the unresolved 2cc family:

```text
reports/structural_candidates/stage7_2cc_candidate_move_frame_audit.json
reports/structural_candidates/stage7_2cc_candidate_move_frame_audit.md
```

Summary:

```text
state.2cc0b3e1033a:
  legal CandidateMoveFrames: 19

common visible move shapes:
  candidate_is_rook_move: 14
  rook_safe_after_candidate: 14
  candidate_is_rook_transfer: 11
  rook_to_edge_file: 8
  rook_lateral_transfer: 7
  rook_transfer_vertical: 7
  candidate_is_king_move: 5
  safe_check_created: 2
```

Interpretation:

```text
The unresolved 2cc family now has visible legal-action hypotheses available
for the next non-causal diagnosis. This does not classify capacity by itself;
it supplies the candidate-frame vocabulary needed to compare DTM/reference,
legal-first, and provider-continuation traces without adding persistent
topology nodes for legal moves.
```

## 2cc CandidateMoveFrame / DTM alignment

I aligned the 2cc CandidateMoveFrames with the DTM oracle, DTM trajectory seed,
and current-graph legal-first probes:

```text
reports/structural_candidates/stage7_2cc_candidate_move_dtm_alignment.json
reports/structural_candidates/stage7_2cc_candidate_move_dtm_alignment.md
```

Result:

```text
diagnosis:
  multi_step_continuation_policy_gap_not_single_move_gap

state DTM:
  27

legal moves:
  19

tablebase-winning legal moves:
  19

current graph legal-first h50:
  19 max_plies
  0 mate

best DTM first moves:
  a6a5
  a6d6
  d1d2
```

Reference trajectory begins:

```text
a6a5
a5f5
d1e2
```

Interpretation:

```text
2cc is not analogous to 0926. It is not missing one visibly separable legal
first move; every legal first move is tablebase-winning, but the current graph
cannot convert after any of them under h50. This supports a narrow post-box
continuation capsule/overlay protocol rather than another single candidate-move
role.
```

## 2cc continuation protocol

Created a non-causal protocol artifact:

```text
reports/structural_candidates/stage7_2cc_continuation_protocol.json
reports/structural_candidates/stage7_2cc_continuation_protocol.md
```

Candidate:

```text
cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1
```

Status:

```text
sandbox_training_protocol_ready
```

This is not training and not promotion. It defines the bounded evaluation path:

```text
static sanity
frozen-weight probe
bounded candidate-local plasticity
target validation
protected guardrails
```

Hard boundaries:

```text
do not train Stage 8
do not promote Stage 7
do not use tablebase/DTM at runtime
do not use state-hash exceptions
do not mutate topology during gameplay
```

## 2cc protocol Phase 0/1

Ran the first two protocol phases without changing runtime behavior:

```text
reports/structural_candidates/stage7_2cc_protocol_phase01.json
reports/structural_candidates/stage7_2cc_protocol_phase01.md
```

Phase 0 static sanity passed:

```text
protocol_non_causal: true
candidate_non_causal: true
candidate_not_promoted: true
tablebase_forbidden: true
dtm_runtime_forbidden: true
state_hash_forbidden: true
model_non_promoted: true
model_default_off: true
```

Phase 1 scored the 2cc CandidateMoveFrames with the existing frozen visible-term
trajectory model:

```text
selected_move: d1e2
selected_child_dtm: 28
selected_forces_mate: true
selected_optimal_dtm_move: false
optimal_dtm_moves: a6a5, a6d6, d1d2
status: frozen_model_selects_winning_nonoptimal_move
```

Interpretation:

```text
The frozen visible-term model has an expressive first-step signal for 2cc,
but it does not select the optimal DTM move. This supports a default-off
sandbox candidate-local probe next, not promotion and not Stage 8 training.
The current status is sandbox_protocol_phase01_complete.
```

## 2cc protocol Phase 2

Ran a non-causal replay classification of the Phase 0/1 selected move against
the existing legal-first probe artifact:

```text
reports/structural_candidates/stage7_2cc_protocol_phase02.json
reports/structural_candidates/stage7_2cc_protocol_phase02.md
```

Result:

```text
selected_move: d1e2
selected_child_dtm: 28
selected_forces_mate: true
selected_optimal_dtm_move: false
current_graph_replay: max_plies at h50
legal_first_probe_count: 19
legal_first_outcome_counts: h50:max_plies = 19
legal_first_mating_moves: none
```

Interpretation:

```text
The frozen visible-term model can identify a tablebase-winning first move, but
the current graph still fails after that move. Since every legal first move is
tablebase-winning and every legal-first current-graph replay fails at h50, the
2cc family is now classified as a downstream multi-step continuation policy
gap rather than a CandidateMoveFrame/action-selection gap.

The candidate status is sandbox_protocol_phase02_complete. The next safe work,
if continued, is a bounded candidate-local plasticity protocol or narrow
continuation sandbox. Stage 7 remains quarantined; this does not justify Stage
8 training or Stage 7 promotion.
```
