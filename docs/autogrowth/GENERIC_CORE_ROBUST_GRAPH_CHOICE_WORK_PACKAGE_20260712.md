# Generic-Core Robust Graph Choice Work Package

Date: 2026-07-12. Track: generic-core development. Status: frozen before code.

## Hypothesis

When the return statistic stored on an anonymous action's graph edge is also the
exact score used for selection, lower-tail empirical value will learn to avoid a
usually rewarding action with a rare catastrophic environment response, while
mean empirical value will prefer it over a consistently moderate action.

## Strongest null

The isolated return-memory result does not change live graph behavior; a helper
selects outside the graph; the catastrophe is specially labeled; host scheduling
guarantees the desired action; lower-tail receives more exploration or different
responses; or confidence/prior differences rather than the declared statistic
cause the result.

## Learner/laboratory boundary

The learner receives anonymous legal action IDs, its graph scores, the selected
action's scalar observed return, and no response label. It does not receive
safe/refutable identity, catastrophe identity, response type, expected value,
task seed, evaluation result, or correct-action label.

## Exactly one factor

- mean arm writes the confidence-adjusted empirical mean to each action graph;
- lower-tail arm writes the confidence-adjusted empirical 0.10 quantile.

Both use the same graph, memory capacity, confidence prior, exploration draws,
episode count, legal actions, environment response stream, and compute budget.

## Frozen tasks and budget

- 20 task seeds 20260821–20260840;
- randomized identities for two actions;
- consistent action return +0.4;
- refutable action has seven +1.0 responses and one -1.0 response in each
  independently shuffled block of eight environment episodes;
- 2,048 online training episodes with epsilon-greedy exploration 0.15;
- 512 untouched greedy evaluation episodes from fresh shuffled response blocks;
- no shaped reward, response label, forced exposure, or replay intervention.

## Frozen learner

- `RobustReturnConfig(capacity=256, lower_quantile=0.10,
  min_observations=8, confidence_prior=3.0)`;
- one bias terminal and weighted SUB edge per anonymous action graph;
- edge weight is exactly the selected memory estimate (`mean_score` or
  `robust_score`);
- graph weighted sum is the action score used for choice;
- only the selected action's distribution is updated;
- the action score is resynchronized immediately after observation;
- constant RNG-call schedule keeps exploration draws matched across arms.

## Measurements

- final selected-action frequency by arm;
- evaluation mean, minimum, and refutation count;
- graph-score/memory-estimate parity mismatches;
- per-action observation count, retained distribution, confidence, mean,
  quantile, and both scores;
- train/evaluation response, implementation, runner, and source hashes;
- matched episode/action/exploration budgets.

## Predicted outcome and gates

Development support requires every gate:

1. lower-tail chooses the consistent action on at least 19/20 tasks;
2. mean chooses the refutable action on at least 19/20 tasks;
3. lower-tail evaluation minimum return exceeds mean minimum return on at least
   19/20 tasks;
4. graph-score/memory-estimate mismatches are zero;
5. episode, legal-action, RNG-call, memory, and compute budgets match on 20/20.

## Kill and stopping rule

Lifecycle tests may use only synthetic fixed return lists, not frozen task
seeds. Commit and push implementation and runner before the sole run. Any failed
gate ends the package without tuning or rerun. Builder-run measurements are
development evidence, never independent confirmation.
