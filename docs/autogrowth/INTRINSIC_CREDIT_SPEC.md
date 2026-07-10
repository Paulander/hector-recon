# Intrinsic Hierarchical Credit Contract

Date: 2026-07-10

## Purpose

Make a previously learned ReCoN competence a valuable successor state without a
trainer-authored intermediate reward. The host supplies only observable world
facts: terminal outcome and elapsed real/virtual work. ReCoN owns value,
eligibility, routing credit, consolidation, and competence availability.

## Root anchors

- checkmate/win: positive terminal value;
- stalemate, rook loss, illegal transition, or loss: terminal failure;
- draw/horizon: bounded non-win value when it is a real terminal, not merely a
  truncated training episode;
- each real White decision: a small metabolic/time cost;
- each virtual frame: a smaller computation cost and no terminal-grounding right.

No geometry, curriculum-stage, mate-distance, tablebase, validator verdict, or
recognizer label is a reward channel.

## Child-value handoff

A child may emit `VALUE/AVAILABLE` only when all of these hold:

1. its topology is MATURE;
2. its value is slow/consolidated rather than transient fast value;
3. its success estimate is grounded in real outcomes or an already-grounded child;
4. it has causal confirmation evidence;
5. an outcome-calibrated availability gate confirms that the current state lies
   inside its competence basin.

The upstream temporal-difference error is:

```text
world outcome - real move cost + gamma * mature child value - current value
```

Local eligibility traces distribute this error to responsible cells and existing
M3 POR/SUB edge weights. Parent responsibility is normalized and learns more
slowly by hierarchy depth/distance. Ordinary correlation cannot mature a stem
cell; paired enabled/disabled intervention remains the promotion boundary.

## Anti-self-delusion rules

- Mere firing is not competence.
- TRIAL or uncalibrated children cannot emit value.
- Grounding provenance is acyclic; A cannot learn from B if B's value ancestry
  already contains A.
- Virtual frames cannot create terminal grounding evidence.
- Negative grounded competences may emit debt under the same rules.
- A child-value ablation and a no-bootstrap control are required before claiming
  causal benefit.

## Alternating schedule

1. Structural epoch: spawn a bounded candidate set while slow weights are frozen.
2. Equilibration: freeze topology and train fast value/routing weights.
3. Consolidation: accept slow updates only after replay/validation.
4. Structural decision: paired enable/disable confirmation, then mature or prune.
5. Replay older curriculum rungs before moving outward.

## Implemented checkpoint

- `IntrinsicCreditEngine` implements grounded value, local eligibility, slower
  parent credit, metabolic costs, provenance-cycle rejection, and M3 edge updates.
- The planted anonymous three-rung benchmark passes: one terminal anchor teaches
  two successive competences without intermediate labels.
- TG46d Mate-in-1/Mate-in-2 values restore from the promoted outcome artifact.
- A content-blind sigmoid `AVAILABLE` gate is trained from policy-response outcome
  rows; on the retired TG46d regression split it confirms 77 successes with zero
  false positives.
- TG48a2 intrinsic mode uses native graph confirmation and real move cost only;
  the exact validator and authored geometry shaping are absent from reward and
  runtime selection.

## Current boundary

The first 8/4 gated TG48a2 smoke is not an advancement: parent, M3, M4, and M3+M4
are all 1.0 because every start lies inside the current gate. One positive handoff
terminal promoted, proving that positive credit now reaches M4, but it has no
causal behavioral room on this pool.

Generator-only probing found the same problem across 64/24/24 broader
edge-killbox rows and decoys: the in-domain gate accepted every start. Actual
four-ply foundation-policy outcomes are non-degenerate, however: train has
15 mate / 46 horizon / 3 rook-loss; heldout 5/17/2; regression 5/18/1; decoy
0/20/4; hard-decoy 8/4/12. These raw outcomes are the next availability-training
signal. A linear gate is insufficient on the mixed boundary; the next bounded
task is a nonlinear/self-grown competence-basin topology, not another reward
heuristic.
