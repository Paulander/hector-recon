# TG26i Terminal Edge/Fence Validation

Artifact: `reports/autogrowth/krk_autogrowth_tg26i_terminal_edge_fence_validation.json`

TG26i reruns bounded edge/fence validation with the TG26h terminal-native
foundation and terminal-native stage learners. `ActionRanker`/TG26g is kept only
as reference scaffolding.

Run shape:

- Foundation: 300 Mate_In_1 train, 100 Mate_In_1 heldout, 40 mirrored, 300
  Mate_In_2 train, 100 Mate_In_2 heldout.
- Edge/fence: 32 filtered train-pool positions, 16 heldout per slice, top-K 3
  deep scoring, 2 train chunks.
- Fence also uses 16 unfiltered rehearsal and 16 boundary rehearsal positions.
- A larger 64/32/top-K 6 run was stopped after about 16 minutes; terminal-native
  handoff scoring needs persisted/progress-aware pool generation before scaling.

Metrics:

- Foundation regression: Mate_In_1 1.0, Mate_In_2 0.90.
- Edge: filtered 13/16, unfiltered 8/16, boundary 4/16.
- Fence: filtered 8/16, unfiltered 1/16, boundary 0/16.
- Safety: 0 rook losses, 0 stalemates, 0 illegal/no-move, 0 confinement
  regressions across all reported slices.
- M3 updates: edge 418,528; fence 432,784.
- M4: 0 for edge/fence.

Interpretation:

This is not a stage advance. The terminal substrate foundation is real and edge
remains stable, but fence boundary transfer is still absent. Compared with TG26g,
fence unfiltered is worse and fence boundary remains zero.

Next:

Run an external/focused audit before adding SCRIPT/LAG or broad KRK. The audit
should inspect fence boundary failures, terminal activation precision, sparse
handoff confidence, and whether the next primitive should be temporal or
compositional terminals rather than more one-step feature terminals.
