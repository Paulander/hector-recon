# Generic-Core Online Composition Work Package

Date: 2026-07-12. Track: generic-core development. Status: frozen before code.

## Hypothesis

A task-agnostic learner-local residual rule can nominate a co-active atom pair,
train it in shadow, and retain it only when it reduces future prediction error
enough to pay a fixed resource cost. On anonymous online XOR streams this rule
will produce causally useful topology more reliably than a support/budget-matched
random proposer.

## Strongest null

Any apparent success comes from friendly atom frequencies, target-aware operator
enumeration, reuse of one dataset, trial candidates affecting the baseline,
post-result tuning, or random proposals doing equally well. If ranked growth does
not beat matched random on every preregistered aggregate gate, the mechanism is
not established.

## Learner/laboratory boundary

The learner may see only:

- anonymous active atom IDs;
- its own scalar prediction and residual;
- scalar observed outcome;
- candidate activation, size, age, and future paired prediction error.

The learner may not see signal/nuisance identity, XOR, operator family, task ID,
correct feature pair, row labels, or evaluation results. The laboratory may
randomize tasks and report which hidden atoms generated them only after the run.

## Exactly one factor

Proposal selection changes:

- ranked arm: pair score is support-weighted contrast between pair-local residual
  mean and global residual mean;
- matched-random arm: seeded random choice among pairs meeting the identical
  support, shape, budget, and exclusion constraints.

All other code, stream order, learning rates, candidate lifecycle, resource cost,
and compute budget are shared.

## Frozen task distribution

- 20 independent task instances, seeds 20260712–20260731;
- randomized atom identities and target inversion;
- independent Bernoulli signal probabilities drawn from {0.25, 0.35, 0.65,
  0.75};
- four nuisance bits with independently drawn probabilities from the same set;
- one active literal per bit, so marginal-frequency shortcuts vary by task;
- 2,048 online training observations and 512 untouched evaluation observations;
- terminal scalar target only: -1 or +1.

## Frozen learner

- additive primitive baseline with bias;
- primitive and candidate learning rate 0.08 with predictions clipped to [-1, 1];
- pair proposals every 128 observations after minimum support 16;
- maximum four candidates;
- trial candidates train in shadow and cannot alter baseline prediction;
- 32 future active confirmations after an eight-activation burn-in;
- paired squared-error improvement must exceed 0.01 plus resource cost 0.002;
- otherwise candidate is pruned; neutral trials expire by age 512;
- mature candidates may affect prediction; composites do not recursively compose
  in this first bounded factor.

## Measurements

- pre-growth and final evaluation mean squared error;
- per-candidate members, support, activation count, shadow weight, paired enabled
  and disabled error, resource cost, and lifecycle decision;
- mature candidate count and size;
- whether any mature candidate contains both hidden signal literals (laboratory
  diagnostic only);
- ranked versus matched-random paired task-level error difference;
- raw per-instance artifact with source and row hashes.

## Predicted outcome and gates

Ranked growth is supported only if all hold:

1. ranked final MSE is lower than matched random on at least 16/20 paired tasks;
2. ranked median paired improvement is positive;
3. at least 16/20 ranked tasks mature a hidden signal-pair candidate;
4. no trial candidate affects evaluation before maturity;
5. matched arms have identical proposal/candidate budgets.

## Frozen stopping rule

Implement the learner once, exercise only instrument/lifecycle tests that do not
preview the 20 frozen tasks, and execute the frozen seed range once. Preserve and
report a negative result without rescue tuning. The builder/runner records raw
gate measurements but is not the independent adjudicator.
