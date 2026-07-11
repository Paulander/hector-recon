# Generic-Core Delayed Action Policy Work Package

Date: 2026-07-12. Track: generic-core development. Status: frozen before code.

## Hypothesis

A policy whose exact action score is a ReCoN graph output can learn anonymous
delayed XOR action tasks from terminal scalar valence when actual decision
activation traces persist across the episode. Its behavior will causally depend
on residual-grown AND subgraphs. Clearing the trace at every intervening step
will prevent that learning under an otherwise identical ecology.

## Strongest null

Any success is due to host-supplied correct actions, immediate or shaped reward,
target-aware features, direct Python scoring disconnected from the graph,
evaluation reuse, primitive marginal shortcuts, trial-topology leakage, or a
control that receives less exploration/compute rather than less temporal
responsibility.

## Learner/laboratory boundary

The learner receives only:

- anonymous active terminal IDs;
- anonymous legal action IDs;
- its own graph action scores and selected activation trace;
- elapsed real-step events;
- one terminal scalar valence, -1 or +1.

The learner does not receive XOR, signal/nuisance identity, correct action,
target inversion, episode answer, task seed, curriculum/stage labels, or
evaluation results. The laboratory creates randomized tasks and reports hidden
identity only after the one frozen run.

## Exactly one factor

- persistent arm: the selected action graph and its active terminal/composite
  responsibility survive the four real intervening steps and receive discounted
  terminal credit;
- per-step-reset arm: the identical trace is cleared at every intervening step.

Both arms see the same observations, legal actions, epsilon draws, action
budget, terminal outcomes for the actions they independently choose, topology
law, learning rates, candidate budget, and compute budget.

## Frozen tasks and budget

- 20 task seeds 20260801–20260820;
- randomized identities for 12 literal terminals and two actions;
- two hidden signal bits, four nuisance bits;
- independent Bernoulli probabilities drawn from {0.25, 0.35, 0.65, 0.75};
- correct action is randomized/inverted XOR of the two hidden signal bits;
- 4,096 online training episodes and 512 untouched greedy evaluation episodes;
- four anonymous real transition events between choice and terminal valence;
- no intermediate reward, successor label, replay label, or host action target.

## Frozen learner

- one graph-backed return channel per legal action;
- graph score equals a bias-terminal edge plus weighted active primitive
  terminals plus weighted mature AND-script activations, clipped to [-1, 1];
- exact graph score used for choice must equal the prediction updated by credit;
- epsilon-greedy exploration 0.15 during training, greedy evaluation;
- terminal return discount 0.97 per elapsed step;
- the frozen online-composition configuration from commit `9f601cd`;
- residual-ranked proposals only; trial scripts are materialized but are not
  linked into the action-score root until mature;
- pruned scripts are removed; maximum four candidates per action;
- no recursive composition in this package.

## Measurements

- final greedy accuracy by arm and task;
- full-graph versus mature-composite-edge-disabled accuracy on the identical
  untouched evaluation rows;
- action-selection counts and terminal returns;
- graph-score/learner-prediction parity mismatches;
- proposal, trial, mature, and pruned counts;
- mature hidden signal-pair count as a laboratory-only diagnostic;
- trace length at terminal and credited decision count;
- task, implementation, runner, and row hashes.

## Predicted outcome and gates

Development support requires every gate:

1. persistent full-graph accuracy exceeds reset accuracy on at least 16/20 tasks;
2. persistent median full-graph accuracy is at least 0.90;
3. median persistent full-minus-composite-disabled accuracy is at least 0.20;
4. at least 16/20 persistent tasks mature a hidden signal-pair script;
5. graph-score/updated-prediction mismatches and trial score influence are zero;
6. both arms receive identical episode, legal-action, epsilon, and candidate
   budgets.

## Kill and stopping rule

Instrument/lifecycle tests may not generate or inspect the frozen task seeds.
Commit and push the implementation and runner before the sole run. A failed
gate ends this package; do not tune, rescue, or rerun it. The builder emits raw
measurements and cannot claim independent confirmation.
