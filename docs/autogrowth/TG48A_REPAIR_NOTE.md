# TG48a Repair Note

Date: 2026-07-01

## Scope

TG48a infrastructure passed but did not behaviorally advance. This note explains the failure and the repair smoke at:

- `reports/autogrowth/clean_slate_krk/tg48a_edge_killbox_repair/krk_tg48a_edge_killbox_repair.json`
- `reports/autogrowth/clean_slate_krk/tg48a_edge_killbox_repair/pools/tg48a_repair_board_samples.md`

TG46d stayed frozen. No runtime tablebase/DTM/Stockfish provider, ActionRanker runtime, Python final selector, direct provider override, hardcoded FEN/move repair, or learner-visible stage/basin/curriculum/tempo/opposition/quality/reply-policy label was introduced.

## Original TG48a Failure

Original TG48a promoted only 4 M4 terminals, all vetoes and 0 affordances. The promoted terminals were generic negative/safety atoms; positive atoms had broad activation and failed decoy/unsafe audit. The original scoring also allowed generic local progress (`fence_preserved` plus `black_mobility_reduced`) to count as success even when `graph_positive_false_basin` was true. That made veto/suppression look better than it was.

The original positive affordance candidates failed mainly because their terminal keys were too atomic:

- action delta alone was too broad;
- before/after geometry atoms activated across both good and false-basin moves;
- positive support was below threshold for many keys;
- decoy/hard-decoy and unsafe activations vetoed broad positive keys.

## Repair Applied

The repair made four local changes:

- strict success: graph-positive validator-false basin and partial-only near-basin no longer count as success;
- compound generic geometry terminals: action + before geometry + after geometry + safety/progress deltas can now become positive affordance or veto terminals;
- decoy-debt training: decoy and hard-decoy rows contribute negative trainer-side credit to graph-mediated terminal weights;
- true M3+M4 combination: mature M4 remains full strength while residual non-promoted M3 trial weights are damped, so fast plasticity does not swamp consolidation.

These are still graph-mediated terminal weights. The trainer uses family/decoy labels only for schedule, credit, and diagnostics.

## Repair Smoke Result

Repair smoke result is an infrastructure pass only:

- parent-only success: `0.1667`
- M3 trial success: `0.0`
- M4 success: `0.1667`
- true M3+M4 success: `0.125`
- M4 promoted terminals: `256`
- M4 promoted affordances: `7`
- M4 promoted vetoes: `249`
- positive affordance candidates/rejected: `44 / 37`
- hard-decoy false handoff: `7`
- graph-positive false basin count: `20`
- rook blunder/stalemate/illegal/confinement regression: `0 / 0 / 0 / 0`

This is not behavioral advancement. Positive affordances now exist, but they do not improve heldout over parent-only, same-side rook-danger regresses to `0.0`, graph-positive false basins increased, and hard-decoy false handoffs increased.

## Promoted Positive Affordances

Promoted positive affordances were all generic compound rook/action geometry terminals:

- `compound_geometry:piece=4|fd=1|rd=0|b_same=0|b_opp=1|a_same=0|a_opp=1|conf=improved|mob=same|support=same`
- `compound_support_action:piece=4|fd_mag=1|rd_mag=0|b_support=1|a_support=1|a_rook_safe=1|conf=improved|mob=same`
- `compound_geometry:piece=4|fd=1|rd=0|b_same=0|b_opp=1|a_same=0|a_opp=0|conf=improved|mob=same|support=same`
- `compound_support_action:piece=4|fd_mag=3|rd_mag=0|b_support=1|a_support=1|a_rook_safe=1|conf=improved|mob=same`
- `compound_geometry:piece=4|fd=0|rd=1|b_same=0|b_opp=1|a_same=0|a_opp=1|conf=improved|mob=same|support=same`
- `compound_geometry:piece=4|fd=1|rd=0|b_same=1|b_opp=0|a_same=0|a_opp=1|conf=improved|mob=regressed|support=same`
- `compound_support_action:piece=4|fd_mag=3|rd_mag=0|b_support=1|a_support=1|a_rook_safe=1|conf=improved|mob=regressed`

Positive rejection reasons:

- insufficient positive support: `28`
- insufficient validated or graded progress activation: `26`
- precision below affordance threshold: `25`
- unsafe activation: `3`
- decoy false-handoff activation: `2`

## Family Failures

M4 family success rates:

- opposed-side: parent `0.2`, M4 `0.2`
- same-side rook-danger: parent `0.1667`, M4 `0.0`
- mixed: parent `0.125`, M4 `0.25`

The repair overfits opposed/mixed rook-motion geometry and still does not solve same-side rook-danger. Same-side positions need a more specific safety/escape distinction before positive promotion.

## Diagnosis

Reward is no longer simply too sparse: the repair can produce positive affordance promotion. Promotion criteria are not too strict in general; they allowed 7 affordances. The remaining failure is that promoted positives are not sufficiently discriminative against validator-false graph-positive basins and hard decoys.

