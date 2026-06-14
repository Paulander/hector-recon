# Scaffold Correction Note

TG26n is a correction to the KRK curriculum direction.

The non-negotiable rule is: curriculum trains one persistent ReCoN graph through progressively harder tasks. Earlier learned topology must mature and carry forward into the next stage. Starting a new network per stage, or orchestrating a special handoff outside the graph, defeats the point of curriculum learning.

## What Was Wrong

TG26l and TG26m produced useful measurements, but they are invalid for autonomy claims.

The issue was not the Mate_In_1 move choice itself. That move was selected by learned terminal weights. The issue was control flow: the Python harness explicitly called the Mate_In_1 learner after a black reply during Mate_In_2 evaluation. That is a hardcoded handoff. For the research claim, that is cheating.

Any result that depends on:

- a separate Mate_In_1 learner object being called by the harness;
- a separate Mate_In_2 first-move learner object;
- Python deciding that a later board should now be routed to Mate_In_1;
- hand-authored stage control at runtime;

must be treated as scaffold evidence only, not autonomous ReCoN competence.

## What Remains Useful

These parts are still useful:

- the repaired curated Mate_In_1 and strict Mate_In_2 FEN bank;
- Stockfish/exact verifier checks for curriculum correctness;
- generic terminal feature extraction;
- stem-cell/TRIAL/MATURE lifecycle state;
- before/action-delta/after triplet representation;
- M3 local weighting and M4 maturation/pruning rules;
- safety/reward instrumentation;
- edge/fence failure-slice diagnostics;
- persisted artifacts and tests that expose regressions.

These are trainer/evaluator tools or graph-local mechanisms. They do not by themselves violate the purity boundary.

## What Should Be Retired Or Quarantined

These are red herrings or invalid for autonomy claims:

- separate per-stage learner objects used as runtime modules;
- direct handoff calls such as "now call Mate_In_1";
- context-gated Mate_In_2 as a separate callable helper;
- edge/fence validation that depends on the helper handoff;
- broad edge/fence scaling before single-graph Mate_In_2 is strong;
- any claim that TG26l/TG26m solved Mate_In_2 autonomously.

They may remain in the repo as diagnostic scaffolds, but artifacts and summaries must label them as scaffolded.

## Current Correct Direction

TG26n is the current baseline direction:

- one persistent graph;
- Mate_In_1 terminals/triplets mature before Mate_In_2;
- Mate_In_2 spawns before-terminal -> action-delta -> after-terminal triplets;
- the same graph chooses every white move;
- no hardcoded Mate_In_1 handoff.

TG26n currently gets Mate_In_1 `18/18` and Mate_In_2 `13/23` after normalizing terminal activation so mature Mate_In_1 fan-in cannot dominate only by terminal count. This is not good enough, but it is the right failure: it exposes missing single-graph chain activation and credit propagation instead of hiding it behind a scaffold.
