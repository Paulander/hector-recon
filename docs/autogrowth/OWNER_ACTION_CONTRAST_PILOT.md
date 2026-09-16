# Action-conditional owner nomination: bounded pilot

Declared before play on 2026-09-16. This is a Boolean mechanism test, not chess.
The completed seeds 21–23 cohort is closed and remains the historical reference.
Its raw archive was not available locally for a no-play action-record audit.

## Single change and controls

Fresh seeds 24, 25, 26; each receives the unchanged 1,920-action schedule from
`run_owner_fresh_start.py`, in three matched arms:

- `current`: fresh owner reference with ordinary development;
- `learning-trial`: existing learning-before-assessment split law;
- `action-contrast`: same learning-before-assessment law and prospective split
  acceptance, but nomination ranks a route by the difference between the two
  executed-action residual contrasts across its two sides.

The new ranker requires at least four actual observations in all four
route-side/action cells; absent that, it abstains. It does not read the target,
correct action, unchosen outcome, row index or evaluation result. No bit is
excluded or preferred by identity. Ordinary action credit, growth, budgets,
randomized split use, readiness and acceptance are unchanged. This is a
two-action study mechanism, not yet a general multi-action law.

## Fixed resource and evidence plan

One worker, 2 GiB memory and 64 MiB file-size ceilings, 3,600 seconds
worker wall/CPU budget, numerical-library threads fixed to one. One action is
credited once; each 64-action block has submitted/credited records, a checkpoint
and 16-case greedy evaluation. Source hashes and snapshot copies are sealed
before play. Stop on the first error; preserve partial evidence, do not retry or
tune. A completed run verifies all block hashes, actual-action credit, trial
evidence, evaluations, initial state and matched exploration RNGs.

Primary descriptive comparison is paired final correct count out of 16, for
action-contrast versus both controls. Secondary observations: checkpoint
trajectories, route identities, mature/pending/pruned trials, held context
retention, physical nodes and parameters. Do not call a higher nominal final
score causal proof of route quality or chess competence. Proceed to a separate
replication only if at least two seeds improve over the learning-trial arm,
none loses more than two rows versus current, integrity checks pass, and the
change reduces irrelevant or infeasible committed partitions without exploding
allocation. Otherwise preserve and stop. No automatic extension.

## Pre-play portability amendment

The initial attempt with seeds 24/25/26 failed before source sealing, actor
construction or any environment action: macOS rejected `RLIMIT_AS`. Its empty
directory is retained as `owner-action-contrast-20260916`. No learner parameter
or observation was exposed. The separately pinned fresh attempt uses seeds
27/28/29. On macOS the existing independent RSS guard enforces 2 GiB; the
worker retains its CPU, wall and file-size limits. The guard's permitted wall
cap was extended from 620 to 3,600 seconds for this one-worker experiment.

The seeds 27/28/29 attempt stopped after seed 27's current control completed
1,920 actions. Report assembly incorrectly assumed every arm had trial-history
fields. No trial or action-contrast arm began, so this is not a paired result.
Its checkpointed data and incomplete result are retained. The report-only
error is fixed and an end-to-end sealed-block fixture for all three arm types
now passes with the original owner checks (17 tests total). A third, separately
pinned attempt uses fresh seeds 30/31/32; the learner and its parameters remain
unchanged. No prior action record is fed into any learner.
