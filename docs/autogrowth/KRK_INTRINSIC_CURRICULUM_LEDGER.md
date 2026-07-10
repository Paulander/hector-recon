# KRK Intrinsic Curriculum Ledger

Date: 2026-07-10

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

1. Use actual foundation-policy rollouts on adjacent edge/decoy strata to train
   positive and negative `AVAILABLE` examples.
2. Spawn/widen a content-blind nonlinear competence gate from generic board and
   graph-response terminals. Compare it with matched random/yoked gates.
3. Freeze the gate and require starts outside its confirmed basin.
4. Collect trajectories that enter the confirmed basin after one to three White
   decisions; the transition itself supplies intrinsic positive value.
5. Train TG48 terminals with the intrinsic scalar, consolidate, and run parent,
   no-bootstrap, M3, M4, M3+M4, and child-ablation arms.
6. Only after a causal positive handoff exists should the curriculum move to the
   next outward band.

This is not exhaustive retrograde search. Positions come from bounded curriculum
generators and played trajectories; no tablebase or exact move provider selects
runtime actions.
