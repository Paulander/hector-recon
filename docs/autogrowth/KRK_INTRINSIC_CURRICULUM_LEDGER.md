# KRK Intrinsic Curriculum Ledger

Date: 2026-07-10

## Central doctrine -- do not broaden early again

The publishable target is one persistent ReCoN ecology starting with zero learned
KRK content and mastering a high-resolution outward curriculum in order. Each
mature rung must emit its own outcome-grounded successor value to train the next
rung. Geometry selects experience only; no forced-move, mate-distance,
recognizer, validator, or stage label may supply learner credit. A rung advances
only after 100% disjoint validation, prior-rung regression, safety, and efficiency
gates. This rule is repeated in root `AGENTS.md` because earlier work repeatedly
lost the chain by moving to broad edge/fence distributions too soon.

"Empty" means empty learned state, not absent embodiment. Generic board sensors,
legal action enumeration/execution, observable terminal facts, time cost, and
content-blind growth/plasticity are ReCoN's starting genome. Any KRK-specific
rule, value, triplet, or prior artifact is forbidden at initialization.

## Already executed

| Work | What was learned/evaluated | Limitation relevant now |
|---|---|---|
| TG46 Mate-in-1/Mate-in-2 | Single-graph foundation, M3/M4, causal regression | No separately calibrated `AVAILABLE` output |
| TG47 broad edge/fence | Local progress, safety, handoff diagnostics | Too broad; useful affordances did not consolidate reliably |
| TG48a edge-killbox | Narrower conversion basin | Trainer-shaped endpoint reward |
| TG48a2 same-side microstage | Local rook reposition signal | Isolated move scoring did not form a useful heldout affordance |
| TG48a2 episodes | Three White moves/six plies, 80 train starts | Reaching foundation was classified and rewarded in Python |
| v1 Phase 0, three seeds | Parent 0.156 to M3+M4 0.240 | Causal gain was veto-driven; positive affordances were neutral |
| v1 preregistered closure | No experimental arm ran | Fresh-pool requirement was infeasible; FINAL touch count remained zero |

The curriculum was therefore run in meaningful pieces. What was missing was a
persistent outward chain whose intermediate reward is emitted by the mature graph
itself.

## Required outward ladder

Use one persistent graph and schedule positions only; stage names never enter the
learner record.

1. R0 Mate-in-1: grounded directly by mate.
2. R1 Mate-in-2: reach mature R0 under every experienced reply.
3. R2 edge trapped, fence present, king close: reach R1/R0.
4. R3 same-side rook/king tempo: reach R2.
5. R4 edge trapped with king farther away: approach while retaining value.
6. R5 edge drive with established fence.
7. R6 safe fence establishment.
8. R7 broad legal nonterminal KRK.

Each rung advances only when real outcome, child-value calibration, prior-rung
replay, safety, move efficiency, and causal ablation gates pass. Curriculum
generators may use geometry to schedule experience, but geometry cannot supply
credit.

## Immediate next work package

1. Build one runner that starts a TG26p-style native graph with root/genome only
   and uses the generic intrinsic-credit kernel. Add tripwires for zero learned
   content, persistent graph identity, graph-selected actions, and reward-channel
   purity.
2. Train R0 Mate-in-1 by letting ReCoN act and observing actual checkmate or
   nonterminal/failure plus move cost. Do not call `_mate_moves` or
   `_move_reward` in the training path. Require 100% disjoint validation and
   regression before consolidation.
3. Without replacing the graph, train R1 Mate-in-2. Its first action receives
   positive bootstrap only when the resulting reply state is accepted by the
   mature R0 competence and R0 emits consolidated value. Expose varied/all legal
   replies as experience; this is local opponent robustness, not exhaustive
   endgame retrograde search.
4. Run no-bootstrap, child-value ablation, topology-frozen, and yoked-random
   growth controls. Require 100% disjoint all-reply validation, R0 retention,
   safety, and move-efficiency gates across seeds.
5. If R0/R1 passes, continue the same graph to R2 edge-killbox. Grow its nonlinear
   `AVAILABLE` topology from real positive/negative outcomes inside the ladder,
The live implementation/result boundary is maintained in
`docs/autogrowth/NATIVE_INTRINSIC_KRK_STATUS.md`.

   then repeat the causal gates at every outward rung.

The complete run contract is
`docs/autogrowth/NATIVE_FROM_SCRATCH_KRK_PLAN.md`.

This is not exhaustive retrograde search. Positions come from bounded curriculum
generators and played trajectories; no tablebase or exact move provider selects
runtime actions.
