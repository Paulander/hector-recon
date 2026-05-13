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
