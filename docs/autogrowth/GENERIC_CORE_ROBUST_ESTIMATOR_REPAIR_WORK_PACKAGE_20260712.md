# Generic-Core Robust Estimator Repair Work Package

Date: 2026-07-12. Track: generic-core development. Status: authorized and
frozen before implementation.

## Authorization and predecessor

The PI explicitly authorized a new estimator package after the failed
`GENERIC_CORE_ROBUST_GRAPH_CHOICE_WORK_PACKAGE_20260712.md`. This is not a
rerun of that package. Its artifact and verdict remain immutable development
data.

## Hypothesis

Separating exact streaming mean statistics from the bounded conservative
lower-tail sketch will restore an identifiable mean control. With that repaired
instrument, live graph choice on fresh rare-refutation tasks will diverge as
predicted: mean value will choose the higher-expectation refutable action and
lower-tail value will choose the consistently moderate action.

## Strongest null

The repair only makes unit tests look correct; compression still contaminates
mean behavior after capacity; graph edges do not reflect the repaired estimate;
online selection bias prevents the predicted action split; lower-tail behavior
depends on hidden response labels or unequal exploration; or fresh tasks do not
replicate the isolated mechanism.

## Exactly one scientific factor

In the fresh policy comparison, only the statistic written to the action graph
changes:

- mean arm: confidence-adjusted exact streaming mean;
- lower-tail arm: confidence-adjusted bounded conservative lower-tail estimate.

All tasks, response streams, action identities, graph code, confidence,
exploration draws, capacity, episode counts, and compute budgets are matched.

## Frozen estimator contract

Each cell state must keep:

- total observation count;
- exact streaming return sum, independent of retained samples;
- at most 256 retained values for the lower-tail sketch.

`mean` and `mean_score` must derive only from exact sum/count.
`lower_quantile`, minimum, maximum, and `robust_score` derive from the
bounded retained sketch. Confidence derives from total observation count.

The lower-tail buffer is explicitly a conservative lifetime exception sketch,
not an unbiased reservoir and not an adaptive recent-window quantile. This
package does not claim distribution-shift adaptation.

## Mandatory calibration before runner commit

Tests must certify without using frozen policy seeds:

1. constant streams at 256, 1,024, and 4,096 observations;
2. exact 7 × +1 / 1 × -1 streams have mean +0.75 at all three counts;
3. mixed deterministic scalar streams match `math.fsum(values) / len(values)`;
4. retained count never exceeds 256;
5. the rare -1 lower tail survives repeated compression;
6. snapshot records exact return sum separately from retained returns;
7. graph edge and selected memory statistic remain equal.

Any calibration failure is an instrument failure and prevents the policy run.

## Fresh task distribution and budget

- 20 seeds 20260901–20260920;
- randomized identities for two legal actions;
- consistent action return +0.4;
- refutable action has seven +1.0 and one -1.0 response in each independently
  shuffled block of eight episodes;
- 2,048 online training episodes with epsilon-greedy exploration 0.15;
- 512 untouched greedy evaluation episodes from fresh shuffled blocks;
- no forced exposure, response label, replay intervention, or shaped reward.

## Measurements and gates

Development support requires every gate:

1. mean chooses the refutable action on at least 19/20 tasks;
2. lower-tail chooses the consistent action on at least 19/20 tasks;
3. lower-tail evaluation minimum exceeds mean minimum on at least 19/20 tasks;
4. refutable exact streaming means lie within 0.10 of +0.75 on at least 19/20
   mean-arm tasks;
5. graph-score/memory-estimate mismatches are zero;
6. episode, action, RNG-call, capacity, and compute budgets match on 20/20.

Report per-action total count, exact sum/mean, retained count/distribution,
lower-tail estimate, confidence, both graph scores, selection counts, evaluation
returns, and all source/implementation/runner/row hashes.

## Stop rule

Commit and push this contract before code. Commit and push calibrated
implementation and runner before generating fresh tasks. Execute once. Any
failed gate closes the package without automatic repair, additional seeds, or
key-door integration. The builder is not the independent adjudicator.