The generator is also too mixed for the current learner: some "hard decoy" positions are validator-confirmed foundation entries after the selected move, so the diagnostic category is catching actual near-foundation geometry as false handoff. This does not mean the learner can use them safely; it means the decoy generator needs a stricter oracle-negative invariant if hard-decoy false handoff is used as a pass gate.

M3+M4 originally underperformed because unpromoted M3 trial weights were combined at full strength with mature M4. The repair damped residual trial weights; true M3+M4 improved from `0.0` to `0.125`, but remains below M4-only `0.1667`.

## Board Samples

Full board samples are in `reports/autogrowth/clean_slate_krk/tg48a_edge_killbox_repair/pools/tg48a_repair_board_samples.md`.

### Sample 1

- Trace: `TG48a_M3_trial_only`, index `0`
- FEN: `8/6R1/2K5/k7/8/8/8/8 w - - 0 1`
- Pieces: `ka5, Kc6, Rg7`
- Family: `edge_killbox_mixed`; selected `c6d7`; buckets `graph_positive_false_basin`

```text
. . . . . . . .
. . . . . . R .
. . K . . . . .
k . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### Sample 2

- Trace: `TG48a_M3_trial_only`, index `1`
- FEN: `8/8/8/7K/8/7k/8/5R2 w - - 0 1`
- Pieces: `Rf1, kh3, Kh5`
- Family: `edge_killbox_same_side_rook_danger`; selected `h5g6`; buckets `graph_positive_false_basin`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . R . .
```

### Sample 3

- Trace: `TG48a_M3_trial_only`, index `2`
- FEN: `1k6/3K4/4R3/8/8/8/8/8 w - - 0 1`
- Pieces: `Re6, Kd7, kb8`
- Family: `edge_killbox_opposed_side`; selected `d7e8`; buckets `graph_positive_false_basin`

```text
. k . . . . . .
. . . K . . . .
. . . . R . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### Sample 4

- Trace: `TG48a_M3_trial_only`, index `3`
- FEN: `2k5/4K3/8/R7/8/8/8/8 w - - 0 1`
- Pieces: `Ra5, Ke7, kc8`
- Family: `edge_killbox_same_side_rook_danger`; selected `e7f6`; buckets `graph_positive_false_basin`

```text
. . k . . . . .
. . . . K . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### Sample 5

- Trace: `TG48a_M3_trial_only`, index `4`
- FEN: `1k6/3R4/K7/8/8/8/8/8 w - - 0 1`
- Pieces: `Ka6, Rd7, kb8`
- Family: `edge_killbox_mixed`; selected `d7c7`; buckets `rook_blunder, graph_positive_false_basin, partial_only_near_basin`

```text
. k . . . . . .
. . . R . . . .
K . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### Sample 6

- Trace: `TG48a_M3_trial_only`, index `5`
- FEN: `8/8/k7/8/1K6/8/3R4/8 w - - 0 1`
- Pieces: `Rd2, Kb4, ka6`
- Family: `edge_killbox_opposed_side`; selected `b4c3`; buckets `graph_positive_false_basin`

```text
. . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
. K . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
```

### Sample 7

- Trace: `TG48a_M3_trial_only`, index `6`
- FEN: `k7/2K5/1R6/8/8/8/8/8 w - - 0 1`
- Pieces: `Rb6, Kc7, ka8`
- Family: `edge_killbox_mixed`; selected `b6b7`; buckets `stalemate`

```text
k . . . . . . .
. . K . . . . .
. R . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### Sample 8

- Trace: `TG48a_M3_trial_only`, index `7`
- FEN: `8/8/1R6/8/K7/8/k7/8 w - - 0 1`
- Pieces: `ka2, Ka4, Rb6`
- Family: `edge_killbox_opposed_side`; selected `a4b5`; buckets `graph_positive_false_basin`

```text
. . . . . . . .
. . . . . . . .
. R . . . . . .
. . . . . . . .
K . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
```

### Sample 9

- Trace: `TG48a_M3_trial_only`, index `8`
- FEN: `2K1k3/8/8/8/8/6R1/8/8 w - - 0 1`
- Pieces: `Rg3, Kc8, ke8`
- Family: `edge_killbox_same_side_rook_danger`; selected `c8b7`; buckets `graph_positive_false_basin`

```text
. . K . k . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . R .
. . . . . . . .
. . . . . . . .
```

### Sample 10

- Trace: `TG48a_M3_trial_only`, index `9`
- FEN: `2R5/8/8/8/6K1/8/7k/8 w - - 0 1`
- Pieces: `kh2, Kg4, Rc8`
- Family: `edge_killbox_opposed_side`; selected `g4f5`; buckets `graph_positive_false_basin`

```text
. . R . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . K .
. . . . . . . .
. . . . . . . k
. . . . . . . .
```

## Next Action

Do not scale TG48a yet. The next repair should separate two blockers:

1. hard-decoy generator/audit validity: determine whether the 7 hard-decoy "false" handoffs are truly false or are valid near-foundation entries mislabeled by the decoy generator;
2. positive affordance precision: add a stricter heldout/decoy guard for promoted affordances and same-side rook-danger before accepting M4 promotion as behavioral progress.
